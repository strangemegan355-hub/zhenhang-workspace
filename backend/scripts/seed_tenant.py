import asyncio

from app.config.settings import settings
from app.db.session import AsyncSessionLocal
from app.models.tenant import Tenant
from app.models.user import User
from sqlalchemy import select


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        existing = (
            await db.execute(select(Tenant).where(Tenant.code == settings.default_tenant_code))
        ).scalar_one_or_none()
        if existing is None:
            tenant = Tenant(code=settings.default_tenant_code, name="默认租户", is_active=True)
            db.add(tenant)
            await db.flush()
        else:
            tenant = existing

        users = list((await db.execute(select(User).where(User.tenant_id.is_(None)))).scalars().all())
        for u in users:
            u.tenant_id = tenant.id
        await db.commit()
        print(f"Tenant {tenant.code} ready; backfilled {len(users)} users.")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
