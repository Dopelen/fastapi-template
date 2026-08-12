"""Тесты эндпоинтов. Kafka и Postgres не нужны - см. tests/conftest.py."""

from app.models.event import Event


async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "Ok"}


async def test_send_without_kafka_returns_503(client):
    """Недоступный брокер - штатная ситуация, а не сбой программы.
    """
    response = await client.post("/send", json={"event_type": "demo", "payload": "hi"})
    assert response.status_code == 503, response.text


async def test_send_uses_producer_from_app_state(client_with_fake_producer):
    """Ради этого клиенты Kafka и переехали в app.state.
    Пока producer лежал в глобальной переменной модуля, подменить его в тесте
    можно было только через monkeypatch на сам модуль. Теперь достаточно
    положить заглушку в state приложения.
    """
    client, fake = client_with_fake_producer

    response = await client.post("/send", json={"event_type": "demo", "payload": "hi"})

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "sent"

    assert len(fake.sent) == 1
    topic, event = fake.sent[0]
    assert event.event_type == "demo"
    assert event.payload == "hi"
    assert event.created_at is not None


async def test_events_empty(client):
    response = await client.get("/events")
    assert response.status_code == 200
    assert response.json() == []


async def test_events_returns_saved_rows(client, session_factory):
    async with session_factory() as session:
        session.add_all([
            Event(event_type="first", payload="a"),
            Event(event_type="second", payload=None),
        ])
        await session.commit()

    response = await client.get("/events")
    assert response.status_code == 200

    rows = response.json()
    assert len(rows) == 2
    assert rows[0]["event_type"] == "second"
    assert rows[0]["payload"] is None
    assert rows[1]["event_type"] == "first"
    assert {"id", "event_type", "payload", "created_at"} == set(rows[0])


async def test_events_pagination(client, session_factory):
    async with session_factory() as session:
        session.add_all([Event(event_type=f"event-{i}") for i in range(5)])
        await session.commit()

    first_page = (await client.get("/events", params={"limit": 2})).json()
    second_page = (await client.get("/events", params={"limit": 2, "offset": 2})).json()

    assert len(first_page) == 2
    assert len(second_page) == 2
    assert {r["id"] for r in first_page} & {r["id"] for r in second_page} == set()


async def test_events_limit_has_ceiling(client):
    """Без потолка клиент вытянул бы всю таблицу одним запросом."""
    assert (await client.get("/events", params={"limit": 500})).status_code == 422
    assert (await client.get("/events", params={"limit": 0})).status_code == 422
    assert (await client.get("/events", params={"offset": -1})).status_code == 422
