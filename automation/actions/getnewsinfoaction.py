from common.internalerror import *
from models import MongoRepository

from ..common import ActionInfo, ActionType, ParamInfo, SelectorBy
from .baseaction import BaseAction
from models.mongorepository import MongoRepository
from datetime import datetime
from utils import get_time_now_string_y_m_now
import requests
import json
import re
from elasticsearch import Elasticsearch
from db.elastic_main import My_ElasticSearch
import time
from models.kafka_producer import KafkaProducer_class
from core.config import settings
from datetime import datetime, timedelta
from ..common.actionstatus import ActionStatus


my_es = My_ElasticSearch(
    host=[settings.ELASTIC_CONNECT], user="USER", password="PASS", verify_certs=False
)


class GetNewsInfoAction(BaseAction):
    @classmethod
    def get_action_info(cls) -> ActionInfo:
        return ActionInfo(
            name="get_news_info",
            display_name="Get News Infomation",
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
            ],
            z_index=4,
        )
    
    def get_keyword_regex(self,keyword_dict):
        pattern = ""
        for key in list(keyword_dict.keys()):
            pattern = pattern + keyword_dict.get(key) +","
        keyword_arr = [keyword.strip() for keyword in pattern.split(",")]
        keyword_arr = [rf"\b{keyword.strip()}\b" for keyword in list(filter(lambda x: x!="", keyword_arr))]
        pattern = "|".join(keyword_arr)
        return pattern
        
    def get_sentiment(self, title:str, content:str):
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
        except Exception as e:
            sentiment = "0"
        return sentiment
    
    def get_chude(self,content:str):
        chude = []
        try:
            class_text_req = requests.post(settings.KEYWORD_CLUSTERING_API, data=json.dumps({"text": content}))
            if not class_text_req.ok:
                raise Exception()
            class_text_clustering = class_text_req.json()
            chude = class_text_clustering
        except Exception as e:
            chude = []
        return chude
    
    def extract_keyword(self, content, lang):
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
        except Exception as e:
            keywords = []
        return keywords
    
    def get_keywords(self, content:str, lang:str, content_translate):
        try:
            if lang == "vi" or lang == "en":
                keywords = self.extract_keyword(content, lang)
            else:
                keywords = self.extract_keyword(content_translate, "vi")
        except Exception as e:
            keywords = []
        return keywords
    
    def get_linhvuc(self, content:str):
        linhvuc = []
        try:
            class_text_req = requests.post(settings.DOCUMENT_CLUSTERING_API, data=json.dumps({"text": content}))
            if not class_text_req.ok:
                raise Exception()
            class_text_clustering = class_text_req.json()
            linhvuc = class_text_clustering
        except Exception as e:
            linhvuc
        return linhvuc

    def translate(self, content, lang):
        lang_dict = {
            'cn': 'chinese',
            'ru': 'russia',
            'en': 'english'
        }
        lang_code = lang_dict.get(lang)
        if lang_code is None:
            return ""
        req = requests.post(settings.TRANSLATE_API, data=json.dumps(
            {
                "language": lang_code,
                "text": content
            }
        ))
        if not req.ok:
            raise Exception()
        result = req.json().get("translate_text")
        return result

    def add_news_to_object(self, news, news_id):
        objects,_ = MongoRepository().get_many("object", {})
        object_ids = []
        for object in objects:
            pattern = self.get_keyword_regex(object.get("keywords"))
            if pattern == "":
                continue
            if re.search(pattern, news['data:content']) or \
               re.search(pattern, news['data:title']) or \
               re.search(pattern, news['data:title_translate'] if news['data:title_translate'] != None else ""):
                object_ids.append(object.get('_id'))
        if(len(object_ids)>0):
            MongoRepository().update_many('object', {"_id": {"$in": object_ids}}, {"$push": {"news_list": news_id}})
    
    def check_news_exists(self, url, day_check):
        exists = False
        a, b = MongoRepository().get_many(
            collection_name="News", filter_spec={"data:url": url, 
                                                 "$and": [
                                                        {"created_at": {"$gte": day_check[0]}}, 
                                                        {"created_at": {"$lte": day_check[1]}}
                                                    ]
                                                 }
        )
        del a
        if str(b) != "0":
            print("url already exist")
            exists = True
            raise Exception(f"{url} exist url")

    def insert_elastic(self, news_info):
        try:
            # doc_es = {}
            doc_es = news_info.copy()
            # try:
            #     doc_es['_id'] = _id
            # except:
            #     pass
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
                    str(news_info["pub_date"]).split(" ")[0] + "T00:00:00Z"
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
                doc_es["data:class_chude"] = news_info["data:class_chude"]
            except:
                pass
            try:
                doc_es["data:class_linhvuc"] = news_info["data:class_linhvuc"]
            except:
                pass
            try:
                doc_es["source_name"] = news_info["source_name"]
            except:
                pass
            try:
                doc_es["source_host_name"] = news_info["source_host_name"]
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
                doc_es["source_source_type"] = news_info["source_source_type"]
            except:
                pass
            try:
                doc_es["created_at"] = (
                    news_info["created_at"].split(" ")[0].replace("/", "-")
                    + "T"
                    + news_info["created_at"].split(" ")[1]
                    + "Z"
                )
            except:
                pass
            try:
                doc_es["modified_at"] = (
                    news_info["modified_at"].split(" ")[0].replace("/", "-")
                    + "T"
                    + news_info["modified_at"].split(" ")[1]
                    + "Z"
                )
            except:
                pass
            try:
                doc_es["data:class_sacthai"] = news_info["data:class_sacthai"]
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
            # print(doc_es)
            try:
                my_es.insert_document(
                    index_name="vosint", id=doc_es["id"], document=doc_es
                )
            except:
                print("insert elastic search false")
        except:
            print("An error occurred while pushing data to the database!")

    def exec_func(self, input_val=None, **kwargs):
        try: 
            collection_name = "News"
            if not input_val:
                raise InternalError(
                    ERROR_REQUIRED, params={"code": ["URL"], "msg": ["URL"]}
                )

            url = ''
            try:
                url = self.driver.get_current_url()
            except:
                pass

            check_url_exist = "0"
            day_check = self.get_check_time(10)
            if kwargs["mode_test"] != True:
                self.check_news_exists(url, day_check)

            by = self.params["by"]
            title_expr = self.params["title_expr"]
            author_expr = self.params["author_expr"]
            time_expr = self.params["time"]["time_expr"]
            time_format = self.params["time"]["time_format"]
            # print(type(time_format),time_format)
            # time_format = ['***',',','dd','/','mm','/','yyyy','-',"***"]
            content_expr = self.params["content_expr"]
            news_info = {}
            news_info["source_favicon"]=kwargs["source_favicon"]
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

            page = input_val
            # check_content = False
            if title_expr != "None" and title_expr != "":
                elems = self.driver.select(page, by, title_expr)
                if len(elems) > 0:
                    news_info["data:title"] = self.driver.get_content(elems[0])
                    news_info["data:title_translate"] = ""
                    try:
                        if kwargs["mode_test"] != True:
                            news_info["data:title_translate"] = self.translate(news_info["data:title"], kwargs["source_language"])
                    except Exception as e:
                        pass

            if author_expr != "None" and author_expr != "":
                elems = self.driver.select(page, by, author_expr)
                if len(elems) > 0:
                    news_info["data:author"] = self.driver.get_content(elems[0])
            # if time_expr != "None" and time_expr !="":
            if True:
                try:
                    # print('time_expr',time_expr)
                    elems = self.driver.select(page, by, time_expr)
                    if len(elems) > 0:
                        news_info["data:time"] = self.driver.get_content(elems[0])
                        time_string = news_info["data:time"]
                        # print(news_info["data:time"])
                        if kwargs["mode_test"] != True:
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
                                news_info["pub_date"] = ""
                                try:
                                    if (
                                        time_result["time_yyyy"] != "None"
                                        and time_result["time_yyyy"] != ""
                                    ):
                                        news_info["pub_date"] += time_result["time_yyyy"]
                                finally:
                                    news_info["pub_date"] += "-"
                                try:
                                    if (
                                        time_result["time_mm"] != "None"
                                        and time_result["time_mm"] != ""
                                    ):
                                        news_info["pub_date"] += time_result["time_mm"]
                                finally:
                                    news_info["pub_date"] += "-"
                                try:
                                    if (
                                        time_result["time_dd"] != "None"
                                        and time_result["time_dd"] != ""
                                    ):
                                        news_info["pub_date"] += time_result["time_dd"]
                                except:
                                    pass
                                finally:
                                    try:
                                        news_info["pub_date"] = datetime.strptime(
                                            str(news_info["pub_date"]), "%Y-%m-%d"
                                        )  # .date()
                                    except:
                                        news_info[
                                            "pub_date"
                                        ] = get_time_now_string_y_m_now()
                            except:
                                news_info["pub_date"] = get_time_now_string_y_m_now()
                except:
                    pass

            # else:
            #     news_info['pub_date'] = get_time_now_string_y_m_now()

            if content_expr != "None" and content_expr != "":
                elems = self.driver.select(page, by, content_expr)
                if len(elems) > 0:
                    if len(elems) == 1:
                        news_info["data:content"] = self.driver.get_content(elems[0])
                    elif len(elems) > 1:
                        news_info["data:content"] = ""
                        for i in range(len(elems)):
                            news_info["data:content"] += self.driver.get_content(elems[i]) +"\n"
                    # check_content = True

                    #translate content 
                    if news_info["data:content"] not in ["None", None, ""]:
                        news_info["data:content_translate"] = ""
                        if kwargs.get("source_language") != "vi":
                            try:
                                news_info["data:content_translate"] = self.translate(news_info["data:content"], kwargs.get("source_language"))
                            except Exception as e:
                                print(e)
                                news_info["data:content_translate"] = ""
                        

                    if kwargs["mode_test"] != True:
                        content_translated = news_info["data:content_translate"]+" "+news_info["data:content_translate"]
                        news_info["keywords"] = self.get_keywords(news_info['data:content'], kwargs["source_language"],content_translated)
                        #--------------------------------------------------------
                        news_info["data:class_chude"] = self.get_chude(news_info["data:content"])
                        #--------------------------------------------------------
                        news_info["data:class_linhvuc"] = self.get_linhvuc(news_info["data:content"])
                        #--------------------------------------------------------
                        if kwargs.get("source_language") != "vi":
                            news_info["data:class_sacthai"] = self.get_sentiment(news_info["data:title_translate"], news_info["data:content_translate"])
                        else:
                            news_info["data:class_sacthai"] = self.get_sentiment(news_info["data:title"], news_info["data:content"])
                        #--------------------------------------------------------
                        do_1 = datetime.now()
                        news_info["data:summaries"] = self.summarize_all_level(kwargs.get("source_language"), news_info["data:title"], news_info["data:content"])
                        do_2 = datetime.now()
                        print("summarize: ", (do_2-do_1).microseconds*1000)

                if news_info["data:content"] == "":
                    self.create_log(ActionStatus.ERROR, "empty content", pipeline_id=kwargs.get("pipeline_id"))
                    # raise Exception("empty content")

                news_info["data:url"] = url
            if content_expr != "None" and content_expr != "":
                elems = self.driver.select(page, by, content_expr)
                if len(elems) == 1:
                    news_info["data:html"] = self.driver.get_html(elems[0])

                    tmp_video = self.driver.select(from_elem=page, by="css", expr="figure")
                    for i in tmp_video:
                        news_info["data:html"] = news_info["data:html"].replace(
                            self.driver.get_html(i), ""
                        )
                elif len(elems) > 1:
                    news_info["data:html"] = ""
                    for i in range(len(elems)):
                        news_info["data:html"] += self.driver.get_html(elems[i])

            if kwargs["mode_test"] != True:
                if  check_url_exist == "0":
                    try:
                        self.check_news_exists(url, day_check)
                        
                        _id = MongoRepository().insert_one(
                            collection_name=collection_name, doc=news_info
                        )
                        self.add_news_to_object(news_info, _id)
                        # print(type(_id))
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
                    except Exception as e:
                        print("An error occurred while pushing data to the database!")
                    # elastícearch
                    if _id != None:
                        self.insert_elastic(news_info) 
            return news_info
        except Exception as e:
            raise e
