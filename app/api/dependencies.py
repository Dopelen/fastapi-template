from fastapi import HTTPException, Request

from app.kafka.producer import KafkaProducer


def get_producer(request: Request) -> KafkaProducer:
    producer = getattr(request.app.state, "kafka_producer", None)
    if producer is None:
        raise HTTPException(status_code=503, detail="Kafka producer is not running")
    return producer
