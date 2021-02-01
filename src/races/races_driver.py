from configparser import ConfigParser
import csv
import time
import os, sys
import pandas as pd
from datetime import datetime
import numpy as np

sys.path.append(".//..//api")
#pylint: disable=import-error
from logger import Logger
from requester import Threaded_Requester, Requester
from config import Config



columns = ['starters','mode','track','pool','date','length','ground','cond','ref','corde','Q1','P1','P2','P3']
for i in range(1,21):
    columns.append(f'PMU{i}')
    columns.append(f'OUV{i}')
    columns.append(f'S/A{i}')
    columns.append(f'BOX{i}')
    columns.append(f'DELTA{i}')
    columns.append(f'NAME{i}')
    columns.append(f'WEIGHT{i}')
columns.append('link')

DF_DCT = {c:[] for c in columns}
RACE_YEAR = {f'{m:02d}' : [] for m in range(1,13)}

def year():
    #generator that steps through the year
    for k,v in config.YEAR_DCT.items():
        yield k,v

def log():
    df = pd.DataFrame.from_dict(DF_DCT)
    df.to_csv(path_or_buf=open(f'races_{config.YEAR}.csv','w'),na_rep='NaN',index=False, encoding="utf-8")
    df.to_excel(excel_writer=open(f'races_{config.YEAR}.xlsx','wb'),index=False,na_rep='NaN', encoding="utf-8")

def setup():
    os.chdir('C://Users//meneu//Documents//prop//code//horrse//git_repo//src//races')
    global requester
    global logger
    global config
    config = Config()
    logger = Logger()
    requester = Threaded_Requester()

    #global columns
    #global RACE_YEAR
    #global DF_DCT
    #DF_DCT = {c:[] for c in columns}
    #RACE_YEAR = {f'{m:02d}' : [] for m in range(1,13)}
    #requester = Requester()
    os.chdir(f'./meetings/{config.MEETING_TYPE}')

    with open(f'meetings_{config.YEAR}.txt','r') as foo:
        input = [line for line in foo.read().split(config.ROW_SEP) if line]

        for line in input:
            date, races = line.split(config.COL_SEP)

            for race in [i for i in races.split(config.DELIM) if i]:
                if not [j for j in race.split('/') if j in config.ILLEGAL_MEETINGS]:
                    RACE_YEAR[date.split('-')[1]].append(race)
                else:
                    pass
    os.chdir(f'./../../races/{config.RACE_TYPE}')

