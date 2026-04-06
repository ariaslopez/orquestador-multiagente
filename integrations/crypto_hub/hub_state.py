"""Sincronizacion de estado entre el orquestador y el crypto-intelligence-hub."""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

STATE_FILE = Path('.hub_sync_state.json')


class HubStateManager:
    """Gestiona el estado de sincronizacion entre orquestador y hub."""

    def __init__(self, state_file: Path = STATE_FILE):
        self.state_file = state_file
        self._state: dict = self._load()

    def _load(self) -> dict:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except Exception:
                return {}
        return {}

    def _save(self) -> None:
        self.state_file.write_text(json.dumps(self._state, indent=2, default=str))

    def mark_synced(self, key: str, value: Any) -> None:
        """Marca un item como sincronizado con el hub."""
        self._state[key] = {'value': value, 'synced': True}
        self._save()

    def get_last_sync(self, key: str) -> Optional[Any]:
        """Obtiene el ultimo valor sincronizado para una key."""
        entry = self._state.get(key)
        return entry.get('value') if entry else None

    def needs_sync(self, key: str, current_value: Any) -> bool:
        """Verifica si un valor necesita sincronizarse con el hub."""
        last = self.get_last_sync(key)
        return last != current_value

    def clear(self) -> None:
        """Limpia el estado de sincronizacion."""
        self._state = {}
        self._save()
