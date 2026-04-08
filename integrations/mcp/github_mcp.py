"""MCP Adaptador — GitHub MCP.

Acceso de lectura/escritura a repositorios GitHub via API.
Complementa PyGithub (que ya existe) con la interfaz MCP estandar
para que los agentes puedan hacer operaciones de repo de forma uniforme.

Herramientas disponibles:
  get_file(repo, path, branch='main')            -> {content, sha}
  search_code(query, repo='')                    -> [{path, url, snippet}]
  list_issues(repo, state='open', limit=10)      -> [{number, title, labels}]
  create_issue(repo, title, body, labels=[])     -> {number, url}
  get_pull_requests(repo, state='open')          -> [{number, title, url}]
  get_commits(repo, branch='main', limit=10)     -> [{sha, message, author, date}]

Env requerida: GITHUB_TOKEN
"""
from __future__ import annotations
import os
import aiohttp
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

GH_API = "https://api.github.com"


class GitHubMCPAdapter:
    def _headers(self) -> Dict:
        token = os.getenv("GITHUB_TOKEN", "")
        h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    async def call(self, tool: str, params: Dict[str, Any]) -> Any:
        if tool == "get_file":          return await self._get_file(**params)
        if tool == "search_code":       return await self._search_code(**params)
        if tool == "list_issues":       return await self._list_issues(**params)
        if tool == "create_issue":      return await self._create_issue(**params)
        if tool == "get_pull_requests": return await self._get_pull_requests(**params)
        if tool == "get_commits":       return await self._get_commits(**params)
        raise ValueError(f"GitHubMCP: tool '{tool}' desconocida")

    async def _get_file(self, repo: str, path: str, branch: str = "main") -> Dict:
        import base64
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{GH_API}/repos/{repo}/contents/{path}",
                params={"ref": branch}, headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as r:
                r.raise_for_status()
                data = await r.json()
        content = base64.b64decode(data.get("content", "")).decode("utf-8") if data.get("content") else ""
        return {"content": content, "sha": data.get("sha"), "size": data.get("size")}

    async def _search_code(self, query: str, repo: str = "") -> List[Dict]:
        q = f"{query} repo:{repo}" if repo else query
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{GH_API}/search/code",
                params={"q": q, "per_page": 10},
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as r:
                r.raise_for_status()
                data = await r.json()
        return [
            {"path": i["path"], "url": i["html_url"], "repo": i["repository"]["full_name"]}
            for i in data.get("items", [])
        ]

    async def _list_issues(self, repo: str, state: str = "open", limit: int = 10) -> List[Dict]:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{GH_API}/repos/{repo}/issues",
                params={"state": state, "per_page": limit},
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as r:
                r.raise_for_status()
                data = await r.json()
        return [{"number": i["number"], "title": i["title"], "labels": [l["name"] for l in i.get("labels", [])]} for i in data]

    async def _create_issue(self, repo: str, title: str, body: str, labels: List[str] = None) -> Dict:
        async with aiohttp.ClientSession() as s:
            async with s.post(
                f"{GH_API}/repos/{repo}/issues",
                json={"title": title, "body": body, "labels": labels or []},
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as r:
                r.raise_for_status()
                data = await r.json()
        return {"number": data["number"], "url": data["html_url"]}

    async def _get_pull_requests(self, repo: str, state: str = "open") -> List[Dict]:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{GH_API}/repos/{repo}/pulls",
                params={"state": state, "per_page": 10},
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as r:
                r.raise_for_status()
                data = await r.json()
        return [{"number": p["number"], "title": p["title"], "url": p["html_url"]} for p in data]

    async def _get_commits(self, repo: str, branch: str = "main", limit: int = 10) -> List[Dict]:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{GH_API}/repos/{repo}/commits",
                params={"sha": branch, "per_page": limit},
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as r:
                r.raise_for_status()
                data = await r.json()
        return [{"sha": c["sha"][:7], "message": c["commit"]["message"][:80],
                 "author": c["commit"]["author"]["name"], "date": c["commit"]["author"]["date"]} for c in data]


def get_adapter() -> GitHubMCPAdapter:
    return GitHubMCPAdapter()
