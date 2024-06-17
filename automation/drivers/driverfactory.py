from common.internalerror import *

from .playwrightdriver import PlaywrightDriver
from .seleniumdriver import SeleniumWebDriver
from models import MongoRepository

class DriverFactory:
    def __new__(cls, name: str , id_proxy = None):
        if id_proxy != None and id_proxy!=[]:
            print(id_proxy)
            proxy = MongoRepository().get_one(collection_name="proxy",filter_spec={"_id":id_proxy})
            if name in ["playwright", "None", None]:
                driver_cls = PlaywrightDriver(
                    ip_proxy=proxy['ip_address'],
                    port=proxy['port'],
                    username=proxy['username'],
                    password=proxy['password']) 
            else:
                driver_cls = SeleniumWebDriver(
                    ip_proxy=proxy['ip_address'],
                    port=proxy['port'],
                    username=proxy['username'],
                    password=proxy['password']) 
        else:
            driver_cls = PlaywrightDriver() if name in ["playwright", "None", None] == "playwright" else SeleniumWebDriver()
        if driver_cls is None:
            raise InternalError(
                ERROR_NOT_FOUND, params={"code": ["DRIVER"], "msg": [f"{name} driver"]}
            )

        return driver_cls
