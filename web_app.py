from decimal import Decimal
from concurrent.futures import ProcessPoolExecutor

from flask import Flask, jsonify, render_template
from subprocess import call
from flask_socketio import SocketIO, send, emit

from trading_bot import Bot
from web_app import *

app = Flask(__name__)
app.secret_key = 'my_secret_key'
socket_io = SocketIO(app)

bot = Bot()


@app.route('/')
def draw():
    return render_template('main.html')


@socket_io.on('updating_event')
def update_orders_info(all_orders):
    if not all_orders:
        orders = [[order['orderId'],
                   order['status'],
                   order['price'],
                   order['side'],
                   order['symbol']] for order in all_orders]

        # Test orders list

        # orders = [
        #     [12344321, "NEW", "0.1", "BUY", "BTCUSDT"],
        #     [12344322, "FILLED", "0.5", "SELL", "BTCUSDT"],
        #     [12344326, "FILLED", "0.3", "SELL", "BTCUSDT"],
        #     [12344329, "NEW", "0.1", "BUY", "BTCUSDT"],
        # ]

        emit('update_orders_table', orders, broadcast=True)


@socket_io.on('change_ma')
def update_orders_info(new_deviation):
    global bot
    try:
        bot.ma_deviation = float(new_deviation)
    except Exception:
        print('An error occurred while changing the bot\'s MA deviation!')


@socket_io.on('change_volume')
def update_orders_info(new_volume):
    global bot
    try:
        bot.trade_quantity = Decimal(new_volume)
    except Exception:
        print('An error occurred while changing the bot\'s trade_quantity!')


def bot_run_process():
    bot.run()


def app_run_process():
    socket_io.run(app, host='localhost', port=8000)


def main():
    processes = [bot_run_process, app_run_process]

    with ProcessPoolExecutor() as executor:
        for p in processes:
            executor.submit(p)


if __name__ == '__main__':
    main()
