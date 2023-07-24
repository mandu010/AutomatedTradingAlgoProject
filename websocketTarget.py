## Main Script
import os
import time
import argparse
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
print("Websocket:",strikePrice,initialSlPrice,EntryPrice,lastClosingPrice,"Target Price is ",targetPrice)

#### Variables
algoDir = "/root/algo"
credFile = "/root/algo/cred.yml"
PP_path = "/root/algo/PP.json"
TOTP = ""
logs = "/root/algo/Logs"
logFileName = logs + '/Setup_1_' + datetime.today().strftime('%d_%m_%Y') + '.log'
hlcPath = '/root/algo/HLC_Data.txt'
scriptPath = '/root/algo/main.py'
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

def loginFunction():
    algoDir = "/root/algo"
    credFile = "/root/algo/cred.yml"
    TOTP = "HHUGE2NNC4D56TAM6A4HO75P7HD3XQ2H"
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

api = loginFunction()

feed_opened = False
feedJson = {}
def event_handler_feed_update(tick_data):
    if 'lp' in tick_data and 'tk' in tick_data:
        #print(tick_data)
        timst = datetime.fromtimestamp(int(tick_data['ft'])).isoformat()
        feedJson[tick_data['tk']] = {'ltp': float(tick_data['lp'])}
#    print(f"feed update {tick_data}")

def event_handler_order_update(tick_data):
    print(f"Order update {tick_data}")

def open_callback():
    global feed_opened
    feed_opened = True
## Functions End

try:
    log("Websocket Target Script: Logging in Now")
    api = loginFunction()
    log('Websocket Target Script: Getting Bank Nifty Current Month Futures token and symbol')
    var = api.searchscrip('NFO', 'Bank Nifty')['values'][0]
    token = var['token']
    BnfSymbol = var['tsym']
    strikePriceVar = api.searchscrip('NFO', strikePrice)['values'][0]
    strikePriceToken = strikePriceVar['token']
### Getting The Open Order of the SP
    openPositions = api.get_positions()
    for position in openPositions:
        if strikePrice.split('_')[0] in position['tsym']: algoPosition = position
    orderBook = api.get_order_book()
    for order in orderBook:
            if (('TRIGGER_PENDING' in order['status']) and (strikePrice.split('_')[0] in order['tsym'])): algoOrder = order
    print("Websocket Script: This is the SL Order",algoOrder)    
    log("Websocket Script: This is the SL Order",algoOrder)
    log("Staring Websocket")
    print("Staring Websocket")

    if str(api.single_order_history(orderno=algoOrder['norenordno'])) == 'COMPLETE':
        log("Websocket Script: SL Hit, Exiting and Calling Main Script, Terminate if Max SL Hit")
        signalFunction.telegramBot("Websocket Script: SL Hit, Exiting and Calling Main Script, Terminate if Max SL Hit")
        #os.system('python /root/algo/main.py &')
        subprocess.Popen(['python', scriptPath], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        sys.exit()
    api.start_websocket(order_update_callback=event_handler_order_update,
                     subscribe_callback=event_handler_feed_update,
                     socket_open_callback=open_callback)
    while(feed_opened==False):
        pass

# subscribe to a single token
    subscribeVar = 'NFO|'+str(strikePriceToken)
    api.subscribe(subscribeVar)
    while True:
        sleep(5)
        print("feedJson",feedJson)
        log("feedJson",feedJson[str(strikePriceToken)])
        if feedJson[str(strikePriceToken)]['ltp']>targetPrice:
            api.modify_order(algoOrder['norenordno'], 'NFO', algoOrder['tsym'], algoOrder['qty'], newprice_type='LMT',newprice=targetPrice)
            signalFunction.telegramBot("Target Achieved and Order Modified")
            log('Target Achieved and Order Modified')


except Exception as e:
    print('Failed to Achieve Target using Websocket due to:',str(e))
    errorlog('Failed to Achieve Target using Websocket due to:'+str(e))
    signalFunction.telegramBot("Failed to Achieve Target using Websocket. Check logs.")
