import websocket, json
import talib
import numpy
from binance.enums import *
from binance.client import Client
import config
import datetime

"""
A trading bot used to make orders on binance.us
The bot was tested and works with buying and selling ethereum

This is only the code and not the tkinter app
"""
client = Client(config.API_KEY, config.API_SECRET, tld='us')

RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
TRADE_SYMBOL = 'ETHUSD'
TRADE_QUANTITY = 0.5
SOCKET = 'wss://stream.binance.us:9443/ws/ethusd@kline_1m'

closes = []
in_position = False


def order(side, quantity, symb, order_type=ORDER_TYPE_MARKET,last_rsi=-1):
    try:
        print("Sending order")
        #change 'create_test_order' to 'create_order' to create real orders
        _order = client.create_test_order(
        symbol=symb,
        side=side,
        type=order_type,
        quantity=quantity)

        cur_time = datetime.datetime.now()
        time_stamp = cur_time.strftime('%m/%d/%Y %H:%M:%S')

        #logs buy and sell orders to text file
        with open('orders.txt', 'a') as file:
            if side == SIDE_SELL:
                file.write("SELL " + str(_order)  + " Current RSI: {cur_rsi} Time: {cur_time}\n".format(cur_rsi=last_rsi,cur_time=time_stamp))
            elif side == SIDE_BUY:
                file.write("BUY " + str(_order)  +  " Current RSI: {cur_rsi} Time: {cur_time}\n".format(cur_rsi=last_rsi,cur_time=time_stamp))
    except Exception as e:
        print("Order failed!")
        print(e.args)
        #logs errors to text file
        with open('order_errors.txt', 'a') as file:
            file.write(str(e.args) + "\n")
        return False
    
    return True


def on_open(ws):
    print("opened connection")

def on_close(ws, status, message):
    print("closed connection")
def on_message(ws, message):
    global closes 
    global in_position

    json_message = json.loads(message)

    candle = json_message['k']
    is_candle_closed = candle['x']
    close = candle['c']

    if is_candle_closed:
        print("candle closed at {}".format(close))
        closes.append(float(close))
        print("closes")
        print(closes)

        if len(closes) > RSI_PERIOD:
            np_closes = numpy.array(closes)
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            print("All RSI calculated so far:")
            print(rsi)
            last_rsi = rsi[-1]
            print("Current RSI is {}".format(last_rsi))

            if last_rsi > RSI_OVERBOUGHT:
                if in_position:
                    print("Sell Order")
                    order_succeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL, ORDER_TYPE_MARKET, last_rsi)
                    if order_succeded:
                        in_position = False
                else:
                    print("Overbought, but you don't own any.")

            if last_rsi < RSI_OVERSOLD:
                if in_position:
                    print("Oversold but you already own it")
                else:
                    print("Buy Order")                    
                    order_succeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL, ORDER_TYPE_MARKET, last_rsi)
                    if order_succeded:
                        in_position = True


ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()