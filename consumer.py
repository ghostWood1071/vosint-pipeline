from models.kafka_consumer import KafkaConsumer_class
from core.config import settings

KafkaConsumer_class.test_connection(topic=settings.KAFKA_TOPIC_CRAWLING_NAME, group_ids=settings.KAFKA_GROUP_CRAWLING_NAME)
kafka_consumer = KafkaConsumer_class()
while True:
    kafka_consumer.poll()
    