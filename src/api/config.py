from configparser import ConfigParser
import os, sys


class Config(object):  

    def __init__(self):
        

        self.CONFIG = ConfigParser()
        os.chdir('..')
        self.CONFIG.read('config.ini')

        self.YEAR_DCT = {1:['january',32],2:['february',29],3:['march',32],4:['april',31],5:['may',32],6:['june',31],
                7:['july',32],8:['august',32],9:['september',31],10:['october',32],11:['november',31],12:['december',32]}

        self.YEAR = self.CONFIG['GENERAL']['year']
        self.COL_SEP = self.CONFIG['TXT']['col_sep']
        self.DELIM = self.CONFIG['TXT']['delimiter']
        self.ROW_SEP = '\n'
        self.MEETING_TYPE = self.CONFIG['MEETINGS']['type'] 
        self.ILLEGAL_MEETINGS = ['reunion-' + loc for loc in self.CONFIG['MEETINGS']['illegal_meetings'].split(',')]     
        self.RACE_TYPE = self.CONFIG['RACES']['type']    
        self.ILLEGAL_PLACEMENTS = self.CONFIG['RACES']['illegal_placements'] 