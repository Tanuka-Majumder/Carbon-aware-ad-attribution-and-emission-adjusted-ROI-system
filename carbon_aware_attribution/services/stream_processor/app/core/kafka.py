from confluent_kafka import Consumer, KafkaError
from app.core.config import settings
import subprocess
from confluent_kafka.admin import AdminClient, NewTopic

def build_consumer() -> Consumer:
    conf = {
        "bootstrap.servers": settings.kafka_bootstrap,
        "group.id": settings.kafka_consumer_group,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    }
    c = Consumer(conf)
    c.subscribe([settings.kafka_topic_events])
    return c

def is_fatal(err: KafkaError) -> bool:
    return err.fatal() if err is not None else False

def ensure_kafka_topic(topic: str, bootstrap_servers: str):
    """
    Create Kafka topic if it does not exist.
    """
    admin = AdminClient({'bootstrap.servers': bootstrap_servers})
    topics = admin.list_topics(timeout=5).topics
    if topic not in topics:
        new_topic = NewTopic(topic, num_partitions=1, replication_factor=1)
        admin.create_topics([new_topic])