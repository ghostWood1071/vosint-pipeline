from common.internalerror import *
from requests.auth import HTTPProxyAuth
from ..common import ActionInfo, ActionType, ParamInfo
from .baseaction import BaseAction
import requests
from models import MongoRepository
from datetime import datetime
import time
from playwright.sync_api import Page
from bson.objectid import ObjectId
from playwright.sync_api import TimeoutError

class TtxvnAction(BaseAction):
    @classmethod
    def get_action_info(cls) -> ActionInfo:
        return ActionInfo(
            name="ttxvn",
            display_name="TTXVN",
            action_type=ActionType.COMMON,
            readme="Thông tấn xã Việt Nam",
            param_infos=[
                ParamInfo(
                    name="limit",
                    display_name="limit news",
                    val_type="select",
                    default_val=20,
                    options=[i*20 for i in range(1,10)],
                    validators=["required_"],
                ),
                ParamInfo(
                    name="is_root",
                    display_name="is_root",
                    val_type="bool",
                    default_val='True',
                    validators=["required_"],
                ),
                ParamInfo(
                    name="send_queue",
                    display_name="send_queue",
                    val_type="bool",
                    default_val='False',
                    validators=["required_"],
                )
            ],
            z_index=20,
        )
    
    def validate_input(self, value, except_values, default, data_type):
        if value in except_values: 
            return default
        else:
            return data_type(value)
    
    def get_news(self, limit):
        try:
            url = "https://news.vnanet.vn/API/ApiAdvanceSearch.ashx"
            params = {
                "func": "searchannonimous",
                "index": "0",
                "limit": str(limit),
                "data": '[{"ContentType":"date","Key":"Created","LogicCon":"geq","Value":"2 day","ValueType":"1"},{"ContentType":"combobox","Key":"ServiceCateID","LogicCon":"eq","Value":"1097","ValueType":"1"},{"ContentType":"number","Key":"SCode","LogicCon":"eq","Value":"1","ValueType":"1"},{"ContentType":"combobox","Key":"QCode","LogicCon":"eq","Value":17,"ValueType":"1"}]',
                "total": "514",
                "lid": "1066",
                "psid": "undefined"
            }
            response = requests.get(url, params=params)
            if response.status_code == 200: 
                data = response.json()['data']['data']
            else:
                data = []
        except Exception as e:
            data = []
        return data

    def check_exists(self, artical):
        check_url_exist = '0'
        artical['PublishDate']=datetime.strptime(artical['PublishDate'],"%Y-%m-%dT%H:%M:%S.%f")
        artical['Created']=datetime.strptime(artical['Created'],"%Y-%m-%dT%H:%M:%S.%f")
        try:
            a,b = MongoRepository().get_many(collection_name='ttxvn',filter_spec={"ArticleID":artical["ArticleID"]})
            del a
            if str(b) != '0':
                print('url already exist')
                check_url_exist = '1'
                return True
        except:
            pass
        if check_url_exist == '0':    
            return False

    def send_queue(self, message): 
        pass

    def select(self, from_element, expr, by = "css="):
        element = from_element.locator(f"{by}{expr}")
        element = [element.nth(i) for i in range(element.count())]
        return element   
     
    def test_proxy(url, proxy):
        try:
            username = proxy.get("username")
            password = proxy.get("password")
            port = proxy.get("port")
            ip = proxy.get("ip")
            auth = None
            if username != "" and password != "":
                auth = HTTPProxyAuth(proxy.get("username"), proxy.get("password"))
            if auth != None:
                response = response = requests.get(url, proxies={'http': f'{ip}:{port}', 'https': f'{ip}:{port}'}, timeout=10, auth=auth)
            else:
                response = requests.get(url, proxies={'http': f'{ip}:{port}', 'https': f'{ip}:{port}'}, timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def get_active_proxy_index(self, url, proxies, index = 0):
        active_index = -1
        for i in range (index, len(proxies)):
            if self.test_proxy(url, proxies[i]):
                return i
        return active_index

    def login_ttxvn(self, page:Page, username, password):
        try: 
            page.goto('https://news.vnanet.vn')
            page.click('#btnSignIn')
            page.fill('#username', username)
            page.fill('#password', password)
            page.click('#login')
            time.sleep(1)
            cookies = page.context.cookies() 
            account = MongoRepository().get_one("user_config", {"username": username, "password": password})
            MongoRepository().update_many("user_config", {"_id": account["_id"]}, {"$set": {"cookies": cookies}})
            return cookies
        except TimeoutError as e:
            raise e
 
    def get_ttxvn_account(self):
        config_ttxvn = MongoRepository().get_one(
            collection_name="user_config", 
            filter_spec={"tag": "using"}
        )
        return config_ttxvn

    def get_proxies(self):
        proxies_filter = [ObjectId(proxy) for proxy in self.account.get("list_proxy")]
        proxies, _ = MongoRepository().get_many("proxy", filter_spec={"_id": {"$in": proxies_filter}})
        return proxies

    def crawl_article_content(self, articles):
        if self.account.get('cookies') == None:
            self.account['cookies'] = self.login_ttxvn(
                self.driver.get_page(),
                self.account.get('username'), 
                self.account.get('password'))
        self.driver.add_cookies(self.account.get('cookies'))
        proxy_index = 0
        for article in articles:
            try:
                link  = 'https://news.vnanet.vn/FrontEnd/PostDetail.aspx?id='+ str(article.get("ID"))
                self.driver.goto(link)
                if "https://vnaid.vnanet.vn/core/login" in self.driver.get_current_url():
                    self.account['cookies'] = self.login_ttxvn(
                        self.driver.get_page(),
                        self.account.get('username'), 
                        self.account.get('password')
                    )
                    self.driver.add_cookies(self.account.get('cookies'))
                try:
                    content = self.select(self.driver.get_page(),".post-content")[0].inner_text()
                    article["content"] = str(content).replace(article["Title"], "", 1)
                except TimeoutError as e:
                    raise Exception("can not select element")
            except TimeoutError as e:
                proxy_index = self.get_active_proxy_index("https://news.vnanet.vn", self.proxies ,proxy_index)
                if proxy_index < 0:
                    raise Exception("There is no proxy work")
                proxy = self.proxies[proxy_index]
                self.driver.init_proxy(proxy)
            except Exception as e2:
                raise e2
    def exec_func(self, input_val=None, **kwargs):
        if not input_val:
            raise InternalError(
                ERROR_REQUIRED, params={"code": ["FROM_ELEM"], "msg": ["From element"]}
            )
        
        is_root = self.validate_input(
            self.params.get('is_root'), 
            except_values=["None", "", None], 
            default= True, 
            data_type=bool
        )
        limit = self.validate_input(
            self.params.get("limit"),
            except_values=["None", "", None],
            default='20',
            data_type=str
        )
        send_queue = self.validate_input(
            self.params.get("send_queue"),
            except_values=["None", "", None],
            default=False,
            data_type=bool
        )
        #MongoRepository().insert_one(collection_name='ttxvn',doc=article)
        self.account = self.get_ttxvn_account()
        self.proxies = self.get_proxies()

        news_headers = []
        if is_root == True:
            news_headers = self.get_news(limit)
        elif is_root == False and send_queue == True:
                pass
        else:
                pass

        for header in news_headers:
            if self.check_exists(header):
                continue
                #process here
        
                    
        # else:
        #     # API call failed
        #     print("Error:", response.status_code)
        return "Succes: True"
