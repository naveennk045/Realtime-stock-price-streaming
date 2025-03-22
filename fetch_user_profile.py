import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

access_token = os.environ.get('UPSTOX_ACCESS_TOKEN')

if not access_token:
    raise ValueError("UPSTOX_ACCESS_TOKEN environment variable is not set")

url = 'https://api.upstox.com/v2/user/profile'
headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {access_token}'
}

response = requests.get(url, headers=headers)
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    
    # print(json.dumps(data, indent=4))
    
    user_data = data['data']
    print("\n===== USER PROFILE =====")
    print(f"User ID: {user_data['user_id']}")
    print(f"Name: {user_data['user_name']}")
    print(f"Email: {user_data['email']}")
    print(f"User Type: {user_data['user_type']}")
    print(f"Broker: {user_data['broker']}")
    print(f"Active Status: {'Active' if user_data['is_active'] else 'Inactive'}")
    
    print("\n----- Available Exchanges -----")
    for exchange in user_data['exchanges']:
        print(f"• {exchange}")
    
    print("\n----- Available Products -----")
    for product in user_data['products']:
        print(f"• {product}")
    
    print("\n----- Available Order Types -----")
    for order_type in user_data['order_types']:
        print(f"• {order_type}")
    
    print("\n----- Account Settings -----")
    print(f"POA: {'Enabled' if user_data['poa'] else 'Disabled'}")
    print(f"DDPI: {'Enabled' if user_data['ddpi'] else 'Disabled'}")
else:
    print(f"Error: {response.text}")