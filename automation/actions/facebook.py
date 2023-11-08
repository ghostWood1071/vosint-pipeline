from common.internalerror import *
from .facebook_crawler.fb_canhan import fb_canhan
from .facebook_crawler.fb_groups import fb_groups
from .facebook_crawler.fb_page import fb_page


from ..common import ActionInfo, ActionType, ParamInfo, SelectorBy
from .baseaction import BaseAction
import json
import time
from models import MongoRepository
from bson.objectid import ObjectId
from pymongo.errors import PyMongoError
from typing import *
import re
import traceback

class FacebookAction(BaseAction):
    @classmethod
    def get_action_info(cls) -> ActionInfo:
        return ActionInfo(
            name="fb",
            display_name="Facebook",
            action_type=ActionType.COMMON,
            readme="fb",
            param_infos=[
                ParamInfo(
                    name="account",
                    display_name="Tài khoản lấy tin",
                    val_type="str",
                    default_val="",
                    validators=["required_"],
                )
            ],
            z_index=14,
        )
    
    def get_source_account(self, id:str):
        try:
            source_account =  MongoRepository().get_one('socials', {"_id": ObjectId(id)})
            if source_account == None:
                raise PyMongoError("account not found")
            return source_account
        except Exception as e:
            raise e
        
    def get_user_follow(self, list_ids:List[Dict[str, Any]]):
        try:
            id_filter = [ObjectId(acc.get("follow_id")) for acc in list_ids]
            accounts,_ = MongoRepository().get_many("social_media", {"_id": {"$in": id_filter}})
            return accounts
        except Exception as e:
            raise e

    def get_facebook_data(self, account:Dict[str, Any], source_account:Dict[str, Any], max_news:int):
        try:
            cookies = json.loads(source_account.get("cookie")) if source_account.get("cookie") not in [" "] else []
            username = source_account.get("username")
            password = source_account.get("password")
            source_account_id = str(source_account.get("_id"))
            link = account.get("account_link")
            link = re.sub("www\.", "m.", link)
            if str(account.get("social_type")) == "Object":
                datas = fb_canhan(
                        browser=self.driver.get_driver(), 
                        link_person=link, 
                        cookies = cookies, 
                        account=username, 
                        password=password, 
                        source_acc_id=source_account_id, 
                        crawl_acc_id = account.get("_id"),
                        max_news = max_news
                    )
            elif str(account.get("social_type")) == "Group":
                datas = fb_groups(
                        browser=self.driver.get_driver(), 
                        link_person=link, 
                        cookies = cookies, 
                        account=username, 
                        password=password, 
                        source_acc_id=source_account_id, 
                        crawl_acc_id = account.get("_id"),
                        max_news = max_news
                    )
            else:
                datas = fb_page(
                    browser=self.driver.get_driver(), 
                    link_person=link + "?v=timeline", 
                    cookies = cookies, 
                    account=username, 
                    password=password, 
                    source_acc_id=source_account_id, 
                    crawl_acc_id = account.get("_id"),
                    max_news = max_news
                )
            return datas
        except Exception as e:
            raise e

    def insert_data(self, data, collection_name):
        for row in data:
            try:
                check_url_exist = "0"
                a, b = MongoRepository().get_many(
                    collection_name=collection_name,
                    filter_spec={
                        "header": row["header"],
                        "content": row["content"],
                    },
                )
                del a
                print("bbbbbbbb", b)
                if str(b) != "0":
                    print("url already exist")
                    check_url_exist = "1"
                if check_url_exist == "0":
                    try:
                        print(row)
                        MongoRepository().insert_one(
                            collection_name=collection_name, doc=row
                        )
                    except:
                        print(
                            "An error occurred while pushing data to the database!"
                        )
            except Exception as e:
                raise e
    
    def get_max_news_quantity(self, kwargs):
        try:
            max_news = int(kwargs.get("first_action").get("params").get("max_new"))
        except Exception as e:
            max_news = 10
        return max_news
    
    def exec_func(self, input_val=None, **kwargs):
        collection_name = "facebook"
        time.sleep(2)
        try:
            source_account = self.get_source_account(self.params['fb'])
            followed_users =  self.get_user_follow(source_account.get("users_follow"))
            max_news = self.get_max_news_quantity(kwargs)
            for account in followed_users:
                try:
                    self.get_facebook_data(account, source_account, max_news)
                    print("______________________________________________________________")
                    source_account = self.get_source_account(self.params['fb'])
                    # data.extend(fb_data)
                except Exception as e:
                    print(e)
                    traceback.print_exc()
            # self.insert_data(data, collection_name)
        except Exception as e:
            traceback.print_exc()
            raise e
