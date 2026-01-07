import orjson
from confluent_kafka import KafkaException

from app.core.config import settings
from app.core.logging import configure_logging, log
from app.core.kafka import build_consumer, ensure_kafka_topic
from app.core.db import get_engine, init_schema
from app.core.redis import get_redis
from app.schemas import AdEvent
from app.processors.idempotency import IdempotencyStore
from app.processors.attribution_processor import AttributionProcessor, ProcessorDeps

def main() -> None:
    configure_logging()
    log.info("stream_processor_starting", env=settings.app_env)

    # Ensure Kafka topic exists before consuming
    ensure_kafka_topic(settings.kafka_topic_events, settings.kafka_bootstrap)

    engine = get_engine()
    init_schema(engine)
    r = get_redis()
    idem = IdempotencyStore(r, ttl_s=settings.idempotency_ttl_s)

    processor = AttributionProcessor(ProcessorDeps(engine=engine, redis=r, idem=idem))
    consumer = build_consumer()

    try:
        while True:
            msg = consumer.poll(settings.poll_timeout_s)
            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())

            ev = AdEvent.model_validate(orjson.loads(msg.value()))
            processor.process(ev)

            consumer.commit(asynchronous=False)

    except KeyboardInterrupt:
        log.info("stream_processor_stopping")
    finally:
        consumer.close()

if __name__ == "__main__":
    main()