def find_races(response):
    global DF_DCT
    #print(response.url)
    illegal_placements = 0

    # columns = ['starters','mode','track','pool','date','length','ground','cond','ref','corde','Q1','P1','P2','P3']
    # for i in range(1,21):
    #     columns.append(f'PMU{i}')
    #     columns.append(f'OUV{i}')
    #     columns.append(f'S/A{i}')
    #     columns.append(f'BOX{i}')
    #     columns.append(f'DELTA{i}')
    #     columns.append(f'NAME{i}')
    # columns.append('link')
    dct = {c:np.nan for c in columns}

    info_paragraph = requester.find('//div[@class ="row-fluid row-no-margin text-left"]/p',response=response)[0]
    pool_paragraph = requester.find('//div[@class ="row-fluid row-no-margin text-left"]/p',response=response)[1]
    info = requester.find('/node()',response=response,parent=info_paragraph)
    
    br_pos = 0
    main = []
    for el in info:
        #get all elements until first <br> HtmlElement (break betwenn main and misc on paris-turf)
        try:
            if el.tag != 'br':
                br_pos += 1
            elif el.tag == 'br':
                for i in info[:br_pos]:
                    main.extend([entry.rstrip().lstrip() for entry in i.text_content().split('-')])
                #misc = ''.join(info[br_pos+1:]).replace('\n','')
                break
        except AttributeError:
            continue

    race_type = main[0]
    logger.write(race_type)
    
    if config.RACE_TYPE not in race_type.lower():
        #print(race_type)
        return None    

    dct['pool'] = requester.find('/node()',response=response,parent=pool_paragraph)[3].strip(' \n').replace('€','EU')

    table = requester.find('//tr[@class="vertical-middle"]',response=response)

    track = requester.find('//header[@class ="text-center CourseHeader"]/h1/node()[not(self::strong)]',response=response)
    
    for entry in track:
        if '/' in entry:
            entry = entry.replace(' ','')
            entry = entry.split('/')[0][1:]
            dct['track'] = entry.replace('é','e')

    dct['mode'] = race_type.replace('é','e')

    dct['link'] = response.url

    dct['date'] = response.url.split('/')[4]

    for i in main:
        if 'sable' in i.lower():
            dct['ground'] = 'sand'
            cond = [word.replace('é','e') for word in main if 'terrain' in word.lower()]
            dct['cond'] = ''.join(cond) if cond else np.nan
        elif 'mètres' in i.lower() and 'lice' not in i.lower():
            dct['length'] = i.replace('mètres','m')
        elif 'réf' in i.lower():
            dct['ref'] = i.replace('é','e').replace(',','.')
        elif 'gauche' in i.lower():
            dct['corde'] = 'left'
        elif 'droit' in i.lower():
            dct['corde'] = 'right'
        elif 'terrain' in i.lower() and dct['ground'] is np.nan:
            dct['ground'] = 'grass'
            dct['cond'] = i.replace('é','e')

    odds_table = requester.find('//table[@class = "table reports first"]/tbody//tr[@class = "vertical-middle text-center"]',response=response)
    dct['Q1'] = requester.find('/td[2]',response=response,parent=odds_table[0])[0].text_content().replace('€','EU').replace(',','.')
    dct['P1'] = requester.find('/td[2]',response=response,parent=odds_table[1])[0].text_content().replace('€','EU').replace(',','.')
    dct['P2'] = requester.find('/td[2]',response=response,parent=odds_table[2])[0].text_content().replace('€','EU').replace(',','.')
    
    try:
        dct['P3'] = requester.find('/td[2]',response=response,parent=odds_table[3])[0].text_content().replace('€','EU').replace(',','.')
    except IndexError:
        pass
    

    for ix,row in enumerate(table):
        ix = ix + 1
        fin = requester.find('/td[@class="fixe strong"]/text()',response=response,parent=row)[0]
        try:
            fin = int(fin[0])
        except ValueError:
            if fin != "Npl.":
                illegal_placements += 1
                print(fin,response.url)
                break
        
        dct[f'BOX{ix}'] =  requester.find('/td[@class="filtered arrivees rapport"][last()]/text()',response=response,parent=row)[0]
        dct[f'WEIGHT{ix}'] =  requester.find('/td[@class="filtered arrivees rapport"][1]/text()',response=response,parent=row)[0]

        try:
            delta = requester.find('/td[@class="filtered arrivees strong"]/text()',response=response,parent=row)[0]
            dct[f'DELTA{ix}'] = delta.replace('ê','e')
        except IndexError:
            pass

        #sex and age combined into single argument (Hongre - 5y/o == "H5")
        dct[f'S/A{ix}'] = requester.find('/td[@class="filtered arrivees"]/text()',response=response,parent=row)[0]
        
        #xpath numbering is indexed from 1
        dct[f'OUV{ix}'] = requester.find('/td[@class="rapport filtered arrivees"][1]/text()',response=response,parent=row)[0]
        dct[f'PMU{ix}'] = requester.find('/td[@class="rapport filtered arrivees"][2]/text()',response=response,parent=row)[0]

        horse = requester.find('/td[@class="nom tooltip-cell strong"]',response=response,parent=row)[0]
        dct[f'NAME{ix}'] = f'{"-".join(horse.text_content().split(" "))}-{horse.attrib["data-id"]}'

        #jock = requester.find('/td[@class="nom tooltip-cell filtered arrivees"][1]/text()',parent=row)[0]
        #trainer = requester.find('/td[@class="nom tooltip-cell filtered arrivees"][2]/text()',parent=row)[0]

    dct['starters'] = len(table) - illegal_placements

    for k,v in dct.items():
        DF_DCT[k].append(v)

    if dct['starters'] is np.nan:
        logger.write(f'parsed {response.url}')
    else:
        logger.write(f'parsed {response.url}, found handicap')

    
def threaded_request_callback(url):
    requester.webpage = url
    find_races(requester.webpage)

if __name__ == '__main__':
    setup()    

    urls = []
    for v in RACE_YEAR.values():
        urls.extend(v)

    all_time = []

    bef = time.time()

    requester.bulk(threaded_request_callback,urls)
    #for i in range(200,300):
    #    threaded_request_callback(urls[i])

    after = time.time()
    all_time.append(after-bef)
    log()

    logger.write(f'{config.YEAR} took {(sum(all_time)/len(all_time) / 60):2f} minutes')
    
    

