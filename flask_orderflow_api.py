
from flask import Flask, jsonify
import requests

app = Flask(__name__)

def get_orderbook_mexc(symbol="BTCUSDT"):
    try:
        url = f"https://api.mexc.com/api/v3/depth?symbol={symbol}&limit=100"
        res = requests.get(url, timeout=10)
        data = res.json()
        bids = [[float(p), float(v)] for p, v in data["bids"]]
        asks = [[float(p), float(v)] for p, v in data["asks"]]
        return bids, asks
    except Exception:
        return [], []

def get_orderbook_lbank(symbol="btc_usdt"):
    try:
        url = f"https://api.lbank.info/v1/depth.do?symbol={symbol}&size=100&type=step0"
        res = requests.get(url, timeout=10)
        data = res.json()
        bids = [[float(p), float(v)] for p, v in data["bids"]]
        asks = [[float(p), float(v)] for p, v in data["asks"]]
        return bids, asks
    except Exception:
        return [], []

def filter_heavy(orders, ratio=3.0, top_n=10):
    if not orders:
        return []
    volumes = [v for _, v in orders]
    avg = sum(volumes) / len(volumes)
    threshold = avg * ratio
    return sorted([(p, v) for p, v in orders if v >= threshold], key=lambda x: x[1], reverse=True)[:top_n]


@app.route('/orderflow/<symbol>', methods=['GET'])
def get_orderflow(symbol):
    symbol_mexc = symbol.upper()
    symbol_lbank = symbol.lower().replace("usdt", "_usdt")

    # MEXC
    mexc_bids, mexc_asks = get_orderbook_mexc(symbol_mexc)
    if not mexc_bids or not mexc_asks:
        return jsonify({"error": "No MEXC data"})
    mexc_price = (mexc_bids[0][0] + mexc_asks[0][0]) / 2
    mexc_supports = filter_heavy(mexc_bids, mexc_price)
    mexc_resistances = filter_heavy(mexc_asks, mexc_price)

    # LBank
    lbank_bids, lbank_asks = get_orderbook_lbank(symbol_lbank)
    lbank_supports, lbank_resistances = [], []
    if lbank_bids and lbank_asks:
        lbank_price = (lbank_bids[0][0] + lbank_asks[0][0]) / 2
        lbank_supports = filter_heavy(lbank_bids, lbank_price)
        lbank_resistances = filter_heavy(lbank_asks, lbank_price)

    return jsonify({
        "symbol": symbol_mexc,
        "mexc": {
            "supports": [{"price": p, "volume": v} for p, v in mexc_supports],
            "resistances": [{"price": p, "volume": v} for p, v in mexc_resistances],
        },
        "lbank": {
            "supports": [{"price": p, "volume": v} for p, v in lbank_supports],
            "resistances": [{"price": p, "volume": v} for p, v in lbank_resistances],
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
