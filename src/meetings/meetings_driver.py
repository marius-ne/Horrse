import time
from configparser import ConfigParser
import os
import sys

sys.path.append(".//..//api")
#pylint: disable=import-error
from browser import Browser
from logger import Logger
from config import Config

RACE_MONTH = {}
MEETINGS = {}

def year():
    #generator that steps through the year
    for k,v in config.YEAR_DCT.items():
        yield k,v
    
def log(month):
    with open(f'meetings_{config.YEAR}.txt','w') as foo:
        s = f''
        for k,v in RACE_MONTH.items():
            s += f"{k}{config.COL_SEP}{f'{config.DELIM}'.join([entry for entry in v])}{config.ROW_SEP}"
        foo.write(s)
    
    with open(f'meeting_index_{config.YEAR}.txt','w') as foo:
        s = ''
        for k,v in MEETINGS.items():
            s += f'{k}{config.COL_SEP}{v}{config.ROW_SEP}'
        foo.write(s)

def setup():
    global browser
    global logger
    global config
    config = Config()
    logger = Logger()
    browser = Browser()

    #sometimes there's a cookie-accept-prompt
    browser.webpage = 'https://www.paris-turf.com/programme-courses/01-01-2020'
    cookie_agree = browser.find('/html/body/div[2]/div/div[1]/div/button[2]')
        
    browser.click(cookie_agree)

    os.chdir(f'meetings/{config.MEETING_TYPE}')

def find_meetings(day,month):
    """
    steps through the month, day to day, and logs french gallop race titles
    """
    browser.webpage = f'https://www.paris-turf.com/programme-courses/{day:02d}-{month:02d}-{config.YEAR}'

    #list with links from french gallop races
    valid_races = []
    today = browser.webpage.split('/')[4]
    logger.write(browser.webpage)

    #waiting until table loads
    browser.find('//ul[@class = "tabs-menu ui-tabs-nav ui-helper-reset ui-helper-clearfix ui-widget-header ui-corner-all"]',wait=1)
    all_type = browser.find(f'//span[@class = "horses-discipline black {config.MEETING_TYPE}"]')
    
    #this block asserts that the previously found gallop meetings are french (by checking the title of the races)
    for race in all_type:    
        parent = browser.find('..',parent=race)[0]
        href = parent.get_attribute('href')
        try:
            title = parent.get_attribute('title').lower()
        except AttributeError:
            title = parent.get_attribute('title')

        logger.write(title)
        #gallop race and presumed french race
        if bool("prix" in title or "handicap de" in title) and bool("prix" in href or "handicap-de" in href):
            meeting = href.split('/')[5]

            for illegal in config.ILLEGAL_MEETINGS:
                if illegal in href:
                    break
            else:
                try:
                    MEETINGS[meeting] += 1
                except KeyError:
                    MEETINGS[meeting] = 1
                valid_races.append(href)
                
    RACE_MONTH[today] = valid_races
    logger.write(f'{config.MEETING_TYPE}: {len(all_type)}, valid: {len(valid_races)}')

    

if __name__ == "__main__":
    setup()
    whole_bef = time.time()
    for month, lst in year():
        before = time.time()
        logger.write(lst[0])
        for day in range(1,lst[1]):
            find_meetings(day,month)
        after = time.time()
        logger.write(f'{lst[0]} took {((after-before) / 60):.2f} minutes\n\n\n')
        log(lst[0])
        browser.renew()
    whole_aft = time.time()
    logger.write(f'{config.YEAR} took {((whole_aft-whole_bef) / 60):.2f} minutes\n\n\n')
    browser.quit()

