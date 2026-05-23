from sqlalchemy import text


async def test_postgres_connection(integration_db_engine, integration_help_text: str):
    try:
        async with integration_db_engine.connect() as conn:
            value = (await conn.execute(text("SELECT 1"))).scalar_one()
            assert value == 1
    except Exception as exc:  # pragma: no cover
        raise AssertionError(f"PostgreSQL integration failed. {integration_help_text}") from exc


async def test_redis_connection(integration_redis, integration_help_text: str):
    try:
        pong = await integration_redis.ping()
        assert pong is True
    except Exception as exc:  # pragma: no cover
        raise AssertionError(f"Redis integration failed. {integration_help_text}") from exc
