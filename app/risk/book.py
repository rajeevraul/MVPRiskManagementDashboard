from app.core.models import Position, PriceTick, Trade, TradeSide


class RiskBook:
    """
    Tracks our book after client trades.

    Important rule:
    - Client BUY means we SELL, so our position decreases.
    - Client SELL means we BUY, so our position increases.
    """

    def __init__(self) -> None:
        self.positions: dict[str, Position] = {}

    def apply_trade(self, trade: Trade) -> None:
        if trade.instrument not in self.positions:
            self.positions[trade.instrument] = Position(instrument=trade.instrument)

        position = self.positions[trade.instrument]

        signed_quantity = (
            -trade.quantity if trade.side == TradeSide.BUY else trade.quantity
        )

        old_quantity = position.net_quantity
        new_quantity = old_quantity + signed_quantity

        if new_quantity == 0:
            position.average_price = 0.0
        elif old_quantity == 0 or (old_quantity > 0) == (signed_quantity > 0):
            total_cost = (
                position.average_price * abs(old_quantity)
                + trade.price * abs(signed_quantity)
            )
            position.average_price = total_cost / abs(new_quantity)

        position.net_quantity = new_quantity

    def apply_trades(self, trades: list[Trade]) -> None:
        for trade in trades:
            self.apply_trade(trade)

    def mark_to_market(self, prices: list[PriceTick]) -> None:
        price_map = {tick.instrument: tick.mid for tick in prices}

        for instrument, position in self.positions.items():
            if instrument not in price_map:
                continue

            market_price = price_map[instrument]

            if position.net_quantity > 0:
                position.unrealized_pnl = (
                    market_price - position.average_price
                ) * position.net_quantity
            elif position.net_quantity < 0:
                position.unrealized_pnl = (
                    position.average_price - market_price
                ) * abs(position.net_quantity)
            else:
                position.unrealized_pnl = 0.0

    def get_positions(self) -> list[Position]:
        return list(self.positions.values())

    def total_unrealized_pnl(self) -> float:
        return sum(position.unrealized_pnl for position in self.positions.values())