# import necessary modules or lib
import requests
import time
import datetime
import urllib
import dateutil.parser
import json
import websockets
import asyncio
import pyodbc
import nest_asyncio
import csv
from splinter import Browser


# personal info
accountId = '8888'
apiKey = "8888"
username = "8888"
password = 8888"


def timer():
     temp = datetime.datetime.fromtimestamp(time.time())
     time_str = temp.strftime("%Y-%m-%d %H:%M:%S\n")
     return time_str


def unix_time_millis(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    return (dt - epoch).total_seconds() * 1000


def write_info(content, file_name, arw):
    content = content
    file_name = file_name
    arw = arw
    f = open(file_name, arw)
    if file_name != 'access_token.txt':
        print(timer(), file=f)
    print(content, end='\n\n', file=f)
    f.close


def get_all_symbol():
    symbol_list = []
    with open('nasdaq_stocks.csv') as nasdaq_symbol:
        f_csv = csv.reader(nasdaq_symbol)
        for row in f_csv:
            symbol_list.append(row[0])
    nasdaq_symbol.close()
    keys_string = ''
    for i in symbol_list:
        keys_string = keys_string + ', ' + i
        keys_string = keys_string[1:]
    return keys_string


# Get refresh token from local file
def get_access_token():
    f = open('access_token.txt', 'r')
    token_dict = eval(f.readline())
    f.close()
    refreshToken = token_dict['refresh_token']
    # Get the latest access token (if it doesn't work, go to NOTE No.1)
    url_token = r"https://api.tdameritrade.com/v1/oauth2/token"
    headers_token = {'Content-Type': "application/x-www-form-urlencoded"}
    payload_token = {'grant_type': 'refresh_token',
                     'access_type': 'offline',
                     'refresh_token': refreshToken,
                     'client_id': apiKey,
                     }
    refreshReply = requests.post(url_token, headers=headers_token, data=payload_token)
    tokens = refreshReply.json()
    write_info(tokens, 'access_token.txt', 'w')
    write_info(tokens, 'token_record.txt', 'a')
    access_token = tokens['access_token']
    return access_token


def get_account_info():
    global accountId, header_1
    url_account = r'https://api.tdameritrade.com/v1/accounts/{}'.format(accountId)
    content_account = requests.get(url=url_account, headers=header_1)
    data_account = content_account.json()
    acct_time = timer()
    ff = open('log.txt', 'a+')
    print(acct_time, '\n', data_account, '\n\n', file=ff)
    print(acct_time, '\n', data_account, '\n\n', )
    ff.close
    time.sleep(1)
    return data_account



class WebSocketClient(object):

    def __init__(self):
        self.cnxn = None
        self.crsr = None
        self.count = 0

    def database_connect(self):
        server = 'USER-20190221FP\\SQLEXPRESS'
        database = 'stock_database'
        sql_driver = '{ODBC Driver 17 for SQL Server}'
        self.cnxn = pyodbc.connect(driver=sql_driver, server=server, database=database, trusted_connection='yes')
        self.crsr = self.cnxn.cursor()
        if self.count == 0:
            self.crsr.execute("TRUNCATE TABLE nasdaq_stocks")
        self.count += 1

    def database_execute(self, query, data=None):
        self.crsr.execute(query, data)
        self.cnxn.commit()

    async def connect(self):
        uri = 'wss://' + user_rsp['streamerInfo']['streamerSocketUrl'] + '/ws'
        self.connection = await websockets.client.connect(uri)
        if self.connection.open:
            print('Connection Established. Client Connectd.')
            return self.connection

    async def sendMsg(self, message):
        await self.connection.send(message)

    async def recvMsg(self, connection):
        while True:
            try:
                message = await connection.recv()
                message_decoded = json.loads(message)
                # print('Received Message From Server: ')
                # print('-'*54)
                # print(message_decoded)
                print('-'*54)
                query = 'INSERT INTO nasdaq_stocks (data_time, symbol, last_price, bid_size, ask_size, total_volume, \
                         last_trade_time, high_price, low_price, volatility, open_price, status, delayed) \
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);'
                if 'data' in message_decoded.keys():
                    self.database_connect()
                    data = message_decoded['data'][0]['content']
                    time_column = message_decoded['data'][0]['timestamp']
                    stocks_num = len(data)
                    data_key_list = ['key', '3', '4', '5', '8', '10', '12', '13', '24', '28', '48', 'delayed']
                    for num in range(stocks_num):
                        stock_value_list = [time_column]
                        for i in data_key_list:
                            if i in data[num].keys():
                                i_value = data[num][i]
                            else:
                                i_value = 0
                            stock_value_list.append(i_value)
                        if stock_value_list[2] != 0:
                            data_tuple = tuple(stock_value_list)
                            self.database_execute(query, data_tuple)
                    query_del = 'DELETE FROM nasdaq_stocks where (data_time > (SELECT MIN(data_time) FROM nasdaq_stocks) and data_time < ?)'
                    data_time = time_column - 600000
                    self.database_execute(query_del, data_time)
                    print(' %d Data Has Successfully Inserted Into the Database.' % stocks_num)
                    print('-'*54)
                    self.cnxn.close()       
            except websockets.exceptions.ConnectionClosed:
                print('Connection with server CLOSED in recvMsg method...')
                break

    async def heartBeat(self, connection):
        while True:
            try:
                await connection.send('ping')
                print('已发送ping...')
                await asyncio.sleep(20)
            except websockets.exceptions.ConnectionClosed as ErrorMsg:
                print('Connection with server CLOSED with no heartbeat...')
                print(ErrorMsg)
                break

    async def dataAnalysis(self):
        i = 1
        while True:
            self.database_connect()
            q = 1
            all_data = {}
            recom_time = timer()
            recom_record_list = [recom_time]
            table = self.crsr.execute('SELECT symbol, data_time, last_price FROM nasdaq_stocks').fetchall()
            symbols = self.crsr.execute('SELECT DISTINCT symbol FROM nasdaq_stocks')
            symbol_latest_list = []
            for row in symbols:
                symbol_latest_list.append(str.strip(row[0]))
            for symbol in symbol_latest_list:
                all_data[symbol] = []
            for row in table:
                all_data[str.strip(row[0])].append({row[1]: row[2]})
            for symbol, time_price in all_data.items():
                time_list = []
                price_list = []
                for tp_dict in time_price:
                    ts, = tp_dict
                    time_list.append(ts)
                time_list.sort(reverse=True)
                for i in time_list:
                    if i < (time_list[0] - 60000):
                        time_list = time_list[:time_list.index(i)]
                        break
                if len(time_list) > 1:
                    for ts in time_list:
                        for tp_dict in time_price:
                            if ts in tp_dict.keys():
                                price_list.append(tp_dict[ts])
                if price_list:
                    p = 0
                    for j in range(len(price_list)):
                        if price_list[0] < 0.98 * price_list[j]:
                            p += 1
                    if p > 0:
                        recom_record = 'Round【%d】 Recommandation【%d】: Buy %s at Price=%.4f' % (i, q, symbol, price_list[0])
                        print(recom_time, '\n', recom_record)
                        recom_record_list.append(recom_record)
                        q += 1
            i += 1
            write_info(recom_record_list, 'Recommandation.txt', 'a')
            self.cnxn.close() 
            await asyncio.sleep(20)
            
            
nest_asyncio.apply()
access_token = get_access_token()
header_1 = {'Authorization': 'Bearer {}'.format(access_token)}
header_2 = {'Authorization': 'Bearer {}'.format(access_token), 'Content-Type': 'application/json'}

# define User Principles endpoint
url = r'https://api.tdameritrade.com/v1/userprincipals'
# defin params
params = {'fields': 'streamerSubscriptionKeys,streamerConnectionInfo'}
# make a request
content = requests.get(url=url, params=params, headers=header_1)
user_rsp = content.json()
write_info(user_rsp, 'td_test.txt', 'a')

tokenTimeStamp = user_rsp['streamerInfo']['tokenTimestamp']
date = dateutil.parser.parse(tokenTimeStamp, ignoretz=True)
tokenMs = unix_time_millis(date)
symbols = get_all_symbol()

credentials = {'userid': user_rsp['accounts'][0]['accountId'], 
               'company': user_rsp['accounts'][0]['company'],
               'segment': user_rsp['accounts'][0]['segment'],
               'cddomain': user_rsp['accounts'][0]['accountCdDomainId'],
               'token': user_rsp['streamerInfo']['token'],
               'usergroup': user_rsp['streamerInfo']['userGroup'],
               'accesslevel': user_rsp['streamerInfo']['accessLevel'],
               'authorized': 'Y',
               'timestamp': int(tokenMs),
               'appid': user_rsp['streamerInfo']['appId'],
               'acl': user_rsp['streamerInfo']['acl']}

request_login = {"requests": [{"service": "ADMIN", 
                               "command": "LOGIN", 
                               "requestid": '0', 
                               "account": user_rsp['accounts'][0]['accountId'], 
                               "source": user_rsp['streamerInfo']['appId'], 
                               "parameters": {"credential": urllib.parse.urlencode(credentials),
                                              "token": user_rsp['streamerInfo']['token'],
                                              "version": "1.0"}}]}

request_data = {"requests": [{"service": "QUOTE",
                              "requestid": "2",
                              "command": "SUBS",
                              "account": user_rsp['accounts'][0]['accountId'],
                              "source": user_rsp['streamerInfo']['appId'],
                              "parameters": {"keys": symbols,
                                             "fields": "0,3,4,5,8,10,12,13,24,28,48"}}]}

login_encoded = json.dumps(request_login)
data_encoded = json.dumps(request_data) 
account = get_account_info()


# if __name__ == '__main__':
#     client = WebSocketClient()
#     loop = asyncio.get_event_loop()
#     connection = loop.run_until_complete(client.connect())
#     tasks = [asyncio.ensure_future(client.recvMsg(connection)),
#              asyncio.ensure_future(client.sendMsg(login_encoded)),
#              asyncio.ensure_future(client.recvMsg(connection)),
#              asyncio.ensure_future(client.sendMsg(data_encoded)),
#              asyncio.ensure_future(client.recvMsg(connection)),
#              asyncio.ensure_future(client.dataAnalysis())]
# loop.run_until_complete(asyncio.wait(tasks))


# header_1 = {'Authorization': 'Bearer {}'.format(access_token)}
# url_accounts = r'https://api.tdameritrade.com/v1/accounts'
# content_accounts = requests.get(url=url_accounts, headers=header_1)
# data_accounts = content_accounts.json()
# ff = open('log.txt', 'a+')
# print(data_accounts, end='\n\n',file=ff)
# ff.close
# account_id = data_accounts[0]['securitiesAccount']['accountId']
# print(account_id)

# url_account = r'https://api.tdameritrade.com/v1/accounts/{}'.format('686151151')
# content_account = requests.get(url=url_account, headers=header_1)
# data_account = content_account.json()
# ff = open('log.txt', 'a+')
# print(data_accounts, end='\n\n',file=ff)
# ff.close
# print(data_account)

# # The daily quotes
# url_quotes = r"https://api.tdameritrade.com/v1/marketdata/quotes"

# # Define payload
# payload_quotes = {'apikey': apiKey, 'symbol': ['RCON', 'GOOG', 'BA', 'AAPL']}

# # Make a request
# content_quotes = requests.get(url=url_quotes, params=payload_quotes)

# # Convert it to a adictionary
# data_quotes = content_quotes.json()
# print(data_quotes)
# ff = open('log.txt', 'a+')
# print(data_quotes, end='\n\n',file=ff)
# ff.close

# # The daily prices endpoint
# url_period_prices = r"https://api.tdameritrade.com/v1/marketdata/{}/pricehistory".format('GOOG')

# # Define payload
# payload_period_prices = {'apikey': apiKey,
#           'periodType': 'day',
#           'frequencyType': 'minute',
#           'frequency': 1,
#           'period': 1,
#           'needExtendedHoursData': 'true'}

# # Make a request
# content = requests.get(url = url_period_prices, params=payload_period_prices)

# # Convert it to a adictionary
# data_period_prices =  content.json()
# print(data_period_prices)
# f = open('access_token.txt', 'a+')
# print(data_period_prices, end='\n\n',file=f)
# f.close


# Place orders
# url_orders = r'https://api.tdameritrade.com/v1/accounts/{}/orders'.format(accountId)
# payload_orders = {'session': 'NORMAL', 
#                 'orderType': 'LIMIT', 
#                 'duration': 'DAY', 
#                 'orderStrategyType': 'SINGLE',
#                 'price': buy_price,                        
#                 'orderLegCollection': [{'instruction': 'BUY', 'quantity': 100, 'instrument': {'symbol': 'RCON', 'assetType': 'EQUITY'}}]}
# content_saved_orders = requests.post(url=url_saved_orders, json=payload_saved_orders, headers=header_2)
# print(content_saved_orders.status_code)

# content_query_orders = requests.get(url=url_saved_orders, headers=header_1)
# print(content_query_orders.status_code)
# data_orders = content_query_orders.json()
# print(data_orders)
# order_id = data_orders[0]['savedOrderId']
# print(order_id)

# =========================== NOTES ==========================

# Note No.1

# def get_new_access_token()
    # If local file doesn't exist or expired, execute the following codes:
    # set browser path and method
    # executable_path = {'executable_path': r'D:\\chromedriver\\chromedriver.exe'}
    # browser = Browser('chrome', **executable_path, headless=True)
    # ready to authentication
    # url_auth = 'https://auth.tdameritrade.com/auth?'
    # client_code = apiKey + '@AMER.OAUTHAP'
    # method = 'GET'
    # payload_auth = {'response_type': 'code', 'redirect_uri': 'http://127.0.0.1', 'client_id': client_code}
    # built_url = requests.Request(method, url_auth, params=payload_auth).prepare()
    # my_url = built_url.url
    # # operate the browser
    # browser.visit(my_url)
    # payload_fill = {'username': username, 'password': password}
    # browser.find_by_id('username').first.fill(payload_fill['username'])
    # browser.find_by_id('password').first.fill(payload_fill['password'])
    # browser.find_by_id('accept').first.click()
    # time.sleep(1)
    # browser.find_by_text('Can\'t get the text message?').first.click()
    # browser.find_by_value("Answer a security question").first.click()
    # if browser.is_text_present('What is your paternal grandfather\'s first name?'):
    #   browser.find_by_id('secretquestion').first.fill('youranswer')
    # elif browser.is_text_present('What was the first name of your first manager?'):
    #   browser.find_by_id('secretquestion').first.fill('youranswer')
    # elif browser.is_text_present('What was the name of your first pet?'):
    #   browser.find_by_id('secretquestion').first.fill('youranswer')
    # elif browser.is_text_present('What is your father\'s middle name?'):
    #   browser.find_by_id('secretquestion').first.fill('youranswer')
    # browser.find_by_id('accept').first.click()
    # time.sleep(1)
    # browser.find_by_id('accept').first.click()
    # time.sleep(1)
    # new_url = browser.url
    # parse_url = urllib.parse.unquote(new_url.split('code=')[1])
    # browser.quit()
    # print(parse_url)
    # get the token
    # url_token = r"https://api.tdameritrade.com/v1/oauth2/token"
    # headers_token = {'Content-Type': "application/x-www-form-urlencoded"}
    # payload_token = {'grant_type': 'authorization_code',
    #                'access_type': 'offline',
    #                'code': parse_url,
    #                'client_id': apiKey,
    #                'redirect_uri': 'http://127.0.0.1'}
    # temp = datetime.datetime.fromtimestamp(time.time())
    # time_str = temp.strftime("%Y-%m-%d %H:%M:%S\n")
    # authReply = requests.post(url_token, headers=headers_token, data=payload_token)
    # decoded_content = authReply.json()
    # f = open('access_token.txt', 'a+')
    # print(decoded_content, end='\n\n', file=f)
    # f.close
    # print(decoded_content)
    # access_token = decoded_content['access_token']
