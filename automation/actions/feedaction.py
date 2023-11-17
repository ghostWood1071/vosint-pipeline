from common.internalerror import *

from ..common import ActionInfo, ActionType, ParamInfo, SelectorBy
from .baseaction import BaseAction
from models import MongoRepository
from datetime import datetime, timedelta
from utils import get_time_now_string_y_m_now

# from nlp.keyword_extraction.keywords_ext import Keywords_Ext
# from nlp.toan.v_osint_topic_sentiment_main.sentiment_analysis import (
#     topic_sentiment_classification,
# )
# from nlp.hieu.vosintv3_text_clustering_main_15_3.src.inference import text_clustering

import requests
from random import randint

import json
from elasticsearch import Elasticsearch
from db.elastic_main import My_ElasticSearch
import time
from models.kafka_producer import KafkaProducer_class
from core.config import settings
import feedparser
from typing import *
my_es = My_ElasticSearch(
    host=settings.ELASTIC_CONNECT.split(',')
)
import re
from urllib.request import ProxyBasicAuthHandler, build_opener, install_opener, urlopen
from ..common import ActionInfo, ActionStatus
from bson.objectid import ObjectId

rss_version_2_0 = {
    "author": "author",
    "link": "link",
    "pubDate": "pubDate",
    "titile": "title",
}
rss_version_1_0 = {
    "author": "author",
    "link": "link",
    "pubDate": "dc:date",
    "titile": "title",
}

def urlib_proxy_request(url, proxy):
    proxy_username = proxy.get("username")
    proxy_password = proxy.get("password")
    proxy_url = proxy_url = f'{proxy.get("ip_address")}:{proxy.get("port")}' if proxy.get("port") else proxy.get("ip_address")
    proxy_auth_handler = ProxyBasicAuthHandler()
    proxy_auth_handler.add_password(realm='realm',
                                    uri=proxy_url,
                                    user=proxy_username,
                                    passwd=proxy_password)
    opener = build_opener(proxy_auth_handler)
    install_opener(opener)
    try:
        with urlopen(url) as response:
            feed_content = response.read()
            return feed_content
    except Exception as e:
        raise Exception(f"Failed to parse the feed. Error: {e}")

def pure_request(url, proxy):
    try:
        proxies = {
            "http": f"http://{proxy.get('username')}:{proxy.get('password')}@{proxy.get('ip_address')}:{proxy.get('port')}",
        }
        req = requests.get(url, proxies=proxies)
        if req.ok:
            return req.content
        raise Exception(f"{req.status_code} {req.reason}")
    except Exception as e:
        raise Exception(f"can not parse feed data when using proxy: {proxy.get('ip_address')}")

def feed(
    url: str = None,
    link_key: str = rss_version_1_0["link"],
    title_key: str = rss_version_1_0["titile"],
    pubDate_key: str = rss_version_1_0["pubDate"],
    author_key: str = rss_version_1_0["author"],
    proxy:Dict[str, Any] = None
):
    # print('fedddddddddddddddddddddddddđ')
    if not url:
        raise InternalError(
            ERROR_REQUIRED, params={"code": ["FROM_ELEM"], "msg": ["From element"]}
        )
    # Parse the feed
    handlers = []
    if proxy:
        raw_feed = pure_request(url, proxy)
        feed = feedparser.parse(raw_feed)
    else:
        feed = feedparser.parse(url)
    if feed.bozo:
        raise feed.bozo_exception
    # Loop through the entries and print the link and title of each news article
    data_feeds = []
    for entry in feed.entries:
        # print(entry)
        data_feed = {}
        try:
            link = getattr(entry, link_key)
            if link != None:
                data_feed["link"] = link
        except:
            data_feed["link"] = ""
        try:
            title = getattr(entry, title_key)
            if title != None:
                data_feed["title"] = title
        except:
            data_feed["title"] = ""
        try:
            pubDate = getattr(entry, pubDate_key)
            if pubDate != None:
                data_feed["pubDate"] = pubDate
        except:
            data_feed["pubDate"] = ""
        try:
            author = getattr(entry, author_key)
            if author != None:
                data_feed["author"] = author
        except:
            data_feed["author"] = ""

        data_feeds.append(data_feed)
    return data_feeds

