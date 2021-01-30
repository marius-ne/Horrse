import time
import selenium
from selenium import webdriver
import urllib3
import sys
from logger import Logger

class Browser(object):

    def __init__(self):
        self.logger = Logger()
        self.driver = webdriver.Firefox()
        self.driver.set_page_load_timeout(30)
        self.driver.maximize_window()
        self.action = webdriver.ActionChains(self.driver)

        self.waited = 0
        sys.setrecursionlimit(1000)

    @property
    def webpage(self):
        return self.driver.current_url

    @webpage.setter
    def webpage(self,url):
        try:
            self.driver.get(url)
        except (selenium.common.exceptions.TimeoutException,urllib3.exceptions.MaxRetryError,selenium.common.exceptions.WebDriverException):
            time.sleep(15)
            self.logger.write('ERROR: page loading error, trying again')
            self.webpage = url

    def reload(self):
        self.logger.write(f'reloading {self.webpage}')
        self.webpage = self.driver.current_url

    def find(self,xpath,parent=0,wait=0,max_wait=15):
        """
        wait forces method into recursion, only use wait if sure
        that element either exists in dom in the first place or, if missing,
        is locatable by reloading the page
        """
        if parent == None:
            raise ValueError("ERROR: given parent doesn't exist!")
        elif parent == 0:
            parent = self.driver
        res = parent.find_elements_by_xpath(xpath)

        if wait and len(res) == 0 and self.waited < max_wait:
            time.sleep(wait)
            self.waited += wait
            return self.find(xpath,parent=parent,wait=wait)
        elif wait and self.waited >= max_wait:
            self.waited = 0
            self.reload()
            return self.find(xpath,parent=parent,wait=wait)
        else:
            self.waited = 0        #setting to zero because next waiting call would inherit any previous self.waited
            return res

    def click(self,el,repeat=1):
        if type(el) == list and len(el) == 1:
            el = el[0]
        elif type(el) == list and len(el) > 1:
            self.logger.write('ERROR: Can only click one element!')
            return None
        elif type(el) == list and len(el) == 0:
            return None
        
        try:
            for _ in range(0,repeat):
                el.click()
        except AttributeError:
            self.logger.write('ERROR: Element ist not clickable!')

    def renew(self):
        self.driver.quit()
        self.driver = webdriver.Firefox()
        self.driver.set_page_load_timeout(30)
        self.driver.maximize_window()
        self.action = webdriver.ActionChains(self.driver)

        self.waited = 0
        sys.setrecursionlimit(1000)

    def quit(self):
        self.driver.quit()