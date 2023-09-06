from models.kafka_consumer import KafkaConsumer_class
kafka_consumer = KafkaConsumer_class()

print('pipeline slave started!')

while True:
    kafka_consumer.poll(topic='crawling_',group_ids='crawling_')
    