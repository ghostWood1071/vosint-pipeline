from models.kafka_consumer import KafkaConsumer_class
kafka_consumer = KafkaConsumer_class()

while True:

    kafka_consumer.poll(topic='crawling_',group_ids='crawling_')
    