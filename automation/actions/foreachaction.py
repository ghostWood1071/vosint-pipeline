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
from .tiktok import TiktokAction
from models import MongoRepository
from datetime import datetime
from ..common import ActionInfo, ActionStatus
from random import randint
from .sendkeyaction import SendKeyAction
from .typingaction import TypingAction
from .inputs.urlinputaction import URLInputAction
import traceback
from core.config import settings
import json

def get_action_class(name: str):
    action_dict = {
        "goto": GotoAction,
        "get_urls": GetUrlsAction,
        "get_news_info": GetNewsInfoAction,
        "select":  SelectAction,
        "get_attr":  GetAttrAction,
        "foreach":  ForeachAction,
        "click": ClickAction,
        "for": ForAction,
        "login": LoginAction,
        "scroll": ScrollAction,
        "hover": HoverAction,
        "fb": FacebookAction,
        "twitter": TwitterAction,
        "feed new": FeedAction,
        "ttxvn": TtxvnAction,
        "send_key" : SendKeyAction,
        "typing": TypingAction,
        "url_input": URLInputAction,
        "tiktok": TiktokAction
    }
    action_cls = action_dict.get(name)
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
                    default_val="True",
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
            task_id = MongoRepository().insert_one("queue", 
                                                   {
                                                       "url": url, 
                                                        "pipeline": pipeline_id, 
                                                        "source": source_name,
                                                        "expire": datetime.now()
                                                    })
            if task_id:
                message["task_id"] = str(task_id)
                KafkaProducer_class().write(settings.KAFKA_TOPIC_CRAWLING_NAME, message)
                print('write to kafka ...')
                self.create_log(ActionStatus.INQUEUE, f'news {str(url)} transported to queue', pipeline_id)
        except Exception as e:
            traceback.print_exc()
            if task_id != None:
                print(f"send to kafka failed, delete_task: {task_id}")
                MongoRepository().delete_one("queue", {"_id": task_id})
            raise e

    def check_queue(self, url, day_range):
        item = MongoRepository().get_one("queue", 
                                {
                                   "url": url, 
                                   "$and": [
                                    {"created_at": {"$gte": day_range[0]}}, 
                                    {"created_at": {"$lte": day_range[1]}}
                                   ]
                                })
        return item != None
        
    def check_exists(self, url, days):
        existed_news, existed_count = MongoRepository().get_many(
                        collection_name="News", filter_spec={"data:url": str(url),
                                                             "$and": [ 
                                                                {"created_at": {"$gte": days[0]}},
                                                                {"created_at": {"$lte": days[1]}}
                                                             ]}
                    )
        del existed_news
        return existed_count > 0

    def exec_func(self, input_val=None, **kwargs):
        actions = self.params["actions"]
        flatten = False if "flatten" not in self.params else self.params["flatten"]
        # Run foreach actions
        if kwargs.get("mode_test") in [None, 'false', 'False', False]:
            kwargs.update({"mode_test": False})
        res = []
        if input_val is not None:
            day_range = 10 
            check_time = self.get_check_time(day_range)
            for val in input_val:
                # check duplicate
                if kwargs["mode_test"] != True:
                    data_url = str(val)
                    start_check = datetime.now()
                    is_existed = self.check_exists(data_url,check_time)
                    end_check = datetime.now()
                    print(f"checking time: {(end_check-start_check).microseconds/1000} miliseconds")
                    if is_existed:
                        print("url already exist")
                        continue
                if str(self.params["send_queue"]) == "True" and kwargs["mode_test"] != True:
                    kwargs_leaf = kwargs.copy()
                    kwargs_leaf["list_proxy"] = [self.random_proxy(kwargs.get("list_proxy"))]
                    kwargs_leaf["origin"] = 
                    message = {
                        "actions": actions, 
                        "input_val": data_url, 
                        "kwargs": kwargs_leaf
                    }
                    try:
                        is_existed_inqueue = self.check_queue(data_url, check_time)
                        if not is_existed_inqueue:
                            self.send_queue(message, kwargs["pipeline_id"], data_url, kwargs["source_name"])
                        else:
                            print("url existed in queue")
                    except Exception as e:
                        print("send queue failed")
                        
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
