import logging
import sys
import os
import time
from datetime import datetime, timezone, timedelta
import openai
from config import load_config
from data.fetch_data import fetch_forex_data
from trading.analyze_market import analyze_data_with_gpt4o, extract_and_place_order
from trading.create_order import place_order
from trading.manage_orders import monitor_and_manage_orders, get_open_positions, get_current_price, get_orders, update_stop_loss
from utils import save_to_json, plot_candlestick_chart, compress_image, encode_image, append_to_csv, save_prompt_to_txt, is_weekend, get_last_weekday
from data.preprocess_data import preprocess_data
import json
from oandapyV20 import API

def main():
    config = load_config()
    openai.api_key = config['openai_api_key']
    
    # Ensure the logs and images directories exist
    os.makedirs('logs', exist_ok=True)
    os.makedirs('images', exist_ok=True)
    
    logging.basicConfig(filename='logs/trader.log', level=logging.INFO)
    
    active_order = None
    csv_file = 'trade_logs.csv'
    api = API(access_token=config['api_token'], environment="practice")
    
    while True:
        now = datetime.now(timezone.utc)

        if is_weekend(now):
            logging.info("It's the weekend. Using last available weekday data.")
            now = get_last_weekday(now)

        start_time = (now - timedelta(days=3)).strftime('%Y-%m-%dT%H:%M:%SZ')
        end_time = now.strftime('%Y-%m-%dT%H:%M:%SZ')

        data = fetch_forex_data(start_time, end_time, config['granularity'], config['instrument'], config['api_token'])
        processed_data = preprocess_data(data)

        if 'time' not in processed_data.columns or 'close' not in processed_data.columns:
            logging.error("'time' or 'close' column is missing in processed data")
            return

        # Generate unique datetime ID
        datetime_id = now.strftime('%Y%m%d%H%M%S')
        filename = f"images/{datetime_id}.png"
        compressed_filename = f"images/{datetime_id}_compressed.jpg"

        # Plot and encode the image
        plot_candlestick_chart(processed_data, filename)  # Use color image
        compress_image(filename, compressed_filename, quality=85)  # Compress without grayscale
        image_base64 = encode_image(compressed_filename)

        price_data = {
            "start_date": start_time,
            "end_date": end_time,
            "close_prices": processed_data['close'].tolist()
        }

        # Analyze data and place orders based on predictions if no active order
        if not active_order:
            analysis_result, data_cost, image_cost, prompt_content = analyze_data_with_gpt4o(price_data, image_base64)
            logging.info(f"OpenAI API Analysis Result: {json.dumps(analysis_result, indent=4)}")

            if analysis_result:
                order_details = extract_and_place_order(api, analysis_result, config['account_id'], config['instrument'])
                if order_details:
                    logging.info("Order placed based on analysis.")
                    active_order = order_details

                    # Save logs to CSV
                    log_data = {
                        "date-time-id": datetime_id,
                        "date_time": now.strftime('%Y-%m-%d %H:%M:%S'),
                        "image_path": filename,
                        "response_prompt": json.dumps(analysis_result['choices'][0]['message']['content']),
                        "order_action": order_details['action'],
                        "entry_price": order_details['entry_price'],
                        "take_profit": order_details['take_profit'],
                        "stop_loss": order_details['stop_loss'],
                        "data_cost": data_cost,
                        "image_cost": image_cost,
                        "total_cost": data_cost + image_cost
                    }
                    append_to_csv(log_data, csv_file)

        # Order management if there is an active order
        if active_order:
            monitor_and_manage_orders(api, config['account_id'], config['instrument'])
            # Check if the order is closed
            open_positions = get_open_positions(api, config['account_id'])
            if not open_positions:
                logging.info(f"Order {active_order} is closed.")
                active_order = None

        logging.info("Waiting for 15 minutes before next run...")
        time.sleep(900)

if __name__ == "__main__":
    main()
