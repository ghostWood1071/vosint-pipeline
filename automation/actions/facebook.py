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

    def get_facebook_data(self, account:Dict[str, Any]):
        try:
            
            link = account.get("account_link")
            link = re.sub("www\.", "mbasic.", link)
            if str(account.get("social_type")) == "Object":
                datas = fb_canhan(browser=self.driver.get_driver(), link_person=link)
            elif str(account.get("social_type")) == "Group":
                datas = fb_groups(browser=self.driver.get_driver(), link_person=link)
            else:
                datas = fb_page(browser=self.driver.get_driver(), link_person=link + "?v=timeline")
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
    
    def exec_func(self, input_val=None, **kwargs):
        collection_name = "facebook"
        time.sleep(2)
        try:
            source_account = self.get_source_account(self.params['account'])
            followed_users =  self.get_user_follow(source_account.get("users_follow"))
            data = []
            for account in followed_users:
                try:
                    fb_data = self.get_facebook_data(account)
                    data.extend(fb_data)
                except Exception as e:
                    pass
            self.insert_data(data, collection_name)
        except Exception as e:
            pass
