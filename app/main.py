import asyncio

from fastapi import FastAPI

from app.clients.trader import ClientTrader
from app.market.price_generator import PriceGenerator
from app.risk.book import RiskBook

from app.core.config import (
    SIMULATION_INTERVAL_SECONDS,
    SIMULATION_SCALE,
    MAX_RECENT_TRADES,
)

app = FastAPI()

pg = PriceGenerator()
trader = ClientTrader()
book = RiskBook()


latest_state = {
    "prices": [],
    "positions": [],
    "pnl": 0.0,
    "client_risk": [],
    "scale": 1,
    "processed_trades_last_tick": 0,
    
}

recent_trades = []


async def simulation_loop():
    while True:
        all_prices = []
        all_trades = []

        for _ in range(SIMULATION_SCALE):
            prices = pg.generate_snapshot()
            trades = trader.generate_trades(prices)

            book.apply_trades(trades)
            book.mark_to_market(prices)

            all_prices = prices
            all_trades.extend(trades)

        recent_trades.extend(all_trades)

        if len(recent_trades) > MAX_RECENT_TRADES:
            del recent_trades[:-MAX_RECENT_TRADES]

        latest_state["prices"] = [p.model_dump() for p in all_prices]
        latest_state["trades"] = [t.model_dump() for t in recent_trades[-25:]]
        latest_state["positions"] = [p.model_dump() for p in book.get_positions()]
        latest_state["pnl"] = book.total_unrealized_pnl()
        latest_state["client_risk"] = [c.model_dump() for c in book.get_client_risk()]
        latest_state["scale"] = SIMULATION_SCALE
        latest_state["processed_trades_last_tick"] = len(all_trades)

        await asyncio.sleep(SIMULATION_INTERVAL_SECONDS)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(simulation_loop())


@app.get("/state")
def get_state():
    return latest_state

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Risk engine running",
    }