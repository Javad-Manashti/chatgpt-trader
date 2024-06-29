import logging
from oandapyV20 import API
from oandapyV20.endpoints.orders import OrderList, OrderReplace
from oandapyV20.endpoints.positions import OpenPositions
from oandapyV20.endpoints.pricing import PricingInfo
from oandapyV20.exceptions import V20Error

def get_open_positions(api, account_id):
    response = api.request(OpenPositions(accountID=account_id))
    positions = response.get('positions', [])
    return positions

def get_current_price(api, account_id, pair):
    params = {"instruments": pair}
    response = api.request(PricingInfo(accountID=account_id, params=params))
    return float(response['prices'][0]['closeoutBid'])

def get_orders(api, account_id):
    r = OrderList(accountID=account_id)
    try:
        response = api.request(r)
        return response.get('orders', [])
    except V20Error as e:
        logging.error(f"Failed to fetch orders: {e}")
        return []
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return []

def find_order_id(trade_id, orders):
    for order in orders:
        if 'tradeID' in order and order['tradeID'] == trade_id:
            return order['id']
    return None

def update_stop_loss(api, account_id, order_id, new_stop_loss):
    data = {
        "order": {
            "type": "STOP_LOSS",
            "price": str(new_stop_loss),
            "timeInForce": "GTC"
        }
    }
    try:
        r = OrderReplace(accountID=account_id, orderID=order_id, data=data)
        response = api.request(r)
        logging.info(f"Stop loss updated for order {order_id} to {new_stop_loss}")
        return response
    except V20Error as e:
        logging.error(f"Failed to update stop loss for order {order_id}: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None

def monitor_and_manage_orders(api, account_id, pair, trailing_stop_pips=10):
    open_positions = get_open_positions(api, account_id)
    if not open_positions:
        logging.info(f"No open positions for {pair}")
        return

    orders = get_orders(api, account_id)
    if not orders:
        logging.info(f"No orders found for account {account_id}")
        return

    for position in open_positions:
        if position['instrument'] != pair:
            continue

        logging.info(f"Inspecting position: {position}")

        if 'long' in position and position['long']['units'] != '0':
            units = position['long']['units']
            entry_price = float(position['long']['averagePrice'])
            stop_loss = float(position['long']['stopLossOrder']['price']) if 'stopLossOrder' in position['long'] else None
            trade_ids = position['long']['tradeIDs'] if 'tradeIDs' in position['long'] else None
        elif 'short' in position and position['short']['units'] != '0':
            units = position['short']['units']
            entry_price = float(position['short']['averagePrice'])
            stop_loss = float(position['short']['stopLossOrder']['price']) if 'stopLossOrder' in position['short'] else None
            trade_ids = position['short']['tradeIDs'] if 'tradeIDs' in position['short'] else None
        else:
            continue

        if not trade_ids:
            logging.warning(f"Trade IDs not found for position: {position}")
            continue

        trade_id = trade_ids[0]
        order_id = find_order_id(trade_id, orders)
        if not order_id:
            logging.warning(f"Order ID not found for trade ID: {trade_id}")
            continue

        current_price = get_current_price(api, account_id, pair)
        logging.info(f"Monitoring position: Entry Price: {entry_price}, Current Price: {current_price}, Units: {units}")

        if float(units) > 0:
            new_stop_loss = current_price - trailing_stop_pips * 0.0001
            if stop_loss is None or new_stop_loss > stop_loss:
                logging.info(f"Updating stop loss for long position to {new_stop_loss}")
                update_stop_loss(api, account_id, order_id, new_stop_loss)
        else:
            new_stop_loss = current_price + trailing_stop_pips * 0.0001
            if stop_loss is None or new_stop_loss < stop_loss:
                logging.info(f"Updating stop loss for short position to {new_stop_loss}")
                update_stop_loss(api, account_id, order_id, new_stop_loss)
