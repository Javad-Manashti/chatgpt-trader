import logging
from oandapyV20 import API
from oandapyV20.contrib.factories import InstrumentsCandlesFactory
import pandas as pd

def fetch_forex_data(from_date, to_date, granularity, instrument, api_token):
    logging.info(f"Fetching forex data from {from_date} to {to_date} with granularity {granularity} for instrument {instrument}")
    api = API(access_token=api_token, environment="practice")
    params = {
        "granularity": granularity,
        "from": from_date,
        "to": to_date
    }
    data = []
    try:
        for request in InstrumentsCandlesFactory(instrument=instrument, params=params):
            response = api.request(request)
            if response:
                for candle in response.get('candles'):
                    rec = {
                        'time': candle.get('time')[0:19],
                        'complete': candle['complete'],
                        'open': float(candle['mid']['o']),
                        'high': float(candle['mid']['h']),
                        'low': float(candle['mid']['l']),
                        'close': float(candle['mid']['c']),
                        'volume': candle['volume'],
                    }
                    data.append(rec)
    except Exception as e:
        logging.error(f"An error occurred fetching data: {e}")
    logging.info(f"Fetched data: {data}")
    return pd.DataFrame(data)
