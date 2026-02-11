"""Pytest configuration and shared fixtures."""
import os
import sys
from pathlib import Path

import pytest

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line(
        "markers", "requires_aws: mark test as requiring AWS credentials"
    )


@pytest.fixture(scope="session")
def test_env():
    """Set up test environment variables."""
    # Save original env vars
    original_env = os.environ.copy()

    # Set test environment
    os.environ["ENVIRONMENT"] = "test"
    os.environ["AWS_REGION"] = os.getenv("AWS_REGION", "us-east-1")
    os.environ["OBSERVABILITY_PROVIDER"] = "none"

    yield

    # Restore original env
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def sample_stock_symbol():
    """Provide a sample stock symbol for testing."""
    return "AMZN"


@pytest.fixture
def sample_user_id():
    """Provide a sample user ID for testing."""
    return "test_user_123"
