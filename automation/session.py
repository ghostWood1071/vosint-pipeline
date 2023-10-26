from .drivers import DriverFactory
from .pipeline import Pipeline
from .storages import StorageFactory
from random import randint

class Session:
    def __init__(
        self, 
        driver_name: str, 
        storage_name: str, 
        actions: list[dict], 
        pipeline_id=None,
        mode_test =None,
        source_favicon=None,
        
    ):
        #print('proxy',str(actions[0]['params']['proxy_list'][0]))
        if str(actions[0]['params']['proxy_list']) == '[]' or str(actions[0]['params']['proxy_list']) == '[None]' or str(actions[0]['params']['proxy_list']) == 'None':
            self.__driver = DriverFactory(driver_name)
        else:
            proxy_list = actions[0]['params']['proxy_list']
            proxy_index = self.random_proxy(proxy_list)
            # if proxy_index >= 0:
            #     self.__driver = DriverFactory(name = driver_name,id_proxy = proxy_list[proxy_index])
            # else:
            self.__driver = DriverFactory(driver_name)
        self.__storage = StorageFactory(storage_name)
        self.__pipeline = Pipeline(self.__driver, self.__storage, actions, pipeline_id ,mode_test,list_proxy = actions[0]['params']['proxy_list'], source_favicon=source_favicon)
        #print(actions)

    def random_proxy(self,proxy_list):
        if isinstance(proxy_list, list):
            if len(proxy_list) == 0:
                return -1
            return randint(0, len(proxy_list)-1)
        return -1
        
    def start(self):
        print("Started session!")
        res = self.__pipeline.run()
        print("Finished session!")

        return res
