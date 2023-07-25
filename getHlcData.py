# -*- coding: utf-8 -*-
"""
Created on Wed May 31 10:04:35 2023

@author: mandl
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Jan 17 23:19:13 2023

@author: mandl
"""

## Main Script
import os
import time
from datetime import  datetime,timedelta,time,date
from time import sleep
import logging
import yaml
from yaml.loader import SafeLoader
from NorenRestApiPy.NorenApi import  NorenApi
from threading import Timer
import pandas as pd
import concurrent.futures
import pyotp
import json
import PivotFunction,signalFunction,alligator,loginFunction
import pandas_ta as ta
import numpy as np
import math
import requests
import re


#### Variables
algoDir = "/root/algo"
credFile = "/root/algo/cred.yml"
PP_path = "/root/algo/PP.json"
TOTP = ""
logs = "/root/algo/Logs"
logFileName = logs + '/Setup_1_' + datetime.today().strftime('%d_%m_%Y') + '.log'
hlcPath = '/root/algo/HLC_Data.txt'
cwd = os.chdir(algoDir)
exchange = 'NFO'
days = 100
interval = 15
ATR = 10
Multi = 3


## Functions Start
class ShoonyaApiPy(NorenApi):
    def __init__(self):
        NorenApi.__init__(self, host='https://api.shoonya.com/NorenWClientTP/', websocket='wss://api.shoonya.com/NorenWSTP/', )        
        global api
        api = self

## Functions End

api = ShoonyaApiPy()        
# Open the file and load the file
with open(credFile) as f:
    data = yaml.load(f, Loader=SafeLoader)
    #print(data)
user    = data['user']
pwd     = data['pwd']
vc      = data['vc']
app_key = data['apikey']
imei    = data['imei']
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    level=logging.INFO, 
                    filename=logFileName, 
                    filemode='a',
                    datefmt='%Y-%m-%d %H:%M:%S')
# Functions 
def log(msg, *args):
    logging.info(msg, *args)
    #print(msg, *args)
def errorlog(msg1,*args):
    logging.error(msg1, *args)
    #print(msg1,*args)
def loginFunction():
    
    #### Variables
    algoDir = "/root/algo"
    credFile = "/root/algo/cred.yml"
    TOTP = ""
    logs = "/root/algoLogs"
    logFileName = logs + '/Setup_1_' + datetime.today().strftime('%d_%m_%Y') + '.log'
    cwd = os.chdir(algoDir)
    exchange = 'NFO'
    days = 100
    interval = 15
    ATR = 10
    Multi = 3
    pattern = re.compile('|'.join(map(str, [300, 600, 900, 1200, 1500, 1800, 2100, 2400, 2700])))
## Functions Start
    class ShoonyaApiPy(NorenApi):
        def __init__(self):
            NorenApi.__init__(self, host='https://api.shoonya.com/NorenWClientTP/', websocket='wss://api.shoonya.com/NorenWSTP/', )        
            global api
            api = self
            
            ## Functions End

    api = ShoonyaApiPy()

    with open(credFile) as f:
        data = yaml.load(f, Loader=SafeLoader)
        #print(data)
        user    = data['user']
        pwd     = data['pwd']
        vc      = data['vc']
        app_key = data['apikey']
        imei    = data['imei']
        logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                            level=logging.INFO, 
                            filename=logFileName, 
                            filemode='a',
                            datefmt='%Y-%m-%d %H:%M:%S')
        login = api.login(userid=user, password=pwd, twoFA=pyotp.TOTP(TOTP).now(), vendor_code=vc, api_secret=app_key, imei=imei)        
        return api

try:
    log("getHlcData : Logging in Now")
    api = loginFunction()
    log('getHlcData : Getting Bank Nifty Current Month Futures token and symbol')
    var = api.searchscrip('NFO', 'Bank Nifty')['values'][0]
    token = var['token']
    BnfSymbol = var['tsym']    
     
    if bool(api):
        n = 3 if ((date.today().weekday()) == 0) else 1
        startDate = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=n)).timestamp()
        endDate = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        print("Starting to get Daily Prices")
        dailyPrice = api.get_daily_price_series(exchange='NFO', tradingsymbol=BnfSymbol, startdate=startDate,enddate=endDate)
        if dailyPrice != []:
            var = json.loads(dailyPrice[0])
            print(var)
            if os.path.exists(hlcPath): os.remove(hlcPath)
            with open(hlcPath, 'w') as file:
                file.write(str(var['inth'])+"\n")
                file.write(str(var['intl'])+"\n")
                file.write(str(var['intc']))
            print("Prices found. High: "+str(var['inth']+" Low: "+str(var['intl']) + " Close: "+str(var['intc'])))
            log("Prices found. High: "+str(var['inth']+" Low: "+str(var['intl']) + " Close: "+str(var['intc'])))
            signalFunction.telegramBot("getHlcData : Prices Found")
        else: 
            print('Shoonya API not Giving Daily Price Write Manually')
            log('getHlcData : Shoonya API not Giving Daily Price Write Manually')
            signalFunction.telegramBot("getHlcData : Shoonya API not Giving Daily Price Write Manually")
except Exception as e:
    errorlog('getHlcData : Error while getting EOD data '+str(e))

