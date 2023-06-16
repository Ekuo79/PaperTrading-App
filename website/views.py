from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from . import db
from .models import User, Trade, Portfolio
import yfinance as yf
from datetime import datetime, timedelta
import locale
from sqlalchemy import desc

views = Blueprint('views', __name__)
locale.setlocale( locale.LC_ALL, 'en_US.utf8')
@views.route('/')
def menu():
    return render_template('menu.html')



search_information = [0,0]
trade_history = []
search_symbol = ""
search_price = ""

def calculatePositions(trades):
        all_positions = []
        for trade in trades:
            calculation = []
            adding = True

            if trade.orderType == "BUY":
                for index, each_position in enumerate(all_positions):
                    if trade.symbol in each_position:
                        adding = False
                        previous_quantity = int(all_positions[index][2])
                        all_positions[index][2] = int(all_positions[index][2]) + int(trade.quantity)
                        all_positions[index][3] += int(trade.quantity) * all_positions[index][1]
                        all_positions[index][4] =  ((int(trade.quantity) * float(trade.price)) + (float(all_positions[index][4]) * int(previous_quantity))) / (previous_quantity + int(trade.quantity))
                        all_positions[index][5] = all_positions[index][3] - (all_positions[index][4] * all_positions[index][2])

            if trade.orderType == "SELL":
                for index, each_position in enumerate(all_positions):
                    if trade.symbol in each_position:          
                        adding = False
                        previous_quantity = int(all_positions[index][2])
                        all_positions[index][2] = int(all_positions[index][2]) - int(trade.quantity)
                        all_positions[index][3] = all_positions[index][2] * all_positions[index][1]
                        all_positions[index][5] = all_positions[index][3] - (float(all_positions[index][4]) * int(all_positions[index][2]))

                        if all_positions[index][2] == 0:
                            all_positions.remove(all_positions[index])

            if adding:
                calculation.append(trade.symbol)
            
                stock = yf.Ticker(trade.symbol)
                price = stock.info.get('currentPrice')
                calculation.append(price)
            
                calculation.append(trade.quantity)

                marketValue = price * int(trade.quantity)
                calculation.append(marketValue)

                calculation.append(trade.price)
        
                #calculate gains/losses
                change = (float(price) * float(trade.quantity)) - (int(trade.quantity) * float(trade.price))
                calculation.append(change)

                all_positions.append(calculation)

        return all_positions

def calculate_trade_history(trades):
    all_trades = []
    for trade in trades:
        current_trade = []

        current_trade.append(trade.symbol)

        current_trade.append(trade.orderType)

        current_trade.append(trade.quantity)

        current_trade.append(trade.price)

        current_trade.append(trade.date)

        all_trades.append(current_trade)
    return all_trades

def calculateAccountValue(user, positions):
    marketValue = 0.0
    for position in positions:
        marketValue += float(position[3])

    last_portfolio = user.portfolios[len(user.portfolios) - 1]
    cash = float(last_portfolio.cash)
    accountValue = marketValue + cash

    return accountValue

def stockData(symbol, timeFrame, timeInterval):
    today = datetime.now().date()
    current_date = today
    weekday_to_exclude = [5, 6]  # Saturday = 5, Sunday = 6

    count = 0
    while count < timeFrame:
        current_date -= timedelta(days=1)
        if current_date.weekday() not in weekday_to_exclude:
            count += 1

    start_date = current_date + timedelta(days=1)
    end_date = today

    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    data = yf.download(symbol, start=start_date_str, end=end_date_str, interval=timeInterval)

    date_list = data.index.tolist()
    date_list_str = [dt.strftime('%Y-%m-%d %H:%M:%S') for dt in date_list]
    date_list_str.append(today.strftime('%Y-%m-%d %H:%M:%S'))

    close_list = data['Close'].tolist()
    search_stock = yf.Ticker(symbol)
    search_price = search_stock.info.get('currentPrice')
    close_list.append(search_price)

    all_information = []
    all_information.append(date_list_str)
    all_information.append(close_list)

    return all_information


