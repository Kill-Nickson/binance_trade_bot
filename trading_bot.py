import time
import json
from decimal import Decimal

import numpy
import websocket
import binance.client
from binance.enums import *
from socketIO_client import SocketIO, LoggingNamespace

import config


class Bot:
    def __init__(self):
        self.socket = "wss://stream.binance.com:9443/ws/btcusdt@kline_5m"
        self.ma_deviation = 1
        self.trade_symbol = 'BTCUSDT'
        self.trade_quantity = Decimal(str(0.001))
        self.in_position = False
        self.client = binance.client.Client(config.API_KEY, config.API_SECRET)

    def run(self):
        ws = websocket.WebSocketApp(self.socket, on_message=self.on_message)
        ws.run_forever()

    def on_message(self, ws, message):  # noqa

        json_message = json.loads(message)
        current_candle = json_message['k']
        is_candle_closed = current_candle['x']
        last_close = float(current_candle['c'])

        if is_candle_closed:
            self.on_candle_closure(last_close)

    def on_candle_closure(self, last_close):
        self.update_orders_info()

        bars = self.client.get_klines(symbol='BTCUSDT', interval='5m')
        nine_last_closes = [b[4] for b in bars[-8:]]
        nine_last_closes.append(last_close)

        nine_last_closes = [float(c) for c in nine_last_closes]
        ma = sum(nine_last_closes) / len(nine_last_closes)

        if last_close > (ma + self.ma_deviation):
            if self.in_position:
                # Binance sell logic
                order_succeeded = self.order(SIDE_SELL)
                if order_succeeded:
                    self.in_position = False

        elif last_close < (ma - self.ma_deviation):
            if not self.in_position:
                # Binance buy logic
                order_succeeded = self.order(SIDE_BUY)
                if order_succeeded:
                    self.in_position = True

    def order(self, side):
        try:
            self.client.create_order(symbol=self.trade_symbol, side=side,
                                     type=ORDER_TYPE_MARKET, quantity=self.trade_quantity)
        except Exception as e:
            print(f"An error occurred while sending order - {e}")
            return False
        return True

    def get_orders(self):
        all_orders = self.client.get_all_orders(symbol=self.trade_symbol)
        all_orders = [order for order in all_orders
                      if order['status'] == 'NEW' or
                      order['status'] == 'FILLED']
        return all_orders

    def update_orders_info(self):
        open_orders = self.client.get_open_orders()

        if open_orders:
            for open_order in open_orders:
                if float(open_order['price']) == ma:
                    self.client.cancel_order(orderId=open_order['orderId'])

        orders = self.get_orders()

        with SocketIO('localhost', 8000, LoggingNamespace) as socketIO:
            socketIO.emit('updating_event', orders)
