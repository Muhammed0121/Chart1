#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quotex Pro Trader — FINAL STABLE VERSION
✅ Smart Adaptive Zoom (TradingView-like)
✅ WebSocket Keep-Alive (No More Sleep)
✅ Auto-Restart Realtime Stream on Idle
✅ Realtime Heartbeat Every 45s
✅ TradingView-like Countdown Overlay
✅ Mouse-Centered Zoom (No Wheel Conflict)
✅ Event-Based Interaction Detection
✅ Accurate Countdown + Full Redraw Safety
✅ Starts on AUD/CAD (OTC)
✅ Candle Colors: #00C510 / #ff0000
"""
import asyncio
import threading
import time
import re
import json
import os
import sys
import eel
import traceback
from queue import Queue

try:
    from pyquotex.stable_api import Quotex
except ImportError:
    print("\n❌ Error: pyquotex not installed\nRun: pip install pyquotex\n")
    sys.exit(1)

# ======================
# Async Loop Manager
# ======================
ASYNC_LOOP = asyncio.new_event_loop()
def start_async_loop():
    asyncio.set_event_loop(ASYNC_LOOP)
    ASYNC_LOOP.run_forever()
threading.Thread(target=start_async_loop, daemon=True, name="AsyncLoop").start()
print("🌀 Async event loop started in background thread")

# ======================
# UI Update Queue (Thread-Safe + Flood Protection)
# ======================
UI_QUEUE = Queue()

def ui_loop():
    while True:
        try:
            payload = UI_QUEUE.get()
            if payload is None:
                break
            eel.updateChart(payload)()
            UI_QUEUE.task_done()
        except Exception as e:
            print(f"[UI Loop Error]: {e}")

threading.Thread(target=ui_loop, daemon=True, name="UIUpdater").start()
print("✅ UI update thread started (thread-safe)")

# ======================
# Global State
# ======================
LAST_TICK_TIME = time.time()
ASSET_DISPLAY_MAP = {}
forex_assets = {
    "AUDCAD": "AUD/CAD", "AUDCAD_otc": "AUD/CAD (OTC)", "AUDCHF": "AUD/CHF", "AUDCHF_otc": "AUD/CHF (OTC)",
    "AUDJPY": "AUD/JPY", "AUDJPY_otc": "AUD/JPY (OTC)", "AUDNZD_otc": "AUD/NZD (OTC)", "AUDUSD": "AUD/USD",
    "AUDUSD_otc": "AUD/USD (OTC)", "CADJPY": "CAD/JPY", "CADJPY_otc": "CAD/JPY (OTC)", "CADCHF_otc": "CAD/CHF (OTC)",
    "CHFJPY": "CHF/JPY", "CHFJPY_otc": "CHF/JPY (OTC)", "EURAUD": "EUR/AUD", "EURAUD_otc": "EUR/AUD (OTC)",
    "EURCAD": "EUR/CAD", "EURCAD_otc": "EUR/CAD (OTC)", "EURCHF": "EUR/CHF", "EURCHF_otc": "EUR/CHF (OTC)",
    "EURGBP": "EUR/GBP", "EURGBP_otc": "EUR/GBP (OTC)", "EURJPY": "EUR/JPY", "EURJPY_otc": "EUR/JPY (OTC)",
    "EURNZD_otc": "EUR/NZD (OTC)", "EURSGD_otc": "EUR/SGD (OTC)", "EURUSD": "EUR/USD", "EURUSD_otc": "EUR/USD (OTC)",
    "GBPAUD": "GBP/AUD", "GBPAUD_otc": "GBP/AUD (OTC)", "GBPCAD": "GBP/CAD", "GBPCad_otc": "GBP/CAD (OTC)",
    "GBPCHF": "GBP/CHF", "GBPCHF_otc": "GBP/CHF (OTC)", "GBPJPY": "GBP/JPY", "GBPJPY_otc": "GBP/JPY (OTC)",
    "GBPNZD_otc": "GBP/NZD (OTC)", "GBPUSD": "GBP/USD", "GBPUSD_otc": "GBP/USD (OTC)", "NZDCAD_otc": "NZD/CAD (OTC)",
    "NZDCHF_otc": "NZD/CHF (OTC)", "NZDJPY_otc": "NZD/JPY (OTC)", "NZDUSD_otc": "NZD/USD (OTC)", "USDCAD": "USD/CAD",
    "USDCAD_otc": "USD/CAD (OTC)", "USDCHF": "USD/CHF", "USDCHF_otc": "USD/CHF (OTC)", "USDJPY": "USD/JPY",
    "USDJPY_otc": "USD/JPY (OTC)", "USDARS_otc": "USD/ARS (OTC)", "USDBDT_otc": "USD/BDT (OTC)", "USDCOP_otc": "USD/COP (OTC)",
    "USDDZD_otc": "USD/DZD (OTC)", "USDEGP_otc": "USD/EGP (OTC)", "USDIDR_otc": "USD/IDR (OTC)", "USDINR_otc": "USD/INR (OTC)",
    "USDMXN_otc": "USD/MXN (OTC)", "USDNGN_otc": "USD/NGN (OTC)", "USDPHP_otc": "USD/PHP (OTC)", "USDPKR_otc": "USD/PKR (OTC)",
    "USDTRY_otc": "USD/TRY (OTC)", "USDZAR_otc": "USD/ZAR (OTC)",
}
ASSET_DISPLAY_MAP.update(forex_assets)
crypto_assets = {
    "ADAUSD_otc": "Cardano (OTC)", "APTUSD_otc": "Aptos (OTC)", "ARBUSD_otc": "Arbitrum (OTC)", "ATOUSD_otc": "ATO (OTC)",
    "AVAUSD_otc": "Avalanche (OTC)", "AXSUSD_otc": "Axie Infinity (OTC)", "BCHUSD_otc": "Bitcoin Cash (OTC)",
    "BNBUSD_otc": "Binance Coin (OTC)", "BONUSD_otc": "Bonk (OTC)", "BTCUSD_otc": "Bitcoin (OTC)", "DASUSD_otc": "Dash (OTC)",
    "DOGUSD_otc": "Dogecoin (OTC)", "DOTUSD_otc": "Polkadot (OTC)", "ETCUSD_otc": "Ethereum Classic (OTC)",
    "ETHUSD_otc": "Ethereum (OTC)", "FLOUSD_otc": "Floki (OTC)", "GALUSD_otc": "Gala (OTC)", "HMSUSD_otc": "Hamster Kombat (OTC)",
    "LINUSD_otc": "Chainlink (OTC)", "LTCUSD_otc": "Litecoin (OTC)", "MELUSD_otc": "Melania Meme (OTC)",
    "SHIBUSD_otc": "Shiba Inu (OTC)", "SOLUSD_otc": "Solana (OTC)", "TIAUSD_otc": "Celestia (OTC)", "TONUSD_otc": "Toncoin (OTC)",
    "TRUUSD_otc": "TrueFi (OTC)", "TRXUSD_otc": "TRON (OTC)", "WIFUSD_otc": "Dogwifhat (OTC)", "XRPUSD_otc": "Ripple (OTC)",
    "ZECUSD_otc": "Zcash (OTC)",
}
ASSET_DISPLAY_MAP.update(crypto_assets)
commodities_assets = {
    "XAUUSD": "Gold", "XAUUSD_otc": "Gold (OTC)", "XAGUSD": "Silver", "XAGUSD_otc": "Silver (OTC)",
    "UKBrent_otc": "UK Brent (OTC)", "USCrude_otc": "US Crude (OTC)",
}
ASSET_DISPLAY_MAP.update(commodities_assets)
stocks_assets = {
    "AXP_otc": "American Express (OTC)", "BA_otc": "Boeing Company (OTC)", "FB_otc": "Facebook (OTC)",
    "INTC_otc": "Intel (OTC)", "JNJ_otc": "Johnson & Johnson (OTC)", "MCD_otc": "McDonald's (OTC)",
    "MSFT_otc": "Microsoft (OTC)", "PFE_otc": "Pfizer Inc (OTC)", "PEPUSD_otc": "PepsiCo (OTC)",
}
ASSET_DISPLAY_MAP.update(stocks_assets)
indices_assets = {
    "DJIUSD": "Dow Jones", "NDXUSD": "NASDAQ 100", "F40EUR": "CAC 40", "FTSGBP": "FTSE 100",
    "HSIHKD": "Hong Kong 50", "IBXEUR": "IBEX 35", "JPXJPY": "Nikkei 225", "CHIA50": "China A50",
    "STXEUR": "EURO STOXX 50",
}
ASSET_DISPLAY_MAP.update(indices_assets)
DISPLAY_TO_INTERNAL = {v: k for k, v in ASSET_DISPLAY_MAP.items()}
ASSET_CATEGORIES = {
    "💱 Forex": list(forex_assets.values()),
    "₿ Crypto": list(crypto_assets.values()),
    "🛢️ Commodities": list(commodities_assets.values()),
    "🏦 Stocks": list(stocks_assets.values()),
    "📊 Indices": list(indices_assets.values()),
}
TIMEFRAMES = {
    "5s": 5, "10s": 10, "15s": 15, "30s": 30,
    "1m": 60, "2m": 120, "3m": 180, "5m": 300,
    "10m": 600, "15m": 900, "30m": 1800,
    "1h": 3600, "4h": 14400
}
CLIENT = None
CURRENT_ASSET = "AUD/CAD (OTC)"
CURRENT_TIMEFRAME = "1m"
CANDLES = {}
CURRENT_CANDLE = {}
SERVER_TIME_OFFSET = 0
CANDLE_COLORS = {
    "upColor": "#00C510",
    "downColor": "#ff0000",
    "borderUpColor": "#00C510",
    "borderDownColor": "#ff0000",
    "wickUpColor": "#00C510",
    "wickDownColor": "#ff0000"
}

# ======================
# Background Tasks
# ======================
async def realtime_heartbeat():
    """💓 Keep WebSocket alive - resubscribe every 45 seconds"""
    global CLIENT, CURRENT_ASSET
    while True:
        await asyncio.sleep(45)
        try:
            if CLIENT and CURRENT_ASSET:
                internal = DISPLAY_TO_INTERNAL.get(CURRENT_ASSET)
                if internal:
                    await CLIENT.start_realtime_price(internal, 1)
                    print("💓 Realtime heartbeat sent")
        except Exception as e:
            print(f"⚠️ Heartbeat error: {e}")

async def market_activity_ping():
    """📡 REST API ping (backup only, not WebSocket keep-alive)"""
    global CLIENT, CURRENT_ASSET, CURRENT_TIMEFRAME
    while True:
        await asyncio.sleep(180)
        try:
            if not CLIENT or not CLIENT.api or CURRENT_ASSET is None:
                continue
            internal_asset = DISPLAY_TO_INTERNAL.get(CURRENT_ASSET, "AUDCAD_otc")
            period_sec = TIMEFRAMES.get(CURRENT_TIMEFRAME, 60)
            await CLIENT.get_candles(
                asset=internal_asset,
                end_from_time=time.time(),
                offset=period_sec * 2,
                period=period_sec
            )
            print("📡 Market activity ping sent")
        except Exception as e:
            print(f"⚠️ Market ping failed: {str(e)[:80]}")

def price_sleep_watcher():
    """♻️ Watch for idle WebSocket and restart realtime stream"""
    global LAST_TICK_TIME, CLIENT, CURRENT_ASSET
    while True:
        time.sleep(20)
        diff = time.time() - LAST_TICK_TIME

        if diff > 60:
            print(f"♻️ Realtime stream idle for {int(diff)}s — restarting stream")

            try:
                if CLIENT and CURRENT_ASSET:
                    internal = DISPLAY_TO_INTERNAL.get(CURRENT_ASSET)
                    if internal:
                        future = asyncio.run_coroutine_threadsafe(
                            CLIENT.start_realtime_price(internal, 1),
                            ASYNC_LOOP
                        )
                        future.result(timeout=5)
                        LAST_TICK_TIME = time.time()
                        print("✅ Realtime stream restarted successfully")
            except Exception as e:
                print(f"❌ Failed to restart realtime stream: {e}")

# Start watchers
threading.Thread(target=price_sleep_watcher, daemon=True, name="PriceWatcher").start()
print("✅ Price sleep watcher started (auto-restart on idle)")

# ======================
# Helpers
# ======================
def safe_stop_realtime_price(asset):
    global CLIENT
    if CLIENT and hasattr(CLIENT, 'stop_realtime_price'):
        try:
            future = asyncio.run_coroutine_threadsafe(CLIENT.stop_realtime_price(asset), ASYNC_LOOP)
            future.result(timeout=5)
        except Exception as e:
            print(f"⚠️ stop_realtime_price error: {e}")

def update_candle(asset, frame, price, ts_sec):
    global CANDLES, CURRENT_CANDLE
    duration = TIMEFRAMES[frame]
    candle_start = (ts_sec // duration) * duration
    curr = CURRENT_CANDLE.get(asset, {}).get(frame, {})
    if not curr or curr.get("time") != candle_start:
        if curr:
            if asset not in CANDLES:
                CANDLES[asset] = {}
            if frame not in CANDLES[asset]:
                CANDLES[asset][frame] = []
            CANDLES[asset][frame].append(curr.copy())
            if len(CANDLES[asset][frame]) > 200:
                CANDLES[asset][frame] = CANDLES[asset][frame][-200:]
        if asset not in CURRENT_CANDLE:
            CURRENT_CANDLE[asset] = {}
        CURRENT_CANDLE[asset][frame] = {
            "time": candle_start,
            "open": price,
            "high": price,
            "low": price,
            "close": price
        }
    else:
        if price > curr["high"]: curr["high"] = price
        if price < curr["low"]: curr["low"] = price
        curr["close"] = price

def process_message(message):
    global CANDLES, CURRENT_CANDLE, CURRENT_ASSET, SERVER_TIME_OFFSET, LAST_TICK_TIME
    LAST_TICK_TIME = time.time()
    if CURRENT_ASSET is None:
        return
    try:
        text = message.decode('utf-8', errors='ignore') if isinstance(message, bytes) else str(message)
        match = re.search(r'\[\[("[^"]+"|[^,\]]+),\s*([\d.]+),\s*([\d.]+),\s*\d+\]\]', text)
        if not match:
            return
        asset_raw = match.group(1).strip('"')
        internal_asset = DISPLAY_TO_INTERNAL.get(CURRENT_ASSET)
        if asset_raw != internal_asset:
            return
        timestamp = float(match.group(2))
        price = float(match.group(3))
        ts_sec = int(timestamp)
        SERVER_TIME_OFFSET = timestamp - time.time()
        for frame in TIMEFRAMES:
            update_candle(CURRENT_ASSET, frame, price, ts_sec)
        
        all_candles = CANDLES.get(CURRENT_ASSET, {}).get(CURRENT_TIMEFRAME, []).copy()
        curr = CURRENT_CANDLE.get(CURRENT_ASSET, {}).get(CURRENT_TIMEFRAME)
        if curr:
            if all_candles and all_candles[-1]["time"] == curr["time"]:
                all_candles[-1] = curr
            else:
                all_candles.append(curr)
        all_candles.sort(key=lambda x: x["time"])
        
        payload = {
            "candles": all_candles,
            "asset": CURRENT_ASSET,
            "timeframe": CURRENT_TIMEFRAME,
            "timeframe_seconds": TIMEFRAMES[CURRENT_TIMEFRAME],
            "server_time": time.time() + SERVER_TIME_OFFSET,
            "last_candle_time": curr["time"] if curr else 0
        }
        if UI_QUEUE.qsize() < 3:
            UI_QUEUE.put(payload)
        else:
            print("⏭️ Skipping update to prevent UI flood")
    except Exception as e:
        print(f"[ERROR] process_message: {e}")
        traceback.print_exc()

async def load_timeframe_data(asset_display, tf_name, period_sec):
    global CANDLES, CURRENT_CANDLE
    internal = DISPLAY_TO_INTERNAL.get(asset_display, "AUDCAD_otc")
    try:
        end_time = time.time()
        offset_seconds = 199 * period_sec
        hist_data = await CLIENT.get_candles(asset=internal, end_from_time=end_time, offset=offset_seconds, period=period_sec)
        loaded = []
        if isinstance(hist_data, list):
            for c in hist_data:
                if not isinstance(c, dict):
                    continue
                if all(k in c for k in ("time", "open", "high", "low", "close")):
                    try:
                        candle_time = (int(c["time"]) // period_sec) * period_sec
                        loaded.append({
                            "time": candle_time,
                            "open": float(c["open"]),
                            "high": float(c["high"]),
                            "low": float(c["low"]),
                            "close": float(c["close"])
                        })
                    except:
                        continue
        loaded.sort(key=lambda x: x["time"])
        CANDLES[asset_display][tf_name] = loaded[-199:]
        print(f"✅ Loaded {len(loaded)} candles for {tf_name}")
    except Exception as e:
        print(f"⚠️ Failed to load {tf_name} for {asset_display}: {e}")

async def connect_to_quotex(email, password):
    global CLIENT
    try:
        CLIENT = Quotex(email=email, password=password, lang="en")
        success, reason = await CLIENT.connect()
        if not success:
            return False, reason
        await CLIENT.change_account("PRACTICE")
        
        # Start background tasks
        asyncio.create_task(realtime_heartbeat())
        asyncio.create_task(market_activity_ping())
        print("✅ Realtime heartbeat started (45s interval)")
        print("✅ Market activity ping started (180s interval)")
        
        ws_app = CLIENT.api.websocket_client.wss
        original = getattr(ws_app, 'on_message', None)
        def handler(ws, msg):
            try:
                process_message(msg)
            except Exception as e:
                print(f"🔥 on_message handler error: {e}")
                traceback.print_exc()
            if original:
                try:
                    return original(ws, msg)
                except:
                    pass
        ws_app.on_message = handler
        return True, ""
    except Exception as e:
        return False, str(e)

async def start_streaming(asset_display):
    global CURRENT_ASSET, CANDLES, CURRENT_CANDLE
    internal = DISPLAY_TO_INTERNAL.get(asset_display, "AUDCAD_otc")
    if CURRENT_ASSET and CLIENT:
        safe_stop_realtime_price(DISPLAY_TO_INTERNAL.get(CURRENT_ASSET, "AUDCAD_otc"))
    CURRENT_ASSET = asset_display
    CANDLES[asset_display] = {}
    CURRENT_CANDLE[asset_display] = {}
    current_tf = CURRENT_TIMEFRAME
    period_sec = TIMEFRAMES[current_tf]
    await load_timeframe_data(asset_display, current_tf, period_sec)
    await CLIENT.start_realtime_price(internal, 1)
    async def load_other_timeframes():
        for tf_name, period_sec in TIMEFRAMES.items():
            if tf_name == current_tf:
                continue
            await load_timeframe_data(asset_display, tf_name, period_sec)
    asyncio.create_task(load_other_timeframes())

# ======================
# Eel Functions
# ======================
@eel.expose
def login(email, password):
    def run_connect():
        try:
            future = asyncio.run_coroutine_threadsafe(connect_to_quotex(email, password), ASYNC_LOOP)
            success, reason = future.result()
            if success:
                eel.onLoginSuccess()()
            else:
                eel.onLoginError(reason)()
        except Exception as e:
            eel.onLoginError(str(e))()
    threading.Thread(target=run_connect, daemon=True).start()

@eel.expose
def change_asset(asset_display):
    def start():
        try:
            future = asyncio.run_coroutine_threadsafe(start_streaming(asset_display), ASYNC_LOOP)
            future.result()
        except Exception as e:
            print(f"Error in change_asset: {e}")
    threading.Thread(target=start, daemon=True).start()

@eel.expose
def change_timeframe(tf):
    global CURRENT_TIMEFRAME
    if tf not in TIMEFRAMES:
        return
    old_tf = CURRENT_TIMEFRAME
    CURRENT_TIMEFRAME = tf
    if tf not in CANDLES.get(CURRENT_ASSET, {}):
        def load_missing():
            try:
                future = asyncio.run_coroutine_threadsafe(
                    load_timeframe_data(CURRENT_ASSET, tf, TIMEFRAMES[tf]), ASYNC_LOOP
                )
                future.result()
                all_candles = CANDLES.get(CURRENT_ASSET, {}).get(tf, []).copy()
                curr = CURRENT_CANDLE.get(CURRENT_ASSET, {}).get(tf)
                if curr:
                    if all_candles and all_candles[-1]["time"] == curr["time"]:
                        all_candles[-1] = curr
                    else:
                        all_candles.append(curr)
                all_candles.sort(key=lambda x: x["time"])
                if UI_QUEUE.qsize() < 3:
                    UI_QUEUE.put({
                        "candles": all_candles,
                        "asset": CURRENT_ASSET,
                        "timeframe": tf,
                        "timeframe_seconds": TIMEFRAMES[tf],
                        "server_time": time.time() + SERVER_TIME_OFFSET,
                        "last_candle_time": curr["time"] if curr else 0
                    })
            except Exception as e:
                print(f"Error loading missing timeframe {tf}: {e}")
        threading.Thread(target=load_missing, daemon=True).start()
        return
    all_candles = CANDLES.get(CURRENT_ASSET, {}).get(tf, []).copy()
    curr = CURRENT_CANDLE.get(CURRENT_ASSET, {}).get(tf)
    if curr:
        if all_candles and all_candles[-1]["time"] == curr["time"]:
            all_candles[-1] = curr
        else:
            all_candles.append(curr)
    all_candles.sort(key=lambda x: x["time"])
    if UI_QUEUE.qsize() < 3:
        UI_QUEUE.put({
            "candles": all_candles,
            "asset": CURRENT_ASSET,
            "timeframe": tf,
            "timeframe_seconds": TIMEFRAMES[tf],
            "server_time": time.time() + SERVER_TIME_OFFSET,
            "last_candle_time": curr["time"] if curr else 0
        })

@eel.expose
def get_asset_categories():
    return ASSET_CATEGORIES

@eel.expose
def get_timeframes():
    return list(TIMEFRAMES.keys())

@eel.expose
def apply_candle_colors(colors):
    global CANDLE_COLORS
    CANDLE_COLORS = colors
    eel.updateCandleColors(colors)()

@eel.expose
def get_candle_colors():
    return CANDLE_COLORS

# ======================
# HTML Templates
# ======================
def write_login_html():
    with open("web/login.html", "w", encoding="utf-8") as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Login — QuotexChart</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src="/eel.js"></script>
<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: Segoe UI, system-ui;
}
body {
  background: radial-gradient(circle at top, #1a1640, #0b0b1a);
  height: 100vh;
  color: #fff;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.header-text {
  text-align: center;
  color: #4dffcc;
  font-size: 22px;
  font-weight: bold;
  margin-bottom: 24px;
}
.content-right {
  max-width: 500px;
  padding: 0 20px;
}
.content-right h4 {
  color: #4dffcc;
  margin: 14px 0 8px;
  font-size: 14px;
}
.content-right p,
.content-right ul {
  font-size: 12px;
  color: #cfd3ff;
  line-height: 1.6;
  margin: 0 0 12px;
}
.content-right ul {
  padding-left: 20px;
}
.content-right li {
  margin-bottom: 4px;
}
.socials-info {
  display: flex;
  gap: 16px;
  margin-top: 16px;
}
.socials-info a img {
  width: 28px;
  height: 28px;
  transition: 0.2s;
}
.socials-info a img:hover {
  transform: scale(1.2);
}

/* Left side */
.center {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 60px; /* أقرب قليلاً */
  padding: 40px 20px;
}
.card {
  width: 360px;
  padding: 32px;
  background: linear-gradient(180deg, #0f1125, #0b0c1a);
  border-radius: 20px;
  box-shadow:
    0 0 40px rgba(77,255,204,0.15),
    0 20px 50px rgba(0,0,0,0.6);
  border: 1px solid rgba(255,255,255,0.05);
  position: relative;
}
.badge {
  position: absolute;
  top: -12px;
  right: -12px;
  background: #4dffcc;
  color: #000;
  font-size: 10px;
  padding: 6px 12px;
  border-radius: 14px;
  font-weight: bold;
  box-shadow: 0 0 15px rgba(77,255,204,0.6);
}
h2 {
  text-align: center;
  color: #4dffcc;
  margin-bottom: 6px;
  letter-spacing: 0.5px;
}
.subtitle {
  text-align: center;
  font-size: 12px;
  color: #cfd3ff;
  margin-bottom: 22px;
  line-height: 1.4;
}
.subtitle span {
  font-size: 11px;
  color: #4dffcc;
}
.inp {
  width: 100%;
  padding: 13px;
  margin: 8px 0;
  background: #141633;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px;
  color: #fff;
  outline: none;
}
.inp:focus {
  border-color: #4dffcc;
  box-shadow: 0 0 10px rgba(77,255,204,0.3);
}
.password-wrapper {
  position: relative;
}
.toggle-pass {
  position: absolute;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
}
.toggle-pass svg {
  width: 18px;
  height: 18px;
  fill: #9aa0ff;
  transition: 0.2s;
}
.toggle-pass:hover svg {
  fill: #4dffcc;
}
.btn {
  width: 100%;
  padding: 13px;
  margin-top: 14px;
  background: linear-gradient(90deg, #4dffcc, #5affdf);
  color: #000;
  border: none;
  border-radius: 12px;
  font-weight: bold;
  cursor: pointer;
  transition: 0.2s;
}
.btn:hover {
  box-shadow: 0 0 20px rgba(77,255,204,0.6);
}
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.spinner {
  display: none;
  width: 26px;
  height: 26px;
  border: 3px solid rgba(255,255,255,0.3);
  border-top: 3px solid #4dffcc;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 14px auto;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.error {
  color: #ff6b6b;
  text-align: center;
  margin-top: 10px;
  font-size: 13px;
}
.telegram-below-card {
  margin-top: 20px; /* أبعد قليلاً */
  display: flex;
  align-items: center;
  gap: 8px;
  color: #cfd3ff;
  font-size: 12px;
}
.telegram-below-card img {
  width: 28px;
  height: 28px;
  transition: 0.2s;
}
.telegram-below-card img:hover {
  transform: scale(1.2);
}
.footer {
  position: absolute;
  bottom: 10px;
  width: 100%;
  text-align: center;
  font-size: 11px;
  color: #aaa;
  opacity: 0.8;
}
</style>
</head>
<body>

<div class="center">
  <!-- البطاقة في اليسار -->
  <div style="display: flex; flex-direction: column; align-items: center;">
    <div class="card">
      <div class="badge">Community Edition</div>
      <h2>QuotexChart</h2>
      <div class="subtitle">
        Realtime Candlestick Viewer<br>
        <span>Indicators & Strategies coming soon</span>
      </div>
      <input type="email" id="email" class="inp" placeholder="Email" required>
      <div class="password-wrapper">
        <input type="password" id="password" class="inp" placeholder="Password" required>
        <span class="toggle-pass" onclick="togglePassword()">
          <svg id="eyeOpen" viewBox="0 0 24 24">
            <path d="M12 5C7 5 3.1 8 1.5 12c1.6 4 5.5 7 10.5 7s8.9-3 10.5-7C20.9 8 17 5 12 5zm0 11a4 4 0 1 1 0-8 4 4 0 0 1 0 8z"/>
          </svg>
          <svg id="eyeClosed" viewBox="0 0 24 24" style="display:none">
            <path d="M2 5.3 3.3 4l17 17-1.3 1.3-3.1-3.1C14.7 19.7 13.4 20 12 20 7 20 3.1 17 1.5 13c.7-1.7 1.8-3.2 3.2-4.4L2 5.3z"/>
          </svg>
        </span>
      </div>
      <button class="btn" onclick="login()">Login</button>
      <div class="spinner" id="spinner"></div>
      <div class="error" id="error"></div>
    </div>
    <div class="telegram-below-card">
      <a href="https://t.me/qxchart" target="_blank">
        <img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/telegram.svg" alt="Telegram" style="fill:#0088cc;">
      </a>
      <span>Join us for updates</span>
    </div>
  </div>

  <!-- النصوص في اليمين بدون خلفية -->
  <div class="content-right">
    <div class="header-text">Welcome to QuotexChart</div>


    <h4>About QuotexChart</h4>
    <p>Free community tool for realtime candlestick visualization on Quotex.<br>This release focuses on chart display only.</p>

    <h4>Current Version</h4>
    <ul>
      <li>Live candlestick chart</li>
      <li>Realtime sync</li>
      <li>Lightweight & fast</li>
    </ul>

    <h4>Next Updates</h4>
    <ul>
      <li>Technical indicators</li>
      <li>Trading strategies</li>
      <li>Advanced tools</li>
    </ul>

    <div style="margin-top: 12px;">
      <strong style="color: #4dffcc; font-size: 13px;">Follow us</strong>
    </div>
    <div class="socials-info">
      <a href="https://www.instagram.com/salah__badi__19?igsh=MTc5cXVvd3E0dm41Zw==" target="_blank">
        <img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/instagram.svg" alt="Instagram" style="fill:#E4405F;">
      </a>
      <a href="https://www.tiktok.com/@salah__badi__5?_r=1&_t=ZS-93oNcQNP4uD" target="_blank">
        <img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/tiktok.svg" alt="TikTok" style="fill:#000000;">
      </a>
    </div>
  </div>
</div>

<div class="footer">
  Designed & Developed by <b>BADI SALAH</b> © 2026
</div>

<script>
async function login() {
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;
  if (!email || !password) {
    showError("Email and password are required");
    return;
  }
  showSpinner();
  try {
    await eel.login(email, password)();
  } catch {
    hideSpinner();
    showError("Connection failed");
  }
}
function togglePassword() {
  const pass = document.getElementById('password');
  const open = document.getElementById('eyeOpen');
  const closed = document.getElementById('eyeClosed');
  if (pass.type === "password") {
    pass.type = "text";
    open.style.display = "none";
    closed.style.display = "block";
  } else {
    pass.type = "password";
    open.style.display = "block";
    closed.style.display = "none";
  }
}
function showSpinner() {
  document.getElementById('spinner').style.display = 'block';
  document.querySelector('.btn').disabled = true;
  document.getElementById('error').textContent = '';
}
function hideSpinner() {
  document.getElementById('spinner').style.display = 'none';
  document.querySelector('.btn').disabled = false;
}
function showError(msg) {
  document.getElementById('error').textContent = msg;
}
document.addEventListener('keydown', e => {
  if (e.key === "Enter") login();
});
eel.expose(onLoginSuccess);
function onLoginSuccess() {
  window.location.href = 'chart.html';
}
eel.expose(onLoginError);
function onLoginError(reason) {
  hideSpinner();
  showError(reason || "Login failed");
}
</script>
</body>
</html>''')

def write_chart_html():
    with open("web/chart.html", "w", encoding="utf-8") as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Quotex Pro Trader</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src="/eel.js"></script>
<style>
:root { --bg:#000; --panel:#000; --border:#1f2128; --text:#d1d4dc; --accent:#4dffcc; }
html, body { margin:0; height:100%; background:var(--bg); color:var(--text); font-family:Arial,sans-serif; overflow:hidden; }
#toolbar {
height:30px;
display:flex;
align-items:center;
gap:6px;
padding:0 8px;
background:#0a0a14;
border-bottom:1px solid var(--border);
font-size:11px;
}
.btn {
background:#1a1a2e;
color:var(--text);
border:1px solid var(--border);
padding:3px 6px;
border-radius:3px;
cursor:pointer;
white-space:nowrap;
font-size:10px;
}
.btn.active { background:var(--accent); color:#000; font-weight:bold; }
#assetSearch {
background:#1a1a2e;
color:var(--text);
border:1px solid var(--border);
border-radius:3px;
padding:3px 6px;
font-size:10px;
width:120px;
outline:none;
}
#assetSearch:focus {
border-color: var(--accent);
}

/* Centered Modal Styles */
.modal-overlay {
position: fixed;
top: 0;
left: 0;
width: 100%;
height: 100%;
background: rgba(0, 0, 0, 0.7);
backdrop-filter: blur(4px);
z-index: 1000;
display: none;
justify-content: center;
align-items: center;
}

/* Assets Modal */
.modal-card {
background: rgba(20, 20, 35, 0.95);
border: 1px solid rgba(77, 255, 204, 0.3);
border-radius: 12px;
box-shadow: 0 0 30px rgba(77, 255, 204, 0.2), 0 10px 40px rgba(0, 0, 0, 0.5);
width: 480px;
max-height: 80vh;
display: flex;
flex-direction: column;
overflow: hidden;
}

.modal-header {
display: flex;
justify-content: space-between;
align-items: center;
padding: 16px 24px;
background: rgba(77, 255, 204, 0.1);
border-bottom: 1px solid rgba(77, 255, 204, 0.2);
}

.modal-title {
font-size: 13px;
font-weight: bold;
color: #4dffcc;
letter-spacing: 0.5px;
}

.modal-close {
width: 26px;
height: 26px;
display: flex;
align-items: center;
justify-content: center;
cursor: pointer;
border-radius: 50%;
transition: all 0.2s;
color: #4dffcc;
font-size: 16px;
}

.modal-close:hover {
background: rgba(77, 255, 204, 0.2);
transform: rotate(90deg);
}

.modal-search {
padding: 16px 24px;
border-bottom: 1px solid rgba(77, 255, 204, 0.1);
}

.modal-search-input {
width: 100%;
padding: 10px 14px;
background: rgba(26, 26, 46, 0.8);
border: 1px solid rgba(77, 255, 204, 0.2);
border-radius: 8px;
color: #d1d4dc;
font-size: 12px;
outline: none;
transition: all 0.2s;
}

.modal-search-input:focus {
border-color: #4dffcc;
box-shadow: 0 0 12px rgba(77, 255, 204, 0.2);
}

.modal-search-input::placeholder {
color: #6b6b7b;
}

.modal-content {
overflow-y: auto;
flex: 1;
padding: 16px;
}

/* Category Styling */
.modal-category {
display: flex;
align-items: center;
gap: 8px;
padding: 12px 16px;
background: rgba(77, 255, 204, 0.08);
font-weight: bold;
font-size: 11px;
color: #4dffcc;
border-radius: 8px;
margin-bottom: 8px;
margin-top: 12px;
border-left: 3px solid #4dffcc;
}

.modal-category:first-child {
margin-top: 0;
}

/* Item Styling */
.modal-item {
display: flex;
align-items: center;
justify-content: space-between;
padding: 12px 16px;
cursor: pointer;
border-radius: 8px;
transition: all 0.2s;
font-size: 12px;
color: #d1d4dc;
margin-bottom: 6px;
border: 1px solid transparent;
}

.modal-item:hover {
background: rgba(77, 255, 204, 0.12);
color: #4dffcc;
transform: translateX(4px);
border-color: rgba(77, 255, 204, 0.2);
}

.modal-item.active {
background: rgba(77, 255, 204, 0.2);
color: #4dffcc;
font-weight: bold;
border-color: rgba(77, 255, 204, 0.4);
box-shadow: 0 0 15px rgba(77, 255, 204, 0.15);
}

.modal-item.active::after {
content: "✓";
font-size: 12px;
color: #4dffcc;
}

/* Timeframe Modal */
.tf-grid {
display: grid;
grid-template-columns: repeat(3, 1fr);
gap: 8px;
padding: 12px;
}

.tf-btn {
padding: 10px;
background: rgba(26, 26, 46, 0.8);
border: 1px solid rgba(77, 255, 204, 0.2);
border-radius: 8px;
cursor: pointer;
text-align: center;
font-size: 11px;
color: #d1d4dc;
transition: all 0.2s;
}

.tf-btn:hover {
background: rgba(77, 255, 204, 0.15);
border-color: rgba(77, 255, 204, 0.4);
color: #4dffcc;
transform: translateY(-2px);
}

.tf-btn.active {
background: rgba(77, 255, 204, 0.25);
border-color: #4dffcc;
color: #4dffcc;
font-weight: bold;
box-shadow: 0 0 15px rgba(77, 255, 204, 0.3);
}

/* Chart Area */
#chart { height:calc(100% - 30px); position:relative; }

/* Countdown Overlay */
#candle-countdown {
position: absolute;
top: 8px;
right: 12px;
background: rgba(20,20,30,0.85);
border: 1px solid #1f2128;
border-radius: 6px;
padding: 4px 8px;
font-size: 11px;
font-weight: bold;
color: #4dffcc;
z-index: 50;
pointer-events: none;
}

/* Settings Panel */
#settings-panel {
position:absolute;
top:35px;
right:10px;
background:rgba(20,20,30,0.95);
border:1px solid var(--border);
border-radius:6px;
padding:12px;
width:220px;
z-index:200;
display:none;
font-size:11px;
}
.setting-row {
display:flex;
align-items:center;
margin:6px 0;
}
.setting-row label {
width:100px;
font-size:10px;
}
.setting-row input[type="color"] {
width:30px;
height:20px;
border:1px solid var(--border);
background:var(--panel);
}
.settings-btns {
display:flex;
gap:6px;
margin-top:8px;
}
.settings-btns button {
flex:1;
padding:4px;
font-size:10px;
border:1px solid var(--border);
border-radius:3px;
cursor:pointer;
}
.apply-btn { background:#4dffcc; color:#000; font-weight:bold; }
.cancel-btn { background:#ff4d4d; color:#fff; }

/* Scrollbar */
.modal-content::-webkit-scrollbar {
width: 6px;
}
.modal-content::-webkit-scrollbar-track {
background: rgba(77, 255, 204, 0.05);
border-radius: 3px;
}
.modal-content::-webkit-scrollbar-thumb {
background: rgba(77, 255, 204, 0.3);
border-radius: 3px;
}
.modal-content::-webkit-scrollbar-thumb:hover {
background: rgba(77, 255, 204, 0.5);
}
</style>
</head>
<body>
<div id="toolbar">
<div class="btn" id="assetsBtn">Assets</div>
<div class="btn" id="timeframesBtn">Timeframes</div>
<div class="btn" id="donchianBtn">Donchian</div>
<div style="margin-right:auto;font-weight:bold;color:var(--accent);" id="currentAsset">AUD/CAD (OTC)</div>
<div id="currentTimeframe" class="btn active">1m</div>
<div class="btn" id="settingsBtn">⚙️</div>
</div>

<!-- Assets Modal -->
<div id="assetsModal" class="modal-overlay">
    <div class="modal-card">
        <div class="modal-header">
            <div class="modal-title">Select Asset</div>
            <div class="modal-close" onclick="closeAssetsModal()">✕</div>
        </div>
        <div class="modal-search">
            <input type="text" id="modalAssetSearch" class="modal-search-input" placeholder="Search assets..." autocomplete="off">
        </div>
        <div class="modal-content" id="assetsModalContent"></div>
    </div>
</div>

<!-- Timeframes Modal -->
<div id="timeframesModal" class="modal-overlay">
    <div class="modal-card" style="width: 280px;">
        <div class="modal-header">
            <div class="modal-title">Select Timeframe</div>
            <div class="modal-close" onclick="closeTimeframesModal()">✕</div>
        </div>
        <div class="tf-grid" id="timeframesModalContent"></div>
    </div>
</div>

<!-- Settings Panel -->
<div id="settings-panel">
<div class="setting-row">
<label>Bull Body:</label>
<input type="color" id="upColor" value="#00C510">
</div>
<div class="setting-row">
<label>Bull Border:</label>
<input type="color" id="borderUpColor" value="#00C510">
</div>
<div class="setting-row">
<label>Bull Wick:</label>
<input type="color" id="wickUpColor" value="#00C510">
</div>
<div class="setting-row">
<label>Bear Body:</label>
<input type="color" id="downColor" value="#ff0000">
</div>
<div class="setting-row">
<label>Bear Border:</label>
<input type="color" id="borderDownColor" value="#ff0000">
</div>
<div class="setting-row">
<label>Bear Wick:</label>
<input type="color" id="wickDownColor" value="#ff0000">
</div>
<div class="settings-btns">
<button class="apply-btn" onclick="applySettings()">Apply</button>
<button class="cancel-btn" onclick="closeSettings()">Cancel</button>
</div>
</div>

<!-- Chart Container -->
<div id="chart">
<div id="candle-countdown">⏱ --:--</div>
</div>

<!-- Lightweight Charts Library -->
<script src="https://cdn.jsdelivr.net/npm/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js"></script>

<script>
let currentAsset = "AUD/CAD (OTC)";
let currentTimeframe = "1m";
let timeframeSeconds = 60;
let serverTimeOffset = 0;
let isFirstLoad = true;
let currentCandles = [];
let allCategories = null;
let needsFullRedraw = false;
let isUserInteracting = false;

// Donchian Strategy State
let donchianEnabled = false;
let signalMarkers = [];
const plottedSignals = new Set();

// Initialize Chart
const chart = LightweightCharts.createChart(document.getElementById('chart'), {
layout: {
background: { color: '#0b0e11' },
textColor: '#d1d4dc'
},
grid: {
vertLines: { color: '#1f2128' },
horzLines: { color: '#1f2128' }
},
crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
handleScroll: { mouseWheel: true, pressedMouseMove: true },
handleScale: { axisPressedMouseMove: true, mouseWheel: false },
rightPriceScale: {
visible: true,
borderColor: '#1f2128',
textColor: '#d1d4dc',
entireTextOnly: false,
minimumWidth: 60,
scaleMargins: { top: 0.15, bottom: 0.15 }
},
timeScale: {
visible: true,
borderColor: '#1f2128',
timeVisible: true,
secondsVisible: true,
minBarSpacing: 4,
maxBarSpacing: 15,
fixLeftEdge: false,
fixRightEdge: false
}
});

// ✅ Fix: Initial resize to make candles visible
const chartContainer = document.getElementById('chart');
chart.resize(chartContainer.clientWidth, chartContainer.clientHeight);

let candleSeries = chart.addCandlestickSeries({
upColor: '#00C510',
downColor: '#ff0000',
borderUpColor: '#00C510',
borderDownColor: '#ff0000',
wickUpColor: '#00C510',
wickDownColor: '#ff0000',
borderVisible: true,
priceFormat: {
type: 'price',
precision: 5,
minMove: 0.00001
}
});

// Interaction Detection
chart.subscribeCrosshairMove(() => { isUserInteracting = true; });
chart.timeScale().subscribeVisibleTimeRangeChange(() => { isUserInteracting = true; });

let interactionResetTimer = null;
function resetInteraction() { isUserInteracting = false; }

chartContainer.addEventListener('wheel', (e) => {
    e.preventDefault();
    const timeScale = chart.timeScale();
    const logicalRange = timeScale.getVisibleLogicalRange();
    if (!logicalRange) return;
    const rect = chartContainer.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const ratio = mouseX / rect.width;
    const rangeSize = logicalRange.to - logicalRange.from;
    const intensity = Math.min(Math.abs(e.deltaY), 100) / 100;
    const zoomFactor = e.deltaY > 0 ? 1 + 0.15 * intensity : 1 - 0.15 * intensity;
    const newRange = rangeSize * zoomFactor;
    const center = logicalRange.from + rangeSize * ratio;
    const newFrom = center - newRange * ratio;
    const newTo = center + newRange * (1 - ratio);
    timeScale.setVisibleLogicalRange({ from: newFrom, to: newTo });
    clearTimeout(interactionResetTimer);
    interactionResetTimer = setTimeout(resetInteraction, 300);
}, { passive: false });

// Countdown Helper
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

let countdownTimer = null;
let lastCandleTimeGlobal = 0;

function startOrUpdateCountdown(lastCandleTime) {
    lastCandleTimeGlobal = lastCandleTime;
    if (countdownTimer) return;
    countdownTimer = setInterval(() => {
        if (!lastCandleTimeGlobal) return;
        const now = Date.now() / 1000 + serverTimeOffset;
        const elapsed = now - lastCandleTimeGlobal;
        let remaining = timeframeSeconds - Math.floor(elapsed);
        if (remaining < 0) remaining = 0;
        document.getElementById('candle-countdown').textContent = `⏱ ${formatTime(remaining)}`;
    }, 1000);
}

// Modal Functions
function openAssetsModal() {
    renderAssetsModal();
    document.getElementById('assetsModal').style.display = 'flex';
    document.getElementById('modalAssetSearch').focus();
}
function closeAssetsModal() { document.getElementById('assetsModal').style.display = 'none'; }
function openTimeframesModal() {
    renderTimeframesModal();
    document.getElementById('timeframesModal').style.display = 'flex';
}
function closeTimeframesModal() { document.getElementById('timeframesModal').style.display = 'none'; }

document.getElementById('assetsModal').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeAssetsModal();
});
document.getElementById('timeframesModal').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeTimeframesModal();
});
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeAssetsModal();
        closeTimeframesModal();
    }
});

function renderAssetsModal(searchTerm = '') {
    const content = document.getElementById('assetsModalContent');
    let html = '';
    const term = searchTerm.toLowerCase();
    for (const [category, assets] of Object.entries(allCategories)) {
        const filteredAssets = assets.filter(asset => asset.toLowerCase().includes(term));
        if (filteredAssets.length > 0) {
            html += `<div class="modal-category">${category}</div>`;
            filteredAssets.forEach(asset => {
                const isActive = asset === currentAsset;
                html += `<div class="modal-item ${isActive ? 'active' : ''}" onclick="selectAsset('${asset}')">${asset}</div>`;
            });
        }
    }
    if (!html && searchTerm) {
        html = '<div style="padding: 30px; text-align: center; color: #6b6b7b; font-size: 12px;">No matching assets found</div>';
    }
    content.innerHTML = html;
}

function selectAsset(asset) {
    currentAsset = asset;
    needsFullRedraw = true;
    document.getElementById('currentAsset').textContent = currentAsset;
    eel.change_asset(currentAsset)();
    closeAssetsModal();
    isFirstLoad = true;
}

function renderTimeframesModal() {
    const content = document.getElementById('timeframesModalContent');
    const tfs = ["5s", "10s", "15s", "30s", "1m", "2m", "3m", "5m", "10m", "15m", "30m", "1h", "4h"];
    let html = '';
    tfs.forEach(tf => {
        const isActive = tf === currentTimeframe;
        html += `<div class="tf-btn ${isActive ? 'active' : ''}" onclick="selectTimeframe('${tf}')">${tf}</div>`;
    });
    content.innerHTML = html;
}

function selectTimeframe(tf) {
    currentTimeframe = tf;
    needsFullRedraw = true;
    timeframeSeconds = {
        "5s":5,"10s":10,"15s":15,"30s":30,
        "1m":60,"2m":120,"3m":180,"5m":300,
        "10m":600,"15m":900,"30m":1800,
        "1h":3600,"4h":14400
    }[currentTimeframe];
    document.getElementById('currentTimeframe').textContent = currentTimeframe;
    eel.change_timeframe(currentTimeframe)();
    closeTimeframesModal();
    isFirstLoad = true;
}

// Donchian Toggle Button
document.getElementById('donchianBtn').addEventListener('click', () => {
    donchianEnabled = !donchianEnabled;
    document.getElementById('donchianBtn').classList.toggle('active', donchianEnabled);
    if (donchianEnabled && currentCandles.length > 0) {
        detectDonchianSignals(currentCandles);
    } else {
        signalMarkers = [];
        plottedSignals.clear();
        candleSeries.setMarkers([]);
    }
});

// Settings Panel
document.getElementById('settingsBtn').addEventListener('click', () => {
    const panel = document.getElementById('settings-panel');
    if (panel.style.display === 'block') {
        panel.style.display = 'none';
    } else {
        eel.get_candle_colors()(function(colors) {
            document.getElementById('upColor').value = colors.upColor;
            document.getElementById('downColor').value = colors.downColor;
            document.getElementById('borderUpColor').value = colors.borderUpColor;
            document.getElementById('borderDownColor').value = colors.borderDownColor;
            document.getElementById('wickUpColor').value = colors.wickUpColor;
            document.getElementById('wickDownColor').value = colors.wickDownColor;
            panel.style.display = 'block';
        });
    }
});

function applySettings() {
    const colors = {
        upColor: document.getElementById('upColor').value,
        downColor: document.getElementById('downColor').value,
        borderUpColor: document.getElementById('borderUpColor').value,
        borderDownColor: document.getElementById('borderDownColor').value,
        wickUpColor: document.getElementById('wickUpColor').value,
        wickDownColor: document.getElementById('wickDownColor').value
    };
    needsFullRedraw = true;
    eel.apply_candle_colors(colors)();
    closeSettings();
}

function closeSettings() {
    document.getElementById('settings-panel').style.display = 'none';
}

// Eel Exposures
eel.expose(updateCandleColors);
function updateCandleColors(colors) {
    chart.removeSeries(candleSeries);
    candleSeries = chart.addCandlestickSeries({
        upColor: colors.upColor,
        downColor: colors.downColor,
        borderUpColor: colors.borderUpColor,
        borderDownColor: colors.borderDownColor,
        wickUpColor: colors.wickUpColor,
        wickDownColor: colors.wickDownColor,
        borderVisible: true,
        priceFormat: { type: 'price', precision: 5, minMove: 0.00001 }
    });
    needsFullRedraw = true;
}

eel.get_asset_categories()(function(categories) {
    allCategories = categories;
    document.getElementById('assetsBtn').addEventListener('click', openAssetsModal);
    document.getElementById('timeframesBtn').addEventListener('click', openTimeframesModal);
});

document.getElementById('modalAssetSearch').addEventListener('input', (e) => {
    renderAssetsModal(e.target.value);
});

eel.get_timeframes()(function(tfs) {});

// === CORRECTED DONCHIAN STRATEGY (FULL HISTORICAL SCAN) ===
function calculateEMA(data, period) {
    if (data.length < period) return null;
    const k = 2 / (period + 1);
    let ema = data[0].close;
    for (let i = 1; i < data.length; i++) {
        ema = data[i].close * k + ema * (1 - k);
    }
    return ema;
}

function highest(arr, len, key = 'high') {
    const start = Math.max(0, arr.length - len);
    let max = -Infinity;
    for (let i = start; i < arr.length; i++) {
        if (arr[i][key] > max) max = arr[i][key];
    }
    return max;
}

function lowest(arr, len, key = 'low') {
    const start = Math.max(0, arr.length - len);
    let min = Infinity;
    for (let i = start; i < arr.length; i++) {
        if (arr[i][key] < min) min = arr[i][key];
    }
    return min;
}

// ✅ FULL HISTORICAL SIGNAL DETECTION (like TradingView)
function detectDonchianSignals(candles) {
    if (!donchianEnabled || candles.length < 32) return;

    signalMarkers = [];
    plottedSignals.clear();

    for (let i = 31; i < candles.length; i++) {
        const slice = candles.slice(0, i + 1);

        const upper = highest(slice, 30, 'high');
        const lower = lowest(slice, 30, 'low');
        const basis = (upper + lower) / 2;
        const ma = calculateEMA(slice, 8);
        if (ma === null) continue;

        const prev = slice[slice.length - 2];
        const curr = slice[slice.length - 1];

        let higherhigh = 0, lowerlow = 0;

        for (let j = slice.length - 1; j >= Math.max(0, slice.length - 5); j--) {
            if (slice[j].high > upper) higherhigh++;
            else break;
        }

        for (let j = slice.length - 1; j >= Math.max(0, slice.length - 5); j--) {
            if (slice[j].low < lower) lowerlow++;
            else break;
        }

        const bullish = curr.close > curr.open;
        const bearish = curr.close < curr.open;
        const aboveMA = curr.close > ma;
        const belowMA = curr.close < ma;

        const buyCondition =
            bullish &&
            aboveMA &&
            ((curr.close > basis && prev.close <= basis) || higherhigh > 1);

        const sellCondition =
            bearish &&
            belowMA &&
            ((curr.close < basis && prev.close >= basis) || lowerlow > 1);

        const key = curr.time;

        if (buyCondition && !plottedSignals.has(key + "_buy")) {
            signalMarkers.push({
                time: curr.time,
                position: "belowBar",
                color: "#1ecb4f",
                shape: "arrowUp",
                text: ""
            });
            plottedSignals.add(key + "_buy");
        }

        if (sellCondition && !plottedSignals.has(key + "_sell")) {
            signalMarkers.push({
                time: curr.time,
                position: "aboveBar",
                color: "#e02424",
                shape: "arrowDown",
                text: ""
            });
            plottedSignals.add(key + "_sell");
        }
    }

    candleSeries.setMarkers(signalMarkers);
}

// Main Chart Update
eel.expose(updateChart);
function updateChart(data) {
    const candles = data.candles;
    currentCandles = candles;
    document.getElementById('currentAsset').textContent = data.asset;
    currentTimeframe = data.timeframe;
    timeframeSeconds = data.timeframe_seconds || 60;
    serverTimeOffset = (data.server_time || 0) - (Date.now() / 1000);

    if (data.last_candle_time) {
        startOrUpdateCountdown(data.last_candle_time);
    }

    if (isFirstLoad && data.candles && data.candles.length > 1) {
        candleSeries.setData(data.candles);
        chart.timeScale().fitContent();
        isFirstLoad = false;
        if (donchianEnabled) {
            detectDonchianSignals(candles);
        }
        return;
    }

    if (needsFullRedraw) {
        candleSeries.setData(candles);
        chart.timeScale().fitContent();
        needsFullRedraw = false;
        if (donchianEnabled) {
            detectDonchianSignals(candles);
        }
        return;
    }

    if (candles.length > 0) {
        candleSeries.update(candles[candles.length - 1]);
        // For real-time updates, we could optimize by scanning only recent candles,
        // but for correctness and simplicity, we re-scan full history when enabled.
        if (donchianEnabled) {
            detectDonchianSignals(candles);
        }
    }
}

// ✅ Correct resize using container size
window.addEventListener('resize', () => {
    chart.resize(chartContainer.clientWidth, chartContainer.clientHeight);
});

// Initial Load
eel.change_asset(currentAsset)();
</script>
</body>
</html>''')

# ======================
# Main
# ======================
if __name__ == '__main__':
    os.makedirs("web", exist_ok=True)
    write_login_html()
    write_chart_html()
    print("\n🚀 Launching Quotex Pro Trader — FINAL STABLE VERSION")
    print("✅ WebSocket Keep-Alive: Enabled")
    print("✅ Auto-Restart on Idle: Enabled")
    print("✅ TradingView-like Countdown: Enabled")
    eel.init('web')
    eel.start('login.html', size=(1200, 700), port=8080, host='0.0.0.0', mode=None)
