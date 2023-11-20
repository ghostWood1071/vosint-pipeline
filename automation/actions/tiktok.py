import traceback

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
from .tiktok_crawler.cookies_expire_exception import CookiesExpireException
from ..common import ActionInfo, ActionStatus


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
                    name="type",
                    display_name="Tài khoản lấy tin",
                    val_type="select",
                    default_val="",
                    options=['account'],
                    validators=["required_"],
                ),
                ParamInfo(
                    name="cookies",
                    display_name="Cookies",
                    val_type="str",
                    default_val="",
                    validators=["required_"],
                )
            ],
            z_index=14,
        )

    def exec_func(self, input_val=None, **kwargs):
        collection_name = "tiktok"
        try:
            first_action = kwargs['first_action']
            max_news = int(first_action['params']['max_new'])
        except:
            print('max_news cannot be converted to integer')
            max_news = 0
        time.sleep(2)
        try:
            pipeline_id = kwargs.get('pipeline_id')
            source_account = self.get_source_account(self.params['tiktok'])
            followed_users = self.get_user_follow(source_account.get("users_follow"))

            if self.params['cookies'].strip() not in ['', '[]'] and self.params['cookies'] is not None:
                cookies_str = self.params['cookies']
            else:
                cookies_str = source_account.get('cookie')
            try:
                cookies = json.loads(cookies_str)
            except Exception as e:
                print(e)
                cookies = []


            browser = self.driver.get_driver()
            page = browser.new_page()
            try:
                tiktok_channel(page=page, accounts=followed_users, cookies=cookies,
                                    max_news=max_news, create_log=self.create_log, pipeline_id=pipeline_id)
            except CookiesExpireException as e:
                raise e
            except Exception as e:
                traceback.print_exc()
                print(e)
        except Exception as e:
            traceback.print_exc()
            raise e

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
