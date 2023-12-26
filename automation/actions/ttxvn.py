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
import sys
import traceback
from models.kafka_producer import KafkaProducer_class
from ..common import ActionInfo, ActionStatus
from typing import Any
from random import randint
from datetime import timedelta
from elasticsearch import helpers
from db.elastic_main import My_ElasticSearch
from core.config import settings

import traceback
class ElementNotFoundError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

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
                    default_val='True',
                    validators=["required_"],
                ),
                ParamInfo(
                    name="document",
                    display_name="document",
                    val_type="any",
                    default_val='None'
                ),
            ],
            z_index=20,
        )
    
    def validate_input(self, value, except_values, default, data_type=Any):
        if value in except_values: 
            return default
        else:
            if data_type == Any:
                return value
            if data_type == bool:
                return str(value).lower() == 'true'
            return data_type(str(value).lower())
    
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
    
    def format_time(self, time):
        result = None
        try:
            result=datetime.strptime(time,"%Y-%m-%dT%H:%M:%S.%f")
        except Exception as e:
            result = datetime.strptime(time,"%Y-%m-%dT%H:%M:%S")
        finally:
            if result == None:
                result = datetime.now()
        return result

    def get_exists(self, articles):
        existed_ids = []
        article_ids = [article["ArticleID"] for article in articles]
        try:
            existed_articles,_ = MongoRepository().get_many(collection_name='ttxvn',filter_spec={"ArticleID": {"$in": article_ids}})
            existed_ids = [article["ArticleID"] for article in existed_articles]
        except:
            pass
        return existed_ids

    def create_es_doc(self, doc_es):
        try:
            doc_es.pop("created_at", None)
            doc_es.pop("modified_at", None)
        except:
            pass
        try:
            doc_es["id"] = str(doc_es["_id"])
            doc_es.pop("_id", None)
        except:
            pass
        try:
            doc_es["PublishDate"] = (
                str(doc_es["PublishDate"]).split(" ")[0] + "T00:00:00Z"
            )
        except:
            pass
        try:
            doc_es["Created"] = str(doc_es["Created"]).split(" ")[0] + "T00:00:00Z"
        except:
            pass
        return doc_es
    
    def insert_multiple_doc_es(self, data):
        my_es = My_ElasticSearch(
            host=settings.ELASTIC_CONNECT.split(','), 
            user="USER", 
            password="PASS", 
            verify_certs=False)
        actions = []
        for row in data:
            doc_es = row.copy() 
            doc_es = self.create_es_doc(doc_es)
            actions.append({
                "_op_type": "index",  # Specify the operation type (index, update, delete, etc.)
                "_index": 'vosint_ttxvn',  # Specify the target index
                "_source": doc_es,
                "_id": str(row["_id"])
            })
            
        try:
            helpers.bulk(my_es.es, actions)
            print("insert to elastic vosint_ttxvn")
        except Exception as e:
            print("insert to elasstic vosint_ttxvn error")

    def check_queue(self, url, day_range):
        item = MongoRepository().get_one("queue", 
                                {
                                   "url": url, 
                                   "$and": [
                                       {"created_at": {"$gte": day_range[0]}}, 
                                       {"created_at": {"$lte": day_range[1]}},
                                   ]
                                })
        return item != None

    def send_queue(self, message, pipeline_id, url, daycheck): 
        try:
            if not self.check_queue(url, daycheck):
                task_id = MongoRepository().insert_one("queue", 
                                                       {
                                                           "url": url, 
                                                            "pipeline": pipeline_id, 
                                                            "source": "TTXVN",
                                                            "expire": datetime.now()
                                                        }
                                                    )
                if task_id:
                    message["task_id"] = task_id
                    KafkaProducer_class().write("crawling_", message)
                    self.create_log(ActionStatus.INQUEUE, f"news: {url} transported to queue", pipeline_id)
        except Exception as e:
            traceback.print_exc()
            if task_id != None:
                MongoRepository().delete_one("queue", {"_id": task_id})
            self.create_log(ActionStatus.ERROR, "send news to queue error", pipeline_id)

    def select(self, from_element, expr, by = "css="):
        try:
            element = from_element.locator(f"{by}{expr}")
            elements = [element.nth(i) for i in range(element.count())]
            return elements
        except TimeoutError as e:
            raise ElementNotFoundError()
     
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
        for article in articles:
            try:
                link  = 'https://news.vnanet.vn/FrontEnd/PostDetail.aspx?id='+ str(article.get("ID"))
                self.driver.goto(link, clear_cookies=False)
                if "https://vnaid.vnanet.vn/core/login" in self.driver.get_current_url():
                    self.account['cookies'] = self.login_ttxvn(
                        self.driver.get_page(),
                        self.account.get('username'), 
                        self.account.get('password')
                    )
                    self.driver.add_cookies(self.account.get('cookies'))
                    self.driver.goto(link, clear_cookies=False)
                try:
                    content = self.select(self.driver.get_page(),".post-content")[0].inner_text()
                    article["content"] = str(content).replace(article["Title"], "", 1)
                except ElementNotFoundError as e:
                    raise Exception("can not select element")
            except Exception as e2:
                raise e2
    
    def save_articles(self, articles):
        try:
            ids = MongoRepository().insert_many('ttxvn',articles)
            id_dict = {index:row_id for index, row_id in enumerate(ids)}
            for key,article in enumerate(articles):
                article["_id"] = str(id_dict.get(key))
            self.insert_multiple_doc_es(articles)
        except Exception as e:
            raise e
    
    def get_ttxvn_action(self, pipeline_id):
        pipeline = MongoRepository().get_one("pipelines", {"_id": pipeline_id})
        if pipeline == None:
           raise Exception("Pipe line not found")
        return pipeline.get("schema")[1]
    
    def random_proxy(self, proxy_list):
        if str(proxy_list) == '[]' or str(proxy_list) == '[None]' or str(proxy_list) == 'None':
            return
        proxy_index = randint(0, len(proxy_list)-1)
        return proxy_list[proxy_index]

    def exec_func(self, input_val=None, **kwargs):
        if not input_val:
            raise InternalError(
                ERROR_REQUIRED, params={"code": ["FROM_ELEM"], "msg": ["From element"]}
            )

        if kwargs.get("mode_test") in [None, 'false', 'False', False]:
            kwargs.update({"mode_test": False})
        
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

        document = self.validate_input(
            self.params.get("document"),
            except_values= ["None", "", None],
            default=False,
            data_type=Any
        )

        day_check = self.get_check_time(10)
        self.account = self.get_ttxvn_account()
        self.proxies = self.get_proxies()

        news_headers = []
        if is_root == True:
            news_headers = self.get_news(limit)
            existed_ids = self.get_exists(news_headers)
            tmp_news = [header for header in news_headers if header["ArticleID"] not in existed_ids]
            news_headers = tmp_news
        
        #is a node
        if is_root == False and send_queue == True:
            try:
                document['PublishDate']=self.format_time(document['PublishDate'])
                document['Created']=self.format_time(document['Created'])
                self.crawl_article_content([document])
                self.save_articles([document])
            except Exception as e:
                raise e
        
        #is a root but not parallel
        elif (is_root == True and send_queue == False) or kwargs["mode_test"] == True:
            for header in news_headers:
                header['PublishDate']=self.format_time(header['PublishDate'])
                header['Created']=self.format_time(header['Created'])
            self.crawl_article_content(news_headers)
            self.save_articles(news_headers)

        #is a root and it parallel
        elif is_root == True and send_queue == True and kwargs["mode_test"] == False:
            self.create_log_permission = False
            ttxvn_action = self.get_ttxvn_action(kwargs.get("pipeline_id"))
            kwargs_leaf = kwargs.copy()
            kwargs_leaf["list_proxy"] = [self.random_proxy(kwargs.get("list_proxy"))]
            ttxvn_action["params"]["is_root"] = str(False)
            for header in news_headers:
                ttxvn_action["params"]["document"] = header
                message = {"actions": [ttxvn_action], "input_val": "null", "kwargs": kwargs_leaf}
                self.send_queue(message, kwargs.get("pipeline_id"), header.get('Url'), day_check)

        return "Succes: True"
