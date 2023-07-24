# -*- coding: utf-8 -*-
"""
Created on Tue Jan 31 10:20:22 2023

@author: mandl
"""

#login function to be called anywhere and returns api variable

from NorenRestApiPy.NorenApi import  NorenApi
import logging
import yaml
from yaml.loader import SafeLoader
import json

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
        log("Logging in Now")
        login = api.login(userid=user, password=pwd, twoFA=pyotp.TOTP(TOTP).now(), vendor_code=vc, api_secret=app_key, imei=imei)
        
        return api
