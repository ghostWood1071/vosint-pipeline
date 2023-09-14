import datetime
import json

from automation import Session
from common.internalerror import *
from features.pipeline.services import PipelineService
from logger import Logger
from models import MongoRepository
from scheduler import Scheduler
from utils import get_time_now_string

# from models import MongoRepository
from db.elastic_main import My_ElasticSearch

# from nlp.hieu.vosint_v3_document_clustering_main_16_3.create_keyword import Create_vocab_corpus
# from nlp.keyword_extraction.keywords_ext import Keywords_Ext
from db.elastic_main import (
    My_ElasticSearch,
)

my_es = My_ElasticSearch()
from .crawling_ttxvn import crawl_ttxvn


def start_job(actions: list[dict], pipeline_id=None, source_favicon=None):
    session = Session(
        driver_name="playwright",
        storage_name="hbase",
        actions=actions,
        pipeline_id=pipeline_id,
        source_favicon = source_favicon
    )
    # print('aaaaaaaaaaaa',pipeline_id)
    return session.start()


class JobService:
    def __init__(self):
        self.__pipeline_service = PipelineService()
        self.__mongo_repo = MongoRepository()
        self.__elastic_search = My_ElasticSearch()

    def run_only(self, id: str, mode_test=None):
        pipeline_dto = self.__pipeline_service.get_pipeline_by_id(id)
        session = Session(
            driver_name="playwright",
            storage_name="hbase",
            actions=pipeline_dto.schema,
            pipeline_id=id,
            mode_test=mode_test,
            source_favicon=pipeline_dto.source_favicon
        )
        result = session.start()
        return result

    def get_result_job(self, News, order_spec, pagination_spec, filter):
        results = self.__mongo_repo.get_many_News(
            News,
            order_spec=order_spec,
            pagination_spec=pagination_spec,
            filter_spec=filter,
        )
        # results['_id'] = str(results['_id'])
        # results['pub_date'] = str(results['pub_date'])
        return results  # pipeline_dto.schema #

    def get_log_history(self, id: str, order_spec, pagination_spec):
        results = self.__mongo_repo.get_many_his_log(
            "his_log",
            {"pipeline_id": id},
            order_spec=order_spec,
            pagination_spec=pagination_spec,
        )
        return results

    def get_log_history_last(self, id: str):
        results = self.__mongo_repo.get_many_his_log(
            "his_log", {"pipeline_id": id, "log": "error"}
        )
        return results

    def get_log_history_error_or_getnews(self, id: str, order_spec, pagination_spec):
        results = self.__mongo_repo.get_many_his_log(
            "his_log",
            {
                "$and": [
                    {"pipeline_id": id},
                    {"$or": [{"actione": "GetNewsInfoAction"}, {"log": "error"}]},
                ]
            },
            order_spec=order_spec,
            pagination_spec=pagination_spec,
        )

        return results

    def run_one_foreach(self, id: str):
        pipeline_dto = self.__pipeline_service.get_pipeline_by_id(id)
        session = Session(
            driver_name="playwright",
            storage_name="hbase",
            # flag = 0,
            actions=pipeline_dto.schema,
        )
        return session.start()  # pipeline_dto.schema #

    def test_only(self, id: str):
        pipeline_dto = self.__pipeline_service.get_pipeline_by_id(id)
        session = Session(
            driver_name="playwright", storage_name="hbase", actions=pipeline_dto.schema
        )
        return session.start()

    def start_job(self, id: str):
        pipeline_dto = self.__pipeline_service.get_pipeline_by_id(id)
        if not pipeline_dto:
            raise InternalError(
                ERROR_NOT_FOUND,
                params={"code": ["PIPELINE"], "msg": [f"pipeline with id: {id}"]},
            )

        if not pipeline_dto.enabled:
            raise InternalError(
                ERROR_NOT_FOUND,
                params={"code": ["PIPELINE"], "msg": [f"Pipeline with id: {id}"]},
            )
        source_favicon = pipeline_dto.source_favicon
        start_job(pipeline_dto.schema, id, source_favicon)

    def start_all_jobs(self, pipeline_ids: list[str] = None):
        # Split pipeline_ids from string to list of strings
        pipeline_ids = pipeline_ids.split(",") if pipeline_ids else None
        enabled_pipeline_dtos = self.__pipeline_service.get_pipelines_for_run(pipeline_ids)
        for pipeline_dto in enabled_pipeline_dtos:
            try:
                session = Session(driver_name="playwright", storage_name="hbase", actions=pipeline_dto.schema)
                session.start()    
            except InternalError as error:
                Logger.instance().error(str(error))

    def stop_job(self, id: str):
        Scheduler.instance().remove_job(id)

    def crawling_ttxvn(self, job_id):
        try:
            data = MongoRepository().get_one(
                collection_name="ttxvn", filter_spec={"_id": job_id}
            )
            doc_es = data.copy()
            # print(data)
            config_ttxvn = MongoRepository().get_one(
                collection_name="config_ttxvn", filter_spec={"tag": "using"}
            )
            id_news = str(data["ID"])
            username = str(config_ttxvn["user"])
            password = str(config_ttxvn["password"])
            data["content"] = crawl_ttxvn(username, password, id_news)
            data["content"] = str(data["content"]).replace(data["Title"], "", 1)
            MongoRepository().update_one(collection_name="ttxvn", doc=data)
            # print(data)

            doc_es["content"] = str(data["content"])
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
            try:
                my_es.insert_document(
                    index_name="vosint_ttxvn", id=doc_es["id"], document=doc_es
                )
                print("insert to elastic vosint_ttxvn")
            except:
                print("insert to elasstic vosint_ttxvn error")
            return {"succes": "True"}
        except:
            return {"succes": "False"}

    def elt_search(self, start_date, end_date, sac_thai, language_source, text_search):
        pipeline_dtos = my_es.search_main(
            index_name="vosint",
            query=text_search,
            gte=start_date,
            lte=end_date,
            lang=language_source,
            sentiment=sac_thai,
        )
        return pipeline_dtos

    def create_required_keyword(self, newsletter_id):
        a = self.__mongo_repo.get_one(
            collection_name="newsletter", filter_spec={"_id": newsletter_id}
        )["news_samples"]
        # print('len aaaaaaaaaa',len(a))
        list_keyword = []
        for i in a:
            # print(i['title']+i['content'])
            b = Keywords_Ext().extracting(
                document=i["title"] + i["content"], num_keywords=3
            )
            # print('aaaaaaaaaaaaaaa',b)
            list_keyword.append(",".join(b))

        doc = self.__mongo_repo.get_one(
            collection_name="newsletter", filter_spec={"_id": newsletter_id}
        )
        doc["required_keyword_extract"] = list_keyword
        self.__mongo_repo.update_one(collection_name="newsletter", doc=doc)

    def get_news_from_id_source(
        sefl,
        id,
        type,
        page_number,
        page_size,
        start_date,
        end_date,
        sac_thai,
        language_source,
        text_search,
    ):
        size = page_number * page_size
        if type == "source":
            name = sefl.__mongo_repo.get_one(
                collection_name="infor", filter_spec={"_id": id}
            )["name"]
            list_source_name = []
            list_source_name.append(name)
            if list_source_name == []:
                return []
            # print(name)
            # query = {
            #     'query': {
            #         'match': {
            #             'source_name': name
            #         }
            #     },
            #     'size':size
            # }
            # a = sefl.__elastic_search.query(index_name='vosint',query=query)
            a = sefl.__elastic_search.search_main(
                index_name="vosint",
                query=text_search,
                gte=start_date,
                lte=end_date,
                lang=language_source,
                sentiment=sac_thai,
                list_source_name=list_source_name,
            )
            for i in range(len(a)):
                a[i]["_source"]["_id"] = a[i]["_source"]["id"]
                a[i] = a[i]["_source"]
            return a

        elif type == "source_group":
            name = sefl.__mongo_repo.get_one(
                collection_name="Source", filter_spec={"_id": id}
            )["news"]
            # value = []
            list_source_name = []
            for i in name:
                list_source_name.append(i["name"])

            if list_source_name == []:
                return []
            # print(value)
            # query = {
            #     'query': {
            #         'terms': {
            #             'source_name': value
            #         }
            #     },
            #     'size':size
            # }
            # a = sefl.__elastic_search.query(index_name='vosint',query=query)
            a = sefl.__elastic_search.search_main(
                index_name="vosint",
                query=text_search,
                gte=start_date,
                lte=end_date,
                lang=language_source,
                sentiment=sac_thai,
                list_source_name=list_source_name,
            )
            for i in range(len(a)):
                a[i]["_source"]["_id"] = a[i]["_source"]["id"]
                a[i] = a[i]["_source"]
            return a

    def stop_all_jobs(self, pipeline_ids: list[str] = None):
        # Split pipeline_ids from string to list of strings
        pipeline_ids = pipeline_ids.split(",") if pipeline_ids else None

        enabled_pipeline_dtos = self.__pipeline_service.get_pipelines_for_run(
            pipeline_ids
        )

        for pipeline_dto in enabled_pipeline_dtos:
            try:
                Scheduler.instance().remove_job(pipeline_dto._id)
            except InternalError as error:
                Logger.instance().error(str(error))

    