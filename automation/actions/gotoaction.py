from common.internalerror import *

from ..common import ActionInfo, ActionType
from .baseaction import BaseAction
from models import MongoRepository
import json
class GotoAction(BaseAction):
    @classmethod
    def get_action_info(cls) -> ActionInfo:
        return ActionInfo(
            name="goto",
            display_name="Goto",
            action_type=ActionType.COMMON,
            readme="Mở địa chỉ URL",
            z_index=1,
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
        return result
