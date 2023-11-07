from common.internalerror import *
from ..common import ActionInfo, ActionType, ParamInfo
from .baseaction import BaseAction
from models import MongoRepository
from pymongo.errors import PyMongoError
from bson.objectid import ObjectId
from playwright.sync_api import Playwright, sync_playwright
import time
from typing import *
import json
import re
from .tiktok_crawler.tiktok_channel import tiktok_channel


def select(from_element, expr, by="css="):
    element = from_element.locator(f"{by}{expr}")
    element = [element.nth(i) for i in range(element.count())]
    return element


class TiktokAction(BaseAction):
    @classmethod
    def get_action_info(cls) -> ActionInfo:
        return ActionInfo(
            name="tiktok",
            display_name="Tiktok",
            action_type=ActionType.COMMON,
            readme="tiktok",
            param_infos=[
                ParamInfo(
                    name="link_person",
                    display_name="cookie",
                    val_type="str",
                    default_val="",
                    validators=["required_"],
                )
            ],
            z_index=14,
        )

    def exec_func(self, input_val=None, **kwargs):
        collection_name = "tiktok"
        time.sleep(2)
        try:
            source_account = self.get_source_account(self.params['account'])
            followed_users = self.get_user_follow(source_account.get("users_follow"))
            for account in followed_users:
                try:
                    self.get_tiktok_data(account, source_account)
                    print("______________________________________________________________")
                    source_account = self.get_source_account(self.params['account'])
                    # data.extend(fb_data)
                except Exception as e:
                    print(e)
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

    def get_user_follow(self, list_ids:List[Dict[str, Any]]):
        try:
            id_filter = [ObjectId(acc.get("follow_id")) for acc in list_ids]
            accounts,_ = MongoRepository().get_many("social_media", {"_id": {"$in": id_filter}})
            return accounts
        except Exception as e:
            raise e

    def get_tiktok_data(self, account: Dict[str, Any], source_account: Dict[str, Any]):
        try:
            cookies = json.loads(source_account.get("cookie"))
            username = source_account.get("username")
            password = source_account.get("password")
            source_account_id = str(source_account.get("_id"))
            link = account.get("account_link")
            if str(account.get("social_type")) == "Object":
                datas = tiktok_channel(browser=self.driver.get_driver(), link_person=link, cookies=cookies, account=username,
                                  password=password, source_acc_id=source_account_id, crawl_acc_id=account.get("_id"))
            else:
                print('cannot determine social_type')
            return datas
        except Exception as e:
            raise e