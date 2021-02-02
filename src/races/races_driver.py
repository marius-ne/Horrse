from configparser import ConfigParser
import csv
import time
import os, sys
import pandas as pd
from datetime import datetime
import numpy as np
import random

sys.path.append(".//..//api")
#pylint: disable=import-error
from logger import Logger
from requester import Threaded_Requester, Requester
from config import Config



columns = ['IX','starters','mode','track','pool','date','length','ground','cond','ref','corde','q1',
           'p1','p2','p3','FIN','PMU','OUV','S/A','BOX','DELTA','WEIGHT','NAME','JOCK','TRAINER','link']

DF_DCT = {c:[] for c in columns}
RACE_YEAR = {f'{m:02d}' : [] for m in range(1,13)}

def year():
    #generator that steps through the year
    for k,v in config.YEAR_DCT.items():
        yield k,v

def log():
    df = pd.DataFrame.from_dict(DF_DCT)
    df.to_csv(path_or_buf=open(f'races_{config.YEAR}.csv','w'),na_rep='NaN',index=False, encoding="utf-8")
    df.to_excel(excel_writer=open(f'races_{config.YEAR}.xlsx','wb'),na_rep='NaN',index=False, encoding="utf-8")

def setup():
    os.chdir('C://Users//meneu//Documents//prop//code//horrse//git_repo//src//races')
    global requester
    global logger
    global config
    global IX
    config = Config()
    logger = Logger()
    requester = Threaded_Requester()

    IX = int(config.YEAR) * 10000

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
                #double checking illegal meetings
                if not [j for j in race.split('/') if j in config.ILLEGAL_MEETINGS]:
                    RACE_YEAR[date.split('-')[1]].append(race)
                else:
                    pass
    os.chdir(f'./../../races/{config.RACE_TYPE}')

