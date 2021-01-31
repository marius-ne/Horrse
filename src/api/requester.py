import requests
from lxml import html
import time
import os,sys 
from logger import Logger
import concurrent.futures
import threading

class Requester(object):

    def __init__(self):
        self.s = requests.Session()
        self.logger = Logger()
        sys.setrecursionlimit(1000)

    @property
    def webpage(self):
        try:
            return self._webpage
        except NameError:
            raise AttributeError('ERROR: No request made yet!')

    @webpage.setter
    def webpage(self,url):
        self.logger.write(url)
        resp = self.s.get(url)
        if resp.status_code == 200:
            self._webpage = resp
        else:
            self.logger.write(f'get got status {resp.status_code} response, requesting again')
            self.webpage = url #recursing if request didn't work

    @property
    def dom(self):
        try:
            return html.fromstring(self._webpage.content)
        except Exception as e:
            raise e

    def find(self,xpath,response=0,parent=0):
        """
        
        """
        if response == None:
            raise ValueError("ERROR: given response doesn't exist!")
        elif response == 0:
            response = self.webpage

        if parent == None:
            raise ValueError("ERROR: given parent doesn't exist!")
        elif parent == 0:
            parent = html.fromstring(response.content)
        
        res = parent.xpath(f'.{xpath}')
        return res

    def post(self,url,data,headers=None):
        if headers:
            resp = self.s.post(url=url,data=data,headers=headers)
        else:
            resp = self.s.post(url=url,data=data)
        if resp.status_code == 200:
            return resp
        else:
            self.logger.write(f'post got status {resp.status_code} response, requesting again')
            self.post(url,data,headers)

    def renew(self):
        self.s.close()
        self.s = requests.Session()

    def quit(self):
        self.s.close()



class Threaded_Requester(object):

    def __init__(self):
        self.thread_local = threading.local()
        self.logger = Logger()
        sys.setrecursionlimit(1000)

    @property
    def webpage(self):
        try:
            return self._webpage
        except NameError:
            raise AttributeError('ERROR: No request made yet!')

    @webpage.setter
    def webpage(self,url):
        self.logger.write(f'requesting {url}')
        s = self.session
        resp = s.get(url)
        if resp.status_code == 200:
            self._webpage = resp
        else:
            self.logger.write(f'got status {resp.status_code} response, requesting again')
            self.webpage = url #recursing if request didn't work

    @property
    def dom(self):
        try:
            return html.fromstring(self._webpage.content)
        except Exception as e:
            raise e

    def bulk(self,callback,urls):
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(callback, urls)

    @property
    def session(self):
        if not hasattr(self.thread_local, "session"):
            self.logger.write('creating new requests.Session')
            self.thread_local.session = requests.Session()
        return self.thread_local.session

    def find(self,xpath,response,parent=0):
        """
        response arg not optional because of threading,
        one requester object for all threads, therefore
        specific response required
        """
        if parent == None:
            raise ValueError("ERROR: given parent doesn't exist!")
        elif parent == 0:
            parent = html.fromstring(response.content)

        res = parent.xpath(f'.{xpath}')
        return res