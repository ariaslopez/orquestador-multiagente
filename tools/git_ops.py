"""GitOpsTool — Operaciones GitHub vía API (PyGithub)."""
from __future__ import annotations
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class GitOpsTool:
    """
    Interactua con GitHub vía API:
    - Crear branches y PRs
    - Leer y escribir archivos
    - Crear commits
    - Listar repos accesibles

    Configuración en .env:
    - GITHUB_TOKEN: token con permisos repo
    - GITHUB_AUTO_PR: si crear PR automático (default: true)
    - GITHUB_PROTECTED_BRANCHES: branches que nunca se tocan directamente
    """

    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN", "")
        self.username = os.getenv("GITHUB_USERNAME", "")
        self.auto_pr = os.getenv("GITHUB_AUTO_PR", "true").lower() == "true"
        self.protected_branches = [
            b.strip() for b in
            os.getenv("GITHUB_PROTECTED_BRANCHES", "main,master,production").split(",")
        ]
        self._github = None

    def _get_github(self):
        if not self._github:
            try:
                from github import Github
                self._github = Github(self.token)
            except ImportError:
                raise RuntimeError("PyGithub no instalado. Ejecuta: pip install PyGithub")
        return self._github

    def get_repo(self, repo_full_name: str):
        """Obtiene un repositorio por su nombre completo (owner/repo)."""
        g = self._get_github()
        return g.get_repo(repo_full_name)

    def list_repos(self) -> List[Dict]:
        """Lista todos los repos accesibles con el token."""
        g = self._get_github()
        repos = []
        for repo in g.get_user().get_repos():
            repos.append({
                "name": repo.full_name,
                "private": repo.private,
                "default_branch": repo.default_branch,
                "url": repo.html_url,
                "description": repo.description or "",
            })
        return repos

    def read_file(self, repo_full_name: str, path: str, branch: str = "main") -> str:
        """Lee el contenido de un archivo en un repo."""
        repo = self.get_repo(repo_full_name)
        content = repo.get_contents(path, ref=branch)
        return content.decoded_content.decode("utf-8")

    def write_file(
        self,
        repo_full_name: str,
        path: str,
        content: str,
        commit_message: str,
        branch: str = "main",
    ) -> Dict:
        """Escribe o actualiza un archivo en un repo."""
        if branch in self.protected_branches:
            raise PermissionError(
                f"Branch '{branch}' está protegida. "
                f"El sistema crea una branch nueva automáticamente."
            )
        repo = self.get_repo(repo_full_name)
        try:
            existing = repo.get_contents(path, ref=branch)
            result = repo.update_file(path, commit_message, content, existing.sha, branch=branch)
            action = "updated"
        except Exception:
            result = repo.create_file(path, commit_message, content, branch=branch)
            action = "created"
        logger.info(f"GitOps.write_file: {action} {path} en {repo_full_name}@{branch}")
        return {"action": action, "path": path, "branch": branch}

    def create_branch(self, repo_full_name: str, branch_name: str, from_branch: str = "main") -> str:
        """Crea una nueva branch desde otra."""
        repo = self.get_repo(repo_full_name)
        source = repo.get_branch(from_branch)
        repo.create_git_ref(f"refs/heads/{branch_name}", source.commit.sha)
        logger.info(f"GitOps.create_branch: {branch_name} desde {from_branch} en {repo_full_name}")
        return branch_name

    def create_pull_request(
        self,
        repo_full_name: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main",
    ) -> Dict:
        """Crea un Pull Request."""
        repo = self.get_repo(repo_full_name)
        pr = repo.create_pull(title=title, body=body, head=head_branch, base=base_branch)
        logger.info(f"GitOps.create_pr: '{title}' en {repo_full_name}")
        return {"number": pr.number, "url": pr.html_url, "title": title}

    def push_files(
        self,
        repo_full_name: str,
        files: Dict[str, str],
        commit_message: str,
        branch: str,
        create_pr: Optional[bool] = None,
        pr_title: Optional[str] = None,
        pr_body: str = "",
    ) -> Dict:
        """
        Push de múltiples archivos en un solo workflow:
        1. Crea branch si no existe
        2. Escribe todos los archivos
        3. Crea PR si auto_pr=True o create_pr=True
        """
        should_pr = create_pr if create_pr is not None else self.auto_pr
        results = []

        for path, content in files.items():
            result = self.write_file(repo_full_name, path, content, commit_message, branch)
            results.append(result)

        output = {"files_pushed": len(results), "branch": branch}

        if should_pr:
            pr = self.create_pull_request(
                repo_full_name,
                title=pr_title or commit_message,
                body=pr_body or f"Cambios generados por CLAW Agent System\n\n{commit_message}",
                head_branch=branch,
            )
            output["pr"] = pr
            logger.info(f"GitOps.push_files: PR creado → {pr['url']}")

        return output
