"""Test configuration and fixtures."""

import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from databases import Database

from app.main import app
from app.infrastructure.database.models import Base
from app.api.dependencies import get_db, get_database
from app.core.config import settings


# Test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine and session
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Create test database
test_database = Database(TEST_DATABASE_URL)


def override_get_db():
    """Override database dependency for testing."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def override_get_database():
    """Override async database dependency for testing."""
    if not test_database.is_connected:
        await test_database.connect()
    return test_database


# Override dependencies
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_database] = override_get_database


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """Setup test database."""
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    # Connect to async database
    await test_database.connect()
    
    yield
    
    # Cleanup
    await test_database.disconnect()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
async def client(setup_database):
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_user_token():
    """Mock user token for testing."""
    return "mock-jwt-token"


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "name": "John Doe",
        "address": {
            "line1": "123 Main Street",
            "line2": "Apt 4B",
            "town": "London",
            "county": "Greater London",
            "postcode": "SW1A 1AA"
        },
        "phone_number": "+447700900123",
        "email": "john.doe@example.com"
    }


@pytest.fixture
def sample_account_data():
    """Sample account data for testing."""
    return {
        "name": "Personal Bank Account",
        "account_type": "personal"
    }


@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for testing."""
    return {
        "amount": 100.50,
        "currency": "GBP",
        "type": "deposit",
        "reference": "Test transaction"
    }
