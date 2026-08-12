"""Тесты схем. Ничего внешнего не требуют."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.event import EventInputSchema, EventKafkaProducerSchema


def test_input_defaults():
    event = EventInputSchema()
    assert event.event_type == "test_event"
    assert event.payload is None


def test_producer_schema_sets_created_at():
    event = EventKafkaProducerSchema(event_type="demo")
    assert isinstance(event.created_at, datetime)


def test_created_at_is_timezone_aware():
    """Колонка в базе объявлена как DateTime(timezone=True).
    """
    event = EventKafkaProducerSchema()
    assert event.created_at.tzinfo is not None
    assert event.created_at.utcoffset() == timezone.utc.utcoffset(None)


def test_created_at_can_be_set_explicitly():
    """Раньше валидатор с mode="before" затирал любое присланное значение:
    поле выглядело настраиваемым, но задать его было нельзя."""
    moment = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
    event = EventKafkaProducerSchema(created_at=moment)
    assert event.created_at == moment


def test_event_type_must_be_string():
    with pytest.raises(ValidationError):
        EventInputSchema(event_type=["не строка"])


def test_serialization_for_kafka():
    """mode="json" нужен, чтобы datetime стал строкой: json.dumps в сериализаторе
    producer'а иначе не справится."""
    payload = EventKafkaProducerSchema(event_type="demo", payload="x").model_dump(mode="json")
    assert isinstance(payload["created_at"], str)
    assert payload["event_type"] == "demo"
