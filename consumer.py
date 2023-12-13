from models.kafka_consumer import KafkaConsumer_class

KafkaConsumer_class.test_connection(topic='crawling_', group_ids='crawling_')
kafka_consumer = KafkaConsumer_class()
while True:
    kafka_consumer.poll(topic='crawling_', group_ids='crawling_')
    