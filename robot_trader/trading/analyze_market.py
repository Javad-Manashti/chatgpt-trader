import logging
import openai
import tiktoken
import json
import sys
import os
import requests
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import save_prompt_to_txt
from trading.create_order import place_order

def analyze_data_with_gpt4o(price_data, image_base64):
    logging.info("Sending data to OpenAI API for analysis")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai.api_key}"
    }

    prompt_content = {
        "content": (
            "Here is the EUR/USD close price data from {price_data['start_date']} to {price_data['end_date']} at a 15-minute interval. Analyze this data and the provided chart to calculate RSI, MACD, Bollinger Bands, and Fibonacci Retracement. Use these indicators, along with the chart, to perform a comprehensive analysis and identify potential trading opportunities. Assign a probability score from 0 to 100 and profit/loss rate for all patterns. Follow these steps:\n"
            "1. Analyze the chart visually and identify possible patterns without considering additional data.\n"
            "2. Using both the chart and calculated indicators, identify possible patterns.\n"
            "3. Analyze the data from the indicators independently and list all possible predictions.\n"
            "4. Combine the results from the three types of analysis (chart-only, chart with data, data-only) to form potential orders. Select the best order based on:\n"
            "   - Majority of detected patterns and predictions.\n"
            "   - Higher benefit-to-loss ratio.\n"
            "   - Predicted profit (minimum 20 to 50 pips).\n"
            "   - Deadline less than one day.\n"
            "5. Verify the selected order with the data and indicators to ensure accuracy.\n"
            "6. If multiple orders are found, only send back the order with the highest confidence and benefit/loss rate.\n"
            "Provide the analysis in JSON format:\n"
            "{\n"
            "   \"order\": {\n"
            "       \"timeframe\": \"15 minutes\",\n"
            "       \"pattern_name\": \"Pattern Name\",\n"
            "       \"confidence_percentage\": xx,\n"
            "       \"action\": \"Buy/Sell\",\n"
            "       \"entry_price\": x.xxxx,\n"
            "       \"take_profit\": x.xxxx,\n"
            "       \"stop_loss\": x.xxxx,\n"
            "       \"profit_loss_ratio\": x.x,\n"
            "       \"deadline_date\": \"yyyy-mm-ddThh:mm:ssZ\"\n"
            "   },\n"
            "   \"best_pattern\": {\n"
            "       \"timeframe\": \"15 minutes\",\n"
            "       \"pattern_name\": \"Pattern Name\",\n"
            "       \"confidence_percentage\": xx,\n"
            "       \"action\": \"Buy/Sell\",\n"
            "       \"entry_price\": x.xxxx,\n"
            "       \"take_profit\": x.xxxx,\n"
            "       \"stop_loss\": x.xxxx,\n"
            "       \"profit_loss_ratio\": x.x,\n"
            "       \"deadline_date\": \"yyyy-mm-ddThh:mm:ssZ\"\n"
            "   }\n"
            "}\n"
        ),
        "price_data": {
            "close_prices": price_data['close_prices']
        },
        "image": f"data:image/png;base64,{image_base64}"
    }

    enc = tiktoken.encoding_for_model("gpt-4o")
    num_tokens = len(enc.encode(json.dumps(prompt_content)))
    data_cost = num_tokens * 0.000005
    image_cost = 0.001275

    logging.info(f"Data tokens before adding image: {num_tokens}, Estimated Data Cost: ${data_cost:.6f}")

    save_prompt_to_txt(prompt_content, 'final_prompt.txt')

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": json.dumps(prompt_content)
            }
        ],
        "max_tokens": 3000
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    try:
        response_data = response.json()
        return response_data, data_cost, image_cost, prompt_content
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON response from OpenAI API")
        return None, data_cost, image_cost, prompt_content

def extract_and_place_order(api, analysis_result, account_id, instrument):
    if not analysis_result or "choices" not in analysis_result:
        logging.error("Invalid response data")
        return None

    content = analysis_result["choices"][0]["message"]["content"]
    start_index = content.find('{')
    end_index = content.rfind('}') + 1
    json_content = content[start_index:end_index]
    
    try:
        analysis = json.loads(json_content)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON content: {e}")
        return None
    
    orders = analysis.get("orders", [])
    best_pattern = analysis.get("best_pattern", {})
    
    for order in orders:
        if order.get("profit_loss_ratio", 0) > 2:
            logging.info(f"Order Details - Action: {order['action']}, Entry Price: {order['entry_price']}, Take Profit: {order['take_profit']}, Stop Loss: {order['stop_loss']}")
            
            order_details = {
                'action': order['action'],
                'entry_price': order['entry_price'],
                'take_profit': order['take_profit'],
                'stop_loss': order['stop_loss'],
                'deadline_date': order['deadline_date']
            }
            response = place_order(api, account_id, instrument, order_details)
            
            if 'orderCancelTransaction' in response:
                logging.info(f"Order {response['orderCancelTransaction']['orderID']} was canceled: {response['orderCancelTransaction']['reason']}")
            return order_details

    logging.info(f"Best Pattern Details - Action: {best_pattern.get('action', 'N/A')}, Entry Price: {best_pattern.get('entry_price', 'N/A')}, Take Profit: {best_pattern.get('take_profit', 'N/A')}, Stop Loss: {best_pattern.get('stop_loss', 'N/A')}")
    return best_pattern
