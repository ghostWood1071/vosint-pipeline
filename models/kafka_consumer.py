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

class KafkaConsumer_class:
    def __init__(self):
        self.preducer = KafkaProducer_class()
        #self.driver = DriverFactory('playwright')
        self.storage = StorageFactory('hbase')

    def create_slave_activity(self, url, source):
        try:
            MongoRepository().insert_one("slave_activity", {
            "id": socket.gethostname(),
            "url": url,
            "source": source 
            })
        except Exception as e:
            print(e)
    
    def delete_slave_activity(self, url):
        try:
            MongoRepository().delete_one("slave_activity", {"url": url,})
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

    def poll(self,topic,group_ids = 'group_id'):
        result = ''
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=settings.KAFKA_CONNECT.split(','),
            auto_offset_reset='earliest',
            enable_auto_commit=False,  # Tắt tự động commit offset
            group_id= group_ids,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )


        messages = consumer.poll(10000,1)
        for tp, messages in messages.items():
            for message in messages:
                # Xử lý message
                message_data = message.value
                # try:
                try:
                    kwargs = message_data.get("kwargs")
                    url = self.get_url(message_data)
                    self.create_slave_activity(url, kwargs.get("source_name"))
                    result = self.excute(message_data)
                except Exception as e:
                    pass
                    #self.preducer.write(topic='crawling',message=message)
                finally:
                    # consumer.commit({
                    #     tp: {
                    #         'offset': message.offset + 1
                    #     }
                    # })
                    self.delete_slave_activity(url)
                    consumer.commit_async()
                # except:
                #     # Nếu xử lý lỗi, không commit offset
                #     pass
        consumer.commit_async()
        consumer.close()
        return result
    
    def excute(self,message):
        #a = message['id_proxy']
        #self.driver = DriverFactory(name='playwright',id_proxy=a)
        try:
            proxy_id = message.get("kwargs").get("list_proxy")[0]
            self.driver = DriverFactory(name='playwright',id_proxy=proxy_id)
        except Exception as e:
            self.driver = DriverFactory('playwright')
        pipe_line = Pipeline_Kafka(driver=self.driver,storage=self.storage,actions=message['actions'],pipeline_id=message['kwargs']['pipeline_id'],mode_test=message['kwargs']['mode_test'],input_val = message['input_val'],kwargs=message['kwargs'])
        return pipe_line.run()
    

        








    