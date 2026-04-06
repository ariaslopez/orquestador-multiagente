"""BacktestReaderAgent — lee y normaliza logs de trading y backtests (CSV, JSON, TXT)."""
from __future__ import annotations
from pathlib import Path
from core.base_agent import BaseAgent
from core.context import AgentContext


class BacktestReaderAgent(BaseAgent):
    name = "BacktestReaderAgent"
    description = "Lee y normaliza logs de trading, backtests y resultados de bots desde archivos."

    async def run(self, context: AgentContext) -> AgentContext:
        input_file = getattr(context, 'input_file', None)
        data_content = ''
        meta = {'source': 'user_input', 'records': 0}

        if input_file and Path(input_file).exists():
            ext = Path(input_file).suffix.lower()
            self.log(context, f"Leyendo datos de trading: {Path(input_file).name}")
            if ext == '.csv':
                import csv
                rows = []
                with open(input_file, encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    all_rows = list(reader)
                    for i, row in enumerate(all_rows[:200]):
                        rows.append(str(dict(row)))
                    if len(all_rows) > 200:
                        rows.append(f'...(truncado, {len(all_rows)} registros totales)')
                data_content = '\n'.join(rows)
                meta = {'source': Path(input_file).name, 'records': len(all_rows), 'type': 'csv'}
            elif ext == '.json':
                import json
                with open(input_file, encoding='utf-8') as f:
                    raw = json.load(f)
                data_content = json.dumps(raw, indent=2)[:4000]
                meta = {'source': Path(input_file).name, 'type': 'json'}
            else:
                data_content = Path(input_file).read_text(encoding='utf-8')[:4000]
                meta = {'source': Path(input_file).name, 'type': ext}
        else:
            data_content = context.user_input
            meta = {'source': 'user_input', 'type': 'text'}
            self.log(context, "Sin archivo — usando descripcion del usuario")

        context.set_data('trade_data', data_content)
        context.set_data('trade_meta', meta)
        self.log(context, f"Datos de trading cargados ({len(data_content)} chars)")
        return context
