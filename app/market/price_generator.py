import random
from dataclasses import dataclass

from app.core.models import PriceTick


@dataclass
class InstrumentState:
    instrument: str
    mid_price: float
    spread: float
    volatility: float


class PriceGenerator:
    """
    Mock market data generator.

    Produces bid/ask prices using a controlled random walk.
    The goal is not realism — the goal is stable, moving market data.
    """

    def __init__(self) -> None:
        self.instruments: dict[str, InstrumentState] = {
            "AAPL": InstrumentState("AAPL", 150.25, 0.01, 0.50),
            "MSFT": InstrumentState("MSFT", 380.50, 0.02, 0.75),
            "GOOGL": InstrumentState("GOOGL", 140.30, 0.015, 0.60),
            "TSLA": InstrumentState("TSLA", 245.80, 0.05, 1.50),
        }

    def generate_tick(self, instrument: str) -> PriceTick:
        state = self.instruments[instrument]

        price_move = random.uniform(-state.volatility, state.volatility)
        state.mid_price = max(0.0001, state.mid_price + price_move)

        spread_noise = random.uniform(-0.2, 0.2) * state.spread
        current_spread = max(state.spread * 0.5, state.spread + spread_noise)

        bid = state.mid_price - current_spread / 2
        ask = state.mid_price + current_spread / 2

        return PriceTick(
            instrument=state.instrument,
            bid=round(bid, 5),
            ask=round(ask, 5),
        )

    def generate_snapshot(self) -> list[PriceTick]:
        return [
            self.generate_tick(instrument)
            for instrument in self.instruments
        ]