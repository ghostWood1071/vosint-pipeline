from common.internalerror import *

from ..common import ActionInfo, ActionType,ParamInfo
from .baseaction import BaseAction
from models import MongoRepository
import json
import time
from playwright.sync_api import Page

class GotoAction(BaseAction):
    @classmethod
    def get_action_info(cls) -> ActionInfo:
        return ActionInfo(
            name="goto",
            display_name="Goto",
            action_type=ActionType.COMMON,
            readme="Mở địa chỉ URL",
            z_index=1,
            param_infos=[
                ParamInfo(
                    name="wait",
                    display_name="Time wait for load",
                    val_type="str",
                    default_val="0",
                )
            ]
        )

    def exec_func(self, input_val=None, **kwargs):
        if not input_val:
            raise InternalError(
                ERROR_REQUIRED, params={"code": ["INPUT_URL"], "msg": ["Input URL"]}
            )

        url = input_val
        plt = MongoRepository().get_one("pielines", {"_id": kwargs.get("pipeline_id")})
        #print(input_val)
        if plt != None:
            cookies = plt.get("cookies")
            if cookies:
                cookies = eval(cookies)
                result = self.driver.goto(url, cookies = cookies)
            else:
                result = self.driver.goto(url)
        else:
            result = self.driver.goto(url)
        time_wait_str = self.params.get("wait")
        if str(time_wait_str).strip() in ["None", ""]:
            time_wait_str = "0"
        time_wait = float(time_wait_str.strip())
        time.sleep(time_wait)
        img = self.driver.get_page().screenshot()
        with open("lol.jpg", mode="wb") as f:
            f.write(img)
        return result
