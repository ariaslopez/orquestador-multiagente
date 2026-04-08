"""MCP Adaptador — Semgrep.

Analisis estatico de seguridad en codigo fuente.
Usado por SecurityAgent y QA agents para detectar vulnerabilidades
OWASP Top 10, inyecciones SQL, XSS, secrets hardcoded, etc.

Herramientas disponibles:
  scan_code(code, lang='python', ruleset='auto')
    -> {findings: [{rule, severity, message, line}], summary}
  scan_repo(repo_path, config='p/default')
    -> {findings: [...], stats: {total, critical, high, medium, low}}
  get_rules(category='security')
    -> [{id, name, severity, description}]

Semgrep OSS no requiere API key (modo local).
Semgrep Cloud requiere SEMGREP_APP_TOKEN.
"""
from __future__ import annotations
import os
import json
import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class SemgrepMCPAdapter:
    async def call(self, tool: str, params: Dict[str, Any]) -> Any:
        if tool == "scan_code":  return await self._scan_code(**params)
        if tool == "scan_repo":  return await self._scan_repo(**params)
        if tool == "get_rules":  return await self._get_rules(**params)
        raise ValueError(f"Semgrep: tool '{tool}' desconocida")

    async def _scan_code(self, code: str, lang: str = "python", ruleset: str = "auto") -> Dict:
        """Escanea un fragmento de codigo en memoria."""
        # Escribe el codigo a un archivo temporal y corre semgrep
        suffix_map = {"python": ".py", "javascript": ".js", "typescript": ".ts",
                      "java": ".java", "go": ".go", "ruby": ".rb", "php": ".php"}
        suffix = suffix_map.get(lang, ".py")

        with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp_path = f.name

        try:
            result = await self._run_semgrep(tmp_path, config="p/default")
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        return result

    async def _scan_repo(self, repo_path: str, config: str = "p/default") -> Dict:
        """Escanea un repositorio local completo."""
        if not Path(repo_path).exists():
            return {"error": f"Ruta '{repo_path}' no existe", "findings": []}
        return await self._run_semgrep(repo_path, config=config)

    async def _run_semgrep(self, target: str, config: str = "p/default") -> Dict:
        """Ejecuta semgrep CLI y parsea el output JSON."""
        cmd = ["semgrep", "--json", f"--config={config}", target]
        token = os.getenv("SEMGREP_APP_TOKEN", "")
        env = {**os.environ}
        if token:
            env["SEMGREP_APP_TOKEN"] = token

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
            data = json.loads(stdout.decode("utf-8", errors="ignore"))
        except FileNotFoundError:
            return {"error": "semgrep no instalado. Ejecuta: pip install semgrep", "findings": []}
        except asyncio.TimeoutError:
            return {"error": "semgrep timeout (120s)", "findings": []}
        except json.JSONDecodeError:
            return {"error": "semgrep output no parseable", "findings": []}

        findings = []
        for r in data.get("results", []):
            findings.append({
                "rule":     r["check_id"],
                "severity": r["extra"].get("severity", "INFO"),
                "message":  r["extra"].get("message", ""),
                "path":     r["path"],
                "line":     r["start"]["line"],
            })

        stats = {
            "total":    len(findings),
            "critical": sum(1 for f in findings if f["severity"] == "ERROR"),
            "high":     sum(1 for f in findings if f["severity"] == "WARNING"),
            "medium":   sum(1 for f in findings if f["severity"] == "INFO"),
            "low":      sum(1 for f in findings if f["severity"] not in ("ERROR","WARNING","INFO")),
        }
        return {"findings": findings, "stats": stats}

    async def _get_rules(self, category: str = "security") -> List[Dict]:
        return [{"id": f"p/{category}", "name": f"Semgrep {category.title()} Ruleset",
                 "severity": "varies", "description": f"Reglas de {category} de Semgrep Registry"}]


def get_adapter() -> SemgrepMCPAdapter:
    return SemgrepMCPAdapter()
