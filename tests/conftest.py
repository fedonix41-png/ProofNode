import os
import pytest
import asyncio
from testcontainers.postgres import PostgresContainer
from testcontainers.rabbitmq import RabbitMqContainer
from testcontainers.redis import RedisContainer
import asyncpg
from backend.app.config import settings

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    policy = asyncio.get_event_loop_policy()
    res = policy.new_event_loop()
    asyncio.set_event_loop(res)
    yield res
    res.close()

@pytest.fixture(scope="session", autouse=True)
def set_testing_env():
    """Sets the ENV setting to testing before loading any endpoints."""
    settings.env = "testing"

@pytest.fixture(scope="session")
def postgres_server():
    # Use standard Postgres image or TimescaleDB image if desired.
    # For testing, standard timescale/timescaledb is preferred to test hypertables.
    container = PostgresContainer("timescale/timescaledb:latest-pg15")
    container.start()
    
    # Override settings
    settings.postgres_host = container.get_container_host_ip()
    settings.postgres_port = int(container.get_exposed_port(5432))
    settings.postgres_user = container.username
    settings.postgres_password = container.password
    settings.postgres_db = container.dbname
    
    # Create the necessary schemas in the test database
    init_db_path = os.path.join(os.path.dirname(__file__), "../database/init_db.sql")
    with open(init_db_path, "r") as f:
        sql_commands = f.read()
        
    import psycopg2
    conn = psycopg2.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        user=settings.postgres_user,
        password=settings.postgres_password,
        database=settings.postgres_db
    )
    conn.autocommit = True
    with conn.cursor() as cursor:
        # Split by command or run entire block
        # Because init_db contains TimescaleDB select calls, we execute it
        cursor.execute(sql_commands)
    conn.close()
    
    yield container
    container.stop()

@pytest.fixture(scope="session")
def rabbitmq_server():
    container = RabbitMqContainer("rabbitmq:3-management")
    container.start()
    
    # Override settings
    settings.rabbitmq_host = container.get_container_host_ip()
    settings.rabbitmq_port = int(container.get_exposed_port(5672))
    settings.rabbitmq_user = "guest"
    settings.rabbitmq_password = "guest"
    
    yield container
    container.stop()

@pytest.fixture(scope="session")
def redis_server():
    container = RedisContainer("redis:alpine")
    container.start()
    
    # Override settings
    settings.redis_host = container.get_container_host_ip()
    settings.redis_port = int(container.get_exposed_port(6379))
    
    yield container
    container.stop()

@pytest.fixture(scope="function")
def mock_dex_service(monkeypatch):
    """Mocks external network calls to DEX APIs to prevent live HTTP requests during tests."""
    from backend.app.services.dex import DEXService
    
    async def mock_stonfi_route(*args, **kwargs):
        return {"route": "mock"}
        
    async def mock_1inch_quote(*args, **kwargs):
        return {"toTokenAmount": "1000"}
        
    async def mock_1inch_swap_tx(*args, **kwargs):
        return {"to": "0x123", "data": "0x"}
        
    async def mock_jupiter_quote(*args, **kwargs):
        return {"outAmount": "1000"}
        
    async def mock_jupiter_swap_tx(*args, **kwargs):
        return "mock_base64_tx"
        
    monkeypatch.setattr(DEXService, "get_stonfi_route", mock_stonfi_route)
    monkeypatch.setattr(DEXService, "get_1inch_quote", mock_1inch_quote)
    monkeypatch.setattr(DEXService, "get_1inch_swap_tx", mock_1inch_swap_tx)
    monkeypatch.setattr(DEXService, "get_jupiter_quote", mock_jupiter_quote)
    monkeypatch.setattr(DEXService, "get_jupiter_swap_tx", mock_jupiter_swap_tx)
    yield
