import asyncio
import json
import ssl
import websockets
import requests
from google.protobuf.json_format import MessageToDict
import MarketDataFeedV3_pb2

class UpstoxLiveDataClient:
    def __init__(self, access_token):
        self.access_token = access_token
        self.websocket = None
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
    def get_websocket_url(self):

        """Get authorized WebSocket URL from Upstox API"""
        clean_token = self.access_token.strip()
        
        headers = {
            "Accept": "application/json",
            "Api-Version": "3.0",
            "Authorization": f"Bearer {clean_token}"
        }
        
        print("Requesting WebSocket authorization...")
        response = requests.get(
            "https://api.upstox.com/v3/feed/market-data-feed/authorize", 
            headers=headers
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("Authentication successful")
            print("Full response:")
            response_data = response.json()
            print(json.dumps(response_data, indent=2))
            
            ws_url = (response_data.get("authorized_redirect_uri") or 
                    response_data.get("data", {}).get("authorized_redirect_uri") or
                    response_data.get("data", {}).get("websocket_url") or
                    response_data.get("websocket_url"))
            
            if ws_url:
                print(f"WebSocket URL found: {ws_url}")
                return ws_url
            else:
                print("WebSocket URL not found in response")
                return None
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
    
    async def listen_for_live_data(self):
        """Listen for and print only live data for subscribed instruments"""
        if not self.websocket:
            print("WebSocket not connected")
            return
            
        try:
            print("\n--- Waiting for live market data... ---\n")
            while True:
                buffer = await self.websocket.recv()
                decoded_data = self.decode_protobuf(buffer)
                
                # Print only live data
                self.print_live_data(decoded_data)
                
        except websockets.exceptions.ConnectionClosed as e:
            print(f"Connection closed: {e}")
        except Exception as e:
            print(f"Error in listen loop: {e}")
        finally:
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
    
    def print_live_data(self, data):
        """Extract and print only the relevant live data"""
        feed_type = data.get('type')
        
        if feed_type != 'live_feed': 
            return
            
        timestamp = data.get('currentTs', 0)
        human_time = self.format_timestamp(timestamp)
        
        print(f"\n[{human_time}] LIVE DATA UPDATE:")
        
        feeds = data.get('feeds', {})
        for instrument_key, feed_data in feeds.items():
            print(f"\n  {instrument_key}:")
            
            if 'ltpc' in feed_data:
                ltp_data = feed_data['ltpc']
                print(f"    LTP: {ltp_data.get('ltp', 'N/A')}")
                print(f"    Change: {ltp_data.get('cp', 'N/A')}")
                print(f"    Last Trade Qty: {ltp_data.get('ltq', 'N/A')}")
                print(f"    Last Trade Time: {self.format_timestamp(ltp_data.get('ltt', 0))}")
                
            elif 'fullFeed' in feed_data:
                full_feed = feed_data['fullFeed']
                
                if 'marketFF' in full_feed:
                    market_ff = full_feed['marketFF']
                    
                    if 'ltpc' in market_ff:
                        ltp_data = market_ff['ltpc']
                        print(f"    LTP: {ltp_data.get('ltp', 'N/A')}")
                        print(f"    Change: {ltp_data.get('cp', 'N/A')}")
                    
                    if 'marketLevel' in market_ff and 'bidAskQuote' in market_ff['marketLevel']:
                        quotes = market_ff['marketLevel']['bidAskQuote']
                        if quotes:
                            print("    Market Depth:")
                            for i, quote in enumerate(quotes[:5]):  # Print top 5 levels
                                print(f"      L{i+1}: Bid {quote.get('bidQ', 'N/A')}@{quote.get('bidP', 'N/A')} | "
                                      f"Ask {quote.get('askQ', 'N/A')}@{quote.get('askP', 'N/A')}")
                    
                    print(f"    Vol Traded Today: {market_ff.get('vtt', 'N/A')}")
                    print(f"    Open Interest: {market_ff.get('oi', 'N/A')}")
                    print(f"    Implied Volatility: {market_ff.get('iv', 'N/A')}")
                    print(f"    Avg Traded Price: {market_ff.get('atp', 'N/A')}")
                    
                elif 'indexFF' in full_feed:
                    index_ff = full_feed['indexFF']
                    if 'ltpc' in index_ff:
                        ltp_data = index_ff['ltpc']
                        print(f"    Index Value: {ltp_data.get('ltp', 'N/A')}")
                        print(f"    Change: {ltp_data.get('cp', 'N/A')}")
            
            elif 'firstLevelWithGreeks' in feed_data:
                first_level = feed_data['firstLevelWithGreeks']
                
                if 'ltpc' in first_level:
                    ltp_data = first_level['ltpc']
                    print(f"    LTP: {ltp_data.get('ltp', 'N/A')}")
                    print(f"    Change: {ltp_data.get('cp', 'N/A')}")
                
                if 'firstDepth' in first_level:
                    quote = first_level['firstDepth']
                    print(f"    Top of Book: Bid {quote.get('bidQ', 'N/A')}@{quote.get('bidP', 'N/A')} | "
                          f"Ask {quote.get('askQ', 'N/A')}@{quote.get('askP', 'N/A')}")
                
                if 'optionGreeks' in first_level:
                    greeks = first_level['optionGreeks']
                    print("    Option Greeks:")
                    print(f"      Delta: {greeks.get('delta', 'N/A')}")
                    print(f"      Theta: {greeks.get('theta', 'N/A')}")
                    print(f"      Gamma: {greeks.get('gamma', 'N/A')}")
                    print(f"      Vega: {greeks.get('vega', 'N/A')}")
                    print(f"      Rho: {greeks.get('rho', 'N/A')}")
    
    @staticmethod
    def format_timestamp(timestamp_ms):
        """Convert millisecond timestamp to human-readable format"""
        from datetime import datetime
        if not timestamp_ms:
            return "N/A"
        # Convert ms to seconds for datetime
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    async def close(self):
        """Close the WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            print("WebSocket connection closed")
async def main():

    access_token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIzTEMyTTMiLCJqdGkiOiI2N2RlODEyNTA2MzJkMzYzZGE4ODYzMjgiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaWF0IjoxNzQyNjM1MzAxLCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NDI2ODA4MDB9.XBdp-WhINWeZS3IGcg3KGqBF9e-DRtqivgdRPIRZAGE"
    
    client = UpstoxLiveDataClient(access_token)
    
    try:
        connected = await client.connect()
        if not connected:
            print("Failed to connect to WebSocket")
            return
        

        instruments = ["NSE_INDEX|Nifty Bank", "NSE_INDEX|Nifty 50", "NSE_EQ|RELIANCE"]
        await client.subscribe(instruments, mode="full")
        await client.listen_for_live_data()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())