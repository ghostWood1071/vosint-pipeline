from models.kafka_consumer import KafkaConsumer_class

KafkaConsumer_class.test_connection(topic='sca_crawl', group_ids='sca')
kafka_consumer = KafkaConsumer_class()
while True:
    kafka_consumer.poll(topic='sca_crawl', group_ids='sca')
    