# conftest.py — shared pytest configuration
# Place this in the project root alongside tests/

import pytest

# Suppress Kafka connection warnings during tests
# (kafka_client.py handles Kafka unavailability gracefully)
import logging
logging.getLogger("kafka").setLevel(logging.ERROR)
