import sys
import time
from pathlib import Path

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from app.core.config import DASHBOARD_REFRESH_SECONDS

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

st.set_page_config(
    page_title="Risk Management Dashboard",
    layout="wide",
)

st.title("Risk Management Dashboard")
st.caption("Live mock market data, client flow, exposure and PnL")

if "pnl_history" not in st.session_state:
    st.session_state.pnl_history = []

if "trade_history" not in st.session_state:
    st.session_state.trade_history = []

response = requests.get("http://127.0.0.1:8000/state", timeout=2)
data = response.json()

prices = data["prices"]
positions = data["positions"]
total_pnl = data["pnl"]
trades = data.get("trades", [])
client_risk = data.get("client_risk", [])
scale = data.get("scale", 1)
processed_trades_last_tick = data.get("processed_trades_last_tick", 0)

for trade in trades:
    st.session_state.trade_history.append(trade)

st.session_state.pnl_history.append(
    {
        "tick": len(st.session_state.pnl_history) + 1,
        "unrealized_pnl": total_pnl,
    }
)

warning_clients = [
    client for client in client_risk
    if client["alert_status"] == "WARNING"
]

breached_clients = [
    client for client in client_risk
    if client["alert_status"] == "BREACHED"
]

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Unrealized PnL", f"${total_pnl:,.2f}")
col2.metric("Open Positions", len(positions))
col3.metric("Trades Displayed", len(trades))
col4.metric("Simulation Scale", f"{scale}x")
col5.metric("Trades Processed", processed_trades_last_tick)

if breached_clients:
    col4.metric("Risk Status", "BREACHED")
    names = ", ".join(client["client_id"] for client in breached_clients)
    st.error(f"Risk limit breached for: {names}")
elif warning_clients:
    col4.metric("Risk Status", "WARNING")
    names = ", ".join(client["client_id"] for client in warning_clients)
    st.warning(f"Risk warning for: {names}")
else:
    col4.metric("Risk Status", "NORMAL")
    st.success("All client risk is within normal operating range.")

st.subheader("Client Risk View")

client_risk_df = pd.DataFrame(client_risk)

if not client_risk_df.empty:
    positions_df = client_risk_df["positions"].apply(pd.Series).fillna(0)

    client_risk_display = pd.concat(
        [
            client_risk_df.drop(columns=["positions"]),
            positions_df,
        ],
        axis=1,
    )

    def color_alert_status(value):
        if value == "BREACHED":
            return "background-color: #ffcccc; color: #8b0000; font-weight: bold"
        if value == "WARNING":
            return "background-color: #fff3cd; color: #856404; font-weight: bold"
        return "background-color: #d4edda; color: #155724; font-weight: bold"


    def color_pnl(value):
        if value > 0:
            return "color: green; font-weight: bold"
        if value < 0:
            return "color: red; font-weight: bold"
        return ""


    styled_client_risk = (
        client_risk_display
        .style
        .map(color_alert_status, subset=["alert_status"])
        .map(color_pnl, subset=["unrealized_pnl"])
    )

    st.dataframe(styled_client_risk, use_container_width=True)

    fig_client_exposure = px.bar(
        client_risk_display,
        x="client_id",
        y="gross_exposure",
        title="Gross Exposure by Client",
    )
    st.plotly_chart(fig_client_exposure, use_container_width=True)
else:
    st.info("No client risk generated yet.")

left, right = st.columns(2)

with left:
    st.subheader("Live Prices")

    price_df = pd.DataFrame(prices)

    if not price_df.empty:
        price_df["mid"] = (price_df["bid"] + price_df["ask"]) / 2
        price_df["spread"] = price_df["ask"] - price_df["bid"]

    st.dataframe(price_df, use_container_width=True)

with right:
    st.subheader("Book Positions")

    position_df = pd.DataFrame(positions)

    if not position_df.empty:
        position_df["total_pnl"] = (
            position_df["realized_pnl"] + position_df["unrealized_pnl"]
        )

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



time.sleep(DASHBOARD_REFRESH_SECONDS)
st.rerun()