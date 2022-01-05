import websocket, json
import talib
import numpy
from binance.enums import *
from binance.client import Client
import config
import datetime
from tkinter import *
import threading
import time


"""
A Tkinter crypto trading bot application

Colors used for messages and ui:
light blue - #c6d9e0
dark green - #54D157
red - #F22534
purple - #f2d7ff
"""

class Window(object):

    def __init__(self, root):
        super().__init__()
        self.root = root
        self.root.title("Crypto Bot")
        self.root.geometry('900x600')
        self.main_app_frame = Frame(root, bg="#d5a8ec")
        self.main_app_frame.grid(row=0, column=0, sticky="news", columnspan=2, ipadx = root.winfo_screenwidth(), ipady = root.winfo_screenheight())

        #for tracking buy, sell, and errors
        self.buy_count = 0
        self.sell_count = 0
        self.error_count = 0
    
        #stringVars
        self.symbol_strvar = StringVar()
        self.min_rsi_strvar = StringVar()
        self.max_rsi_strvar = StringVar()
        self.rsi_period_strvar = StringVar()
        self.trade_qty_strvar = StringVar()
        self.duration_strvar = StringVar()

        #for connection handling
        self.is_connection_closed = True
        self.is_connection_error = False
        self.retry_conn_btn = Button(self.main_app_frame, text="Retry Connection", command=self.retry_connecting)

        #initial entry field values
        self.RSI_PERIOD = 14
        self.RSI_OVERBOUGHT = 70
        self.RSI_OVERSOLD = 30
        self.SOCKET = 'wss://stream.binance.us:9443/ws/{}@kline_1m'.format("ethusd")
        self.TRADE_SYMBOL = 'ETHUSD'
        self.TRADE_QUANTITY = 0.02
        self.DURATION = 3600
        self.COUNTDOWN_SLEEP_TIME = 1
        self.closes = []
        self.in_position = False
        self.is_running = False

        #help page frame
        self.help_frame = Frame(root, bg = "#6e76c1")
        help_to_main_btn = Button(self.help_frame, text='Back',command=lambda:self.back_to_main(self.main_app_frame))
        help_to_main_btn.grid(row=0, column=0)
        about_label = Label(self.help_frame, text="Info:\n"+
        "\u2022 Values in fields are populated by default, but can be changed to match your preferences\n" +
        "\u2022 Make sure the trade symbol is correct and values are not negative\n" +
        "\u2022 In the 'order' function, changed 'create_test_order' to 'create_order' to execute real trades\n" +
        "\u2022 Buys, sells, and errors are counted and are reset once application is closed\n" +
        "\u2022 When RSIs are reset, it will take time to recalculate the current RSI\n" +
        "\u2022 Current state of the program will appear in the message box\n" +
        "\u2022 Buy and sell orders are logged to 'orders.txt' file\n" +
        "\u2022 Order errors are logged to 'order_errors.txt' file\n" +
        "\u2022 Connection or other errors are logged to 'conn_errors.txt' file\n", 
        font='Helvetica 12 bold', borderwidth=2, relief="solid", justify=LEFT, anchor='w')
        about_label.grid(row=1,column=1)


        #about page frame
        self.about_frame = Frame(self.root, bg = '#9EA097')
        #self.about_frame.grid(row=0, column=0, sticky="news")
        about_to_main_btn = Button(self.about_frame, text='Back',command=lambda:self.back_to_main(self.main_app_frame))
        about_to_main_btn.grid(row=0, column=0)
        about_label = Label(self.about_frame, text="A Tkinter crypto bot application made by TCbacon", bg = 'white')
        about_label.grid(row=1,column=1)

        #set up switching between frames
        for frame in (self.main_app_frame, self.about_frame, self.help_frame):
            frame.grid(row=0, column=0, sticky='news')

        #initially raise the main app frame
        self.main_app_frame.tkraise()

        #help button
        help_button = Button(self.main_app_frame, text="Help", command=lambda:self.show_help_frame(self.help_frame))
        help_button.grid(row=0, column=0)

        #about button
        about_button = Button(self.main_app_frame, text="About", command=lambda:self.show_about_frame(self.about_frame))
        about_button.grid(row=0, column=1) 

        title = Label(self.main_app_frame,text="Crypto Bot", font="Helvetica 15")
        title.grid(row=0, column=7)

        self.symbol_lbl = Label(self.main_app_frame,text="Symbol", font="Helvetica 15")
        self.symbol_lbl.grid(row=1, column=4)
  
        self.symbol_entry = Entry(self.main_app_frame, textvariable=self.symbol_strvar ,width=20)
        self.symbol_entry.grid(row=1, column=6, padx= 10)
        self.symbol_entry.insert(0, "ethusd")
   
        min_rsi_lbl = Label(self.main_app_frame,text="Min RSI", font="Helvetica 15")
        min_rsi_lbl.grid(row=2, column=4)

        self.min_rsi_entry = Entry(self.main_app_frame, width=20, textvariable=self.min_rsi_strvar)
        self.min_rsi_entry.grid(row=2, column=6, padx= 10)
        self.min_rsi_entry.insert(0, 30)

        max_rsi_lbl = Label(self.main_app_frame,text="Max RSI", font="Helvetica 15")
        max_rsi_lbl.grid(row=3, column=4)

        self.max_rsi_entry = Entry(self.main_app_frame, width=20, textvariable=self.max_rsi_strvar)
        self.max_rsi_entry.grid(row=3, column=6, padx= 10)
        self.max_rsi_entry.insert(0, 70)

        rsi_period_lbl = Label(self.main_app_frame,text="RSI Periods", font="Helvetica 15")
        rsi_period_lbl.grid(row=4, column=4)

        self.rsi_period_entry = Entry(self.main_app_frame, width=20, textvariable=self.rsi_period_strvar)
        self.rsi_period_entry.grid(row=4, column=6, padx= 10)
        self.rsi_period_entry.insert(0, 14)

        trade_qty_lbl = Label(self.main_app_frame,text="Trade Quantity", font="Helvetica 15")
        trade_qty_lbl.grid(row=5, column=4)

        self.trade_qty_entry = Entry(self.main_app_frame, width=20, textvariable=self.trade_qty_strvar)
        self.trade_qty_entry.grid(row=5, column=6, padx= 10)
        self.trade_qty_entry.insert(0, 0.02)
      
        self.duration_lbl = Label(self.main_app_frame,text="Duration (seconds)", font="Helvetica 15")
        self.duration_lbl.grid(row=6, column=4)

        self.duration_lbl_entry = Entry(self.main_app_frame, textvariable=self.duration_strvar, width=20)
        self.duration_lbl_entry.grid(row=6, column=6, padx= 10)
        self.duration_lbl_entry.insert(0, 3600)

        self.run_btn = Button(self.main_app_frame, text='Run', command=self.run_program, font="Helvetica 12", bg="#caff51", width=10)
        self.run_btn.grid(row=7, column=6)
        
        self.message_lbl =  Label(self.main_app_frame, text="Message", font="Helvetica 12")
        self.message_lbl.grid(row=10, column=4)

        self.message_entry =  Entry(self.main_app_frame, width=30, font="Helvetica 12")
        self.message_entry.grid(row=10, column=5, columnspan=3)

        self.ticker_lbl = Label(self.main_app_frame,text="Ticker: " + self.TRADE_SYMBOL, font= "Helvetica 15", fg="#a766e4")
        self.ticker_lbl.grid(row=1, column=8)

        self.price_lbl = Label(self.main_app_frame,text="Current Price", font= "Helvetica 15")
        self.price_lbl.grid(row=2, column=8)

        self.rsi_lbl = Label(self.main_app_frame,text="Current RSI", font= "Helvetica 15")
        self.rsi_lbl.grid(row=3, column=8)
        
        self.timer_lbl = Label(self.main_app_frame,text="Duration: 00:00:00", font= "Helvetica 15")
        self.timer_lbl.grid(row=4, column=8)

        self.buys_lbl = Label(self.main_app_frame, text="Buys: 0", font= "Helvetica 15", bg="#31ff78")
        self.buys_lbl.grid(row=5, column=8)

        self.sells_lbl = Label(self.main_app_frame, text="Sells: 0", font= "Helvetica 15", bg="#ffb130")
        self.sells_lbl.grid(row=6, column=8)

        self.error_count_lbl = Label(self.main_app_frame, text="Errors: 0", font= "Helvetica 15", bg="#ff7878")
        self.error_count_lbl.grid(row=7, column=8)

        self.reset_rsi_btn =  Button(self.main_app_frame,text="Reset RSIs", font= "Helvetica 10", bg="#f8885f", command=self.reset_rsi_list)
        self.reset_rsi_btn.grid(row=10, column=8)

        try:
            self.client = Client(config.API_KEY, config.API_SECRET, tld='us')
            self.set_message("API connection success!", "#54D157")
            self.is_connection_error = False
        except Exception as e:
            self.run_btn.config(state="disabled")
            self.retry_conn_btn.grid(row=8, column=6)
            self.is_connection_error = True
            self.set_message("Error occured, check internet connection...", "#ff7878")
    

    def show_help_frame(self, event):
        event.tkraise()

    def show_about_frame(self, event):
        event.tkraise()

    def back_to_main(self,event):
        event.tkraise()

    def retry_connecting(self):

        def run_retry():
            try:
                self.client = Client(config.API_KEY, config.API_SECRET, tld='us')
                self.run_btn.config(state="normal")
                self.retry_conn_btn.grid_forget()
                self.set_message("API connection success!", "#caff51")
            except Exception as e:
                print("retry failed cannot connect")
                self.set_message("Retry failed cannot connect")
                self.run_btn.config(state="disabled")
        
        retry_conn_thread = threading.Thread(target=run_retry)
        retry_conn_thread.start()
            

    def order(self, side, quantity, symb, order_type=ORDER_TYPE_MARKET,last_rsi=-1):
        cur_time = datetime.datetime.now()
        time_stamp = cur_time.strftime('%m/%d/%Y %H:%M:%S')

        try:
            #change 'create_test_order' to 'create_order' to execute real trades
            _order = self.client.create_test_order(
            symbol=symb,
            side=side,
            type=order_type,
            quantity=quantity)

            with open('orders.txt', 'a') as file:
                if side == SIDE_SELL:
                    file.write("SELL " + str(_order)  + " Current RSI: {cur_rsi} Time: {cur_time}\n".format(cur_rsi=last_rsi,cur_time=time_stamp))
                elif side == SIDE_BUY:
                    file.write("BUY " + str(_order)  +  " Current RSI: {cur_rsi} Time: {cur_time}\n".format(cur_rsi=last_rsi,cur_time=time_stamp))
        except Exception as e:
            print("ORDER FAILED!")
            self.error_count += 1
            self.error_count_lbl.config(text="Errors: "+str(self.error_count))
            with open('order_errors.txt', 'a') as file:
                file.write(str(e.args) + " Time: {}".format(time_stamp) +"\n")
            return False
        
        return True


    def on_open(self, ws):
        print("opened connection")
        self.price_lbl.config(text='Calculating...')
        self.rsi_lbl.config(text='Calculating...')
        timer_thread = threading.Thread(target=lambda:self.countdown(ws))
        timer_thread.start()

    def on_close(self, ws, status, message):
        print("closing connection...")
        self.run_btn.config(text='Run')
        self.is_running = False
        self.is_connection_closed = True
    
    def on_error(self, ws, exception):
        self.is_running = False
        self.run_btn.config(text='Run')
        cur_time = datetime.datetime.now()
        time_stamp = cur_time.strftime('%m/%d/%Y %H:%M:%S')
        self.set_message("Oops, an error occured. Check internet connection.", "#F22534")
        with open('conn_errors.txt', 'a') as file:
            file.write("An error occured. " + str(exception) + " Time: {}".format(time_stamp) + "\n")
        self.error_count += 1
        self.error_count_lbl.config(text="Errors: "+str(self.error_count))

    def on_message(self, ws, message):
        json_message = json.loads(message)
        candle = json_message['k']
        is_candle_closed = candle['x']
        close = candle['c']

        if is_candle_closed:
            print("candle closed at {}".format(close))
            self.closes.append(float(close))
            print(self.closes)
            self.price_lbl.config(text="Current Price: " + str(close))

            if len(self.closes) > self.RSI_PERIOD:
                np_closes = numpy.array(self.closes)
                rsi = talib.RSI(np_closes, self.RSI_PERIOD)
                print("all rsi calc so far")
                print(rsi)
                last_rsi = rsi[-1]
                print("cur rsi is {}".format(last_rsi))
                self.rsi_lbl.config(text='Current RSI: ' + str(last_rsi))

                if last_rsi > self.RSI_OVERBOUGHT:
                    if self.in_position:
                        order_succeded = self.order(SIDE_SELL, self.TRADE_QUANTITY, self.TRADE_SYMBOL, ORDER_TYPE_MARKET, last_rsi)
                        print("order sell success? ", order_succeded)
                        if order_succeded:
                            self.sell_count +=1
                            self.sells_lbl.config(text="Sells: " +str(self.sell_count))
                            self.in_position = False
                    else:
                        print("it is overbought, but you DONT OWN any")

                if last_rsi < self.RSI_OVERSOLD:
                    if self.in_position:
                        print("it is oversold but you ALREADY OWN it")
                    else:                        
                        order_succeded = self.order(SIDE_BUY, self.TRADE_QUANTITY, self.TRADE_SYMBOL, ORDER_TYPE_MARKET, last_rsi)
                        print("order buy success? ", order_succeded)
                        if order_succeded:
                            self.buy_count +=1
                            self.buys_lbl.config(text="Buys: " + str(self.buy_count))
                            self.in_position = True
    
    #reset rsi values for next run
    def reset_rsi_list(self):
        self.closes = []
        self.set_message("RSI List has been cleared", "#54D157")

    def ui_disable_enable_handler(self, _state):
        self.symbol_entry.config(state=_state)
        self.min_rsi_entry.config(state=_state)
        self.max_rsi_entry.config(state=_state)
        self.rsi_period_entry.config(state=_state)
        self.trade_qty_entry.config(state=_state)
        self.duration_lbl_entry.config(state=_state)
        self.reset_rsi_btn.config(state=_state)

    def run_program(self):
        try:
            trade_symbol = self.symbol_strvar.get().lower()
            self.SOCKET = 'wss://stream.binance.us:9443/ws/{}@kline_1m'.format(trade_symbol)
            self.ws = websocket.WebSocketApp(self.SOCKET, on_open=self.on_open, on_close=self.on_close, on_message=self.on_message, on_error=self.on_error)
            
            self.RSI_PERIOD = int(self.rsi_period_strvar.get())
            self.RSI_OVERBOUGHT = int(self.max_rsi_strvar.get())
            self.RSI_OVERSOLD = int(self.min_rsi_strvar.get())
            self.TRADE_SYMBOL = trade_symbol.upper()
            self.TRADE_QUANTITY = float(self.trade_qty_strvar.get())
            self.DURATION = int(self.duration_strvar.get())
 

            if self.RSI_PERIOD < 1 or \
            self.RSI_OVERSOLD < 1 or \
            self.RSI_OVERBOUGHT <= self.RSI_OVERSOLD or \
            self.TRADE_QUANTITY <= 0 or \
            self.DURATION < 1:
                self.set_message("Error, check field values")
                return

            def run():
                if not self.is_running:
                    self.is_running = True
                    self.is_connection_closed = False
                    self.run_btn.config(text='Stop')
                    self.set_message("Program Running...", "#54D157")
                    self.ui_disable_enable_handler('disabled')
                    self.ticker_lbl.config(text="Ticker: " + self.TRADE_SYMBOL)
                    self.ws.run_forever()
                else:
                    self.ui_disable_enable_handler('normal')
                    self.is_running = False
                    self.run_btn.config(text='Run')

            self.run_program_thread = threading.Thread(target=run)
            self.run_program_thread.start()
        except Exception as e:
            self.set_message("Error, make sure values are entered correctly.", "#F22534")
            print(e)
            
    def countdown(self, ws):
        msg = "Program Stopped..."

        if self.DURATION <= 0:
            msg = "Program Stopped... Input must be greater than 0 seconds"
            self.set_message(msg, "#F22534")
            return
        
        while self.DURATION:
            if not self.is_running:
                break

            secs = self.DURATION % 60
            mins = (self.DURATION // 60) % 60
            hrs = self.DURATION // 3600 

            timer = '{:02d}:{:02d}:{:02d}'.format(hrs, mins, secs)
            self.timer_lbl.config(text=timer)
            print(timer, end="\r")
            time.sleep(self.COUNTDOWN_SLEEP_TIME)
            self.DURATION -= 1

        self.run_btn.config(text='Run')
        self.is_running = False
        self.set_message(msg, "#ff7878")
        ws.close()


    def clear_messages(self):
        self.message_entry.delete(0, END)

    def set_message(self, msg):
        self.clear_messages()
        self.message_entry.insert(0, msg)

    def set_message(self, msg="messages appear here", _fg="#ff7878"):
        self.clear_messages()
        self.message_entry.config(fg=_fg)
        self.message_entry.insert(0, msg)
    
    #handle stuff when user clicks on X out button to close app
    def on_closing(self):
        if self.is_connection_closed:
            root.destroy()
        else:
            self.set_message("Stop program from running before closing...")
            
root = Tk()
win = Window(root)
root.protocol("WM_DELETE_WINDOW", win.on_closing)
root.mainloop()