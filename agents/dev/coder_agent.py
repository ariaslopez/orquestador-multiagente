"""
CoderAgent v2 — Genera el código de cada archivo del plan.

Estrategia:
  1. context7 MCP disponible  → resuelve IDs de librerías + inyecta doc real en el prompt
  2. LLM genera el código completo y funcional (siempre, independiente del MCP)
  3. github_mcp disponible + ctx.target_repo definido → push de archivos al repo destino
     Fallback: escribe en disco local (comportamiento anterior)

Inputs esperados en ctx:
  - ctx.data['plan']         : {project_name, files[], stack[], run_command, ...}
  - ctx.data['subtasks']     : lista de subtareas del PlannerAgent (opcional)
  - ctx.output_path          : ruta base local (default: './output')
  - ctx.target_repo          : 'owner/repo' para push vía github_mcp (opcional)
  - ctx.target_branch        : rama destino (default: 'main')

Outputs en ctx:
  - ctx.data['generated_files']  : {path: code_str, ...}
  - ctx.data['pushed_files']     : [path, ...] si se usó github_mcp
  - ctx.data['context7_used']    : bool
  - ctx.data['github_mcp_used']  : bool
  - ctx.output_path              : ruta local del proyecto generado
"""
from __future__ import annotations
import json
import re
import logging
from pathlib import Path
from core.base_agent import BaseAgent
from core.context import AgentContext

logger = logging.getLogger(__name__)


