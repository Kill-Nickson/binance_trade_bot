from multiprocessing import Value, Process

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from trading_bot import Bot


def bot_run_process(m_d, t_q):
    bot = Bot(ma_deviation=m_d, trade_quantity=t_q)
    bot.run()


def app_run_process(m_d, t_q):
    app = Flask(__name__)
    app.secret_key = 'my_secret_key'
    socket_io = SocketIO(app)

    @app.route('/')
    def draw():
        return render_template('main.html')

    @socket_io.on('updating_event')
    def update_orders_info(all_orders):
        if not all_orders:
            # Test orders list
            orders = [
                [12344321, "NEW", "0.1", "BUY", "BTCUSDT"],
                [12344322, "FILLED", "0.5", "SELL", "BTCUSDT"],
                [12344326, "FILLED", "0.3", "SELL", "BTCUSDT"],
                [12344329, "NEW", "0.1", "BUY", "BTCUSDT"],
            ]
        else:
            orders = [[order['orderId'],
                       order['status'],
                       order['price'],
                       order['side'],
                       order['symbol']] for order in all_orders]
        emit('update_orders_table', orders, broadcast=True)

    @socket_io.on('change_ma')
    def update_orders_info(new_deviation):
        try:
            with m_d.get_lock():
                m_d.value = float(new_deviation)
        except Exception:
            print('An error occurred while changing the bot\'s MA deviation!')

    @socket_io.on('change_volume')
    def update_orders_info(new_volume):
        try:
            with t_q.get_lock():
                t_q.value = float(new_volume)
        except Exception:
            print('An error occurred while changing the bot\'s trade_quantity!')

    socket_io.run(app, host='localhost', port=8000)


def main():
    ma_deviation = Value('f', 1)
    trade_quantity = Value('f', 0.001)

    Process(target=bot_run_process, args=(ma_deviation, trade_quantity)).start()
    Process(target=app_run_process, args=(ma_deviation, trade_quantity)).start()


if __name__ == '__main__':
    main()
