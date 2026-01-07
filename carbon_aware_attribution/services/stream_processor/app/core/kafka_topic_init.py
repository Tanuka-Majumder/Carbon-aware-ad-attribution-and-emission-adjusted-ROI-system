from confluent_kafka.admin import AdminClient, NewTopic
from app.core.config import settings
import time


def ensure_topic():
    admin = AdminClient({'bootstrap.servers': settings.kafka_bootstrap})
    topic = settings.kafka_topic_events
    existing = admin.list_topics(timeout=10).topics
    if topic not in existing:
        new_topic = NewTopic(topic, num_partitions=1, replication_factor=1)
        fs = admin.create_topics([new_topic])
        for t, f in fs.items():
            try:
                f.result()  # Wait for topic creation
                print(f"Created topic: {t}")
            except Exception as e:
                print(f"Failed to create topic {t}: {e}")
        # Wait for Kafka to propagate topic
        time.sleep(2)
    else:
        print(f"Topic '{topic}' already exists.")