class CoderAgent(BaseAgent):
    name = "CoderAgent"
    description = (
        "Genera el contenido real de cada archivo del proyecto. "
        "Usa context7 para documentación actualizada y github_mcp para push directo al repo."
    )

    async def run(self, ctx: AgentContext) -> AgentContext:
        self.log(ctx, "[Coder] Iniciando generación de código...")

        plan = ctx.get_data("plan") or {}
        files = plan.get("files", [])
        if not files:
            self.log(ctx, "[Coder] No hay archivos en el plan.")
            return ctx

        stack: list[str] = plan.get("stack", [])
        project_name: str = plan.get("project_name", "project")
        base_output = Path(ctx.output_path or "./output")
        project_dir = base_output / project_name

        # --- Paso 1: Resolver documentación de librerías con context7 ---
        stack_docs: dict[str, str] = {}
        context7_used = False

        if ctx.is_mcp_available("context7") and stack:
            for lib in stack:
                try:
                    # Primero resolvemos el ID de la librería en context7
                    resolve_result = await ctx.mcp_call(
                        "context7",
                        "resolve-library-id",
                        {"libraryName": lib},
                    )
                    lib_id = (
                        resolve_result.get("libraryId")
                        or (resolve_result.get("results") or [{}])[0].get("id")
                    )
                    if not lib_id:
                        logger.debug("[Coder] context7: no ID para '%s', saltando", lib)
                        continue

                    # Luego obtenemos el snippet de documentación relevante
                    doc_result = await ctx.mcp_call(
                        "context7",
                        "get-library-docs",
                        {
                            "context7CompatibleLibraryID": lib_id,
                            "topic": plan.get("description", ""),
                            "tokens": 4000,
                        },
                    )
                    doc_text = doc_result.get("text") or doc_result.get("content") or ""
                    if doc_text:
                        stack_docs[lib] = doc_text[:3000]  # Cap para no inflar el prompt
                        context7_used = True
                        self.log(ctx, f"[Coder] context7: doc de '{lib}' cargada ({len(doc_text)} chars)")

                except Exception as exc:
                    logger.warning("[Coder] context7 falló para '%s': %s — continuando sin doc", lib, exc)
        else:
            logger.debug("[Coder] context7 no disponible o stack vacío — generando con LLM puro")

        # --- Paso 2: Generar código por archivo con LLM ---
        generated_files: dict[str, str] = {}
        for file_info in sorted(files, key=lambda x: x.get("priority", 99)):
            file_path: str = file_info["path"]
            self.log(ctx, f"[Coder] Generando {file_path}...")

            # Construir bloque de documentación si context7 entrego algoó
            doc_block = ""
            relevant_libs = [
                lib for lib in stack_docs
                if lib.lower() in file_path.lower()
                   or lib.lower() in file_info.get("description", "").lower()
                   or lib.lower() in plan.get("description", "").lower()
            ]
            if not relevant_libs:
                relevant_libs = list(stack_docs.keys())[:2]  # fallback: primeras 2 libs
            if relevant_libs:
                doc_block = "\n\nDOCUMENTACIÓN OFICIAL DE LIBRERÍAS (context7):\n"
                for lib in relevant_libs:
                    doc_block += f"\n--- {lib} ---\n{stack_docs[lib]}\n"

            prompt = f"""Eres un desarrollador senior experto en {', '.join(stack) or 'Python'}.
Genera el contenido COMPLETO y FUNCIONAL del archivo `{file_path}`.

Proyecto: {plan.get('description', ctx.user_input)}
Stack: {', '.join(stack)}
Descripción del archivo: {file_info.get('description', '')}
{doc_block}
Reglas estrictas:
- Código completo, listo para producción, sin TODOs sin implementar
- Manejo explícito de errores (no swallow exceptions)
- Variables y funciones descriptivas, sin abreviaciones crípticas
- Comentarios solo cuando el código no es autoexplicativo
- Solo el código del archivo, sin explicaciones adicionales fuera de él"""

            code = await self.llm(ctx, prompt, temperature=0.2)
            code = self._clean_code(code)
            generated_files[file_path] = code
            self.log(ctx, f"[Coder]   {file_path} listo ({len(code)} chars)")

        ctx.set_data("generated_files", generated_files)
        ctx.set_data("project_dir", str(project_dir))
        ctx.set_data("context7_used", context7_used)
        ctx.output_path = str(project_dir)

        # --- Paso 3: Push a GitHub si target_repo está definido y github_mcp disponible ---
        pushed_files: list[str] = []
        github_mcp_used = False
        target_repo: str = getattr(ctx, "target_repo", None) or ctx.get_data("target_repo") or ""
        target_branch: str = getattr(ctx, "target_branch", None) or ctx.get_data("target_branch") or "main"

        if target_repo and ctx.is_mcp_available("github_mcp"):
            owner, _, repo = target_repo.partition("/")
            if owner and repo:
                self.log(ctx, f"[Coder] github_mcp: subiendo {len(generated_files)} archivos a {target_repo}@{target_branch}...")
                files_payload = [
                    {"path": path, "content": content}
                    for path, content in generated_files.items()
                ]
                try:
                    await ctx.mcp_call(
                        "github_mcp",
                        "push_files",
                        {
                            "owner": owner,
                            "repo": repo,
                            "branch": target_branch,
                            "files": files_payload,
                            "message": f"feat: {plan.get('description', project_name)} — generado por CoderAgent v2",
                        },
                    )
                    pushed_files = list(generated_files.keys())
                    github_mcp_used = True
                    self.log(ctx, f"[Coder] github_mcp: ✓ {len(pushed_files)} archivos subidos a {target_repo}")
                except Exception as exc:
                    logger.warning(
                        "[Coder] github_mcp falló al hacer push: %s — archivos disponibles solo localmente", exc
                    )
        else:
            if target_repo:
                logger.debug("[Coder] github_mcp no disponible — push omitido")

        ctx.set_data("pushed_files", pushed_files)
        ctx.set_data("github_mcp_used", github_mcp_used)

        self.log(
            ctx,
            f"[Coder] ✓ {len(generated_files)} archivos generados → {project_dir} "
            f"| context7={'sí' if context7_used else 'no'} "
            f"| github_mcp={'sí (' + str(len(pushed_files)) + ' pushed)' if github_mcp_used else 'no'}",
        )
        return ctx

    def _clean_code(self, text: str) -> str:
        match = re.search(r"```(?:\w+)?\n([\s\S]+?)```", text)
        if match:
            return match.group(1).strip()
        return text.strip()