@views.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    global search_information
    global trade_history
    userCurrent = current_user
    trades = userCurrent.trades
    print(search_information)
    
    cashCurrent = locale.currency(float(userCurrent.portfolios[len(userCurrent.portfolios) - 1].cash), grouping = True)
    def showTrades():
        for trade in trades:
            print(f"Trade ID: {trade.id}")
            print(f"Symbol: {trade.symbol}")
            print(f"Order Type: {trade.orderType}")
            print(f"Price: {trade.price}")
            print(f"Quantity: {trade.quantity}")
            print(f"Date: {trade.date}")
            print("----------")
    
    calculate_positions = calculatePositions(trades)
    trade_history = calculate_trade_history(trades)
    curAccountValue = calculateAccountValue(userCurrent, calculate_positions)

    accountValue = locale.currency(curAccountValue, grouping = True)
    
    
    if request.method == "POST":
        
        if 'search_button' in request.form:
            global search_symbol
            search_symbol = request.form.get('search_input').upper()
            try:
                global search_price
                search_stock = yf.Ticker(search_symbol)
                search_price = search_stock.info.get('currentPrice')
                search_information[0] = search_symbol
                if search_price != None:
                    search_information[1] = search_price
            except:
                search_price = "This stock symbol does not exists!"
                flash("This stock symbol literally does not exists!", category="error")
                return render_template("home.html", user=current_user, position_calculations=calculate_positions, searched=False, trade_history=trade_history, curAccountValue=accountValue, currentCash=cashCurrent)
            graph_info = stockData(search_symbol, 5, '15m')
            return render_template("home.html", user=current_user, position_calculations=calculate_positions, search_symbol=search_symbol, search_price=search_price, searched=True, currentCash=cashCurrent, trade_history=trade_history, curAccountValue=accountValue, date_list=graph_info[0], close_list=graph_info[1], title="5 Day Graph")
        
        elif 'fiveD_button' in request.form:
            graph_info = stockData(search_information[len(search_information)-2], 5, '15m')
            return render_template("home.html", user=current_user, position_calculations=calculate_positions, search_symbol=search_symbol, search_price=search_price, searched=True, currentCash=cashCurrent, trade_history=trade_history, curAccountValue=accountValue, date_list=graph_info[0], close_list=graph_info[1], title="5 Day Graph")

        elif 'oneM_button' in request.form:
            graph_info = stockData(search_information[len(search_information)-2], 26, '1h')
            return render_template("home.html", user=current_user, position_calculations=calculate_positions, search_symbol=search_symbol, search_price=search_price, searched=True, currentCash=cashCurrent, trade_history=trade_history, curAccountValue=accountValue, date_list=graph_info[0], close_list=graph_info[1], title="1 Month Graph")

        elif 'threeM_button' in request.form:
            graph_info = stockData(search_information[len(search_information)-2], 62, '1D')
            return render_template("home.html", user=current_user, position_calculations=calculate_positions, search_symbol=search_symbol, search_price=search_price, searched=True, currentCash=cashCurrent, trade_history=trade_history, curAccountValue=accountValue, date_list=graph_info[0], close_list=graph_info[1], title="3 Month Graph")

        elif 'oneY_button' in request.form:
            graph_info = stockData(search_information[len(search_information)-2], 261, '1D')
            return render_template("home.html", user=current_user, position_calculations=calculate_positions, search_symbol=search_symbol, search_price=search_price, searched=True, currentCash=cashCurrent, trade_history=trade_history, curAccountValue=accountValue, date_list=graph_info[0], close_list=graph_info[1], title="1 Year Graph")

        elif 'buy_button' in request.form:
            quantity = request.form.get('quantity_input')
            last_portfolio = userCurrent.portfolios[len(userCurrent.portfolios) - 1]
            cash = float(last_portfolio.cash)

            if not quantity.isdigit():
                flash('Quantity must be an integer (which is, a whole number in case u dropped out to be a day trader)!', category="error")
            elif int(quantity) * search_information[len(search_information)-1] > cash:
                flash('Don\'t got enough cash you brokie!', category='error')
            else:

                new_trade = Trade(symbol=search_information[len(search_information)-2], orderType="BUY", price=search_information[len(search_information)-1], quantity=quantity, user_id=userCurrent.id)
                db.session.add(new_trade)
                db.session.commit()

                #update trade history to be displayed
                current_trade = []
                current_trade.append(search_information[len(search_information)-2])
                current_trade.append("BUY")
                current_trade.append(quantity)
                current_trade.append(search_information[len(search_information)-1])
                current_trade.append(new_trade.date)
                trade_history.append(current_trade)

                #update user Portfolio
                cashUsed = float(quantity) * float(search_information[len(search_information)-1])
                last_portfolio = userCurrent.portfolios[len(userCurrent.portfolios) - 1]
                cash = float(last_portfolio.cash)
                cash = str(cash - cashUsed)
            
                trades = userCurrent.trades
                calculate_positions = calculatePositions(trades)
                valueSum = 0
                for i in range(len(calculate_positions)):
                    valueSum += calculate_positions[i][3]
                accountValue = str(float(cash) + valueSum)

                new_portfolio = Portfolio(cash=cash, account_value=accountValue, user_id=userCurrent.id)
                db.session.add(new_portfolio)
                db.session.commit()

               
                accountValue = locale.currency(float(accountValue), grouping = True)
                cash = locale.currency(float(cash), grouping = True)

                return render_template("home.html", user=current_user, position_calculations=calculate_positions, searched=False, trade_history=trade_history, curAccountValue=accountValue, currentCash=cash)
            

        elif 'sell_button' in request.form:
            quantity = request.form.get('quantity_input')
            if not quantity.isdigit():
                flash('Quantity must be an integer (which is, a whole number in case u dropped out to be a day trader)!', category="error")
                return render_template("home.html", user=current_user, position_calculations=calculate_positions, search_symbol=search_symbol, search_price=search_price, searched=False, currentCash=cashCurrent, trade_history=trade_history, curAccountValue=curAccountValue)
            for each_position in calculate_positions:
                if search_information[len(search_information)-2] in each_position:
                    if int(quantity) > int(each_position[2]):
                        flash('Trying to sell your imaginary shares???', category='error')
                    else:
                        new_trade = Trade(symbol=search_information[len(search_information)-2], orderType="SELL", price=search_information[len(search_information)-1], quantity=quantity, user_id=userCurrent.id)
                        db.session.add(new_trade)
                        db.session.commit()

                        #update trade history to be displayed
                        current_trade = []
                        current_trade.append(search_information[len(search_information)-2])
                        current_trade.append("SELL")
                        current_trade.append(quantity)
                        current_trade.append(search_information[len(search_information)-1])
                        current_trade.append(new_trade.date)
                        trade_history.append(current_trade)

                        #update user Portfolio
                        cashGained = float(quantity) * float(search_information[len(search_information)-1])
                        last_portfolio = userCurrent.portfolios[len(userCurrent.portfolios) - 1]
                        cash = float(last_portfolio.cash)
                        cash = str(cash + cashGained)

                        trades = userCurrent.trades
                        calculate_positions = calculatePositions(trades)
                        valueSum = 0
                        for i in range(len(calculate_positions)):
                            valueSum += calculate_positions[i][3]
                        accountValue = str(float(cash) + valueSum)
                        new_portfolio = Portfolio(cash=cash, account_value=accountValue, user_id=userCurrent.id)
                        db.session.add(new_portfolio)
                        db.session.commit()

                        accountValue = locale.currency(float(accountValue), grouping = True)
                        cash = locale.currency(float(cash), grouping = True)

                        return render_template("home.html", user=current_user, position_calculations=calculate_positions, searched=False, trade_history=trade_history, curAccountValue=accountValue, currentCash=cash)
                    
                else:
                    flash('Trying to sell your imaginary shares???', category='error')


    return render_template("home.html", user=current_user, position_calculations=calculate_positions, searched=False, trade_history=trade_history, curAccountValue=accountValue, currentCash=cashCurrent)


@views.route('/leaderboard', methods=['GET', 'POST'])
@login_required
def leaderboard():
    users = User.query.all()

    all_account_values = {}
    for user in users:
        positions = []
        trades = user.trades
        positions = calculatePositions(trades)
        accountValue = calculateAccountValue(user, positions)
        

        all_account_values[user.userName] = accountValue

    sorted_leaderboard = dict(sorted(all_account_values.items(), key=lambda item: item[1], reverse=True))
    
   
    for key in sorted_leaderboard:
        sorted_leaderboard[key] = locale.currency(sorted_leaderboard[key], grouping = True)


    return render_template("leaderboard.html", sorted_leaderboard=sorted_leaderboard, user=current_user)

