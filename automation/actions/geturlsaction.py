from common.internalerror import *

from ..common import ActionInfo, ActionType, ParamInfo, SelectorBy
from .baseaction import BaseAction
from urllib.parse import urlparse
import re

class GetUrlsAction(BaseAction):
    @classmethod
    def get_action_info(cls) -> ActionInfo:
        return ActionInfo(
            name="get_urls",
            display_name="Get URLs",
            action_type=ActionType.COMMON,
            readme="Lấy danh sách các địa chỉ URLs trong một trang",
            param_infos=[
                ParamInfo(
                    name="by",
                    display_name="Select by",
                    val_type="select",
                    default_val=SelectorBy.CSS,
                    options=SelectorBy.to_list(),
                    validators=["required"],
                ),
                ParamInfo(
                    name="expr",
                    display_name="Expression",
                    val_type="str",
                    default_val="",
                    validators=["required"],
                ),
                ParamInfo(
                    name="origin",
                    display_name="Additional",
                    val_type="str",
                    default_val="",
                ),
                ParamInfo(
                    name="filter",
                    display_name="Filter (Regex)",
                    val_type="str",
                    default_val="",
                ),
            ],
            z_index=3,
        )

    def exec_func(self, input_val=None, **kwargs):
        if not input_val:
            # TODO Put error msg to logs field (Pipeline mongo)
            raise InternalError(
                ERROR_REQUIRED, params={"code": ["INPUT_URL"], "msg": ["Input URL"]}
            )

        #url = input_val


        by = self.params["by"]
        expr = self.params["expr"]
        filter_link = self.params.get("filter")
        origin = self.params.get("origin")

        #page = self.driver.goto(url)
        page = input_val

        elems = self.driver.select(page, by, expr)

        # Map from elements to urls
        urls = list(map(self.__map_to_url, elems, str(filter_link), origin))
        # Ignore None items
        urls = list(filter(lambda url: url is not None and  url !="", urls))
        # Distinct value
        urls = list(set(urls))
        
        #print(urls)
        return urls

    def __map_to_url(self, elem, filter_link, origin):
        href = self.driver.get_attr(elem, "href")
        if href is None:
            return None
        if href.startswith("//"):
            url = href.lstrip("//")
        else:
            url = href

        if 'http://' in url or 'www.' in url or 'https://' in url:
            pass
        else:
            url = f"{origin}{href}" if origin is not None and origin not in href else href
        
        if "http://" not in url and "https://" not in url:
            protocol = urlparse(self.driver.get_current_url()).scheme
            url = f"{protocol}://{url}"
        if filter_link not in ["None", None, ""]:
            if not re.search(filter_link, url):
                return None
        return url
