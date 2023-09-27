from fastapi import APIRouter
from fastapi.responses import JSONResponse
from .jobcontroller import JobController
from db.elastic_main import (
    My_ElasticSearch,
)
from pydantic import BaseModel
import asyncio


class Translate(BaseModel):
    lang: str
    content: str


class Filter_spec(BaseModel):
    Filter_spec: dict = {}


job_controller = JobController()
router = APIRouter()


@router.post("/api/crawling_ttxvn")
def crawling_ttxvn(job_id: str):
    response = job_controller.crawling_ttxvn(job_id)
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
