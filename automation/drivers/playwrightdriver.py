import time

from playwright.sync_api import sync_playwright, Locator, TimeoutError

from ..common import SelectorBy
from .basedriver import BaseDriver
from core.config import settings

class PlaywrightDriver(BaseDriver):
    def __init__(self,ip_proxy = None, port = None, username = None, password = None):
        if ip_proxy != None and port != None and username != None and password != None:
            self.create_proxy_browser(ip_proxy, port, username, password)
        else:
            self.create_browser(headless=False)
    
    def create_browser(self, headless=True):
        self.playwright = sync_playwright().start()
        self.driver = self.playwright.chromium.launch(channel="chrome", headless=headless, args=[
            f"--disable-extensions-except={settings.EXTENSIONS_PATH}/shadow-root",
            f"--load-extension={settings.EXTENSIONS_PATH}/shadow-root",
        ])
        self.page = self.driver.new_page(user_agent=settings.USER_AGENT)

    def create_proxy_browser(self, ip_proxy, port ,username, password):
        proxy_server = {
                'server': ip_proxy+":"+port,
                'username': username,
                'password': password
            }
        self.playwright = sync_playwright().start()
        self.driver = self.playwright.chromium.launch(channel="chrome",proxy=proxy_server, args=[
            f"--disable-extensions-except={settings.EXTENSIONS_PATH}/shadow-root",
            f"--load-extension={settings.EXTENSIONS_PATH}/shadow-root",
        ])
        self.page = self.driver.new_page(proxy={
            'server': ip_proxy+":"+port,
            'username': username,
            'password': password
        }, user_agent=settings.USER_AGENT) #self.driver.new_page()
        
        print("using proxy ...")

    def get_driver(self):
        return self.driver
    
    def get_page(self):
        return self.page

    def destroy(self):
        self.page.close()
        for context in self.driver.contexts:
            for page in context.pages:
                page.close()
        self.playwright.stop()
        print("closed driver")

    def goto(self, url: str, proxy=None):
        if proxy:
            self.page.close()
            self.driver.close()
            proxy_dict = {
                'ip_proxy': proxy.get('ip_address'),
                'port': proxy.get('port'),
                'username': proxy.get('username'),
                'password': proxy.get('password')
            }
            self.create_proxy_browser(**proxy_dict)
        self.page.context.clear_cookies()
        try:
            self.page.goto(url)
        except TimeoutError as e:
            locator = self.page.locator('body')
            if locator.inner_html() == '':
                raise e
        return self.page

    def select(self, from_elem, by: str, expr: str):
        by = self.__map_selector_by(by)
        elems = from_elem.locator(f"{by}{expr}")
        # Cast elems to list
        elems = [elems.nth(i) for i in range(elems.count())]
        return elems

    def get_attr(self, from_elem, attr_name: str):
        return from_elem.get_attribute(attr_name)

    def get_content(self, from_elem) -> str:
        return from_elem.inner_text()
    
    def get_html(self, from_elem) -> str:
        return from_elem.inner_html()    

    def click(self, from_elem, time_sleep = 0.3):
        from_elem.click()
        time.sleep(float(time_sleep))
        return self.page

    # TODO DoanCT: Bo sung scroll, sendkey
    def scroll(self, from_elem:Locator, value: int = 1, time_sleep: float=0.3):
        for i in range(value):  # make the range as long as needed
            from_elem.keyboard.press('End')
            from_elem.wait_for_selector('body')
            time.sleep(time_sleep)
    
        return from_elem
    # TODO DoanCT: Bo sung scroll, sendkey
    def scroll_page(self, value: int = 1, time_sleep: float=0.3):
        for i in range(value):  # make the range as long as needed
            self.page.keyboard.press('End')
            self.page.wait_for_selector('body')
            time.sleep(time_sleep)
        
        return self.page
    
    def sendkey(self, from_elem, value: str):
        return from_elem.type(value)

    def fill(self, from_elem, value: str):
        return from_elem.fill(value)

    def __map_selector_by(self, selector_by: str) -> str:
        return "xpath=" if selector_by == SelectorBy.XPATH else "css="
    
    def hover(self, from_elem):
        return from_elem[0].hover()
    
    def get_current_url(self):
        return self.page.url

    def add_cookies(self, cookies):
        self.page.context.add_cookies(cookies)

    def init_proxy(self, proxy):
        proxy_dict = {
                'ip_proxy': proxy.get('ip_address'),
                'port': proxy.get('port'),
                'username': proxy.get('username'),
                'password': proxy.get('password')
            }
        self.create_proxy_browser(**proxy_dict)
        