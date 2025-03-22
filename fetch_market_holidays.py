import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

access_token = os.environ.get('UPSTOX_ACCESS_TOKEN')

if not access_token:
    raise ValueError("UPSTOX_ACCESS_TOKEN environment variable is not set")

url = 'https://api.upstox.com/v2/market/holidays'

headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {access_token}'
}


response = requests.get(url, headers=headers)


if response.status_code == 200:
    data = response.json()

    if 'data' in data and isinstance(data['data'], list):
        print("\n📅 Market Holidays Retrieved Successfully!\n")
        print("{:<12} {:<25} {:<15}".format("Date", "Holiday Name", "Market Type"))
        print("=" * 55)

        for holiday in data['data']:
            date = holiday.get("date", "N/A")
            name = holiday.get("name", "N/A")
            market_type = holiday.get("segment", "N/A")
            
            print("{:<12} {:<25} {:<15}".format(date, name, market_type))

        print("\nTotal Holidays:", len(data['data']))
    
        # Save response to a file
        with open("market_holidays.json", "w") as file:
            json.dump(data, file, indent=2)
        
        print("\nMarket holiday details saved to 'market_holidays.json'")

    else:
        print("No holiday data found in response.")
    
else:
    print(f"Error: {response.status_code} - {response.text}")
