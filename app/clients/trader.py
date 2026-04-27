import random
import uuid

from app.core.models import PriceTick, Trade, TradeSide


class ClientTrader:
    def __init__(self) -> None:
        self.clients = {
            "ALPHA_CAPITAL": {
                "activity": 0.45,
                "max_order_size": 500,
                "bias": "aggressive",
            },
            "NOVA_TRADING": {
                "activity": 0.35,
                "max_order_size": 350,
                "bias": "balanced",
            },
            "ORBIT_FUND": {
                "activity": 0.25,
                "max_order_size": 250,
                "bias": "mean_reversion",
            },
            "RETAIL_FLOW": {
                "activity": 0.65,
                "max_order_size": 80,
                "bias": "random",
            },
            "APEX_HEDGE": {
                "activity": 0.30,
                "max_order_size": 400,
                "bias": "momentum",
            },
        }

    def generate_trades(self, prices: list[PriceTick]) -> list[Trade]:
        trades: list[Trade] = []

        for tick in prices:
            for client_id, profile in self.clients.items():
                if random.random() > profile["activity"]:
                    continue

                side = self._choose_side(profile["bias"])
                execution_price = tick.ask if side == TradeSide.BUY else tick.bid
                quantity = random.randint(10, int(profile["max_order_size"]))

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

    def _choose_side(self, bias: str) -> TradeSide:
        if bias == "aggressive":
            return random.choices(
                [TradeSide.BUY, TradeSide.SELL],
                weights=[0.6, 0.4],
            )[0]

        if bias == "mean_reversion":
            return random.choices(
                [TradeSide.BUY, TradeSide.SELL],
                weights=[0.45, 0.55],
            )[0]

        if bias == "momentum":
            return random.choices(
                [TradeSide.BUY, TradeSide.SELL],
                weights=[0.55, 0.45],
            )[0]

        return random.choice([TradeSide.BUY, TradeSide.SELL])