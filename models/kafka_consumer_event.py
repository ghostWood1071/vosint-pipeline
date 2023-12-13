from kafka import KafkaConsumer
from models.kafka_producer import KafkaProducer_class

# from nlp.vosint_v3_event_extraction.processing_events import Extrac_events
import json
import time
import datetime
from core.config import settings


class KafkaConsumer_event_class:
    def __init__(self):
        self.preducer = KafkaProducer_class()
        #self.extract_event = Extrac_events()
        # self.extract_event = Extrac_events()
        # self.driver = DriverFactory('playwright')
        # self.storage = StorageFactory('hbase')

    def run(self, topic, group_ids="group_id"):
        result = ""
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=settings.KAFKA_CONNECT.split(','),
            auto_offset_reset="earliest",
            enable_auto_commit=False,  # Tắt tự động commit offset
            group_id=group_ids,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )

        messages = consumer.poll(10000, 1)
        for tp, messages in messages.items():
            for message in messages:
                # Xử lý message
                message = message.value
                result = self.excute(message)
                # try:
                #     try:
                #         result = self.excute(message)

                #     except:
                #         pass
                #         #self.preducer.write(topic='crawling',message=message)
                #     finally:
                #         consumer.commit({
                #             tp: {
                #                 'offset': message.offset + 1
                #             }
                #         })
                #         consumer.commit_async()
                # except:
                #     # Nếu xử lý lỗi, không commit offset
                #     pass
        consumer.commit_async()
        consumer.close()
        return result

    def excute(self, message):
        # print(message)
        start_time = time.time()
        self.extract_event.merge(
            datetime.datetime.strptime(message["pubdate"].split(" ")[0], "%Y-%m-%d"),
            message["title"],
            message["content"],
            message["id_new"],
        )
        # i = 0
        # f = open('/home/ds1/vosint/v-osint-backend/vosint_ingestion/time_log_events.txt','a')
        # f.write(str(i)+ ' '+str(time.time()-start_time)+'\n')
        # f.close()
        # i+=1
        # print("time processing per event", time.time()-start_time)
