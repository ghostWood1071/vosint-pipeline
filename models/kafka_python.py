from kafka.admin import KafkaAdminClient, NewTopic
from core.config import settings
class Kafka_class:  ## khi write tự động tạo
    def create_topic(self,topic_name,num_partitions = 3,replication_factor = 1):
        try:
            admin_client = KafkaAdminClient(bootstrap_servers=settings.KAFKA_CONNECT.split(','))
            topic = NewTopic(name=topic_name)
            admin_client.create_topics([topic])
            return True
        except:
            return False