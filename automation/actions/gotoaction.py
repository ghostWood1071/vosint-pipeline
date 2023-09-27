from common.internalerror import *

from ..common import ActionInfo, ActionType
from .baseaction import BaseAction


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
            print ("Loi input url khong co ....")
            raise InternalError(
                ERROR_REQUIRED, params={"code": ["INPUT_URL"], "msg": ["Input URL"]}
            )

        url = input_val
        
        #print(input_val)
        result = self.driver.goto(url)
        return result
