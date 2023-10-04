from fastapi import APIRouter
from fastapi.responses import JSONResponse
from .jobcontroller import JobController
from db.elastic_main import (
    My_ElasticSearch,
)
from pydantic import BaseModel
import asyncio
from typing import *
import re
from models import MongoRepository
from bson.objectid import ObjectId

class Translate(BaseModel):
    lang: str
    content: str


class Filter_spec(BaseModel):
    Filter_spec: dict = {}


job_controller = JobController()
router = APIRouter()


@router.post("/api/crawling_ttxvn")
def crawling_ttxvn(job_ids: List[str]):
    response = job_controller.crawling_ttxvn(job_ids)
    return JSONResponse(response)


@router.post("/api/start_job/{pipeline_id}")
def start_job(pipeline_id: str):
    job_controller.start_job(pipeline_id)
    return JSONResponse({"done": "ok"})


@router.post("/api/start_all_jobs")
def start_all_jobs(
    pipeline_ids,
):  # Danh sách Pipeline Id phân tách nhau bởi dấu , (VD: 636b5322243dd7a386d65cbc,636b695bda1ea6210d1b397f)
    return JSONResponse(job_controller.start_all_jobs(pipeline_ids))

#need to call
@router.post("/api/run_only_job/{pipeline_id}")
def run_only_job(pipeline_id: str, mode_test=True):
    if str(mode_test) == "True" or str(mode_test) == "true":
        mode_test = True
    return JSONResponse(job_controller.run_only(pipeline_id, mode_test))


@router.post("/api/crawling_ttxvn_news")
def crawling_ttxvn_news():
    try:
        return JSONResponse(job_controller.crawl_ttxvn_news())
    except:
        return JSONResponse({"succes: false"})

def get_keyword_regex(keyword_dict):
    pattern = ""
    for key in list(keyword_dict.keys()):
        pattern = pattern + keyword_dict.get(key) +","
    keyword_arr = [keyword.strip() for keyword in pattern.split(",")]
    keyword_arr = [rf"\b{keyword.strip()}\b" for keyword in list(filter(lambda x: x!="", keyword_arr))]
    pattern = "|".join(keyword_arr)
    return pattern

@router.post("/api/test-add-object")
def add_news_to_object(news_id:str):
    news = MongoRepository().get_one("News", {"_id": news_id})
    objects,_ = MongoRepository().get_many("object", {"_id": ObjectId("651d3821fad69d3f13e62055")})
    object_ids = []
    for object in objects:
        pattern = get_keyword_regex(object.get("keywords"))
        if pattern == "":
            continue
        match1 = re.search(pattern, news['data:content'])
        match2 = re.search(pattern, news['data:title'])
        match3 = re.search(pattern, news['data:title_translate'] if news['data:title_translate'] != None else "")
        if match1 or match2 or match3:
            object_ids.append(object.get('_id'))
    if(len(object_ids)>0):
        MongoRepository().update_many('object', {"_id": {"$in": object_ids}}, {"$push": {"news_list": news_id}})
