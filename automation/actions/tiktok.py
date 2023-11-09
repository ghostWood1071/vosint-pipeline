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
                    name="type",
                    display_name="Tài khoản lấy tin",
                    val_type="select",
                    default_val="",
                    options=['account'],
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
            source_account = self.get_source_account(self.params['tiktok'])
            followed_users = self.get_user_follow(source_account.get("users_follow"))

            for account in followed_users:
                try:
                    self.get_tiktok_data(account, source_account, max_news)
                    print("______________________________________________________________")
                    source_account = self.get_source_account(self.params['tiktok'])
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

    def get_tiktok_data(self, account: Dict[str, Any], source_account: Dict[str, Any], max_news: int):
        try:
            cookies = json.loads(source_account.get("cookie"))
            # cookies = '[{"name": "tt_csrf_token", "value": "fcJwMaV1-SeT8ToJfJox-j41TbVdXyeC1FTo", "domain": ".tiktok.com", "path": "/", "expires": -1, "httpOnly": true, "secure": true, "sameSite": "Lax"}, {"name": "tt_chain_token", "value": "5VnTRLcGqmTEyxFicqS37g==", "domain": ".tiktok.com", "path": "/", "expires": 1715081903.670745, "httpOnly": true, "secure": true, "sameSite": "Lax"}, {"name": "__tea_cache_tokens_1988", "value": "{%22_type_%22:%22default%22%2C%22user_unique_id%22:%227299425036372854280%22%2C%22timestamp%22:1699529845514}", "domain": ".www.tiktok.com", "path": "/", "expires": 1700134704, "httpOnly": false, "secure": false, "sameSite": "Lax"}, {"name": "tiktok_webapp_theme", "value": "light", "domain": ".www.tiktok.com", "path": "/", "expires": 1725449904, "httpOnly": false, "secure": true, "sameSite": "Lax"}, {"name": "csrf_session_id", "value": "d2bfbf0c54507d1fa45d5db178081309", "domain": "webcast.tiktok.com", "path": "/", "expires": -1, "httpOnly": false, "secure": true, "sameSite": "None"}, {"name": "s_v_web_id", "value": "verify_lor46un4_s6XXKQAP_t68g_4Btr_8l7Y_PGiYybgdfMRE", "domain": ".tiktok.com", "path": "/", "expires": -1, "httpOnly": false, "secure": true, "sameSite": "None"}, {"name": "perf_feed_cache", "value": "{%22expireTimestamp%22:1699700400000%2C%22itemIds%22:[%227283425131404233985%22]}", "domain": ".www.tiktok.com", "path": "/", "expires": 1699961850, "httpOnly": false, "secure": true, "sameSite": "Lax"}, {"name": "passport_csrf_token", "value": "e32038de3b24d52cac74ef67729485c3", "domain": ".tiktok.com", "path": "/", "expires": 1704713857.7703, "httpOnly": false, "secure": true, "sameSite": "None"}, {"name": "passport_csrf_token_default", "value": "e32038de3b24d52cac74ef67729485c3", "domain": ".tiktok.com", "path": "/", "expires": 1704713857.770433, "httpOnly": false, "secure": false, "sameSite": "Lax"}, {"name": "multi_sids", "value": "7290765131746362376%3A2fdb8eb8987156a2d362c29a44a3b52b", "domain": ".tiktok.com", "path": "/", "expires": 1704713895.096808, "httpOnly": true, "secure": true, "sameSite": "Lax"}, {"name": "cmpl_token", "value": "AgQQAPOFF-RO0rUQ7uXSuR0x_y1dVioH_4oOYNOujg", "domain": ".tiktok.com", "path": "/", "expires": 1704713895.096957, "httpOnly": true, "secure": true, "sameSite": "Lax"}, {"name": "sid_guard", "value": "2fdb8eb8987156a2d362c29a44a3b52b%7C1699529894%7C15552000%7CTue%2C+07-May-2024+11%3A38%3A14+GMT", "domain": ".tiktok.com", "path": "/", "expires": 1730633895.097017, "httpOnly": true, "secure": true, "sameSite": "Lax"}, {"name": "uid_tt", "value": "bcf029d7cbebeb7be8a3e4ef44f3c4012c9bf5ca18f4385b3a43315f7ecfcf50", "domain": ".tiktok.com", "path": "/", "expires": 1715081895.097043, "httpOnly": true, "secure": true, "sameSite": "Lax"}, {"name": "uid_tt_ss", "value": "bcf029d7cbebeb7be8a3e4ef44f3c4012c9bf5ca18f4385b3a43315f7ecfcf50", "domain": ".tiktok.com", "path": "/", "expires": 1715081895.097067, "httpOnly": true, "secure": true, "sameSite": "None"}, {"name": "sid_tt", "value": "2fdb8eb8987156a2d362c29a44a3b52b", "domain": ".tiktok.com", "path": "/", "expires": 1715081895.097092, "httpOnly": true, "secure": true, "sameSite": "Lax"}, {"name": "sessionid", "value": "2fdb8eb8987156a2d362c29a44a3b52b", "domain": ".tiktok.com", "path": "/", "expires": 1715081895.097116, "httpOnly": true, "secure": true, "sameSite": "Lax"}, {"name": "sessionid_ss", "value": "2fdb8eb8987156a2d362c29a44a3b52b", "domain": ".tiktok.com", "path": "/", "expires": 1715081895.097152, "httpOnly": true, "secure": true, "sameSite": "None"}, {"name": "sid_ucp_v1", "value": "1.0.0-KDQ0NmI5MmRlMzdjNjAwZDMyNzAzMjA0Mzg5MzdhZWNlMTJlNTRhYjMKIAiIiK_UpYiAl2UQpomzqgYYswsgDDD5gLipBjgEQOoHEAMaBm1hbGl2YSIgMmZkYjhlYjg5ODcxNTZhMmQzNjJjMjlhNDRhM2I1MmI", "domain": ".tiktok.com", "path": "/", "expires": 1715081895.097177, "httpOnly": true, "secure": true, "sameSite": "Lax"}, {"name": "ssid_ucp_v1", "value": "1.0.0-KDQ0NmI5MmRlMzdjNjAwZDMyNzAzMjA0Mzg5MzdhZWNlMTJlNTRhYjMKIAiIiK_UpYiAl2UQpomzqgYYswsgDDD5gLipBjgEQOoHEAMaBm1hbGl2YSIgMmZkYjhlYjg5ODcxNTZhMmQzNjJjMjlhNDRhM2I1MmI", "domain": ".tiktok.com", "path": "/", "expires": 1715081895.097203, "httpOnly": true, "secure": true, "sameSite": "None"}, {"name": "store-idc", "value": "alisg", "domain": ".tiktok.com", "path": "/", "expires": 1715081894.10066, "httpOnly": true, "secure": false, "sameSite": "Lax"}, {"name": "store-country-code", "value": "vn", "domain": ".tiktok.com", "path": "/", "expires": 1715081894.100715, "httpOnly": true, "secure": false, "sameSite": "Lax"}, {"name": "store-country-code-src", "value": "uid", "domain": ".tiktok.com", "path": "/", "expires": 1715081894.100733, "httpOnly": true, "secure": false, "sameSite": "Lax"}, {"name": "tt-target-idc", "value": "alisg", "domain": ".tiktok.com", "path": "/", "expires": 1715081894.100771, "httpOnly": true, "secure": false, "sameSite": "Lax"}, {"name": "tt-target-idc-sign", "value": "H7VAOXumfm3REGilbjyPfkQrecxPDyI1eyq_KU3La24_w7R8g-oz94Cnna-FgUnYyA8NiI_T0KgQDunVP6ALM-BRVT3shTn6gYi7xNYNkSw45hQBbh3Ko32xkuLCUvvSnUdMcIhcf1uOXnZmjSF_ORU6ShZeLoaAmZLxISFdBjLBSknzVKcwAdvsZRdJXHIZO8M5uwd8QWHu2wIjukvd7uDMy1eIpSIe0mJM87j6aD37cxuYSUzrD9997AljwNU4OhI2-yQX-Ike-djzCYCHNOzSyQfmkI95pIGRyKxmKFtEbldwuHXH7OWoA-QcaxCY0rTV77J3YmMUv5Ey-Ni5G7W8JJOkT0O1qh2wWuwhWUTW8Tc_jzkKHm0HBa15coQBvpb917vWx6ZGzFSgeUWb_yf8FJhgzYhcDx_38D5pGFvh55wWCIgUmhaLuhKXQEBXDNGwZx4xUioX5v_OWgioN5nBzmzShol7ldkgVbn54610KjSnb1Z_aENYlRpvy1xM", "domain": ".tiktok.com", "path": "/", "expires": 1731065901.610648, "httpOnly": true, "secure": false, "sameSite": "Lax"}, {"name": "tea_sid", "value": "3f7d5843-e967-425d-b0ed-43174b46a00f", "domain": "www.tiktok.com", "path": "/", "expires": -1, "httpOnly": false, "secure": true, "sameSite": "Strict"}, {"name": "passport_fe_beating_status", "value": "true", "domain": ".www.tiktok.com", "path": "/", "expires": -1, "httpOnly": false, "secure": false, "sameSite": "Lax"}, {"name": "ttwid", "value": "1%7CDrQR3eQknqr8AVB9Z_ljyGM8v3Cikb5812A1jLtBHPw%7C1699529904%7Ca6b4c1720b20bb57cd00385b32d9b94e4826fd98f22e0d5bf91c53650d89905e", "domain": ".tiktok.com", "path": "/", "expires": 1731065904.962998, "httpOnly": true, "secure": true, "sameSite": "None"}, {"name": "odin_tt", "value": "77a784d574ef29fd6867f00daee05550e2acb3dbaebd730d024e171a8872ac02e0df81991b403dc40c79599a6fb4f4bfb2947e7fdf5e2023ab280d31b4491e68318d22dffc6455f9e268de63e646b186", "domain": ".tiktok.com", "path": "/", "expires": 1731065906.099331, "httpOnly": true, "secure": false, "sameSite": "Lax"}, {"name": "msToken", "value": "2L7nm9ibF7MHpWwcq2LiQuge8OuSdwI7ICh3dV6qxi47ZHkIQTuK706SgI-22DW3On6zuJSHzGD9AoS_i55UAomDW3S5MsJTCFUxhnhWkzdNvIUw1HWkheUD7pmNlQJ0TzKaO_topKNCHl4=", "domain": ".tiktok.com", "path": "/", "expires": 1700393908.917799, "httpOnly": false, "secure": true, "sameSite": "None"}, {"name": "msToken", "value": "2L7nm9ibF7MHpWwcq2LiQuge8OuSdwI7ICh3dV6qxi47ZHkIQTuK706SgI-22DW3On6zuJSHzGD9AoS_i55UAomDW3S5MsJTCFUxhnhWkzdNvIUw1HWkheUD7pmNlQJ0TzKaO_topKNCHl4=", "domain": "www.tiktok.com", "path": "/", "expires": 1707305908, "httpOnly": false, "secure": false, "sameSite": "Lax"}]'
            cookies = json.loads(cookies)
            print(type(cookies))
            link = account.get("account_link")
            if str(account.get("social_type")) == "Object":
                datas = tiktok_channel(browser=self.driver.get_driver(), link_person=link, cookies=cookies, crawl_acc_id=account.get("_id"), max_news=max_news)
            else:
                print('cannot determine social_type')
            return datas
        except Exception as e:
            raise e