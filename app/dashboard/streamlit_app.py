import time

import pandas as pd
import plotly.express as px
import streamlit as st

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from app.clients.trader import ClientTrader
from app.market.price_generator import PriceGenerator
from app.risk.book import RiskBook

st.set_page_config(
    page_title="Risk Management Dashboard",
    layout="wide",
)

st.title("Risk Management Dashboard")
st.caption("Live mock market data, client flow, exposure and PnL")

if "price_generator" not in st.session_state:
    st.session_state.price_generator = PriceGenerator()

if "trader" not in st.session_state:
    st.session_state.trader = ClientTrader()

if "book" not in st.session_state:
    st.session_state.book = RiskBook()

if "pnl_history" not in st.session_state:
    st.session_state.pnl_history = []

if "trade_history" not in st.session_state:
    st.session_state.trade_history = []

prices = st.session_state.price_generator.generate_snapshot()
trades = st.session_state.trader.generate_trades(prices)

st.session_state.book.apply_trades(trades)
st.session_state.book.mark_to_market(prices)

positions = st.session_state.book.get_positions()
total_pnl = st.session_state.book.total_unrealized_pnl()

st.session_state.pnl_history.append(
    {
        "tick": len(st.session_state.pnl_history) + 1,
        "unrealized_pnl": total_pnl,
    }
)

for trade in trades:
    st.session_state.trade_history.append(trade.model_dump())

col1, col2, col3 = st.columns(3)

col1.metric("Unrealized PnL", f"${total_pnl:,.2f}")
col2.metric("Open Positions", len(positions))
col3.metric("Trades This Tick", len(trades))

left, right = st.columns(2)

with left:
    st.subheader("Live Prices")
    price_df = pd.DataFrame([p.model_dump() | {"mid": p.mid, "spread": p.spread} for p in prices])
    st.dataframe(price_df, use_container_width=True)

with right:
    st.subheader("Book Positions")
    position_df = pd.DataFrame([p.model_dump() | {"total_pnl": p.total_pnl} for p in positions])
    st.dataframe(position_df, use_container_width=True)

st.subheader("PnL Curve")
pnl_df = pd.DataFrame(st.session_state.pnl_history)

if not pnl_df.empty:
    fig = px.line(
        pnl_df,
        x="tick",
        y="unrealized_pnl",
        title="Unrealized PnL Over Time",
    )
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Recent Trades")
trade_df = pd.DataFrame(st.session_state.trade_history[-25:])

if not trade_df.empty:
    st.dataframe(trade_df, use_container_width=True)
else:
    st.info("No trades generated yet.")

time.sleep(1)
st.rerun()