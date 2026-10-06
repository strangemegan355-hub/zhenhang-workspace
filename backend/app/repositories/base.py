from sqlalchemy.ext.asyncio import AsyncSession


async def commit_session(db: AsyncSession) -> None:
    """Commit the current session.

    Lived byte-identically in `procurement_payable_repository` and `quote_receivable_repository` until round 129;
    both now import it, so their call sites are unchanged.
    """
    await db.commit()
