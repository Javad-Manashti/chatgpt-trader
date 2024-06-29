import pandas as pd
import logging

def preprocess_data(data):
    logging.info(f"Data received for preprocessing: {data}")
    if isinstance(data, pd.DataFrame):
        processed_data = {
            'time': data['time'].tolist(),
            'open': data['open'].astype(float).tolist(),
            'high': data['high'].astype(float).tolist(),
            'low': data['low'].astype(float).tolist(),
            'close': data['close'].astype(float).tolist(),
            'volume': data['volume'].tolist()
        }
        return pd.DataFrame(processed_data)
    else:
        raise ValueError("Data format is not as expected.")
