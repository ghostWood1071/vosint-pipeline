from common.internalerror import *

from ..common import ActionInfo, ActionType, ParamInfo
from .baseaction import BaseAction

class TypingAction(BaseAction):
    @classmethod
    def get_action_info(cls) -> ActionInfo:
        return ActionInfo(
            name="typing",
            display_name="Typing",
            action_type=ActionType.COMMON,
            readme="Nhập dữ liệu từ bàn phím",
            param_infos=[
                ParamInfo(
                    name="send_key",
                    display_name="Key",
                    val_type="str",
                    default_val="",
                    validators=["required"],
                )
            ],
            z_index=9,
        )

    def exec_func(self, input_val=None, **kwargs):
        if not input_val:
            raise InternalError(
                ERROR_REQUIRED, params={"code": ["FROM_ELEM"], "msg": ["From element"]}
            )

        from_elem = input_val
        send_key = self.params["send_key"]
        self.driver.sendkey(from_elem[0], send_key)
        return self.driver.get_page()
