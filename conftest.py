# conftest.py — shared pytest configuration
# Place this in the project root alongside tests/

import pytest
from app.main import limiter

@pytest.fixture(autouse=True)
def disable_rate_limiter():
    limiter.enabled = False
    yield
    limiter.enabled = True 

# Suppress Kafka connection warnings during tests
# (kafka_client.py handles Kafka unavailability gracefully)
import logging
logging.getLogger("kafka").setLevel(logging.ERROR)
