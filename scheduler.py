from typing import Callable

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.mongodb import MongoDBJobStore
from common.internalerror import *
from core.config import settings

class Scheduler:
    __instance = None

    def __init__(self):
        if Scheduler.__instance is not None:
            raise InternalError(
                ERROR_SINGLETON_CLASS,
                params={
                    "code": [self.__class__.__name__.upper()],
                    "msg": [self.__class__.__name__],
                },
            )

        # self.__bg_scheduler = BackgroundScheduler(
        #     jobstores={"default": SQLAlchemyJobStore(url="sqlite:///jobs.sqlite")}
        # )
        mongo_config = {
            "host": settings.mong_host,
            "port": settings.mongo_port,
            "username": settings.mongo_username,
            "password": settings.mongo_passwd,
            "database": settings.mongo_db_name,
            "collection": "jobstore"
        }
        jobstore = {"default": MongoDBJobStore(**mongo_config)}
        self.__bg_scheduler = BackgroundScheduler(
            jobstores=jobstore
        )
        self.__bg_scheduler.start()

        Scheduler.__instance = self

    @staticmethod
    def instance():
        """Static access method."""
        if Scheduler.__instance is None:
            Scheduler()
        return Scheduler.__instance

    def add_job(self, id: str, func: Callable, cron_expr: str, args: list = []):
        # print('args..............',args)
        self.__bg_scheduler.add_job(
            id=id, func=func, args=args, trigger=CronTrigger.from_crontab(cron_expr)
        )

    def add_job_interval(self, job_id: str, func: Callable, interval: float, args: list = []):
        # print('args..............',args)
        self.__bg_scheduler.add_job(
            id=job_id, func=func, args=args, trigger=IntervalTrigger(seconds=interval)
        )

    def remove_job(self, id: str):
        self.__bg_scheduler.remove_job(id)

    def get_jobs(self) -> list:
        jobs = [job.id for job in self.__bg_scheduler.get_jobs()]
        return jobs
