"""Local dev entrypoint — forces SelectorEventLoop on Windows for psycopg async."""

from __future__ import annotations

import asyncio
import selectors
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if sys.platform == "win32":
    if sys.version_info >= (3, 14):
        def _LOOP_FACTORY():
            return asyncio.SelectorEventLoop(selectors.SelectSelector())
    else:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        _LOOP_FACTORY = None
else:
    _LOOP_FACTORY = None

import uvicorn


async def _serve() -> None:
    config = uvicorn.Config("app.main:app", host="0.0.0.0", port=8000, reload=False, loop="asyncio")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    if _LOOP_FACTORY is not None:
        with asyncio.Runner(loop_factory=_LOOP_FACTORY) as runner:
            runner.run(_serve())
    else:
        asyncio.run(_serve())
