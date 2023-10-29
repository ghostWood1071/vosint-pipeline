from .services import JobService
from threading import Thread, Timer
from scheduler import Scheduler
from typing import *

def get_depth(mylist):
    if isinstance(mylist, list):
        return 1 + max(get_depth(item) for item in mylist)
    else:
        return 0


class JobController:
    def __init__(self):
        self.__job_service = JobService()

    def start_job(self, pipeline_id: str):
        job_thread = Thread(target=self.__job_service.start_job,args=[pipeline_id])
        job_thread.start()
        return {"success": True}

    def start_all_jobs(self, pipeline_ids):
        # Receives request data
        # pipeline_ids = request.args.get('pipeline_ids')

        self.__job_service.start_all_jobs(pipeline_ids)

        return {"success": True}

    def stop_job(self, pipeline_id: str):
        self.__job_service.stop_job(pipeline_id)

        return {"success": True}

    def stop_all_jobs(self, pipeline_ids):
        # Receives request data
        # pipeline_ids = request.args.get('pipeline_ids')

        self.__job_service.stop_all_jobs(pipeline_ids)
        return {"success": True}

    ### Doan
    def get_news_from_id_source(
        self,
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
        page_number = int(page_number)
        page_size = int(page_size)
        result = self.__job_service.get_news_from_id_source(
            id,
            type,
            page_number,
            page_size,
            start_date,
            end_date,
            sac_thai,
            language_source,
            text_search,
        )
        return {
            "total_record": len(result),
            "result": result[
                (int(page_number) - 1)
                * int(page_size) : (int(page_number))
                * int(page_size)
            ],
        }

    def create_required_keyword(self, newsletter_id):
        try:
            self.__job_service.create_required_keyword(newsletter_id)
            return {"success": True}
        except:
            return {"success": True}

    def elt_search(
        self,
        page_number,
        page_size,
        start_date,
        end_date,
        sac_thai,
        language_source,
        text_search,
    ):
        pipeline_dtos = self.__job_service.elt_search(
            start_date, end_date, sac_thai, language_source, text_search
        )
        for i in range(len(pipeline_dtos)):
            try:
                pipeline_dtos[i]["_source"]["_id"] = pipeline_dtos[i]["_source"]["id"]
            except:
                pass
            pipeline_dtos[i] = pipeline_dtos[i]["_source"].copy()
        return {
            "total_record": len(pipeline_dtos),
            "result": pipeline_dtos[
                (int(page_number) - 1)
                * int(page_size) : (int(page_number))
                * int(page_size)
            ],
        }

    def crawling_ttxvn(self, job_ids: List[str]):
        return self.__job_service.crawling_ttxvn(job_ids)

    def run_only(self, pipeline_id: str, mode_test):
        result = self.__job_service.run_only(pipeline_id, mode_test)
        try:
            tmp = result.copy()
        except:
            tmp = result
        # print('huuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu',get_depth(result))
        # print(result)
        try:
            depth = get_depth(result)
        except:
            depth = 0
        try:
            if type(result) == list and mode_test == True and depth != 0:
                for i in range(depth):
                    result = result[0]
                try:
                    result["pub_date"] = str(result["pub_date"])
                except:
                    pass
                try:
                    result["_id"] = str(result["_id"])
                except:
                    pass
                return {"success": True, "result": result}
            else:
                return {"success": True, "result": str(tmp)}
        except:
            return {"success": True, "result": str(tmp)}

    def get_result_job(self, News, order, page_number, page_size, filter):
        # Receives request data
        # order = request.args.get('order')
        # order = request.args.get('order')
        # page_number = request.args.get('page_number')
        page_number = int(page_number) if page_number is not None else None
        # page_size = request.args.get('page_size')
        page_size = int(page_size) if page_size is not None else None

        # Create sort condition
        order_spec = order.split(",") if order else []

        # Calculate pagination information
        page_number = page_number if page_number else 1
        page_size = page_size if page_size else 20
        pagination_spec = {"skip": page_size * (page_number - 1), "limit": page_size}
        pipeline_dtos, total_records = self.__job_service.get_result_job(
            News, order_spec=order_spec, pagination_spec=pagination_spec, filter=filter
        )
        for document in pipeline_dtos:
            for key in document:
                document[key] = str(document[key])
        # for i in pipeline_dtos:
        #     try:
        #         i["_id"] = str(i["_id"])
        #     except:
        #         pass
        #     try:
        #         i["pub_date"] = str(i["pub_date"])
        #     except:
        #         pass
        return {"success": True, "total_record": total_records, "result": pipeline_dtos}

    def run_one_foreach(self, pipeline_id: str):
        result = self.__job_service.run_one_foreach(pipeline_id)

        return {"result": str(result)}

    def test_only(self, pipeline_id: str):
        result = self.__job_service.test_only(pipeline_id)
        print(str(result))
        return {"result": str(result)}

    def get_log_history(self, pipeline_id: str, order, page_number, page_size):
        # Receives request data
        # order = request.args.get('order')
        # order = request.args.get('order')
        # page_number = request.args.get('page_number')
        page_number = int(page_number) if page_number is not None else None
        # page_size = request.args.get('page_size')
        page_size = int(page_size) if page_size is not None else None

        # Create sort condition
        order_spec = order.split(",") if order else []

        # Calculate pagination information
        page_number = page_number if page_number else 1
        page_size = page_size if page_size else 20
        pagination_spec = {"skip": page_size * (page_number - 1), "limit": page_size}

        result = self.__job_service.get_log_history(
            pipeline_id, order_spec=order_spec, pagination_spec=pagination_spec
        )

        return {"success": True, "total_record": result[1], "result": result[0]}

    def get_log_history_last(self, pipeline_id: str):
        result = self.__job_service.get_log_history_last(pipeline_id)

        return {"success": True, "total_record": result[1], "result": result[0]}

    def get_log_history_error_or_getnews(
        self, pipeline_id: str, order, page_number, page_size
    ):
        # Receives request data
        # order = request.args.get('order')
        # order = request.args.get('order')
        # page_number = request.args.get('page_number')
        page_number = int(page_number) if page_number is not None else None
        # page_size = request.args.get('page_size')
        page_size = int(page_size) if page_size is not None else None

        # Create sort condition
        order_spec = order.split(",") if order else []

        # Calculate pagination information
        page_number = page_number if page_number else 1
        page_size = page_size if page_size else 20
        pagination_spec = {"skip": page_size * (page_number - 1), "limit": page_size}

        result = self.__job_service.get_log_history_error_or_getnews(
            pipeline_id, order_spec=order_spec, pagination_spec=pagination_spec
        )

        return {"success": True, "total_record": result[1], "result": result[0]}

    def crawl_ttxvn_news(self):
        job_thread = Thread(target=self.__job_service.crawl_ttxvn_news)
        job_thread.start()
        return {"success": True}