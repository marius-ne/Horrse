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

columns = ['finish','date','age','track','type','mode','length','jockey','link']
sections = ['victories','success','trainer','earnings','birthday']


def merge(y1,y2):
    df = pd.concat([pd.read_csv(f'races_{y}.csv',engine='python') for y in range(y1,y2)])

    df.to_csv(open('all.csv','w'),na_rep='NaN',index=False,encoding="utf-8")
    df.to_excel(open('all.xlsx','wb'),na_rep='NaN',index=False,encoding="utf-8")

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
    
    df = pd.read_csv('all.csv',engine='python')
    for ix in range(1,21):
        for i in df[f'NAME{ix}']:
            if i is not np.nan:
                HORSES.append(i)

    print(len(HORSES),len(set(HORSES)))
    tracks = set(df['track'])
    print(tracks)

def find_horses(response):
    print(response.url)
    c_dct = {c:[] for c in columns}
    s_dct = {s:np.nan for s in sections}
    
    table = requester.find('//table[@class = "table tooltip-enable race-table sortable"]/tbody//tr',response=response)

    s_dct['trainer'] = requester.find('//span[@class="text-color-flashy-2"][1]/..',response=response)[0].attrib["href"].split('/')[-1]
    s_dct['victories'] = requester.find('//span[@class="icon-trophy"]/span',response=response)[0].text_content()
    s_dct['success'] = requester.find('//div[@id="gauge"]/span[@class="text-color-flashy-2"]',response=response)[0].text_content().strip(' \n')
    s_dct['earnings'] = requester.find('//span[@class="title text-color-flashy-2 text-size-lg text-bold"]',response=response)[0].text_content().strip(' \n')
    birthday_row = requester.find('//div[@class="row-fluid row-no-margin historyBlock"]' +
                                  '/div[@class="col-xs-4"][1]//tr[@class="vertical-middle"][2]',response=response)[0]
    if "Date de naissance" in birthday_row[0].text_content():
        s_dct['birthday'] = birthday_row[1].text_content()
    else:
        raise Exception

    bday_time = datetime.strptime(s_dct['birthday'],'%Y-%m-%d')
    for row in table:
        c_dct['jockey'].append(requester.find('/td[@class="nom"][2]/a',response=response,parent=row)[0].attrib["href"].split('/')[-1])
        c_dct['link'].append(requester.find('/td[@class="nom"][1]/a',response=response,parent=row)[0].attrib["href"].split('/')[-1].split('?')[0])

        date = requester.find('/td[@class="date fixe fixed-column tooltip-cell"]',response=response,parent=row)[0].text_content()
        c_dct['date'].append(date)
        c_dct['finish'].append(requester.find('/td[@class="fixe fixed-column classement tooltip-cell"]',response=response,parent=row)[0].text_content())

        race_time = datetime.strptime(date,'%d/%m/%y')
        delta = race_time-bday_time
        c_dct['age'].append(delta.days)

    print(c_dct,s_dct,sep='\n')

def threaded_request_callback(url):
    requester.webpage = url
    find_horses(requester.webpage)

if __name__ == '__main__':
    setup()

    for horse in HORSES:
        url = 'https://www.paris-turf.com/fiche-cheval/' + horse
        threaded_request_callback(url)
        break