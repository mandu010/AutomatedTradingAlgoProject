# -*- coding: utf-8 -*-
"""
Created on Thu Jan 19 10:49:55 2023

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
import os.path as path
import time
import requests
import websocket

logs = "/root/algo/Logs"
logFileName = logs + '/Setup_1_' + datetime.today().strftime('%d_%m_%Y') + '.log'
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    level=logging.INFO, 
                    filename=logFileName, 
                    filemode='a',
                    datefmt='%Y-%m-%d %H:%M:%S')
def log(msg, *args):
    logging.info(msg, *args)
    #print(msg, *args)
def errorlog(msg1,*args):
    logging.error(msg1, *args)
    #print(msg1,*args)

def is_file_older_than_x_days(file, days=1): 
    if os.path.isfile(file):
        file_time = path.getmtime(file)
        # Check against 24 hours 
        return ((time.time() - file_time) / 3600 > 24*days)
    else:
        return True

def telegramBot(botmessage):
    bot_token = '' ## Telegram Bot Token goes here
    bot_chatID = '' ## Your telegram chat ID goes here
    send_text = 'https://api.telegram.org/bot'+ bot_token +'/sendMessage?chat_id=' + bot_chatID + '&parse_mode=MarkdownV2&text='+botmessage
    
    response = requests.get(send_text)
    return response.json()

def loginFunction():
    
    #### Variables
    algoDir = "/root/algo"
    credFile = "/root/algo/cred.yml"
    TOTP = ""
    logs = "/root/algo/Logs"
    logFileName = logs + '/Setup_1_' + datetime.today().strftime('%d_%m_%Y') + '.log'
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




def supertrend(exchange, token, days, interval, ATR, Multi, PP, api):#, userid, password, twoFA, vendor_code, api_secret, imei):
    try:
        # Getting Time Series Days
        df = sti = ema = result = results = last_candle_ST_signal = last_candle_closing = last_candle_high = last_candle_Alligator = None
        prev_day_timestamp = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days)).timestamp()
        print("Getting Data from SuperTrend Function at",datetime.now())        
        df = pd.DataFrame(api.get_time_price_series(exchange=exchange, token=token, starttime=prev_day_timestamp, interval=interval))  
        if df.empty:
            api = loginFunction()
            df = pd.DataFrame(api.get_time_price_series(exchange=exchange, token=token, starttime=prev_day_timestamp, interval=interval))
        df = df.sort_index(ascending=False)        
        df[['into','intl','intc','inth']] = df[['into','intl','intc','inth']].apply(pd.to_numeric)
        
            
        sti = ta.supertrend(df['inth'], df['intl'], df['intc'], length=ATR, multiplier=Multi)
        sti = sti.sort_index(ascending=True)
        ema = .05 * round((((df['inth'] + df['intl'])/2).rolling(window=25).mean().shift(periods=8))[0]/.05) ## This is more accurate
        last_candle_Alligator = ema = round(ema,2)
        last_candle_Alligator
        sti['super_trend'] = sti[['SUPERT_10_3.0']]
        result = pd.concat([df, sti], axis=1)
        results = result.sort_index(ascending=True).rename(columns={'SUPERTd_10_3.0': 'signal', 'SUPERTl_10_3.0': 'S_UPT','SUPERTs_10_3.0': 'S_DT'})
        results[['into','inth','intl','intc','SUPERT_10_3.0','signal']]=results[['into','inth','intl','intc','SUPERT_10_3.0','signal']].apply(pd.to_numeric)
        last_candle_ST_signal = results['signal'][0] ### Change this to get current candle or 1 candle previous
        last_candle_open = round(results['into'][0],2)
        last_candle_high = round(results['inth'][0],2)
        last_candle_low = round(results['intl'][0],2)
        last_candle_closing = round(results['intc'][0],2)
        openArr=[]
        arr2=[]
        result={'last_candle_open':last_candle_open,'last_candle_high':last_candle_high,'last_candle_low':last_candle_low,'last_candle_closing':last_candle_closing,
               'Alligator':last_candle_Alligator, 'ST Signal':last_candle_ST_signal,'Signal':''}
        if last_candle_ST_signal == -1: ### Sell Signal
            if ((last_candle_closing < last_candle_Alligator) and (last_candle_closing < last_candle_open)):
                for pivotPoint in PP.values():
                    if last_candle_open < pivotPoint:
                        openArr.append(pivotPoint)
                    if last_candle_closing < pivotPoint:
                        arr2.append(pivotPoint)
                if (len((set(openArr) ^ set(arr2))) != 0) and (last_candle_high-last_candle_low < 230) :
                    print("Found a difference")
                    buy = (100 * round(last_candle_low/100))+800
                    result['Signal'] = str(buy)+"_P" 
                    if last_candle_high-last_candle_low <= 65:
                        result['Qty'] = 25 ### Reduce Position Size
                    else:
                        result['Qty'] = 25
                    return result
                else:
                    result['Signal'] = "No Signal"
                    return result
                    #print("No Signal")
            else:
                result['Signal'] = "No Signal"
                return result
                #print("No Signal")
                
        else: #last_candle_ST_signal == 1: ### Buy Signal
            if ((last_candle_closing > last_candle_Alligator) and (last_candle_closing > last_candle_open)):
                for pivotPoint in PP.values():
                    if last_candle_open < pivotPoint:
                        openArr.append(pivotPoint)
                for pivotPoint in PP.values():
                    if last_candle_closing < pivotPoint:
                        arr2.append(pivotPoint)
                if (len((set(openArr) ^ set(arr2))) != 0) and (last_candle_high-last_candle_low < 250):
                    buy = (100 * round(last_candle_high/100))-800
                    result['Signal'] =  str(buy)+"_C"
                    if last_candle_high-last_candle_low <= 60:
                        result['Qty'] = 25 ### Reduce Position Size
                    else:
                        result['Qty'] = 25
                    return result
                else:
                    result['Signal'] = "No Signal"
                    return result
            else:
                result['Signal'] =  "No Signal"
                return result

                
        #return results[['time','into','inth','intl','intc','signal','EMA','SUPERT_10_3.0','S_UPT','S_DT']]        
    except Exception as e:
        var = f"Error in Signal Function: {e}"
        return var
    
def monthlyPivotSignal(exchange, token, days, interval, PP, api): #, userid, password, twoFA, vendor_code, api_secret, imei):
    try:
        # Getting Time Series Days
        #now = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).timestamp()
        api = loginFunction()
        df = sti = ema = result = results = last_candle_ST_signal = last_candle_closing = last_candle_high = last_candle_Alligator = None
        prev_day_timestamp = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days)).timestamp()
        df = pd.DataFrame(api.get_time_price_series(exchange=exchange, token=token, starttime=prev_day_timestamp, interval=interval))
        if df.empty:
            api = loginFunction()
            df = pd.DataFrame(api.get_time_price_series(exchange=exchange, token=token, starttime=prev_day_timestamp, interval=interval))
        df = df.sort_index(ascending=True)
        df[['into','intl','intc','inth']] = df[['into','intl','intc','inth']].apply(pd.to_numeric)
        last_candle_open = round(df['into'][0],2)
        last_candle_high = round(df['inth'][0],2)
        last_candle_low = round(df['intl'][0],2)
        last_candle_closing = round(df['intc'][0],2)
        openArr=[]
        arr2=[]
        result={'last_candle_open':last_candle_open,'last_candle_high':last_candle_high,'last_candle_low':last_candle_low,'last_candle_closing':last_candle_closing,'Signal':''}
        if (last_candle_closing < last_candle_open):
            for pivotPoint in PP.values():
                if last_candle_open < pivotPoint:
                    openArr.append(pivotPoint)
            for pivotPoint in PP.values():
                if last_candle_closing < pivotPoint:
                    arr2.append(pivotPoint)
            if (len((set(openArr) ^ set(arr2))) != 0) and (last_candle_high-last_candle_low < 250):
                print("Found a difference")
                buy = (100 * round(last_candle_low/100))+800                
                result['Signal'] =  str(buy)+"_P" 
                if last_candle_open-last_candle_closing <= 65:
                    result['Qty'] = 50
                else:
                    result['Qty'] = 25
                return result
                    #print(str(buy)+"_P")
            else:
                result['Signal'] =  "No Signal"
                return result                
        else:
            for pivotPoint in PP.values():
                if last_candle_open < pivotPoint:
                    openArr.append(pivotPoint)
            for pivotPoint in PP.values():
                if last_candle_closing < pivotPoint:
                    arr2.append(pivotPoint)
            if (len((set(openArr) ^ set(arr2))) != 0) and (last_candle_high-last_candle_low < 250):
                #print("Found a difference")
                buy = (100 * round(last_candle_high/100))-800
                result['Signal'] = str(buy)+"_C"
                if last_candle_closing-last_candle_open <= 65: ### If Candle Body is less than 50 pts then 
                    result['Qty'] = 50
                else:
                    result['Qty'] = 25
                return result
            else:
                result['Signal'] =  "No Signal"
                return result
    except Exception as e:
        var = f"Error in Signal Function: {e}"
        return var        
        
    

def placeOrder (strikePrice, exchange, interval, api, qty):
    try:
        api = loginFunction()
        token = api.searchscrip(exchange, strikePrice)['values'][0]
        print(f"Strike Price Found {token['dname']}")
        days = 3 if ((date.today().weekday()) == 0) else 1
        #days=1
        prev_day_timestamp = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days)).timestamp()
        df = pd.DataFrame(api.get_time_price_series(exchange=exchange, token=token['token'], starttime=prev_day_timestamp, interval=interval))
        if df.empty:
            api = loginFunction()
            df = pd.DataFrame(api.get_time_price_series(exchange=exchange, token=token, starttime=prev_day_timestamp, interval=interval))        
        df = df.sort_index(ascending=False)
        df[['into','intl','intc','inth']] = df[['into','intl','intc','inth']].apply(pd.to_numeric)
        last_candle_high = round(df['inth'][0]) ### Change this to get current candle or 1 candle previous
        last_candle_low = round(df['intl'][0])
        triggerPrice = last_candle_high
        limitPrice = last_candle_high + 2        
        placingOrder = api.place_order(buy_or_sell='B', product_type='I',
                        exchange=exchange, tradingsymbol=token['tsym'], 
                        quantity=qty, discloseqty=0,price_type='SL-LMT', price=limitPrice, trigger_price=triggerPrice,
                        retention='DAY', remarks='placed_By_Algo')
        orderHistory = api.single_order_history(orderno=placingOrder['norenordno'])
        finalOrderObj = {'OrderNo':placingOrder['norenordno'],'LimitPrice':limitPrice,'SlPrice':last_candle_low,'OrderStatus':orderHistory[-1]['status'],'token':token['tsym'],'qty':qty}
        return finalOrderObj
        #return orderHistory[0]['status']
    except Exception as e:
        var = f"Error in Placing Order Function: {e}"
        return var
    
def trailingData(strikePrice, exchange, interval, api):
    try:
        api = loginFunction()
        token = api.searchscrip(exchange, strikePrice)['values'][0]
        #print(f"Strike Price Found {token['dname']}")
        days = 3 if ((date.today().weekday()) == 0) else 1
        #days=1
        prev_day_timestamp = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days)).timestamp()
        df = pd.DataFrame(api.get_time_price_series(exchange=exchange, token=token['token'], starttime=prev_day_timestamp, interval=interval))
        if df.empty:
            api = loginFunction()
            df = pd.DataFrame(api.get_time_price_series(exchange=exchange, token=token, starttime=prev_day_timestamp, interval=interval))        
        df = df.sort_index(ascending=False)
        df[['into','intl','intc','inth']] = df[['into','intl','intc','inth']].apply(pd.to_numeric)
        #last_candle_high = round(df['inth'][0]) ### Change this to get current candle or 1 candle previous
        #last_candle_close = round(df['intc'][0])
        returnData = {'last_high':str(round(df['inth'][0])),'last_closing':str(round(df['intc'][0]))}
        print(f"Last Closing Price Data of {token['dname']} at",str(datetime.now().strftime("%d_%m_%Y_%H_%M")),str(returnData))
        return returnData
        
    except Exception as e:
        var = f"trailingData Function: Error in getting 15 Min Data: {e}"
        return var   
