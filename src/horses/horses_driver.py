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

columns = ['IX','name','sex','birthday','success','trainer','FIN','BOX','DATE','AGE','JOCK','TRACK','TYPE','MODE','LENGTH','GROUND','COND','WEIGHT','LINK']

def merge(y1,y2):
    df = pd.concat([pd.read_csv(f'races_{y}.csv',engine='python') for y in range(y1,y2)])

    with open('all.csv','w') as f:
        df.to_csv(f,na_rep='NaN',index=False,encoding="utf-8")
    with open('all.xlsx','wb') as f:
        df.to_excel(f,na_rep='NaN',index=False,encoding="utf-8")

def log():
    df = pd.DataFrame.from_dict(DF_DCT)
    df.to_csv(path_or_buf=open(f'horses.csv','w'),na_rep='NaN',index=False, encoding="utf-8")
    #df.to_excel(excel_writer=open(f'horses.xlsx','wb'),na_rep='NaN',index=False, encoding="utf-8")

def login():
    url = 'https://www.paris-turf.com/compte/login_check'
    requester.login(url,login_data,login_headers)

def setup():
    global requester
    global logger
    global config
    global login_headers
    global login_data
    global DF_DCT
    global HORSES
    requester = Threaded_Requester()
    logger = Logger()
    config = Config()

    DF_DCT = {c:[] for c in columns}
    HORSES = []

    with open('login_headers.json','r') as f_in:
        login_headers = json.load(f_in)

    with open('login_data.json','r') as f_in:
        login_data = json.load(f_in)

    os.chdir(f'./races/{config.RACE_TYPE}')

    #merge(2006,2021)
    
    df = pd.read_csv('all.csv',engine='python')
    for i in df[f'NAME']:
        if i is not np.nan:
            HORSES.append(i)

    os.chdir('./../../horses')

def find_horse_data(name,response):
    dct = {c:np.nan for c in columns}
    
    table = requester.find('//table[@class = "table tooltip-enable race-table sortable"]/tbody//tr',response=response)

    dct['IX'] = name.split('-')[-1]
    dct['name'] = name
    dct['trainer'] = requester.find('//span[@class="text-color-flashy-2"][1]/..',response=response)[0].attrib["href"].split('/')[-1]
    #s_dct['victories'] = requester.find('//span[@class="icon-trophy"]/span',response=response)[0].text_content()
    dct['success'] = requester.find('//div[@id="gauge"]/span[@class="text-color-flashy-2"]',response=response)[0].text_content().strip(' \n%')
    #s_dct['earnings'] = requester.find('//span[@class="title text-color-flashy-2 text-size-lg text-bold"]',response=response)[0].text_content().strip(' \n')
    general_table = requester.find('//div[@class="row-fluid row-no-margin historyBlock"]' +
                                  '/div[@class="col-xs-4"][1]//tr[@class="vertical-middle"]',response=response)

    for row in general_table:
        if "Date de naissance" in row[0].text_content():
            dct['birthday'] = row[1].text_content()
        elif "Sexe" in row[0].text_content():
            dct['sex'] = row[1].text_content()

    bday_time = datetime.strptime(dct['birthday'],'%Y-%m-%d')

    specifics = ['FIN','BOX','DATE','AGE','JOCK','TRACK','TYPE','MODE','LENGTH','GROUND','COND','WEIGHT','LINK']
    for row in table:
        for param in specifics:
            dct[param] = np.nan
        dct['JOCK'] = requester.find('/td[@class="nom"][2]/a',response=response,parent=row)[0].attrib["href"].split('/')[-1]
        dct['LINK'] = 'https://paris-turf.com' + requester.find('/td[@class="nom stadium"]/a',response=response,parent=row)[0].attrib["href"].split('?')[0]
        dct['TRACK'] = requester.find('/td[@class="nom stadium"]/a',response=response,parent=row)[0].text_content()
        dct['TYPE'] = requester.find('/td[3]',response=response,parent=row)[0].text_content()
        dct['MODE'] = requester.find('/td[@class="italiques"]',response=response,parent=row)[0].text_content()
        dct['LENGTH'] = requester.find('/td[5]',response=response,parent=row)[0].text_content()
        ground = requester.find('/td[6]',response=response,parent=row)[0].text_content()
        if not ground:
            ground = 'grass'
        elif ground == 'PSF':
            ground = 'sand'
        dct['GROUND'] = ground
        dct['COND'] = requester.find('/td[7]',response=response,parent=row)[0].text_content()
        dct['WEIGHT'] = requester.find('/td[@class="nom"][2]/following-sibling::td[2]',response=response,parent=row)[0].text_content().replace(',','.')
        box = requester.find('/td[@class="nom"][2]/following-sibling::td[3]',response=response,parent=row)[0].text_content()
        if box.strip() != '-':
            if "D" not in box and "G" not in box:
                box = 'D' + box
            dct['BOX'] = box.replace(' ','')

        date = requester.find('/td[@class="date fixe fixed-column tooltip-cell"]',response=response,parent=row)[0].text_content()
        dct['DATE'] = date
        dct['FIN'] = requester.find('/td[@class="fixe fixed-column classement tooltip-cell"]',response=response,parent=row)[0].text_content()

        race_time = datetime.strptime(date,'%d/%m/%y')
        delta = race_time-bday_time
        dct['AGE'] = delta.days

        dct = {k:v.strip() if type(v) == str else v for k,v in dct.items()}
        for k,v in dct.items():
            DF_DCT[k].append(v)
    logger.write(f'parsed {response.url}')

def threaded_request_callback(horse):
    login()

    url = 'https://www.paris-turf.com/fiche-cheval/' + horse
    requester.webpage = url  

    find_horse_data(horse,requester.webpage)  

if __name__ == '__main__':
   
    setup()
    bef = time.time()
    print(len(set(HORSES)))
    requester.bulk(threaded_request_callback,set(HORSES))
    aft = time.time()
    log()
    logger.write(f'logging {len(set(HORSES))} took {(aft-bef)/60} minutes')
    #threaded_request_callback('Litura-IRE-1013207')