# Realtime Stock Price Streaming

A real-time stock market data streaming application using Upstox API with FastAPI backend.

## Prerequisites

- Python 3.10 or higher
- Upstox API credentials (API Key and Secret)
- Modern web browser

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/realtime-stock-price-streaming.git
cd realtime-stock-price-streaming
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Unix/macOS
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory:
```env
API_KEY="your_upstox_api_key"
API_SECRET="your_upstox_api_secret"
UPSTOX_ACCESS_TOKEN=""  # Will be populated automatically after authentication
```

## Project Structure

```
realtime-stock-price-streaming/
├── auth.py                     # Authentication backend
├── fetch_history.py            # Fetch historical data
├── fetch_market_holidays.py    # Fetch market holidays
├── fetch_profile.py            # Fetch user profile
├── market_streamer/
│   ├── __init__.py
│   ├── MarketDataFeedV3.proto  # Protobuf 
│   ├── websocket_client.py     # WebSocket client
│   └── MarketDataFeedV3_pb2.py # Generated protobuf code
├── templates/
│   ├── index.html             # Authentication page
│   └── dashboard.html         # Trading dashboard
├── .env                       # Environment variables
├── requirements.txt           # Python dependencies
└── README.md                 # Documentation
```

## Usage

1. Start the authentication server:
```bash
python auth.py
```

2. Navigate to `http://localhost:8000/authorize` in your web browser to get the authorization URL.

3. Use the authorization URL to log in to Upstox. If the login is successful, the token will be updated in the `.env` file automatically.

4. To start the market data streamer:
```bash
python -m market_streamer.websocket_client
```

5. To fetch profile, history, and market holidays, run the respective scripts:
```bash
python fetch_profile.py
python fetch_history.py
python fetch_market_holidays.py
```

## API Endpoints

### Authentication

- `GET /authorize` - Initiate Upstox OAuth flow
- `GET /exchange-token` - Handle OAuth callback
- `GET /token/{user_id}` - Retrieve stored token
- `GET /user-profile/{user_id}` - Get user profile

### Market Data

The WebSocket client connects to Upstox's market data feed and provides:
- Real-time LTPC (Last Traded Price and Quantity)
- Market depth (order book)
- OHLC data
- Index values
- Market status updates

## Market Data Structure

```python
{
  "type": "live_feed",
  "feeds": {
    "NSE_FO|45450": {
      "fullFeed": {
        "marketFF": {
          "ltpc": {
            "ltp": 213.75,
            "ltt": "1740727891235",
            "ltq": "150",
            "cp": 494.05
          },
          "marketLevel": {
            "bidAskQuote": [
              {
                "bidQ": "75",
                "bidP": 213.45,
                "askQ": "525",
                "askP": 213.9
              },
              {
                "bidQ": "225",
                "bidP": 213.3,
                "askQ": "150",
                "askP": 213.95
              },
              {
                "bidQ": "150",
                "bidP": 213.25,
                "askQ": "75",
                "askP": 214
              },
              {
                "bidQ": "150",
                "bidP": 213.2,
                "askQ": "225",
                "askP": 214.05
              },
              {
                "bidQ": "225",
                "bidP": 213.1,
                "askQ": "75",
                "askP": 214.1
              }
            ]
          },
          "optionGreeks": {
            "delta": 0.4952,
            "theta": -8.4067,
            "gamma": 0.0007,
            "vega": 16.769,
            "rho": 3.8673
          },
          "marketOHLC": {
            "ohlc": [
              {
                "interval": "1d",
                "open": 400,
                "high": 400,
                "low": 208.7,
                "close": 213.75,
                "vol": "779400",
                "ts": "1740681000000"
              },
              {
                "interval": "I1",
                "open": 210,
                "high": 212.8,
                "low": 208.7,
                "close": 212.15,
                "vol": "8475",
                "ts": "1740727800000"
              }
            ]
          },
          "atp": 272.9,
          "vtt": "779625",
          "oi": 210000,
          "iv": 0.131378173828125,
          "tbq": 46050,
          "tsq": 41850
        }
      }
    }
  },
  "currentTs": "1740727891739"
}
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `API_KEY` | Your Upstox API key |
| `API_SECRET` | Your Upstox API secret |
| `UPSTOX_ACCESS_TOKEN` | OAuth access token (auto-populated) |

## Security Features

- SSL/TLS encryption for WebSocket connections
- Token-based authentication
- Secure credential storage
- Cross-Origin Resource Sharing (CORS) protection

## Error Handling

The application includes comprehensive error handling for:
- Network connectivity issues
- Authentication failures
- WebSocket disconnections
- Market data parsing errors

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Upstox API team for their comprehensive market data feed
- FastAPI framework developers
- WebSocket protocol contributors

## Support

For support, please open an issue in the GitHub repository.

## Disclaimer

This software is for educational purposes only. Trading in financial markets carries risk. Make sure you understand these risks before using this software for real trading.

## Documentation

For more information on the Upstox API, please refer to the [Upstox API Documentation](https://upstox.com/developer/api-documentation/open-api/).