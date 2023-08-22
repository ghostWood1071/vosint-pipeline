from .actions import BaseAction
from datetime import datetime

import pytz
def get_time_now_string_y_m_d(
    tz: str = "Asia/Ho_Chi_Minh", fmt: str = "%Y/%m/%d"
) -> str:
    return datetime.now(pytz.timezone(tz)).strftime(fmt)
def get_time_now_string_y_m_now(
    tz: str = "Asia/Ho_Chi_Minh", fmt: str = "%Y/%m/%d"
) -> str:
    return datetime.strptime(str(get_time_now_string_y_m_d()), "%Y/%m/%d")

def get_action_infos() -> list[dict]:
    action_classes = BaseAction.__subclasses__()
    action_infos = list(
        map(lambda action_cls: action_cls.get_action_info().to_json(), action_classes)
    )
    action_infos.sort(key=lambda ai: ai["z_index"])
    return action_infos


def get_action_info(name) -> dict:
    action_infos = get_action_infos()
    action_info = next(filter(lambda ai: ai["name"] == name, action_infos), None)
    return action_info
