from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.proxy import Proxy,  ProxyType
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from seleniumwire.webdriver import Chrome as ProxyChrome
from .basedriver import BaseDriver
import time
from core.config import settings
from selenium_stealth import stealth

KEY_MAP = {
    "Cancel":Keys.CANCEL,
    "Help":Keys.HELP,
    "Backspace":Keys.BACKSPACE,
    "Tab":Keys.TAB,
    "Clear":Keys.CLEAR,
    "Return":Keys.RETURN,
    "Enter":Keys.ENTER,
    "Shift":Keys.SHIFT,
    "Control":Keys.CONTROL,
    "Alt":Keys.ALT,
    "Pause":Keys.PAUSE,
    "Escape":Keys.ESCAPE,
    "Space":Keys.SPACE,
    "PageUp":Keys.PAGE_UP,
    "PageDown":Keys.PAGE_DOWN,
    "End":Keys.END,
    "Home":Keys.HOME,
    "ArrowLeft":Keys.ARROW_LEFT,
    "ArrowUp":Keys.ARROW_UP,
    "ArrowRight":Keys.ARROW_RIGHT,
    "ArrowDown":Keys.ARROW_DOWN,
    "Insert":Keys.INSERT,
    "Delete":Keys.DELETE,
    "Multiply":Keys.MULTIPLY,
    "Add":Keys.ADD,
    "Separator":Keys.SEPARATOR,
    "Subtract":Keys.SUBTRACT,
    "Decimal":Keys.DECIMAL,
    "Divide":Keys.DIVIDE,
    "F1":Keys.F1,
    "F2":Keys.F2,
    "F3":Keys.F3,
    "F4":Keys.F4,
    "F5":Keys.F5,
    "F6":Keys.F6,
    "F7":Keys.F7,
    "F8":Keys.F8,
    "F9":Keys.F9,
    "F10":Keys.F10,
    "F11":Keys.F11,
    "F12":Keys.F12
}

class SeleniumWebDriver(BaseDriver):
    def __init__(self,ip_proxy = None, port = None, username = None, password = None):
        chrome_option = Options()
        chrome_option.add_argument("--headless")
        chrome_option.add_argument('--disable-gpu')
        chrome_option.add_argument('--no-sandbox')
        if ip_proxy != None and port != None and username != None and password != None:
            proxy_server ={    
                'proxy': {
                    'http': f'http://{username}:{password}@{ip_proxy}:{port}',
                    'verify_ssl': False,
                }
            }
            self.driver = ProxyChrome(seleniumwire_options = proxy_server, options = chrome_option)
            print("selenium using proxy!")
        else:
            self.driver = Chrome(options = chrome_option)
        
        stealth(self.driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True)
        
        
    def get_driver(self):
        return self.driver
    
    def get_page(self):
        return self.driver

    def destroy(self):
        try:
            self.driver.close()
            self.driver.quit()
            print("closed driver")
        except Exception as e:
            print("driver already closed")

    def goto(self, url: str):
        self.driver.delete_all_cookies()
        self.driver.set_page_load_timeout(15)
        try:
            self.driver.get(url)
        except TimeoutException as e:
            if self.driver.find_element(By.TAG_NAME, 'body').get_attribute("innerHTML"):
                pass
            else:
                raise e
        except NoSuchElementException as ne:
            raise e
        self.driver.save_screenshot("./gotoresults/selenium.png")
        return self.driver

    def select(self, from_elem, by: str, expr: str):
        by = self.__map_selector_by(by)
        elems = from_elem.find_elements(by, expr)
        return elems

    def get_attr(self, from_elem, attr_name: str):
        return from_elem.get_attribute(attr_name)

    def get_content(self, from_elem) -> str:
        return from_elem.text
    
    def get_html(self, from_elem) -> str:
        return from_elem.get_attribute("innerHTML")


    def click(self, from_elem, time_sleep = 0.3):
        from_elem.click()
        time.sleep(float(time_sleep))
        return self.driver

    # TODO DoanCT: Bo sung scroll, sendkey
    def scroll(self, from_elem, value: int = 1, time_sleep: float=0.3):
        
        if isinstance(from_elem, Chrome):
            from_elem = self.driver.find_element(By.TAG_NAME, 'body')
            
        for i in range(value):  # make the range as long as needed
            from_elem.send_keys(Keys.END)
            wait = WebDriverWait(self.driver,time_sleep).until(expected_conditions.presence_of_element_located((By.TAG_NAME, 'body')))
            time.sleep(time_sleep)
        return self.driver

    # TODO DoanCT: Bo sung scroll, sendkey
    def scroll_page(self, value: int = 1, time_sleep: float=0.3):
        for i in range(value):  # make the range as long as needed
            self.driver.send_keys(Keys.END)
            wait = WebDriverWait(self.driver,time_sleep).until(expected_conditions.presence_of_element_located(By.TAG_NAME, 'body'))
            time.sleep(time_sleep)
        return self.driver
    
    def sendkey(self, from_elem, value: str):
        key = KEY_MAP.get(value) if KEY_MAP.get(value) is not None else value
        return from_elem.send_keys(key)

    def fill(self, from_elem:WebElement, value: str):
        return from_elem.send_keys(value)
        # return from_elem.fill(value)

    def __map_selector_by(self, selector_by: str) -> str:
        return By.CSS_SELECTOR if selector_by == 'css' else By.XPATH
    
    def hover(self, from_elem):
        actions = ActionChains(self.driver)
        hover = actions.move_to_element(from_elem).perform()
        return hover
    
    def get_current_url(self):
        return self.driver.current_url