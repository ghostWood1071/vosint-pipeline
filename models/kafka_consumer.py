# -*- coding: utf-8 -*-
from kafka import KafkaConsumer
from models.kafka_producer import KafkaProducer_class

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

    @staticmethod
    def test_connection(topic, group_ids):
        print("--------------TEST KAFKA CONNECTION START----------")
        try:
            print(f"kafa-connect-server: {settings.KAFKA_CONNECT}")
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=[settings.KAFKA_CONNECT],
                auto_offset_reset='earliest',
                enable_auto_commit=True,  # Tắt tự động commit offset
                group_id= group_ids,
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            print(f"connect status: {consumer.bootstrap_connected()}")
        except Exception as e:
            print(f"connect status: ", e)
        print("------------TEST KAFKA CONNECTION END--------------")

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

    def delete_task(self, task_id):
        MongoRepository().delete_one("queue", {"_id": task_id})

    def poll(self,topic,group_ids = 'group_id'):
        result = ''
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=settings.KAFKA_CONNECT.split(','),
            auto_offset_reset='earliest',
            enable_auto_commit=True,  # Tắt tự động commit offset
            group_id= group_ids,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )

        messages = consumer.poll(10000,1)
        consumer.close()
        activity_id = None
        for tp, messages in messages.items():
            for message in messages:
                message_data = message.value
                try:
                    task = self.get_task(message_data.get("task_id"))
                    url = task.get("url")
                    source = task.get("source")
                    activity_id = self.create_slave_activity(url, source)
                    result = self.excute(message_data)
                except Exception as e:
                    pass
                finally:
                    #self.delete_task(message_data.get("task_id"))
                    if activity_id != None:
                        self.delete_slave_activity(activity_id)
        consumer.commit_async()
        return result
    
    def excute(self,message):
        try:
            proxy_id = message.get("kwargs").get("list_proxy")[0]
            self.driver = DriverFactory(name='playwright',id_proxy=proxy_id)
        except Exception as e:
            self.driver = DriverFactory('playwright')
        pipe_line = Pipeline_Kafka(driver=self.driver,storage=self.storage,actions=message['actions'],pipeline_id=message['kwargs']['pipeline_id'],mode_test=message['kwargs']['mode_test'],input_val = message['input_val'],kwargs=message['kwargs'])
        return pipe_line.run()
    

        








    