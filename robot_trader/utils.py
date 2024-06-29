import json
import os
import matplotlib.pyplot as plt
import mplfinance as mpf
from PIL import Image
import logging
import csv
import pandas as pd
from datetime import datetime, timedelta  # Add timedelta import
import base64

def encode_image(image_path):
    with open(image_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def save_to_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def save_image(image_data, filename):
    with open(filename, 'wb') as f:
        f.write(image_data)

def plot_candlestick_chart(df, filename):
    df.index = pd.to_datetime(df['time'])
    df.index.name = 'Date'

    mc = mpf.make_marketcolors(up='green', down='red', wick={'up':'green', 'down':'red'}, edge={'up':'green', 'down':'red'})
    s = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=False)

    addplots = [
        mpf.make_addplot(df['low'].rolling(window=20).min(), color='blue', linestyle='dashed'),
        mpf.make_addplot(df['high'].rolling(window=20).max(), color='orange', linestyle='dashed'),
        mpf.make_addplot(calculate_rsi(df['close']), panel=1, color='purple', secondary_y=False),
    ]

    kwargs = dict(
        type='candle', 
        style=s, 
        addplot=addplots, 
        volume=True, 
        figscale=2.5, 
        figratio=(10, 8), 
        title='EUR_USD', 
        ylabel='Price', 
        ylabel_lower='Volume', 
        panel_ratios=(2, 1), 
        tight_layout=True, 
        fontscale=1.2, 
    )

    mpf.plot(df, **kwargs, savefig=dict(fname=filename, dpi=100, pad_inches=0.1))

def compress_image(input_path, output_path, quality=85):
    with Image.open(input_path) as img:
        img = img.convert('RGB')
        img = img.resize((510, 510), Image.LANCZOS)
        img.save(output_path, 'JPEG', quality=quality)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def append_to_csv(log_data, csv_file):
    file_exists = os.path.isfile(csv_file)
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=log_data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(log_data)

def calculate_rsi(data, length=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

import json

def save_prompt_to_txt(prompt_content, filename):
    with open(filename, 'w') as file:
        file.write(json.dumps(prompt_content, indent=4))



def is_weekend(date):
    return date.weekday() > 4

def get_last_weekday(date):
    while date.weekday() > 4:
        date -= timedelta(days=1)
    return date

def save_data_to_csv(data, filename):
    data.to_csv(filename, index=False)
