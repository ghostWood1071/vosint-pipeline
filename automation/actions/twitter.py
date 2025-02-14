from common.internalerror import *
from ..common import ActionInfo, ActionType, ParamInfo, ActionStatus
from .baseaction import BaseAction
from models import MongoRepository
from playwright.sync_api import Playwright, sync_playwright
import time
from .twitter_crawler.authenticate import authenticate
from bson.objectid import ObjectId
from .twitter_crawler.twitter_account import twitter_account
from pymongo.errors import PyMongoError
from typing import *
import traceback
import json
import re

def select(from_element, expr, by = "css="):
    element = from_element.locator(f"{by}{expr}")
    element = [element.nth(i) for i in range(element.count())]
    return element


class TwitterAction(BaseAction):
    @classmethod
    def get_action_info(cls) -> ActionInfo:
        return ActionInfo(
            name="twitter",
            display_name="Twitter",
            action_type=ActionType.COMMON,
            readme="twitter",
            param_infos=[
                ParamInfo(
                    name="type",
                    display_name="Tài khoản lấy tin",
                    val_type="select",
                    default_val="",
                    options = ['account'],
                    validators=["required_"],
                )
            ],
            z_index=14,
        )

    def exec_func(self, input_val=None, **kwargs):
        collection_name = "twitter"
        try:
            first_action = kwargs['first_action']
            max_news = int(first_action['params']['max_new'])
        except:
            print('max_news cannot be converted to integer')
            max_news = 0

        time.sleep(2)
        try:
            try:
                self.driver.goto("https://twitter.com/")
            except:
                pass
            pipeline_id = kwargs['pipeline_id']
            source_account = self.get_source_account(self.params['twitter'])
            followed_users =  self.get_user_follow(source_account.get("users_follow"))
            for account in followed_users:
                try:
                    self.get_twitter_data(account, source_account, max_news)
                    print("______________________________________________________________")
                    source_account = self.get_source_account(self.params['twitter'])
                    self.create_log(ActionStatus.COMPLETED, account.get('account_link'), pipeline_id)
                except Exception as e:
                    print(e)
                    traceback.print_exc()
            # self.insert_data(data, collection_name)
        except Exception as e:
            pass


    def get_source_account(self, id: str):
        try:
            source_account = MongoRepository().get_one('socials', {"_id": ObjectId(id)})
            if source_account == None:
                raise PyMongoError("account not found")
            return source_account
        except Exception as e:
            raise e

    def get_user_follow(self, list_ids: List[Dict[str, Any]]):
        try:
            id_filter = [ObjectId(acc.get("follow_id")) for acc in list_ids]
            accounts, _ = MongoRepository().get_many("social_media", {"_id": {"$in": id_filter}})
            return accounts
        except Exception as e:
            raise e

    def get_twitter_data(self, account:Dict[str, Any], source_account:Dict[str, Any], max_news: int):
        try:
            cookies = json.loads(source_account.get("cookie"))
            username = source_account.get("username")
            password = source_account.get("password")
            source_account_id = str(source_account.get("_id"))
            link = account.get("account_link")
            header = account.get("social_name")
            if str(account.get("social_type")) == "Object":
                datas = twitter_account(browser=self.driver.get_driver(), link_person=link, cookies = cookies, account=username, password=password, source_acc_id=source_account_id, crawl_acc_id = account.get("_id"), header=header, max_news=max_news)
            return datas
        except Exception as e:
            raise e

    