import sys

sys.path.insert(
    0,
    "/home/ds1/vosint/v-osint-backend/vosint_ingestion/nlp/vosint_v3_event_extraction",
)
from models.kafka_consumer_event import KafkaConsumer_event_class

kafka_consumer = KafkaConsumer_event_class()

while True:
    kafka_consumer.run(topic="events", group_ids="events")
