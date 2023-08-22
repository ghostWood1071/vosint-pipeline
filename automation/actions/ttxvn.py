from common.internalerror import *

from ..common import ActionInfo, ActionType, ParamInfo
from .baseaction import BaseAction
import requests
from models import MongoRepository
from datetime import datetime

class TtxvnAction(BaseAction):
    @classmethod
    def get_action_info(cls) -> ActionInfo:
        return ActionInfo(
            name="ttxvn",
            display_name="TTXVN",
            action_type=ActionType.COMMON,
            readme="Thông tấn xã Việt Nam",
            param_infos=[
                ParamInfo(
                    name="limit",
                    display_name="limit news",
                    val_type="select",
                    default_val=20,
                    #options = [1,2,3,4,5],
                    options=[i*20 for i in range(1,10)],
                    validators=["required_"],
                )
            ],
            z_index=20,
        )

    def exec_func(self, input_val=None, **kwargs):
        if not input_val:
            raise InternalError(
                ERROR_REQUIRED, params={"code": ["FROM_ELEM"], "msg": ["From element"]}
            )

        from_elem = input_val
        limit = self.params["limit"]
        url = "https://news.vnanet.vn/API/ApiAdvanceSearch.ashx"

        params = {
            "func": "searchannonimous",
            "index": "0",
            "limit": str(limit),
            "data": '[{"ContentType":"date","Key":"Created","LogicCon":"geq","Value":"7 day","ValueType":"1"},{"ContentType":"combobox","Key":"ServiceCateID","LogicCon":"eq","Value":"3","ValueType":"1"},{"ContentType":"number","Key":"SCode","LogicCon":"eq","Value":"1","ValueType":"1"},{"ContentType":"combobox","Key":"QCode","LogicCon":"eq","Value":17,"ValueType":"1"}]',
            "total": "514",
            "lid": "1066",
            "psid": "undefined"
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            # API call successful
            data = response.json()
            # Process the response data here
            for i in data['data']['data']:
                check_url_exist = '0'
                i['PublishDate']=datetime.strptime(i['PublishDate'],"%Y-%m-%dT%H:%M:%S.%f")
                i['Created']=datetime.strptime(i['Created'],"%Y-%m-%dT%H:%M:%S.%f")

                ###########3 kiểm tra trùng 
                try:
                    a,b = MongoRepository().get_many(collection_name='ttxvn',filter_spec={"ArticleID":i["ArticleID"]})
                    del a
                    if str(b) != '0':
                    
                        print('url already exist')
                        check_url_exist = '1'
                except:
                    pass
                if check_url_exist == '0':
                    MongoRepository().insert_one(collection_name='ttxvn',doc=i)
        else:
            # API call failed
            print("Error:", response.status_code)
        return "Succes: True"
