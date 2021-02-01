import csv
import time
import os, sys
import pandas as pd
from datetime import datetime
import numpy as np
import json
from configparser import ConfigParser
from pprint import pprint

sys.path.append(".//..//api")
#pylint: disable=import-error
from logger import Logger
from requester import Threaded_Requester, Requester
from config import Config

HORSES = []

columns = ['finish','box','date','age','jockey','track','type','mode','length','ground','cond','weight','link']
sections = ['name','sex','birthday','victories','success','trainer','earnings']

def merge(y1,y2):
    df = pd.concat([pd.read_csv(f'races_{y}.csv',engine='python') for y in range(y1,y2)])

    with open('all.csv','w') as f:
        df.to_csv(f,na_rep='NaN',index=False,encoding="utf-8")
    with open('all.xlsx','wb') as f:
        df.to_excel(f,na_rep='NaN',index=False,encoding="utf-8")

def log(name,data):
    sections = data[0]
    rows = data[1]

    cfg = ConfigParser()
    cfg['GENERAL'] = sections
    for row in rows:
        cfg[row['date']] = row

    with open(f'{name}.ini','w') as f:
        cfg.write(f)
    logger.write(f'written {name}.ini')

def login():
    url = 'https://www.paris-turf.com/compte/login_check'
    requester.login(url,login_data,login_headers)

def setup():
    global requester
    global logger
    global config
    global login_headers
    global login_data
    requester = Threaded_Requester()
    logger = Logger()
    config = Config()

    with open('login_headers.json','r') as f_in:
        login_headers = json.load(f_in)

    with open('login_data.json','r') as f_in:
        login_data = json.load(f_in)

    os.chdir(f'./races/{config.RACE_TYPE}')
    
    df = pd.read_csv('all.csv',engine='python')
    for ix in range(1,21):
        for i in df[f'NAME{ix}']:
            if i is not np.nan:
                HORSES.append(i)

    os.chdir('./../../horses/data')

def find_horse_data(name,response):
    r_dcts = []
    s_dct = {s:np.nan for s in sections}
    
    table = requester.find('//table[@class = "table tooltip-enable race-table sortable"]/tbody//tr',response=response)

    s_dct['name'] = name
    s_dct['trainer'] = requester.find('//span[@class="text-color-flashy-2"][1]/..',response=response)[0].attrib["href"].split('/')[-1]
    s_dct['victories'] = requester.find('//span[@class="icon-trophy"]/span',response=response)[0].text_content()
    s_dct['success'] = requester.find('//div[@id="gauge"]/span[@class="text-color-flashy-2"]',response=response)[0].text_content().strip(' \n') + '%' #percent needs to be escaped for configparser
    s_dct['earnings'] = requester.find('//span[@class="title text-color-flashy-2 text-size-lg text-bold"]',response=response)[0].text_content().strip(' \n')
    general_table = requester.find('//div[@class="row-fluid row-no-margin historyBlock"]' +
                                  '/div[@class="col-xs-4"][1]//tr[@class="vertical-middle"]',response=response)
    for row in general_table:
        if "Date de naissance" in row[0].text_content():
            s_dct['birthday'] = row[1].text_content()
        elif "Sexe" in row[0].text_content():
            s_dct['sex'] = row[1].text_content()

    bday_time = datetime.strptime(s_dct['birthday'],'%Y-%m-%d')
    for row in table:
        dct = {c:np.nan for c in columns}
        dct['jockey'] = requester.find('/td[@class="nom"][2]/a',response=response,parent=row)[0].attrib["href"].split('/')[-1]
        dct['link'] = 'https://paris-turf.com' + requester.find('/td[@class="nom stadium"]/a',response=response,parent=row)[0].attrib["href"].split('?')[0]
        dct['track'] = requester.find('/td[@class="nom stadium"]/a',response=response,parent=row)[0].text_content()
        dct['type'] = requester.find('/td[3]',response=response,parent=row)[0].text_content()
        dct['mode'] = requester.find('/td[@class="italiques"]',response=response,parent=row)[0].text_content()
        dct['length'] = requester.find('/td[5]',response=response,parent=row)[0].text_content()
        ground = requester.find('/td[6]',response=response,parent=row)[0].text_content()
        if not ground:
            ground = 'grass'
        elif ground == 'PSF':
            ground = 'sand'
        dct['ground'] = ground
        dct['cond'] = requester.find('/td[7]',response=response,parent=row)[0].text_content()
        dct['weight'] = requester.find('/td[@class="nom"][2]/following-sibling::td[2]',response=response,parent=row)[0].text_content()
        box = requester.find('/td[@class="nom"][2]/following-sibling::td[3]',response=response,parent=row)[0].text_content()
        if "D" not in box and "G" not in box:
            box = 'D' + box
        dct['box'] = box.replace(' ','')

        date = requester.find('/td[@class="date fixe fixed-column tooltip-cell"]',response=response,parent=row)[0].text_content()
        dct['date'] = date
        dct['finish'] = requester.find('/td[@class="fixe fixed-column classement tooltip-cell"]',response=response,parent=row)[0].text_content()

        race_time = datetime.strptime(date,'%d/%m/%y')
        delta = race_time-bday_time
        dct['age'] = delta.days

        r_dcts.append(dct)
        
    return s_dct, r_dcts

def threaded_request_callback(horse):
    login()

    url = 'https://www.paris-turf.com/fiche-cheval/' + horse
    requester.webpage = url
    
    data = find_horse_data(horse,requester.webpage)
    log(horse,data)

if __name__ == '__main__':
    setup()

    requester.bulk(threaded_request_callback,set(HORSES[0:10]))