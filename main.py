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
import subprocess

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
    log("Main Script: Logging in Now")
    api = loginFunction()
    log('Main Script: Getting Bank Nifty Current Month Futures token and symbol')
    var = api.searchscrip('NFO', 'Bank Nifty')['values'][0]
    token = var['token']
    BnfSymbol = var['tsym']    
#    if signalFunction.is_file_older_than_x_days(PP_path,1):
    with open(hlcPath) as f: hlc_data = f.readlines()
    inth = float(hlc_data[0].replace('\n',''))
    intl = float(hlc_data[1].replace('\n',''))
    intc = float(hlc_data[2].replace('\n',''))
    if api:
        dailyPrice = {"inth":inth,"intl":intl,"intc":intc}   
        PP=PivotFunction.build_PP(dailyPrice)
        with open(PP_path, "w") as outfile: json.dump(PP, outfile)
        log("Main Script: New Pivots Generated: "+str(PP))
        print("New Pivots Generated: "+str(PP))
    else:
        with open(PP_path, 'r') as f:
            PP = json.load(f)            
except Exception as e:
    errorlog('Main Script: Failed Error: '+str(e))
print(PP)

#### Starting to check for signals from here.      
while datetime.now().minute not in {0, 15, 30, 45}: sleep(1)

while ( (int(datetime.now().strftime("%H%M%S")) > int(time(9,15,00).strftime("%H%M%S")) ) and ( int(datetime.now().strftime("%H%M%S")) < int(time(14,35,00).strftime("%H%M%S")) ) ):
    try:
        api = loginFunction()
        log("Main Script: Time Synced now at: "+str(datetime.now()))        
        strikePrice = {'Signal':'No Signal'}
        try:
            strikePrice = signalFunction.supertrend(exchange, token, days, interval, ATR, Multi, PP, api)
            print(strikePrice)            
            signalFunction.telegramBot("Alligator Setup Signal: "+re.sub("{|}|'|_", "", str(strikePrice['Signal'])))
            log(str(strikePrice))
        except Exception as e:
            errorlog('Error while searching for signal '+str(e))
            print('Error while searching for signal '+str(e))
        
        checkPosition = 0
        if api.get_positions() != None: 
            for i in api.get_positions(): checkPosition+=int(i['netqty']) ### Getting Live Positions Qty   
        if ((strikePrice['Signal'] != 'No Signal')):
            order = signalFunction.placeOrder(strikePrice['Signal'],'NFO', interval, api, strikePrice['Qty'])
            print(order)
            log("Main Script: order variable: ",order)
            log(f"Main Script: Signal Found {strikePrice}. Placed order. Order Status: {order['OrderStatus']}")
            signalFunction.telegramBot("Alligator Setup Signal: "+re.sub("{|}|'|_", "", str(strikePrice['Signal'])) + " Order Placed:"+re.sub("{|}|'|_", "", order['OrderStatus']))
            print(order)
            slCounter = 1800 
            api = loginFunction()
            pattern = re.compile('|'.join(map(str, [300, 600, 900, 1200, 1500, 1800, 2100, 2400, 2700])))
            sleep(5)
            orderNum = order['OrderNo']
            orderCheck = {'Status':api.single_order_history(orderno=order['OrderNo'])[0]['status']}
            while orderCheck['Status'] != 'COMPLETE':                           ### Checking if Placed Order is Completed
                try:
                   if pattern.search(str(slCounter)): api = loginFunction() 
                   latestStatus = (api.single_order_history(orderno=orderNum))[0]['status']
                   orderCheck ={'Status' : latestStatus}
                   print(orderCheck)
                   slCounter = slCounter-5
                   if orderCheck['Status'] != 'COMPLETE' : sleep(5)
                except Exception as f:
                    errorlog('Error while checking if Placed Order is Completed. '+str(f))
            api = loginFunction()
            try:
                placingOrder = api.place_order(buy_or_sell='S', product_type='I',   ### Placing SL Order
                               exchange=exchange, tradingsymbol=order['token'], 
                               quantity=order['qty'], discloseqty=0,price_type='SL-LMT', price=round(order['SlPrice']), trigger_price=(round(order['SlPrice'])+2),
                               retention='DAY', remarks='placed_By_Algo')

                ### Calling Trailing & Websocket Script
                orderNum = order['OrderNo']
                entryPrice = (api.single_order_history(orderno=orderNum))[0]['prc']
                argumentsVar = ['-sp', str(strikePrice['Signal']), '-sl', str(round(order['SlPrice'])), '-ep', str(entryPrice)]
                trailingScript = '/root/algo/trailingScript.py'
                targetScript = '/root/algo/websocketTarget.py'
                sleep(5)
                subprocess.Popen(['python', trailingScript] + argumentsVar, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
                sleep(5)
                log(f"Main Script: Trailing Script Called successfully.")
                signalFunction.telegramBot('Trailing Script Called successfully')
                break ### EXITING SCRIPT ONCE SL ORDER IS PLACED
            except Exception as g:
                errorlog('Main Script: Error while Triggering Trailing and Websocket Script'+str(g))
                print('Main Script: Error while searching for signal '+str(g))
                signalFunction.telegramBot('Main Script: Error while Triggering Trailing and Websocket Script')
        
        del strikePrice
        strikePrice = {'Signal':'No Signal'}
        print(datetime.now())
        sleep(round(((datetime.now() + timedelta(minutes=15 - ((datetime.now()).minute % 15))).replace(second=0, microsecond=0) - datetime.now()).total_seconds()) + 2)
        
    except Exception as e:
        print('Error while searching for signal and placing orders '+str(e))
        errorlog('Main Script: Error while searching for signal and placing orders '+str(e))
