"""MCP Adaptador — Playwright.

Testing de UI con browser real (headless Chromium).
Usado por QA agents para validar interfaces web, formularios,
flujos de autenticacion y performance de paginas.

Herramientas disponibles:
  screenshot(url, full_page=True)              -> {base64_image, width, height}
  check_links(url)                             -> {broken: [], valid: [], total}
  run_test(url, actions=[])                    -> {passed, steps_completed, errors}
  get_page_content(url)                        -> {title, text, links, meta}
  measure_performance(url)                     -> {load_time_ms, ttfb_ms, cls, lcp}

Requerimiento: playwright instalado + chromium
  pip install playwright
  playwright install chromium
"""
from __future__ import annotations
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class PlaywrightMCPAdapter:
    async def call(self, tool: str, params: Dict[str, Any]) -> Any:
        if tool == "screenshot":        return await self._screenshot(**params)
        if tool == "check_links":       return await self._check_links(**params)
        if tool == "run_test":          return await self._run_test(**params)
        if tool == "get_page_content":  return await self._get_page_content(**params)
        if tool == "measure_performance": return await self._measure_performance(**params)
        raise ValueError(f"Playwright: tool '{tool}' desconocida")

    def _get_playwright(self):
        try:
            from playwright.async_api import async_playwright
            return async_playwright
        except ImportError:
            raise ImportError("Playwright no instalado. Ejecuta: pip install playwright && playwright install chromium")

    async def _screenshot(self, url: str, full_page: bool = True) -> Dict:
        import base64
        async_playwright = self._get_playwright()
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page    = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            img_bytes = await page.screenshot(full_page=full_page)
            await browser.close()
        return {
            "base64_image": base64.b64encode(img_bytes).decode(),
            "url":          url,
        }

    async def _get_page_content(self, url: str) -> Dict:
        async_playwright = self._get_playwright()
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page    = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            title  = await page.title()
            text   = await page.inner_text("body")
            links  = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
            await browser.close()
        return {"title": title, "text": text[:3000], "links": links[:50], "url": url}

    async def _check_links(self, url: str) -> Dict:
        import aiohttp
        content = await self._get_page_content(url)
        links   = content.get("links", [])
        broken  = []
        valid   = []
        async with aiohttp.ClientSession() as session:
            for link in links[:30]:  # max 30 links
                try:
                    async with session.head(link, timeout=aiohttp.ClientTimeout(total=5), allow_redirects=True) as r:
                        if r.status < 400:
                            valid.append(link)
                        else:
                            broken.append({"url": link, "status": r.status})
                except Exception:
                    broken.append({"url": link, "status": "unreachable"})
        return {"broken": broken, "valid": valid, "total": len(links)}

    async def _measure_performance(self, url: str) -> Dict:
        async_playwright = self._get_playwright()
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page    = await browser.new_page()
            start   = __import__("time").time()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            load_ms = round((__import__("time").time() - start) * 1000, 1)
            metrics = await page.evaluate("() => JSON.stringify(window.performance.timing)")
            await browser.close()
        import json
        timing = json.loads(metrics)
        ttfb   = timing.get("responseStart", 0) - timing.get("navigationStart", 0)
        return {"load_time_ms": load_ms, "ttfb_ms": max(ttfb, 0), "url": url}

    async def _run_test(self, url: str, actions: List[Dict] = None) -> Dict:
        """Ejecuta una secuencia de acciones en el browser."""
        actions = actions or []
        results = []
        async_playwright = self._get_playwright()
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page    = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            for action in actions:
                try:
                    atype = action.get("type")
                    if atype == "click":    await page.click(action["selector"])
                    elif atype == "fill":   await page.fill(action["selector"], action["value"])
                    elif atype == "assert": assert await page.is_visible(action["selector"])
                    results.append({"action": atype, "status": "ok"})
                except Exception as e:
                    results.append({"action": action.get("type"), "status": "failed", "error": str(e)})
            await browser.close()
        passed = all(r["status"] == "ok" for r in results)
        return {"passed": passed, "steps": results, "url": url}


def get_adapter() -> PlaywrightMCPAdapter:
    return PlaywrightMCPAdapter()
