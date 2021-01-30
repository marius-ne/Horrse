import csv
import time
import os, sys
import pandas as pd
from datetime import datetime
import numpy as np
import json

sys.path.append(".//..//api")
#pylint: disable=import-error
from logger import Logger
from requester import Threaded_Requester, Requester
from config import Config

HORSES = {}

def setup():
    global requester
    global logger
    global config
    requester = Requester()
    logger = Logger()
    config = Config()

    url = 'https://www.paris-turf.com/compte/login_check'

    os.chdir('./horses')
    with open('login_headers.json','r') as f_in:
        login_headers = json.load(f_in)

    with open('login_data.json','r') as f_in:
        login_data = json.load(f_in)
    requester.post(url,login_data,login_headers)

    os.chdir(f'./../races/{config.RACE_TYPE}')

    df12 = pd.read_csv(f'races_2012.csv',engine='python')
    df13 = pd.read_csv(f'races_2013.csv',engine='python')
    df14 = pd.read_csv(f'races_2014.csv',engine='python')

    df = pd.concat([df12,df13,df14])

    df.to_csv(open('test.csv','w'),na_rep='NaN',index=False,encoding="utf-8")
    df.to_excel(open('test.xlsx','wb'),na_rep='NaN',index=False,encoding="utf-8")

    horses = []
    for ix in range(1,21):
        horses.extend([i for i in df[f'NAME{ix}'] if i is not np.nan])

    bef = time.time()
    for h in horses:
        HORSES[h] = horses.count(h)
    aft = time.time()
    print(aft-bef, len(HORSES))

def find_horses(horse):
    url = 'https://www.paris-turf.com/fiche-cheval/' + horse
    requester.webpage = url

    table = requester.find(requester.webpage,'//table[@class = "table tooltip-enable race-table sortable"]/tbody')
    for row in table:
        pass



if __name__ == '__main__':
    setup()

    for horse in HORSES:
        find_horses(horse)
        break