import asyncio
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.db.session import AsyncSessionLocal
from app.services.workflow_service import seed_default_workflows


async def _run() -> None:
    async with AsyncSessionLocal() as db:
        result = await seed_default_workflows(db)
        print(f"workflow seed done: {result}")


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
