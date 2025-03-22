import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

access_token = os.environ.get('UPSTOX_ACCESS_TOKEN')

if not access_token:
    raise ValueError("UPSTOX_ACCESS_TOKEN environment variable is not set")

# Format: EXCHANGE_SEGMENT|INSTRUMENT_ID
instrument_key = "NSE_EQ|INE848E01016" 
interval = "day"
to_date = "2023-11-19"  

from_date = "2023-11-12"
url = f"https://api.upstox.com/v2/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"

# Option 2: Get data up to a specific date (without specifying from_date)
# url = f"https://api.upstox.com/v2/historical-candle/{instrument_key}/{interval}/{to_date}"

headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {access_token}'  #
}

response = requests.get(url, headers=headers)

if response.status_code == 200:

    data = response.json()
    print("Daily Candle Data Retrieved Successfully!")
    print(f"Instrument: {instrument_key}")
    print(f"Time Period: {from_date} to {to_date}")
    
    if 'data' in data and 'candles' in data['data']:
        print(f"\nTotal Candles: {len(data['data']['candles'])}")
        print("\nSample Candle Data:")
        
        for i, candle in enumerate(data['data']['candles'][:3]):  # Show first 3 candles
            timestamp, open_price, high, low, close, volume, *extra = candle
            print(f"\nCandle {i+1}:")
            print(f"  Date: {timestamp}")
            print(f"  Open: {open_price}")
            print(f"  High: {high}")
            print(f"  Low: {low}")
            print(f"  Close: {close}")
            print(f"  Volume: {volume}")
    else:
        print("No candle data found in the response")
        print(json.dumps(data, indent=2))
else:
    print(f"Error: {response.status_code} - {response.text}")