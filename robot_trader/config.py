import os
import logging
from dotenv import load_dotenv

def load_config():
    load_dotenv()
    config = {
        'api_token': os.getenv('OANDA_API_TOKEN'),
        'account_id': os.getenv('OANDA_ACCOUNT_ID'),
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'granularity': 'M15',
        'instrument': 'EUR_USD',
        'logging_level': logging.INFO,
    }
    return config