class FeedAction(BaseAction):
    @classmethod
    def get_action_info(cls) -> ActionInfo:
        return ActionInfo(
            name="feed new",
            display_name="Feed new",
            action_type=ActionType.COMMON,
            readme="Lấy thông tin bài viết",
            param_infos=[
                ParamInfo(
                    name="by",
                    display_name="Select by",
                    # val_type="str",
                    val_type="select",
                    default_val=SelectorBy.CSS,
                    options=SelectorBy.to_list(),
                    validators=["required"],
                ),
                ParamInfo(
                    name="title_expr",
                    display_name="Title Expression",
                    val_type="str",
                    default_val="None",
                    validators=["required_"],
                ),
                ParamInfo(
                    name="author_expr",
                    display_name="Author Expression",
                    val_type="str",
                    default_val="None",
                    validators=["required_"],
                ),
                ParamInfo(
                    name="time",
                    display_name="Time Expression",
                    val_type="pubdate",
                    default_val={
                        "time_expr": "None",
                        "time_format": ["***", ",", "dd", ",", "mm", ",", "yyyy"],
                    },
                    options=["***", "dd", "mm", "yyyy", ",", ".", "/", "_", "-", " "],
                    validators=["required_"],
                ),
                ParamInfo(
                    name="content_expr",
                    display_name="Content Expression",
                    val_type="str",
                    default_val="None",
                    validators=["required_"],
                ),
                ParamInfo(
                    name="send_queue",
                    display_name="Send queue",
                    val_type="bool",
                    default_val="True",
                    validators=["required_"],
                ),
                ParamInfo(
                    name="is_root",
                    display_name="Is root",
                    val_type="bool",
                    default_val="True",
                ),
                ParamInfo(
                    name="data_feed",
                    display_name="Data Feed",
                    val_type="any",
                    default_val="True"
                )
            ],
            z_index=4,
        )

    def create_es_doc(self, doc_es, news_info):
        try:
            doc_es["id"] = str(doc_es["_id"])
            doc_es.pop("_id", None)
        except:
            pass
        try:
            doc_es["data:title"] = news_info["data:title"]
        except:
            pass
        try:
            doc_es["data:author"] = news_info["data:author"]
        except:
            pass
        try:
            doc_es["data:time"] = news_info["data:time"]
        except:
            pass
        try:
            doc_es["pub_date"] = (
                str(news_info["pub_date"]).split(" ")[0]
                + "T00:00:00Z"
            )
        except:
            pass
        try:
            doc_es["data:content"] = news_info["data:content"]
        except:
            pass
        try:
            doc_es["keywords"] = news_info["keywords"]
        except:
            pass
        try:
            doc_es["data:url"] = news_info["data:url"]
        except:
            pass
        try:
            doc_es["data:html"] = news_info["data:html"]
        except:
            pass
        try:
            doc_es["data:class_chude"] = news_info[
                "data:class_chude"
            ]
        except:
            pass
        try:
            doc_es["data:class_linhvuc"] = news_info[
                "data:class_linhvuc"
            ]
        except:
            pass
        try:
            doc_es["source_name"] = news_info["source_name"]
        except:
            pass
        try:
            doc_es["source_host_name"] = news_info[
                "source_host_name"
            ]
        except:
            pass
        try:
            doc_es["source_language"] = news_info["source_language"]
        except:
            pass
        try:
            doc_es["source_publishing_country"] = news_info[
                "source_publishing_country"
            ]
        except:
            pass
        try:
            doc_es["source_source_type"] = news_info[
                "source_source_type"
            ]
        except:
            pass
        try:
            doc_es["created_at"] = (
                news_info["created_at"]
                .split(" ")[0]
                .replace("/", "-")
                + "T"
                + news_info["created_at"].split(" ")[1]
                + "Z"
            )
        except:
            pass
        try:
            doc_es["modified_at"] = (
                news_info["modified_at"]
                .split(" ")[0]
                .replace("/", "-")
                + "T"
                + news_info["modified_at"].split(" ")[1]
                + "Z"
            )
        except:
            pass
        try:
            doc_es["data:class_sacthai"] = news_info[
                "data:class_sacthai"
            ]
        except:
            pass
        try:
            doc_es["class_tinmau"] = news_info["class_tinmau"]
        except:
            pass
        try:
            doc_es["class_object"] = news_info["class_object"]
        except:
            pass
        try:
            doc_es["data:title_translate"] = news_info[
                "data:title_translate"
            ]
        except:
            pass
        try:
            doc_es["data:content_translate"] = news_info[
                "data:content_translate"
            ]
        except:
            pass
        return doc_es

    def get_chude(self, content:str):
        chude = []
        try:
            class_text_req = requests.post(settings.KEYWORD_CLUSTERING_API, params={"text": content})
            if not class_text_req.ok:
                raise Exception()
            class_text_clustering = class_text_req.json()
            chude = class_text_clustering
        except:
            return []
        return chude
    
    def get_linhvuc(self, content:str):
        linhvuc=[]
        try:
            class_text_req = requests.post(settings.DOCUMENT_CLUSTERING_API, params={"text": content})
            if not class_text_req.ok:
                raise Exception()
            class_text_clustering = class_text_req.json()
            linhvuc = class_text_clustering
        except:
            return []
        return linhvuc
    
    def get_sentiment(self, content:str, title:str):
        sentiment = "0"
        try:
            sentiment_req = requests.post(settings.SENTIMENT_API, data = json.dumps({
                'title': title, 
                'content': content,
                'description': 'string'
            }))
            if not sentiment_req.ok:
                raise Exception()
            sentiments = sentiment_req.json().get("result")
            if len(sentiments) == 0:
                raise Exception()
            
            if sentiments[0] == "tieu_cuc":
                kq = "2"
            elif sentiments[0] == "trung_tinh":
                kq = "0"
            elif sentiments[0] == "tich_cuc":
                kq = "1"
            else:
                kq = ""
            sentiment = kq
        except:
            return "0"
        return sentiment

    def extract_keywords(self, content:str, lang):
        keywords = []
        try:
            extkey_request = requests.post(settings.EXTRACT_KEYWORD_API, data=json.dumps({
                "lang": lang,
                "number_keyword": 6,
                "text": content
            }))
            if not extkey_request.ok:
                raise Exception()
            keywords = extkey_request.json().get("translate_text")
        except:
            return []
        return keywords

    def get_keywords(self, content, lang, content_translated):
        if lang == "vi" or lang == "en":
            keywords = self.extract_keywords(content, lang)
        else:
            # translated = self.translate(lang, content)
            keywords = self.extract_keywords(content_translated, "vi")
        return keywords
            
    def translate(self, language:str, content:str):
        result = ""
        try:
            lang_dict = {
                'cn': 'chinese',
                'ru': 'russia',
                'en': 'english'
            }
            lang_code = lang_dict.get(language)
            if lang_code is None:
                return ""
            req = requests.post(settings.TRANSLATE_API, data=json.dumps(
                {
                    "language": lang_code,
                    "text": content
                }
            ))
            result = req.json().get("translate_text")
            if not req.ok:
                raise Exception()
        except:
            result = ""
        return result

    def get_title(self, page, feed_title, title_expr, by):
        if (
            title_expr != "None"
            and title_expr != ""
            and feed_title == ""
        ):
            elems = self.driver.select(page, by, title_expr)
            if len(elems) > 0:
                return self.driver.get_content(elems[0])
            else:
                return ""
        else:
            return feed_title
            
    def get_author(self, page, feed_author, author_expr, by):
        if (
            author_expr != "None"
            and author_expr != ""
            and feed_author == ""
        ):
            elems = self.driver.select(page, by, author_expr)
            if len(elems) > 0:
                return self.driver.get_content(elems[0])
            else:
                return ""
        else:
            return feed_author

    def get_time (self, page, feed_date, time_expr, by):
        if (
            time_expr != "None"
            and time_expr != ""
            and feed_date == ""
        ):
            elems = self.driver.select(page, by, time_expr)
            if len(elems) > 0:
               return self.driver.get_content(elems[0])
            else:
               return ""
        else:
            return feed_date
    
    def get_publish_date(self, time_format):
        result = ""
        try:
            format = [",", ".", "/", "_", "-", " "]
            my_concat = lambda arr: "".join(arr)
            len_time_format = len(time_format)
            time_result = {}
            for i in range(len_time_format):
                if time_format[i] in format:
                    if i > 0:
                        name_time_format_1 = "time_" + str(
                            time_format[i - 1]
                        )
                        # print(time_format[i])
                        # print(time_string)
                        index = time_string.index(
                            time_format[i]
                        )  # split the string at the delimiter
                        # tg = time_string.split(time_format[i])
                        tg = time_string
                        time_string = time_string[index + 1 :]
                        if str(time_format[i - 1]) == "***":
                            continue

                        time_result[f"{name_time_format_1}"] = (
                            f"{tg[:index]}".replace(" ", "")
                            .replace("\n", "")
                            .replace("\t", "")
                        )
                    elif i < (len_time_format - 1):
                        tg = time_string.split(time_format[i])
                        time_string = my_concat(tg[1:])
                    else:
                        pass
            result = ""
            try:
                if (
                    time_result["time_yyyy"] != "None"
                    and time_result["time_yyyy"] != ""
                ):
                    result += time_result["time_yyyy"]
            finally:
                result += "-"
            try:
                if (
                    time_result["time_mm"] != "None"
                    and time_result["time_mm"] != ""
                ):
                    result += time_result["time_mm"]
            finally:
                result += "-"
            try:
                if (
                    time_result["time_dd"] != "None"
                    and time_result["time_dd"] != ""
                ):
                    result += time_result["time_dd"]
            except:
                pass
            finally:
                try:
                    result = datetime.strptime(
                        str(result), "%Y-%m-%d"
                    )  # .date()
                except:
                    result = get_time_now_string_y_m_now()
        except:
            result = get_time_now_string_y_m_now()
        return result

    def get_content(self, page, content_expr, by):
        result = ""
        if content_expr != "None" and content_expr != "":
            elems = self.driver.select(page, by, content_expr)
        
            if len(elems) > 0:
                if len(elems) == 1:
                    result = self.driver.get_content(elems[0])
                elif len(elems) > 1:
                    result = ""
                    for i in range(len(elems)):
                        result += self.driver.get_content(elems[i])+"\n"   
        return result

    def get_html_content(self, page, content_expr, by):
        elems = self.driver.select(page, by, content_expr)
        result = ""
        if len(elems) == 1:
            result = self.driver.get_html(elems[0])
            tmp_video = self.driver.select(from_elem=page, by="css", expr="figure")
            for i in tmp_video:
                result = result.replace(self.driver.get_html(i), "")

        elif len(elems) > 1:
            result = ""
            for i in range(len(elems)):
                result += self.driver.get_html(elems[i])
        return result

    def send_event_to_queue(self, _id, news_info):
        try:
            message = {
                "title": str(news_info["data:title"]),
                "content": str(news_info["data:content"]),
                "pubdate": str(news_info["pub_date"]),
                "id_new": str(_id),
            }
            KafkaProducer_class().write("events", message)
        except:
            print("kafka write message error")

    def get_keyword_regex(self,keyword_dict):
        pattern = ""
        for key in list(keyword_dict.keys()):
            pattern = pattern + keyword_dict.get(key) +","
        keyword_arr = [keyword.strip() for keyword in pattern.split(",")]
        keyword_arr = [rf"\b{keyword.strip()}\b" for keyword in list(filter(lambda x: x!="", keyword_arr))]
        pattern = "|".join(keyword_arr)
        return pattern

    def insert_mongo(self, collection_name, news_info, detect_event):
        try:
            _id = MongoRepository().insert_one(
                collection_name=collection_name, doc=news_info
            )
            self.add_news_to_object(news_info, _id)
            print("insert_mongo_succes")
            if detect_event:
                self.send_event_to_queue(_id, news_info)
            return _id
        except:
            print(
                "An error occurred while pushing data to the database!"
            )
            return None

    def insert_elastic(self, news_info):
        try:
            doc_es = self.create_es_doc(news_info.copy(), news_info)
            try:
                my_es.insert_document(
                    index_name="vosint",
                    id=doc_es["id"],
                    document=doc_es,
                )
            except:
                print("insert elastic search false")
        except:
            print(
                "An error occurred while pushing data to the database!"
            )

    def get_feed_action(self, pipeline_id:str):
        pipeline = MongoRepository().get_one("pipelines", {"_id": pipeline_id})
        if pipeline == None:
           raise Exception("Pipe line not found")
        return pipeline.get("schema")[1]

    def add_news_to_object(self, news, news_id):
        objects,_ = MongoRepository().get_many("object", {})
        object_ids = []
        for object in objects:
            pattern = self.get_keyword_regex(object.get("keywords")).lower()
            if pattern == "":
                continue
            if re.search(pattern, news['data:content'].lower()) or \
               re.search(pattern, news['data:title'].lower()) or \
               re.search(pattern, news['data:title_translate'].lower() if news['data:title_translate'] != None else ""):
                object_ids.append(object.get('_id'))
        if(len(object_ids)>0):
            MongoRepository().update_many('object', {"_id": {"$in": object_ids}}, {"$push": {"news_list": news_id}})

    def random_proxy(self, proxy_list):
        if str(proxy_list) == '[]' or str(proxy_list) == '[None]' or str(proxy_list) == 'None':
            return 
        proxy_index = randint(0, len(proxy_list)-1)
        return proxy_list[proxy_index]

    def check_queue(self, url, day_range):
        item = MongoRepository().get_one("queue", 
                                {
                                   "url": url, 
                                   "$and": [
                                        {"created_at": {"$gte": day_range[0]}}, 
                                        {"created_at": {"$lte": day_range[1]}}
                                   ]
                                })
        return item != None #return True if existed False if not existed

    def check_exists(self, url, days):
        existed_news, existed_count = MongoRepository().get_many(
                        collection_name="News", 
                        filter_spec={
                            "data:url": str(url), 
                            "$and": [
                                {"created_at": {"$gte": days[0]}},
                                {"created_at": {"$lte": days[1]}}
                            ]
                        }
                    )
        del existed_news
        return existed_count > 0 # return True if existed

    def send_queue(self, message, data_feed, kwargs):
        try:
            task_id = MongoRepository().insert_one("queue", {"url": data_feed['link'], "pipeline": kwargs["pipeline_id"], "source": kwargs["source_name"]})
            message["task_id"] = str(task_id)
            KafkaProducer_class().write("crawling_", message)
            self.create_log(ActionStatus.INQUEUE, f"{data_feed['link']} is transported to queue", kwargs["pipeline_id"])
        except Exception as e:
            if task_id != None:
                MongoRepository().delete_one("queue", {"_id": task_id})
            print(e)
    
    
    def process_news_data(self, data_feed, kwargs, title_expr, author_expr, time_expr, content_expr, time_format, by, detect_event, is_send_queue):
        try:
            url = data_feed["link"]
            collection_name = "News"
            #check existed
            if kwargs["mode_test"] != True:
                day_range = 10
                days = self.get_check_time(day_range)
                if self.check_exists(url,days=days):
                    if is_send_queue:
                        raise Exception(f"{url} url existed")
                    else:
                        self.create_log(ActionStatus.ERROR, f"{url} url existed", kwargs.get("pipeline_id"))
                        return None
            # init news info dictionary
            news_info = {}
            news_info["source_favicon"] = kwargs["source_favicon"]
            news_info["source_name"] = kwargs["source_name"]
            news_info["source_host_name"] = kwargs["source_host_name"]
            news_info["source_language"] = kwargs["source_language"]
            news_info["source_publishing_country"] = kwargs["source_publishing_country"]
            news_info["source_source_type"] = kwargs["source_source_type"]
            news_info["data:class_chude"] = []
            news_info["data:class_linhvuc"] = []
            news_info["data:title"] = ""
            news_info["data:content"] = ""
            news_info["pub_date"] = get_time_now_string_y_m_now()

            #go to link
            page = self.driver.goto(url=data_feed["link"])
            # get title
            news_info["data:title"] = self.get_title(page, data_feed["title"], title_expr, by)
            
            #get author
            news_info["data:author"] = self.get_author(page, data_feed["author"], author_expr, by)
            #get_time
            news_info["data:time"] = self.get_time(page, data_feed["pubDate"], time_expr,by)
            #get_publish_date
            if kwargs["mode_test"] != True:
                news_info["pub_date"] = self.get_publish_date(time_format)
            #get_content -------------------------------------------------------
            news_info["data:content"] = self.get_content(page, content_expr, by)
            if news_info["data:content"] not in ["None", None, ""]:
                # check_content = True
                if kwargs["mode_test"] != True:
                    
                    news_info["data:content_translate"] = self.translate(kwargs.get("source_language"), news_info["data:content"])
                    #---------------------------------------------------------------------------
                    news_info["data:title_translate"] = self.translate(kwargs["source_language"], news_info["data:title"])
                    #---------------------------------------------------------------------------
                    translated_content = news_info["data:title_translate"] + " " + news_info["data:content_translate"]
                    news_info["keywords"] = self.get_keywords(news_info["data:content"], kwargs["source_language"], translated_content)
                    #----------------------------------------------------------------------------        
                    news_info["data:class_chude"] = self.get_chude(news_info["data:content"])
                    #----------------------------------------------------------------------------
                    news_info["data:class_linhvuc"] = self.get_linhvuc(news_info["data:content"])
                    #--------------------------------------------------------------------------------   
                    if kwargs.get("source_language") != "vi": 
                        news_info["data:class_sacthai"] = self.get_sentiment(news_info["data:content_translate"], news_info["data:title_translate"])
                    else:
                        news_info["data:class_sacthai"] = self.get_sentiment(news_info["data:content"], news_info["data:title"])
                    #-----------------------------------------------------------------------------
                    news_info["data:summaries"] = self.summarize_all_level(kwargs.get("source_language"), news_info["data:title"], news_info["data:content"])
                    #-----------------------------------------------------------------------------
            if news_info["data:content"] == "":
                self.create_log(ActionStatus.ERROR, "empty content", pipeline_id=kwargs.get("pipeline_id"))
            #-----------------------------------------------------------------------
            #get_url
            news_info["data:url"] = url
            #get_html_content
            if content_expr != "None" and content_expr != "":
                news_info["data:html"] = self.get_html_content(page, content_expr, by)
            if kwargs["mode_test"] != True:
                if self.check_exists(url,days=days):
                    raise Exception(f"{url} url existed")
                #insert to mongo
                insert_ok = self.insert_mongo(collection_name, news_info, detect_event)
                # elastícearch
                if insert_ok != None:
                    self.insert_elastic(news_info)
            return news_info
        except Exception as e:
            raise e

    def exec_func(self, input_val=None, **kwargs):
        if not input_val:
            raise InternalError(
                ERROR_REQUIRED, params={"code": ["URL"], "msg": ["URL"]}
            )
        detect_event = kwargs.get("detect_event")
        url = str(input_val)
        by = self.params["by"]
        title_expr = self.params["title_expr"]
        author_expr = self.params["author_expr"]
        time_expr = self.params["time"]["time_expr"]
        time_format = self.params["time"]["time_format"]
        content_expr = self.params["content_expr"]
        is_send_queue = "False" if self.params.get("send_queue") == None or self.params.get("send_queue") == "False" else "True"  
        is_root = True if self.params.get("is_root") == None or self.params.get("is_root") =="True" else False
        result_test = None
        if is_root:
            proxy = None 
            if kwargs.get("list_proxy"):
                proxy_id =  self.random_proxy(kwargs.get("list_proxy"))
                proxy = MongoRepository().get_one("proxy", {'_id': proxy_id})
            data_feeds = feed(url=url, proxy=proxy)
            # data_feeds = feed(url=url)
            if len(data_feeds) == 0:
                raise Exception("There is no news in this source")
        
        if is_send_queue != "True" and is_root: #process news list
            for data_feed in data_feeds:
                try:
                    news_info = self.process_news_data(data_feed, kwargs, title_expr, 
                                        author_expr, time_expr, content_expr, 
                                        time_format, by, detect_event, is_send_queue=False)

                    result_test = news_info.copy() if news_info is not None else news_info
                    if kwargs["mode_test"] != True:
                        del news_info
                    else:
                        break
                except Exception as e:
                    raise e
                
        elif is_send_queue == "True" and is_root: #send news to queue
            feed_action = self.get_feed_action(kwargs["pipeline_id"])
            kwargs_leaf = kwargs.copy()
            kwargs_leaf["list_proxy"] = [self.random_proxy(kwargs.get("list_proxy"))]
            feed_action["params"]["is_root"] = "False"
            day_check = self.get_check_time(10)
            for data_feed in data_feeds:
                feed_action["url"] = data_feed["link"]
                feed_action["params"]["data_feed"] = data_feed
                message = {"actions": [feed_action], "input_val": "null", "kwargs": kwargs_leaf}
                try:
                    if not self.check_queue(data_feed['link'], day_check) and not self.check_exists(data_feed['link'], day_check):
                        self.send_queue(message, data_feed, kwargs)
                except Exception as e:
                    print(e)

        elif is_send_queue == "True" and not is_root: #process_news
            try:
                news_info = self.process_news_data(self.params.get("data_feed"), kwargs, title_expr, 
                                                   author_expr, time_expr, content_expr, 
                                                   time_expr, by, detect_event, is_send_queue= True)
                result_test = news_info.copy()
            except Exception as e:
                raise e
                
        

        if kwargs["mode_test"] == True:
            if result_test:
                tmp = news_info.copy()
                news_info = []
                news_info.append(tmp)
        return result_test
