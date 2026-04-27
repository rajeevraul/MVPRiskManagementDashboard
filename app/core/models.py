from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator


class TradeSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class PriceTick(BaseModel):
    instrument: str = Field(..., min_length=1)
    bid: float = Field(..., gt=0)
    ask: float = Field(..., gt=0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @validator("ask")
    def ask_must_be_at_or_above_bid(cls, ask, values):
        bid = values.get("bid")
        if bid is not None and ask < bid:
            raise ValueError("ask must be greater than or equal to bid")
        return ask

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2

    @property
    def spread(self) -> float:
        return self.ask - self.bid


class Trade(BaseModel):
    trade_id: str = Field(..., min_length=1)
    client_id: str = Field(..., min_length=1)
    instrument: str = Field(..., min_length=1)
    side: TradeSide
    quantity: float = Field(..., gt=0)
    price: float = Field(..., ge=0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def value(self) -> float:
        return self.quantity * self.price


class Position(BaseModel):
    instrument: str = Field(..., min_length=1)
    net_quantity: float = 0.0
    average_price: float = Field(0.0, ge=0)
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0

    @property
    def total_pnl(self) -> float:
        return self.realized_pnl + self.unrealized_pnl
    
class ClientRisk(BaseModel):
    client_id: str
    positions: dict[str, float] = Field(default_factory=dict)
    gross_exposure: float = 0.0
    net_exposure: float = 0.0
    unrealized_pnl: float = 0.0
    alert_status: str = "NORMAL"


class DashboardSnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    prices: list[PriceTick] = Field(default_factory=list)
    trades: list[Trade] = Field(default_factory=list)
    positions: list[Position] = Field(default_factory=list)
    total_unrealized_pnl: float = 0.0
    total_realized_pnl: float = 0.0

    @root_validator(pre=True)
    def compute_totals(cls, values):
        positions = values.get("positions")
        if isinstance(positions, list):
            total_realized = sum(p.realized_pnl for p in positions)
            total_unrealized = sum(p.unrealized_pnl for p in positions)
            values["total_realized_pnl"] = total_realized
            values["total_unrealized_pnl"] = total_unrealized
        return values

    @property
    def total_pnl(self) -> float:
        return self.total_realized_pnl + self.total_unrealized_pnl