def find_races(response):
    """
    writing a row for each legal finishing horse
    dct (general dct) is the general info, needs to be looked up only once
    sdct (specific dct) is unique for each horse, needs to be looked up for every row
    """
    global DF_DCT
    global IX
    
    dct = {c:np.nan for c in columns}

    info_paragraph = requester.find('//div[@class ="row-fluid row-no-margin text-left"]/p',response=response)[0]
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
                    main.extend([entry.strip() for entry in i.text_content().split('-')])
                break
        except AttributeError:
            #UnicodeElements have no .tag attribute
            continue

    race_type = main[0]
    logger.write(race_type)
    
    if config.RACE_TYPE not in race_type.lower():
        logger.write(f'parsed {response.url}')
        return None  

    table = requester.find('//tr[@class="vertical-middle"]',response=response)  

    dct['mode'] = race_type.replace('é','e')

    dct['link'] = response.url

    dct['date'] = response.url.split('/')[4]

    dct['starters'] = len(table)

    dct['IX'] = IX

    pool_paragraph = requester.find('//div[@class ="row-fluid row-no-margin text-left"]/p',response=response)[1]
    dct['pool'] = requester.find('/node()',response=response,parent=pool_paragraph)[3].replace('€','').strip(' \n')

    track = requester.find('//header[@class ="text-center CourseHeader"]/h1/node()[not(self::strong)]',response=response)
    for entry in track:
        if '/' in entry:
            entry = entry.replace(' ','')
            entry = entry.split('/')[0][1:]
            dct['track'] = entry.replace('é','e')    

    #parsing the paragraph above the table for the relevant info
    for i in main:
        if 'sable' in i.lower():
            dct['ground'] = 'sand'
            cond = [word.replace('é','e') for word in main if 'terrain' in word.lower()]
            dct['cond'] = ''.join(cond) if cond else np.nan
        elif 'mètres' in i.lower() and 'lice' not in i.lower():
            dct['length'] = i.replace('mètres','m')
        elif 'réf' in i.lower():
            dct['ref'] = i.replace('é','e').replace(',','.').strip('Ref: ')
        elif 'gauche' in i.lower():
            dct['corde'] = 'left'
        elif 'droit' in i.lower():
            dct['corde'] = 'right'
        elif 'terrain' in i.lower() and dct['ground'] is np.nan:
            dct['ground'] = 'grass'
            dct['cond'] = i.replace('é','e')

    odds_table = requester.find('//table[@class = "table reports first"]/tbody//tr[@class = "vertical-middle text-center"]',response=response)
    dct['q1'] = requester.find('/td[2]',response=response,parent=odds_table[0])[0].text_content().replace('€','').replace(',','.')
    dct['p1'] = requester.find('/td[2]',response=response,parent=odds_table[1])[0].text_content().replace('€','').replace(',','.')
    dct['p2'] = requester.find('/td[2]',response=response,parent=odds_table[2])[0].text_content().replace('€','').replace(',','.')
    try:
        dct['p3'] = requester.find('/td[2]',response=response,parent=odds_table[3])[0].text_content().replace('€','').replace(',','.')
    except IndexError:
        pass
    
    legals = []
    #trying to find the number of legal finishers
    for row in table:
        #finishing position
        fin = requester.find('/td[@class="fixe strong"]/text()',response=response,parent=row)[0]
        try:
            #is the finishing a number? -> else is illegal if not Npl. (unplaced)
            fin = int(fin[0])
            legals.append(row)
        except ValueError:
            if fin != "Npl.":
                print(fin,response.url.split('/')[-1])
                break
            else:
                legals.append(row)
            
    dct['starters'] = len(legals)
    
    specifics = ['FIN','PMU','OUV','S/A','BOX','DELTA','WEIGHT','NAME','JOCK','TRAINER']
    #now comes horse specific info, general info in dct is unchanged, specific gets generated for each legal finishing horse
    for pos,row in enumerate(legals):
        for param in specifics:
            dct[param] = np.nan

        dct['FIN'] = pos + 1
        
        dct['BOX'] =  requester.find('/td[@class="filtered arrivees rapport"][last()]/text()',response=response,parent=row)[0]
        weight =  requester.find('/td[@class="filtered arrivees rapport"][1]',response=response,parent=row)[0].text_content().replace(',','.')
        #sometimes xpath changes when preceding column is "-", then weight moves to [2]
        if weight.strip() == '-':
             weight =  requester.find('/td[@class="filtered arrivees rapport"][2]',response=response,parent=row)[0].text_content().replace(',','.')
        try:
            #
            num_test = int(weight[0])
            dct['WEIGHT'] = weight
        except ValueError:
            pass #weight stays np.nan

        try:
            delta = requester.find('/td[@class="filtered arrivees strong"]/text()',response=response,parent=row)[0]
            dct['DELTA'] = delta.replace('ê','e')
        except IndexError:
            pass #delta stays np.nan

        #sex and age combined into single argument (Hongre - 5y/o == "H5")
        dct['S/A'] = requester.find('/td[@class="filtered arrivees"]/text()',response=response,parent=row)[0]
        
        #xpath numbering is indexed from 1
        ouv = requester.find('/td[@class="rapport filtered arrivees"][1]/text()',response=response,parent=row)[0]
        try:
            ouv = int(ouv[0])
            dct['OUV'] = ouv
        except ValueError:
            pass #ouv stays np.nan

        pmu =  requester.find('/td[@class="rapport filtered arrivees"][2]/text()',response=response,parent=row)[0]
        try:
            pmu = int(pmu[0])
            dct['PMU'] = pmu
        except ValueError:
            pass #pmu stays np.nan

        horse = requester.find('/td[@class="nom tooltip-cell strong"]',response=response,parent=row)[0]
        #getting name in the url format (made up of name and id)
        dct['NAME'] = f'{"-".join(horse.text_content().split(" "))}-{horse.attrib["data-id"]}'

        dct['JOCK'] = requester.find('/td[@class="nom tooltip-cell filtered arrivees"][1]/a',response=response,parent=row)[0].attrib['href'].split('/')[-1]
        dct['TRAINER'] = requester.find('/td[@class="nom tooltip-cell filtered arrivees"][2]/a',response=response,parent=row)[0].attrib['href'].split('/')[-1]
        
        dct = {k : v.strip() if type(v) == str else v for k,v in dct.items()}
        for k,v in dct.items():
            DF_DCT[k].append(v)
    IX += 1
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
    #for i in range(200,250):
    #    threaded_request_callback(urls[i])

    after = time.time()
    all_time.append(after-bef)
    log()

    logger.write(f'{config.YEAR} took {(sum(all_time)/len(all_time) / 60):2f} minutes')
    
    

