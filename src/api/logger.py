import sys, os
from datetime import datetime

class Logger(object):
    def __init__(self):
        self.filename = f'.//logs//{(datetime.now().strftime("%H_%M_%S"))}.txt'
        try:
            self.log = open(self.filename, "a")
        except FileNotFoundError:
            self.filename = f'.//..//logs//{(datetime.now().strftime("%H_%M_%S"))}.txt'
            self.log = open(self.filename, "a")

    def write(self, message):
        self.log.write(message)
        self.log.flush()
        self.log.write('\n')
        self.log.flush()

    def quit(self):
        self.log.close()