import os
import uuid
import pytest
from datetime import datetime, timezone

# Ensure testing environment variables
os.environ["APP_ENV"] = "testing"
os.environ["SECRET_KEY"] = "test_secret_key_at_least_32_bytes_long_1234567890"
os.environ["AUDIT_CHECKPOINT_SECRET"] = "test_audit_checkpoint_secret_32_bytes_long"
os.environ["DATABASE_URL"] = "postgresql://solar_user:solar_test@localhost:5432/solar_test"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()

@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()
