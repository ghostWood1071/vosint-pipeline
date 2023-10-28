from common.internalerror import *

from ..common import ActionInfo, ActionType, ParamInfo
from .baseaction import BaseAction

from models.kafka_producer import KafkaProducer_class
from .clickaction import ClickAction
from .getattraction import GetAttrAction
from .getnewsinfoaction import GetNewsInfoAction
from .geturlsaction import GetUrlsAction
from .gotoaction import GotoAction
from .login import LoginAction
from .selectaction import SelectAction
from .foraction import ForAction
from .scrollaction import ScrollAction
from .hoveraction import HoverAction
from .facebook import FacebookAction
from .twitter import TwitterAction
from .feedaction import FeedAction
from .ttxvn import TtxvnAction
from models import MongoRepository
from datetime import datetime
from ..common import ActionInfo, ActionStatus
from random import randint
from datetime import timedelta
from bson.objectid import ObjectId

def get_action_class(name: str):
    action_cls = (
        GotoAction
        if name == "goto"
        else GetUrlsAction
        if name == "get_urls"
        else GetNewsInfoAction
        if name == "get_news_info"
        else SelectAction
        if name == "select"
        else GetAttrAction
        if name == "get_attr"
        else ForeachAction
        if name == "foreach"
        else ClickAction
        if name == "click"
        else ForAction
        if name == "for"
        else LoginAction
        if name == "login"
        else ScrollAction
        if name == "scroll"
        else HoverAction
        if name == "hover"
        else FacebookAction
        if name == "fb"
        else TwitterAction
        if name == "twitter"
        else FeedAction
        if name == "feed new"
        else TtxvnAction
        if name == "ttxvn"
        else None
    )
    if action_cls is None:
        raise InternalError(
            ERROR_NOT_FOUND,
            params={"code": [f"{name.upper()}_ACTION"], "msg": [f"{name} action"]},
        )

    return action_cls


class ForeachAction(BaseAction):
    @classmethod
    def get_action_info(cls) -> ActionInfo:
        return ActionInfo(
            name="foreach",
            display_name="Foreach",
            action_type=ActionType.COMMON,
            readme="Cấu trúc lặp cho mỗi phần tử",
            param_infos=[
                ParamInfo(
                    name="actions",
                    display_name="List of actions",
                    val_type="list",
                    default_val=[],
                    validators=["required"],
                ),
                ParamInfo(
                    name="send_queue",
                    display_name="Send_Queue",
                    val_type="select",
                    default_val="False",
                    options=["False", "True"],
                    validators=["required_"],
                ),
            ],
            z_index=6,
        )
    
    def random_proxy(self, proxy_list):
        if str(proxy_list) == '[]' or str(proxy_list) == '[None]' or str(proxy_list) == 'None':
            return 
        proxy_index = randint(0, len(proxy_list)-1)
        return proxy_list[proxy_index]
    
    def send_queue(self, message, pipeline_id, url, source_name):
        try:
            task_id = MongoRepository().insert_one("queue", {"url": url, "pipeline": pipeline_id, "source": source_name})
            message["task_id"] = str(task_id)
            KafkaProducer_class().write("crawling_", message)
            print('write to kafka ...')
            self.create_log(ActionStatus.INQUEUE, f'news {str(url)} transported to queue', pipeline_id)
        except Exception as e:
            if task_id != None:
                MongoRepository().delete_one("queue", {"_id": task_id})
            raise e

    def check_queue(self, url, day_range):
        item = MongoRepository().get_one("queue", 
                                {
                                   "url": url, 
                                   "created_at": {"$gte": day_range[0]}, 
                                   "created_at": {"$lte": day_range[1]} 
                                })
        return item != None
        
    def get_check_time(self, day_range):
        date_now = datetime.now()
        end_time = datetime(date_now.year, date_now.month, date_now.day, 0, 0, 0, 0)
        start_time = end_time - timedelta(day_range)
        end_str = datetime.strftime(end_time, "%Y/%m/%d 23:59:00")
        start_str = datetime.strftime(start_time, "%Y/%m/%d %H:%M:%S")
        return (start_str, end_str)

    def check_exists(self, url, days):
       
        existed_news, existed_count = MongoRepository().get_many(
                        collection_name="News", filter_spec={"data:url": str(url), 
                                                             "created_at": {"$gte": days[0]},
                                                             "created_at": {"$lte": days[1]}}
                    )
        del existed_news
        return existed_count > 0

    def exec_func(self, input_val=None, **kwargs):
        actions = self.params["actions"]
        flatten = False if "flatten" not in self.params else self.params["flatten"]
        # print(input_val)
        # Run foreach actions
        res = []
        if input_val is not None:
            day_range = 10 
            check_time = self.get_check_time(day_range)
            for val in input_val:
                if kwargs["mode_test"] != True:
                    data_url = str(val)
                    start_check = datetime.now()
                    is_existed = self.check_exists(data_url,check_time)
                    end_check = datetime.now()
                    print(f"checking time: {(end_check-start_check).microseconds/1000} miliseconds")
                    if is_existed:
                        print("url already exist")
                        continue
                if str(self.params["send_queue"]) == "True":
                    kwargs_leaf = kwargs.copy()
                    kwargs_leaf["list_proxy"] = [self.random_proxy(kwargs.get("list_proxy"))]
                    message = {"actions": actions, "input_val": data_url, "kwargs": kwargs_leaf}
                    try:
                        is_existed_inqeueu = self.check_queue(data_url, check_time)
                        if not is_existed_inqeueu:
                            self.send_queue(message, kwargs["pipeline_id"], data_url, kwargs["source_name"])
                        else:
                            print("url existed in queue")
                    except Exception as e:
                        print("url existed in queue")
                        pass
                    if kwargs["mode_test"] == True:
                        break
                else:
                    
                    if flatten == False:
                        res.append(self.__run_actions(actions, val, **kwargs))
                    else:
                        res += self.__run_actions(actions, val, **kwargs)
                    if kwargs["mode_test"] == True:  
                        break
        return res

    def __run_actions(self, actions: list[dict], input_val, **kwargs):
        start_lol = datetime.now()
        tmp_val = input_val
        
        for act in actions:
            params = act["params"] if "params" in act else {}
            try:
                # print(act["id"])
                id_schema = act["id"]
                # print(a)
                params["id_schema"] = id_schema
            except:
                pass
            action = get_action_class(act["name"])(self.driver, self.storage, **params)
            tmp_val = action.run(tmp_val, **kwargs)
        return tmp_val
