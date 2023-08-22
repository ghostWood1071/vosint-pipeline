from common.internalerror import *
from ..common import ActionInfo, ActionType, ParamInfo
from .baseaction import BaseAction
from models import MongoRepository
from playwright.sync_api import Playwright, sync_playwright
import time

def select(from_element, expr, by = "css="):
    element = from_element.locator(f"{by}{expr}")
    element = [element.nth(i) for i in range(element.count())]
    return element


class TwitterAction(BaseAction):
    @classmethod
    def get_action_info(cls) -> ActionInfo:
        return ActionInfo(
            name="twitter",
            display_name="Twitter",
            action_type=ActionType.COMMON,
            readme="twitter",
            param_infos=[
                ParamInfo(
                    name="link_person",
                    display_name="Link đối tượng theo dõi",
                    val_type="str",
                    default_val="",
                    validators=["required_"],
                )
            ],
            z_index=14,
        )

    def exec_func(self, input_val=None, **kwargs):
        collection_name = "twitter"
        link = self.params["link_person"]
        #data = {}

        browser = self.driver.get_driver()
       
        context = browser.new_context()
        page = context.new_page()

        page.goto(link)
        time.sleep(2)

        page.keyboard.press('End')
        page.wait_for_selector('body')
        time.sleep(2)

        twit =  select(page,'article')
        for i in twit:
            data = {}
            try:
                data["raw_data_text"] = i.inner_text()
                data["raw_data_html"] = i.inner_html()
                data["header"] = select(i,".css-1dbjc4n.r-k4xj1c.r-18u37iz.r-1wtj0ep")[0].inner_text()
                data["content"] = select(i,".css-901oao.r-18jsvk2.r-37j5jr.r-a023e6.r-16dba41.r-rjixqe.r-bcqeeo.r-bnwqim.r-qvutc0")[0].inner_text()
                tmp = select(i,".css-1dbjc4n.r-1ta3fxp.r-18u37iz.r-1wtj0ep.r-1s2bzr4.r-1mdbhws")[0]
                a = select(tmp,".css-901oao.css-16my406.r-poiln3.r-bcqeeo.r-qvutc0")
                data["reply"] = a[0].inner_text()
                data["retweet"] = a[1].inner_text()
                data["like"] = a[2].inner_text()
                data["view"] = a[3].inner_text()
        
                check_url_exist = '0'
                # a,b = MongoRepository().get_many(collection_name=collection_name,filter_spec={"id_data_ft":data['id_data_ft']})
                # del a
                # if str(b) != '0':
                
                #     print('url already exist')
                #     check_url_exist = '1'
                if check_url_exist == '0':
                    try:
                        #print(data)
                        MongoRepository().insert_one(collection_name=collection_name, doc=data)
                    except:
                        print("An error occurred while pushing data to the database!")
            except:
                pass
            
            # if check_url_exist == '1':
            #     try:
            #         a = MongoRepository().get_one(collection_name=collection_name,filter_spec={"id_data_ft":data['id_data_ft']})
            #         #print('abcccccccccccccccccccccccccccccccccccccccccccc',a["_id"])
            #         news_info_tmp = data
            #         news_info_tmp["_id"] = str(a["_id"])
            #         MongoRepository().update_one(collection_name=collection_name, doc=news_info_tmp)
            #         print('update new ....')
            #     except:
            #         print("An error occurred while pushing data to the database!")
    