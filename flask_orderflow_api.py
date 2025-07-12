
from flask import Flask, jsonify
import requests

app = Flask(__name__)

def get_orderbook_mexc(symbol="BTCUSDT", depth=20):
    try:
        url = f"https://api.mexc.com/api/v3/depth?symbol={symbol}&limit=100"
        res = requests.get(url, timeout=10)
        data = res.json()
        bids = [[float(p), float(v)] for p, v in data["bids"]]
        asks = [[float(p), float(v)] for p, v in data["asks"]]
        return bids[:depth], asks[:depth]
    except Exception as e:
        return [], []

def get_orderbook_lbank(symbol="btc_usdt", depth=20):
    try:
        url = f"https://api.lbank.info/v1/depth.do?symbol={symbol}&size=100&type=step0"
        res = requests.get(url, timeout=10)
        data = res.json()
        bids = [[float(p), float(v)] for p, v in data["bids"]]
        asks = [[float(p), float(v)] for p, v in data["asks"]]
        return bids[:depth], asks[:depth]
    except Exception as e:
        return [], []

def extract_levels(bids, asks, top_n=5):
    supports = sorted(bids[10:], key=lambda x: x[1], reverse=True)[:top_n]
    resistances = sorted(asks[10:], key=lambda x: x[1], reverse=True)[:top_n]
    return supports, resistances

@app.route('/orderflow/<symbol>', methods=['GET'])
def get_orderflow(symbol):
    symbol_mexc = symbol.upper()
    symbol_lbank = symbol.lower().replace("usdt", "_usdt")

    mexc_bids, mexc_asks = get_orderbook_mexc(symbol_mexc)
    lbank_bids, lbank_asks = get_orderbook_lbank(symbol_lbank)

    mexc_supports, mexc_resistances = extract_levels(mexc_bids, mexc_asks)
    lbank_supports, lbank_resistances = extract_levels(lbank_bids, lbank_asks)

    data = {
        "symbol": symbol_mexc,
        "mexc": {
            "supports": [{"price": s[0], "volume": s[1]} for s in mexc_supports],
            "resistances": [{"price": r[0], "volume": r[1]} for r in mexc_resistances]
        },
        "lbank": {
            "supports": [{"price": s[0], "volume": s[1]} for s in lbank_supports],
            "resistances": [{"price": r[0], "volume": r[1]} for r in lbank_resistances]
        }
    }

    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
