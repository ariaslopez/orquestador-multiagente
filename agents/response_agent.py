"""Agente que sintetiza todos los resultados en una respuesta final."""
from core.base_agent import BaseAgent
from core.context import AgentContext


class ResponseAgent(BaseAgent):
    """
    Agente final: consolida el output de todos los agentes anteriores
    y genera la respuesta al usuario.
    
    En modo offline: usa plantillas y extracción directa de docs.
    Con LLM local (Ollama): puede generar respuesta natural.
    """

    def __init__(self, use_llm: bool = False, llm_model: str = "llama3"):
        super().__init__(
            name="ResponseAgent",
            description="Sintetiza la respuesta final para el usuario"
        )
        self.use_llm = use_llm
        self.llm_model = llm_model

    def run(self, context: AgentContext) -> AgentContext:
        if self.use_llm:
            context.final_response = self._generate_with_llm(context)
        else:
            context.final_response = self._generate_template(context)
        return context

    def _generate_template(self, context: AgentContext) -> str:
        """Genera respuesta estructurada sin LLM."""
        parts = []

        parts.append(f"📋 **Consulta:** {context.user_query}")
        parts.append(f"🔍 **Lenguaje detectado:** {context.detected_language or 'general'}")
        parts.append("")

        if context.relevant_docs:
            parts.append(f"📚 **Documentación encontrada ({len(context.relevant_docs)} archivos):**")
            for doc in context.relevant_docs:
                source_name = doc["source"].split("/")[-1]
                preview = doc["content"][:500].strip()
                parts.append(f"\n--- {source_name} ---\n{preview}...")
        else:
            parts.append("⚠️ No se encontró documentación relevante para esta consulta.")
            parts.append("   Agrega archivos .md en knowledge_base/docs/<lenguaje>/")

        if context.code_analysis:
            a = context.code_analysis
            parts.append(f"\n🔬 **Análisis de código:**")
            parts.append(f"   Archivos: {', '.join(a['files_analyzed'])}")
            parts.append(f"   Total líneas: {a['total_lines']}")
            if a["functions"]:
                parts.append(f"   Funciones: {', '.join(a['functions'])}")
            if a["classes"]:
                parts.append(f"   Clases: {', '.join(a['classes'])}")
            if a["issues"]:
                parts.append(f"   ⚠️ Problemas: {'; '.join(a['issues'])}")

        if context.has_errors():
            parts.append(f"\n❌ **Errores durante ejecución:** {context.errors}")

        return "\n".join(parts)

    def _generate_with_llm(self, context: AgentContext) -> str:
        """Genera respuesta usando Ollama (LLM local)."""
        try:
            import ollama
            doc_content = "\n\n".join(
                f"[{d['source']}]\n{d['content'][:1000]}"
                for d in context.relevant_docs
            )
            prompt = (
                f"Basándote en la siguiente documentación local, responde la consulta del usuario.\n\n"
                f"Documentación:\n{doc_content}\n\n"
                f"Consulta: {context.user_query}\n\n"
                f"Responde de forma clara y concisa en el mismo idioma de la consulta."
            )
            response = ollama.chat(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response["message"]["content"]
        except ImportError:
            return self._generate_template(context) + "\n\n⚠️ Ollama no instalado. Usando respuesta estructurada."
        except Exception as e:
            return self._generate_template(context) + f"\n\n⚠️ Error LLM: {e}"
