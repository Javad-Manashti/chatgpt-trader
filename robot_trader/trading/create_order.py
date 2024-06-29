import logging
from oandapyV20 import API
from oandapyV20.endpoints.orders import OrderCreate
from oandapyV20.contrib.requests import MarketOrderRequest, TakeProfitDetails, StopLossDetails

def place_order(order_details):
    api = API(access_token=config['api_token'], environment="practice")
    instrument = "EUR_USD"
    
    mkt_order = MarketOrderRequest(
        instrument=instrument,
        units=-10000 if order_details['action'].upper() == 'SELL' else 10000,
        takeProfitOnFill=TakeProfitDetails(price=order_details['take_profit']).data,
        stopLossOnFill=StopLossDetails(price=order_details['stop_loss']).data
    )
    
    r = OrderCreate(accountID=config['account_id'], data=mkt_order.data)
    try:
        response = api.request(r)
        logging.info(f"Order placed successfully: {response}")
        return response
    except V20Error as e:
        logging.error(f"Error placing order: {e}")
        return {"error": str(e)}
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return {"error": str(e)}
