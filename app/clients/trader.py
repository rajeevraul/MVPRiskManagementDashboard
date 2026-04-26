import random
import uuid

from app.core.models import PriceTick, Trade, TradeSide


class ClientTrader:
    """
    Mock client trading engine.

    Clients see our bid/ask prices and occasionally trade.
    If client buys, we sell to them.
    If client sells, we buy from them.
    """

    def __init__(self) -> None:
        self.clients = {
            "ALPHA_CAPITAL": {"activity": 0.45, "size_multiplier": 1.5},
            "NOVA_TRADING": {"activity": 0.30, "size_multiplier": 1.0},
            "ORBIT_FUND": {"activity": 0.20, "size_multiplier": 0.8},
            "RETAIL_FLOW": {"activity": 0.60, "size_multiplier": 0.3},
        }

    def generate_trades(self, prices: list[PriceTick]) -> list[Trade]:
        trades: list[Trade] = []

        for tick in prices:
            for client_id, profile in self.clients.items():
                if random.random() > profile["activity"]:
                    continue

                side = random.choice([TradeSide.BUY, TradeSide.SELL])

                # Client buys at our ask, client sells at our bid
                execution_price = tick.ask if side == TradeSide.BUY else tick.bid

                quantity = random.randint(10, 200) * profile["size_multiplier"]

                trades.append(
                    Trade(
                        trade_id=str(uuid.uuid4()),
                        client_id=client_id,
                        instrument=tick.instrument,
                        side=side,
                        quantity=quantity,
                        price=execution_price,
                    )
                )

        return trades