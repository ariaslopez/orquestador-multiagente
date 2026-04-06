"""GitAgent — Integracion con GitHub API para clonar, leer y hacer commits."""
from __future__ import annotations
import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict


class GitAgent:
    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN', '')
        self.has_token = bool(self.token) and 'your_' not in self.token

    def clone(self, repo: str, dest_dir: str, branch: str = 'main') -> Path:
        """Clona un repositorio publico o privado (con token)."""
        dest = Path(dest_dir)
        if dest.exists():
            return dest
        if self.has_token:
            url = f"https://{self.token}@github.com/{repo}.git"
        else:
            url = f"https://github.com/{repo}.git"
        result = subprocess.run(
            ['git', 'clone', '--depth=1', '--branch', branch, url, str(dest)],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            raise RuntimeError(f"Error clonando {repo}: {result.stderr[:300]}")
        return dest

    def read_file(self, repo: str, file_path: str, ref: str = 'HEAD') -> str:
        """Lee el contenido de un archivo en un repo via GitHub API."""
        if not self.has_token:
            raise ValueError("GITHUB_TOKEN requerido para leer archivos via API")
        import urllib.request
        import json
        owner, name = repo.split('/', 1)
        url = f"https://api.github.com/repos/{owner}/{name}/contents/{file_path}?ref={ref}"
        req = urllib.request.Request(url, headers={
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        import base64
        return base64.b64decode(data['content']).decode('utf-8')

    def list_files(self, repo: str, path: str = '') -> List[Dict]:
        """Lista archivos en un directorio del repo."""
        if not self.has_token:
            return []
        import urllib.request
        import json
        owner, name = repo.split('/', 1)
        url = f"https://api.github.com/repos/{owner}/{name}/contents/{path}"
        req = urllib.request.Request(url, headers={
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
