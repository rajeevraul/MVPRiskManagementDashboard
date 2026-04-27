from app.core.models import ClientRisk, Position, PriceTick, Trade, TradeSide


class RiskBook:
    def __init__(self) -> None:
        self.positions: dict[str, Position] = {}
        self.client_positions: dict[str, dict[str, Position]] = {}

    def apply_trade(self, trade: Trade) -> None:
        signed_quantity = (
            -trade.quantity if trade.side == TradeSide.BUY else trade.quantity
        )

        self._apply_position(
            self.positions,
            trade.instrument,
            signed_quantity,
            trade.price,
        )

        if trade.client_id not in self.client_positions:
            self.client_positions[trade.client_id] = {}

        self._apply_position(
            self.client_positions[trade.client_id],
            trade.instrument,
            signed_quantity,
            trade.price,
        )

    def _apply_position(
        self,
        position_store: dict[str, Position],
        instrument: str,
        signed_quantity: float,
        trade_price: float,
    ) -> None:
        if instrument not in position_store:
            position_store[instrument] = Position(instrument=instrument)

        position = position_store[instrument]

        old_quantity = position.net_quantity
        new_quantity = old_quantity + signed_quantity

        if new_quantity == 0:
            position.average_price = 0.0
        elif old_quantity == 0 or (old_quantity > 0) == (signed_quantity > 0):
            total_cost = (
                position.average_price * abs(old_quantity)
                + trade_price * abs(signed_quantity)
            )
            position.average_price = total_cost / abs(new_quantity)

        position.net_quantity = new_quantity

    def apply_trades(self, trades: list[Trade]) -> None:
        for trade in trades:
            self.apply_trade(trade)

    def mark_to_market(self, prices: list[PriceTick]) -> None:
        price_map = {tick.instrument: tick.mid for tick in prices}

        self._mark_positions(self.positions, price_map)

        for positions in self.client_positions.values():
            self._mark_positions(positions, price_map)

    def _mark_positions(
        self,
        positions: dict[str, Position],
        price_map: dict[str, float],
    ) -> None:
        for instrument, position in positions.items():
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

    def get_client_risk(self) -> list[ClientRisk]:
        client_risks: list[ClientRisk] = []

        for client_id, positions in self.client_positions.items():
            gross_exposure = sum(
                abs(p.net_quantity * p.average_price)
                for p in positions.values()
            )

            net_exposure = sum(
                p.net_quantity * p.average_price
                for p in positions.values()
            )

            unrealized_pnl = sum(
                p.unrealized_pnl
                for p in positions.values()
            )

            alert_status = "NORMAL"

            if abs(unrealized_pnl) > 10000 or gross_exposure > 500000:
                alert_status = "BREACHED"
            elif abs(unrealized_pnl) > 5000 or gross_exposure > 300000:
                alert_status = "WARNING"

            client_risks.append(
                ClientRisk(
                    client_id=client_id,
                    positions={
                        instrument: position.net_quantity
                        for instrument, position in positions.items()
                    },
                    gross_exposure=gross_exposure,
                    net_exposure=net_exposure,
                    unrealized_pnl=unrealized_pnl,
                    alert_status=alert_status,
                )
            )

        return client_risks

    def total_unrealized_pnl(self) -> float:
        return sum(
            position.unrealized_pnl
            for position in self.positions.values()
        )