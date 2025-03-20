import asyncio
import json
import ssl
import websockets
import requests
from google.protobuf.json_format import MessageToDict
import MarketDataFeedV3_pb2

class UpstoxWebsocketClient:
    def __init__(self, access_token):
        self.access_token = access_token
        self.websocket = None
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
    def get_websocket_url(self):
        """Get authorized WebSocket URL from Upstox API"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(
            "https://api.upstox.com/v3/feed/market-data-feed/authorize", 
            headers=headers
        )
        if response.status_code == 200:
            return response.json().get("authorized_redirect_uri")
        else:
            print(f"Error: {response.status_code}")
            print(response.json())
            return None
    
    @staticmethod
    def decode_protobuf(buffer):
        """Decode protobuf binary data to Python dictionary"""
        feed_response = MarketDataFeedV3_pb2.FeedResponse()
        feed_response.ParseFromString(buffer)
        return MessageToDict(feed_response, preserving_proto_field_name=True)
    
    async def subscribe(self, instrument_keys, mode="full"):
        """Subscribe to specified instruments"""
        if not self.websocket:
            print("WebSocket not connected. Call connect() first.")
            return False
            
        subscription = {
            "guid": "subscription-" + "-".join(instrument_keys),
            "method": "sub",
            "data": {"mode": mode, "instrumentKeys": instrument_keys}
        }
        
        try:
            await self.websocket.send(json.dumps(subscription))
            print(f"Subscribed to {instrument_keys} in {mode} mode")
            return True
        except Exception as e:
            print(f"Subscription error: {e}")
            return False
    
    async def unsubscribe(self, instrument_keys):
        """Unsubscribe from specified instruments"""
        if not self.websocket:
            return False
            
        unsubscription = {
            "guid": "unsubscription-" + "-".join(instrument_keys),
            "method": "unsub",
            "data": {"instrumentKeys": instrument_keys}
        }
        
        try:
            await self.websocket.send(json.dumps(unsubscription))
            print(f"Unsubscribed from {instrument_keys}")
            return True
        except Exception as e:
            print(f"Unsubscription error: {e}")
            return False
    
    async def connect(self):
        """Establish WebSocket connection"""
        ws_url = self.get_websocket_url()
        if not ws_url:
            print("Failed to get WebSocket URL")
            return False
            
        try:
            self.websocket = await websockets.connect(
                ws_url, 
                ssl=self.ssl_context,
                ping_interval=30,
                ping_timeout=10
            )
            print("Connected to Upstox WebSocket")
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    async def listen(self, callback=None):
        """Listen for incoming WebSocket messages"""
        if not self.websocket:
            print("WebSocket not connected")
            return
            
        try:
            while True:
                buffer = await self.websocket.recv()
                decoded_data = self.decode_protobuf(buffer)
                
                if callback:
                    # Call user-provided callback with decoded data
                    await callback(decoded_data)
                else:
                    # Default behavior: print formatted JSON
                    print(json.dumps(decoded_data, indent=2))
        except websockets.exceptions.ConnectionClosed as e:
            print(f"Connection closed: {e}")
        except Exception as e:
            print(f"Error in listen loop: {e}")
        finally:
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
    
    async def close(self):
        """Close the WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            print("WebSocket connection closed")

async def process_market_data(data):
    """Example callback function to process market data"""
    # Process different types of feed data
    feed_type = data.get('type')
    
    if feed_type == 'initial_feed':
        print("Received initial feed data")
    elif feed_type == 'live_feed':
        print("Received live feed update")
    elif feed_type == 'market_info':
        print("Received market info update")
    
    # Access specific data points if needed
    feeds = data.get('feeds', {})
    for instrument_key, feed_data in feeds.items():
        # Check which feed type we have
        if 'ltpc' in feed_data:
            ltp_data = feed_data['ltpc']
            print(f"{instrument_key} - LTP: {ltp_data.get('ltp')}, Change: {ltp_data.get('cp')}")
        elif 'fullFeed' in feed_data:
            # Handle full feed data
            full_feed = feed_data['fullFeed']
            if 'marketFF' in full_feed:
                market_data = full_feed['marketFF']
                # Process market full feed
                print(f"{instrument_key} - Market data received")
            elif 'indexFF' in full_feed:
                index_data = full_feed['indexFF']
                # Process index full feed
                print(f"{instrument_key} - Index data received")

async def main():
    # Replace with your actual access token
    access_token = "your_access_token_here"
    
    client = UpstoxWebsocketClient(access_token)
    
    # Connect to WebSocket
    connected = await client.connect()
    if not connected:
        print("Failed to connect to WebSocket")
        return
    
    # Subscribe to instruments
    instruments = ["NSE_INDEX|Nifty Bank", "NSE_INDEX|Nifty 50"]
    subscribed = await client.subscribe(instruments)
    
    if subscribed:
        # Start listening for updates with custom callback
        try:
            await client.listen(callback=process_market_data)
        except KeyboardInterrupt:
            print("Interrupted by user")
        finally:
            # Clean up
            await client.unsubscribe(instruments)
            await client.close()

if __name__ == "__main__":
    asyncio.run(main())