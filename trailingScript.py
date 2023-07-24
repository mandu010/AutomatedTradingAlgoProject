# -*- coding: utf-8 -*-
"""
Created on Thu May 25 11:31:42 2023

@author: mandl
"""

## Trailing Script
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
import argparse
import sys
import subprocess

parser = argparse.ArgumentParser(description="Just an example",formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-sp','--strikePrice', type=str, help='Strike Price, Eg: 43000_C')
parser.add_argument('-sl','--initialPrice', type=str, help='Initial SL Price, SL Price while setting the SL')
parser.add_argument('-ep', '--entryPrice', type=str, help='Entry Price')
args = parser.parse_args()
strikePrice = args.strikePrice
initialSlPrice = args.initialPrice
EntryPrice = args.entryPrice
targetPrice = ( float(EntryPrice) + ((float(EntryPrice) - float(initialSlPrice))*2) )

initialSlPrice = round(float(initialSlPrice))
EntryPrice = round(float(EntryPrice))
lastClosingPrice = EntryPrice
print(strikePrice,initialSlPrice,EntryPrice,lastClosingPrice,"Target Price is ",targetPrice)
#sys.exit()

#### Variables
algoDir = "/root/algo"
credFile = "/root/algo/cred.yml"
PP_path = "/root/algo/PP.json"
TOTP = ""
logs = "/root/algo/Logs"
trailingDir = os.path.join(algoDir,"TrailingData")
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
#    strikePrice = '44400_P'
#    initialSlPrice='700'
#    initialSlPrice = round(float(initialSlPrice))
#    EntryPrice = '845'
#    EntryPrice = round(float(EntryPrice))
#    lastClosingPrice = '700'
    strikeJsonFileName = strikePrice+"_"+str(datetime.now().strftime("%d_%m_%Y_%H_%M"))
    trailingDataPath = os.path.join(trailingDir,strikeJsonFileName)
    
    log("Trailing Script: Logging in Now")
    api = loginFunction()
    log('Trailing Script: Getting Bank Nifty Current Month Futures token and symbol')
    var = api.searchscrip('NFO', 'Bank Nifty')['values'][0]
    token = var['token']
    BnfSymbol = var['tsym']
    openPositions = api.get_positions()
    for position in openPositions:
        if strikePrice.split('_')[0] in position['tsym']: algoPosition = position
    orderBook = api.get_order_book()
    for order in orderBook:
            if (('TRIGGER_PENDING' in order['status']) and (strikePrice.split('_')[0] in order['tsym'])): algoOrder = order
    print(algoOrder) 
    trailingData = {'strikePrice':str(strikePrice), ### Initiating Trailing JSON File
                   'Entry_Price':str(EntryPrice),
                   'SL_Price':str(initialSlPrice),
                   'Last_Closing_Price':str(EntryPrice)}
    with open(trailingDataPath,'w') as j:
        json.dump(trailingData, j)
    print("Start")
    while datetime.now().minute not in {0, 15, 30, 45}: sleep(1)
    while ( (int(datetime.now().strftime("%H%M%S")) > int(time(9,15,00).strftime("%H%M%S")) ) and ( int(datetime.now().strftime("%H%M%S")) < int(time(14,35,00).strftime("%H%M%S")) ) ):
#    while ( (int(datetime.now().strftime("%H%M%S")) > int(time(9,15,00).strftime("%H%M%S")) ) ):
        try:
            api = loginFunction()
            log("Trailing Script Time Synced for Trailing Script now at: "+str(datetime.now()))
            if str(api.single_order_history(orderno=algoOrder['norenordno'])) == 'COMPLETE':
                log("Trailing Script: SL Hit, Exiting and Calling Main Script, Terminate if Max SL Hit")
                signalFunction.telegramBot("Trailing Script: SL Hit, Exiting and Calling Main Script, Terminate if Max SL Hit")
                #os.system('python /root/algo/main.py &')
                scriptPath = '/root/algo/main.py'
                subprocess.Popen(['python', scriptPath], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
                sys.exit()
            x = open(trailingDataPath)
            getTrailingData = json.load(x)
            newClosingData = signalFunction.trailingData(trailingData['strikePrice'],'NFO', interval, api)
            newClosingPrice = newClosingData['last_high'] if (int(datetime.now().strftime("%H%M%S")) > int(time(13,00,00).strftime("%H%M%S")) ) else newClosingData['last_closing']
            
            if float(newClosingPrice) > float(getTrailingData['Last_Closing_Price']):
                ### Trail algoOrder and Update the 'Last_Closing_Price' of JSON File
                print('Inside newclosing price > trailing')
                if bool(api.get_positions()) == False: api = loginFunction() 
            ### Modifying SL Order 
                newTrailPrice = round(int(trailingData['SL_Price'])) + round(  (round(int(newClosingPrice)) - round(int(trailingData['Entry_Price'])))/2 )
                api.modify_order(algoOrder['norenordno'], 'NFO', algoOrder['tsym'], algoOrder['qty'], newprice_type='SL-LMT',newprice=int(newTrailPrice),newtrigger_price=(int(newTrailPrice)+2))
                with open(trailingDataPath,'r') as file:
                    json_data = json.load(file)
                getTrailingData['Last_Closing_Price'] = str(newClosingPrice)
                with open(trailingDataPath,'w') as j: json.dump(getTrailingData, j)                
                signalFunction.telegramBot("Trailed Successfully to "+str(newTrailPrice))
            else:
                log(f"Nothing to Trail.New Closing Data: {newClosingData}")
                signalFunction.telegramBot("Nothing to Trail")
            print(datetime.now())
            sleep(round(((datetime.now() + timedelta(minutes=15 - ((datetime.now()).minute % 15))).replace(second=0, microsecond=0) - datetime.now()).total_seconds()) + 2)
#            sleep(900-datetime.now().second+2)

        except Exception as e:
            print(f"Failed to Trail: Error: {e}")
except Exception as e:
    print(f"Failed to Trail: Error: {e}")
