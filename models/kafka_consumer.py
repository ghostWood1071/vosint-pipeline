# -*- coding: utf-8 -*-
from kafka import KafkaConsumer, KafkaAdminClient
from kafka.admin import NewPartitions, NewTopic
from models.kafka_producer import KafkaProducer_class
from kafka.coordinator.assignors.roundrobin import RoundRobinPartitionAssignor

import json

from automation.drivers import DriverFactory
from automation.storages import StorageFactory

from automation.pipeline import Pipeline_Kafka
from core.config import settings
import traceback
from .mongorepository import MongoRepository
import socket
import time
class KafkaConsumer_class:
    def __init__(self):
        self.preducer = KafkaProducer_class()
        self.storage = StorageFactory('hbase')
        # self.consumer = self.create_consumer(settings.KAFKA_TOPIC_CRAWLING_NAME, settings.KAFKA_GROUP_CRAWLING_NAME)

    @staticmethod
    def test_connection(topic, group_ids):
        print("--------------TEST KAFKA CONNECTION START----------")
        try:
            print(f"kafa-connect-server: {settings.KAFKA_CONNECT.split(',')}")
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=settings.KAFKA_CONNECT.split(","),
                auto_offset_reset='earliest',
                enable_auto_commit=True,  # Tắt tự động commit offset
                group_id= group_ids,
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            print(f"connect status: {consumer.bootstrap_connected()}")
        except Exception as e:
            print(f"connect status: ", e)
        print("------------TEST KAFKA CONNECTION END--------------")


    def prepare(self):
        topic_id = settings.KAFKA_TOPIC_CRAWLING_NAME
        kafka_client = KafkaAdminClient(bootstrap_servers = settings.KAFKA_CONNECT.split(","))
        group_ds = kafka_client.describe_consumer_groups([settings.KAFKA_GROUP_CRAWLING_NAME])[0]
        topic_ds = kafka_client.describe_topics([topic_id])[0]
        if group_ds.state=='Dead' or topic_ds["error_code"] == 3:
            if self.create_topic(kafka_client):
                return
            else:
                raise RuntimeError("create topic failed")
        if len(group_ds.members) > len(topic_ds["partitions"]):
            self.create_new_partition(kafka_client, topic_id, len(topic_ds["partitions"]))

    def create_consumer(self, topic, group_ids):
        return KafkaConsumer(
            topic,
            bootstrap_servers=settings.KAFKA_CONNECT.split(","),
            auto_offset_reset='earliest',
            enable_auto_commit=True,  # Tắt tự động commit offset
            group_id= group_ids,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            partition_assignment_strategy = [RoundRobinPartitionAssignor]
        )

    def create_slave_activity(self, url, source):
        try:
            activity_id = MongoRepository().insert_one("slave_activity", {
            "id": socket.gethostname(),
            "url": url,
            "source": source 
            })
            return activity_id
        except Exception as e:
            print(e)
            return None
    
    def delete_slave_activity(self, activity_id):
        try:
            MongoRepository().delete_one("slave_activity", {"_id": activity_id})
        except Exception as e:
            print(e)

    def get_url(self, msg):
        url = None
        try:
           url = msg.get("actions")[0].get("url")
        except:
            pass
        #ttxvn
        try:
           if url == None: 
            url = msg.get("actions")[0].get("params").get("document").get("Url")
        except:
            pass
        #
        try:
            if url == None: 
                url = msg.get("input_val")
        except:
            pass
        return url

    def get_task(self, task_id):
        task = MongoRepository().get_one("queue", {"_id": task_id})
        return task
    
    def create_new_partition(self, kafka_client:KafkaAdminClient, topic_name:str, current_num_partitions):
        kafka_client.create_partitions({topic_name: NewPartitions(total_count=current_num_partitions+1)})
    
    def create_topic(self, admin_client:KafkaAdminClient):
        try:
            admin_client.create_topics([NewTopic(settings.KAFKA_TOPIC_CRAWLING_NAME, 1, 1)])
            return True
        except Exception as e:
            return False
    
    def update_task(self, task_id):
        task = MongoRepository().update_many("queue", {"_id": task_id}, {"$set": {"executed": True}})
        return task
        
    def poll(self):
        result = ''
        self.consumer = self.create_consumer(settings.KAFKA_TOPIC_CRAWLING_NAME, settings.KAFKA_GROUP_CRAWLING_NAME)
        messages = self.consumer.poll(10000,1)
        self.consumer.close()
        activity_id = None
        for tp, messages in messages.items():
            for message in messages:
                message_data = message.value
                try:
                    task = self.get_task(message_data.get("task_id"))
                    if task is None:
                        task = {
                            "executed": False,
                            "source": "old news",
                            "url": self.get_url(message_data)
                        }
                    if task.get("executed"):
                        continue
                    url = task.get("url")
                    source = task.get("source")
                    activity_id = self.create_slave_activity(url, source)
                    result = self.excute(message_data)
                    self.update_task(message_data.get("task_id"))
                except Exception as e:
                    print(e)
                finally:
                    if activity_id != None:
                        self.delete_slave_activity(activity_id)
        return result
    
    def excute(self,message):
        try:
            proxy_id = message.get("kwargs").get("list_proxy")[0]
            self.driver = DriverFactory(name='playwright',id_proxy=proxy_id)
        except Exception as e:
            self.driver = DriverFactory('playwright')
        pipe_line = Pipeline_Kafka(
            driver = self.driver,
            storage = self.storage,
            actions = message['actions'],
            pipeline_id = message['kwargs']['pipeline_id'],
            mode_test = message['kwargs']['mode_test'],
            input_val = message['input_val'],
            kwargs = message['kwargs']
        )
        return pipe_line.run()
    

        








    