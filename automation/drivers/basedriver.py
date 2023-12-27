from abc import abstractmethod

class BaseDriver:
    @abstractmethod
    def destroy(self):
        raise NotImplementedError()

    @abstractmethod
    def goto(self, url: str, proxy=None, clear_cookies=True, cookies=[]):
        raise NotImplementedError()

    @abstractmethod
    def select(self, from_elem, by: str, expr: str):
        raise NotImplementedError()

    @abstractmethod
    def get_attr(self, from_elem, attr_name: str):
        raise NotImplementedError()

    @abstractmethod
    def get_content(self, from_elem) -> str:
        raise NotImplementedError()
    
    @abstractmethod
    def get_html(self, from_elem) -> str:
        raise NotImplementedError()

    @abstractmethod
    def click(self, from_elem, time_sleep: float=0.3):
        raise NotImplementedError()

    @abstractmethod
    def fill(self, from_elem, value: str):
        raise NotImplementedError()

    @abstractmethod
    def scroll(self, from_elem, value: int, time_sleep: float=0.3):
        raise NotImplementedError()

    @abstractmethod
    def sendkey(self, from_elem, value: str):
        raise NotImplementedError()
    
    @abstractmethod
    def hover(self, from_elem):
        raise NotImplementedError()
    
    @abstractmethod
    def get_current_url(self):
        raise NotImplementedError()
    
    @abstractmethod
    def get_page(self):
        raise NotImplementedError()

    @abstractmethod
    def add_cookies(self, cookies):
        raise NotImplementedError()
    
    @abstractmethod
    def get_cookies(self):
        raise NotImplementedError()
    
    @abstractmethod
    def init_proxy(self, proxy):
        raise NotImplementedError()
    
    @abstractmethod
    def get_device(self, device_name):
        raise NotImplementedError()
