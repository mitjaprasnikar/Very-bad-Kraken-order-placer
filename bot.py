import time
import os
import requests
import urllib.parse
import hashlib
import hmac
import base64
import datetime
import json

# Read Kraken API key and secret stored in environment variables
api_url = "https://api.kraken.com"
api_key = "9XfvFgfv/tXAmckYH3eduS7NzeSSI1BGSaF74r2qziyDSKoqXqo33A77"
api_sec = "wLCf+3QfE7xPAhcGz+WG3LMkctwXDVngItuOOKsqAJQNhEfjp71tQoWdcpvfcFPs4RF+E0dpd6H5n2+sqzHwxA=="
last_set_limit_price = 0
current_price_eth=0
last_sell_price=299
last_buy_price=299


def get_kraken_signature(urlpath, data, secret):

    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()

    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()
    
def get_open_order_value():
    resp = kraken_request('/0/private/OpenOrders', {
    "nonce": str(int(1000*time.time())),
    "trades": True
    }, api_key, api_sec)
    data = resp.json()
    name=data["result"]["open"]
    if len(name) == 0:
        return 0
    else:
        
        for k in name:
            n1 = k
        return float(data["result"]["open"][n1]["descr"]["price"])


    




# Attaches auth headers and returns results of a POST request
def kraken_request(uri_path, data, api_key, api_sec):
    headers = {}
    headers['API-Key'] = api_key
    # get_kraken_signature() as defined in the 'Authentication' section
    headers['API-Sign'] = get_kraken_signature(uri_path, data, api_sec)             
    req = requests.post((api_url + uri_path), headers=headers, data=data)
    return req
    
    # Get Current ETH value on Kraken
def get_ETH_value():
    resp = kraken_request('/0/public/Ticker?pair=BCHEUR', {
    "nonce": str(int(1000*time.time()))
    }, api_key, api_sec)
    
    data = resp.json()
    
    
    value = float(data["result"]["BCHEUR"]["a"][0])
    
    return round(value,2)
    
def get_user_EUR_value():
    resp = kraken_request('/0/private/Balance?asset=ZEUR', {
    "nonce": str(int(1000*time.time()))
    }, api_key, api_sec)
    data = resp.json()
    
    value = float(data["result"]["ZEUR"])
    
    return round(value,2)
    
def get_user_ETH_value():
    resp = kraken_request('/0/private/Balance?asset=BCH', {
    "nonce": str(int(1000*time.time()))
    }, api_key, api_sec)
    data = resp.json()
    
    value = float(data["result"]["BCH"])
    
    return value

    
def place_order_to_buy_ETH(eth_price,volume):
    resp = kraken_request('/0/private/AddOrder', {
    "nonce": str(int(1000*time.time())),
    "ordertype": "stop-loss",
    "type": "buy",
    "volume": round(volume,5),
    "pair": "BCHEUR",
    "price": round(eth_price,2)
    }, api_key, api_sec)
    data = resp.json()
    #text = data["result"]["descr"]["order"]
    print("New limit to buy is set:",data)
   
def place_order_to_sell_ETH(eth_price,volume):
    resp = kraken_request('/0/private/AddOrder', {
    "nonce": str(int(1000*time.time())),
    "ordertype": "stop-loss",
    "type": "sell",
    "volume": volume,
    "pair": "BCHEUR",
    "price": round(eth_price,2)
    }, api_key, api_sec)
    data = resp.json()
    text = data["result"]["descr"]["order"]
    print("New limit to sell is set:",text)
       
    
def cancel_all_orders():
    resp = kraken_request('/0/private/CancelAll', {
    "nonce": str(int(1000*time.time()))
    }, api_key, api_sec)
    

    
starttime = time.time()
while True: 
    print("----------------------------------------")
    print("Time:",datetime.datetime.now())
    
    current_price_eth = get_ETH_value()
    last_set_limit_price = get_open_order_value()
    user_eur = get_user_EUR_value()
    
    print("Current price of BCH: ",current_price_eth)
    
    if user_eur > 30:
        print("User have: ",user_eur)
        if last_set_limit_price == 0:
            if last_sell_price > current_price_eth + (current_price_eth*0.02):
                new_limit = current_price_eth + (current_price_eth*0.02)
                print("Setting order to buy BCH - User have: ",user_eur)
                place_order_to_buy_ETH(new_limit,((user_eur-0.5)/new_limit))
            else:
                 print("Still not low enough",last_sell_price,current_price_eth + (current_price_eth*0.02))

        elif last_set_limit_price > current_price_eth + (current_price_eth*0.02):
            print("Setting new order to buy BCH - User have: ",user_eur)
            new_limit = current_price_eth + (current_price_eth*0.02)
            last_buy_price=new_limit
            cancel_all_orders()
            place_order_to_buy_ETH(new_limit,((user_eur-0.5)/new_limit))
        else:
            print("Still on last price ",last_set_limit_price,current_price_eth + (current_price_eth*0.02))
            
    else:
        
        if last_set_limit_price < current_price_eth -(current_price_eth*0.02) and current_price_eth -(current_price_eth*0.02) > last_buy_price:
            print("Settin new order to sell BCH - User have: ",get_user_ETH_value())
            new_limit = current_price_eth -(current_price_eth*0.02)
            last_sell_price=new_limit
            cancel_all_orders()
            place_order_to_sell_ETH(new_limit,get_user_ETH_value())
        else:
            print("Still on last price ",last_set_limit_price,current_price_eth -(current_price_eth*0.02))
    
    time.sleep(600)


