import csv
import time
import os, sys
import pandas as pd
from datetime import datetime
import numpy as np
import json
from configparser import ConfigParser

sys.path.append(".//..//api")
#pylint: disable=import-error
from logger import Logger
from requester import Threaded_Requester, Requester
from config import Config

HORSES = []

columns = ['finish','date','age','track','type','mode','length','jockey']
sections = ['victories','success','trainer','earnings','birthday']

def setup():
    global requester
    global logger
    global config
    requester = Requester()
    logger = Logger()
    config = Config()

    url = 'https://www.paris-turf.com/compte/login_check'

    with open('login_headers.json','r') as f_in:
        login_headers = json.load(f_in)

    with open('login_data.json','r') as f_in:
        login_data = json.load(f_in)
    requester.post(url,login_data,login_headers)

    os.chdir(f'./races/{config.RACE_TYPE}')

    df = pd.concat([pd.read_csv(f'races_{y}.csv',engine='python') for y in range(2008,2021)])

    df.to_csv(open('all.csv','w'),na_rep='NaN',index=False,encoding="utf-8")
    df.to_excel(open('all.xlsx','wb'),na_rep='NaN',index=False,encoding="utf-8")

    for ix in range(1,21):
        HORSES.extend([i for i in df[f'NAME{ix}'] if i is not np.nan])

    print(len(HORSES),len(set(HORSES)))

def find_horses(response):
    url = 'https://www.paris-turf.com/fiche-cheval/' + horse
    requester.webpage = url

    c_dct = {c:[] for c in columns}
    s_dct = {s:np.nan for s in sections}

    table = requester.find('//table[@class = "table tooltip-enable race-table sortable"]/tbody//tr',response=response)
    
    s_dct['trainer'] = requester.find('//span[@class="text-color-flashy-2"][1]/..',response=response)[0].attrib["href"].split('/')[-1]
    s_dct['victories'] = requester.find('//span[@class="icon-trophy"]/span',response=response)[0].text_content()
    s_dct['success'] = requester.find('//div[@id="gauge"]/span[@class="text-color-flashy-2"]',response=response)[0].text_content()
    s_dct['earnings'] = requester.find('//span[@class="title text-color-flashy-2 text-size-lg text-bold"]',response=response)[0].text_content()
    s_dct['birthday'] = requester.find('//div[@class="row-fluid row-no-margin historyBlock"]/div[@class="col-xs-4"][1]//tr[@class="vertical-middle"][2]/td[2]',response=response)[0].text_content()

    for row in table:
        c_dct['jockey'].append(requester.find('/td[@class="nom"][2]/a',response=response,parent=row)[0].attrib["href"].split('/')[-1])
        c_dct['date'].append(requester.find('/td[@class="date fixe fixed-column tooltip-cell"]',response=response,parent=row)[0].text_content())
        c_dct['finish'].append(requester.find('/td[@class="fixe fixed-column classement tooltip-cell"]',response=response,parent=row)[0].text_content())

def threaded_request_callback(url):
    requester.webpage = url
    find_horses(requester.webpage)

if __name__ == '__main__':
    setup()

    for horse in HORSES:
        url = 'https://www.paris-turf.com/fiche-cheval/' + horse
        threaded_request_callback(url)
        break