import json
import random
import time
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers="kafka:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

CHANNELS = ["email", "search", "display", "video"]
EVENTS = ["impression", "click", "conversion"]

def generate_event(i):
    channel = random.choice(CHANNELS)
    event = random.choice(EVENTS)

    return {
        "event_id": f"evt_{i}",
        "event_type": event,
        "ts_ms": int(time.time() * 1000),  # milliseconds
        "user_id": f"user_{random.randint(1, 1000)}",
        "campaign_id": f"camp_{random.randint(1, 10)}",
        "adgroup_id": f"adg_{random.randint(1, 100)}",
        "channel": channel,
        "geo": random.choice(["US", "EU", "AS", None]),
        "cost_usd": round(random.uniform(0.01, 10.0), 2),
        "revenue_usd": round(random.uniform(0.0, 50.0), 2) if event == "conversion" else 0.0,
    }

if __name__ == "__main__":
    for i in range(200):
        evt = generate_event(i)
        producer.send("ad_events", evt)
        print("sent:", evt)
        time.sleep(0.05)

    producer.flush()
    print("done")