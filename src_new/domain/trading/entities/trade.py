"""Trade entity for the trading domain.

This module defines the core Trade entity following Domain-Driven Design principles.
The Trade entity encapsulates all business logic related to individual trades.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from ..value_objects.trade_id import TradeId
from ..value_objects.asset_symbol import AssetSymbol
from ..value_objects.money import Money
from ..events.trade_events import (
    TradeCreated,
    TradeExecuted,
    TradeClosed,
    TradeModified
)


class TradeStatus(Enum):
    """Trade status enumeration."""
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class TradeDirection(Enum):
    """Trade direction enumeration."""
    CALL = "call"  # Higher/Up prediction
    PUT = "put"    # Lower/Down prediction


class TradeResult(Enum):
    """Trade result enumeration."""
    WIN = "win"
    LOSS = "loss"
    TIE = "tie"
    PENDING = "pending"


@dataclass(frozen=True)
class TradeExecution:
    """Trade execution details."""
    executed_at: datetime
    execution_price: Decimal
    execution_id: str
    platform_trade_id: Optional[str] = None


@dataclass(frozen=True)
class TradeClosure:
    """Trade closure details."""
    closed_at: datetime
    closing_price: Decimal
    result: TradeResult
    payout_amount: Optional[Money] = None
    profit_loss: Optional[Money] = None


class Trade:
    """Trade aggregate root.
    
    Represents a single trading position with complete lifecycle management.
    Encapsulates all business rules and invariants for trades.
    """
    
    def __init__(
        self,
        trade_id: TradeId,
        asset_symbol: AssetSymbol,
        direction: TradeDirection,
        stake_amount: Money,
        expiry_time: datetime,
        strategy_id: Optional[str] = None,
        signal_strength: Optional[str] = None
    ):
        """Initialize a new trade.
        
        Args:
            trade_id: Unique trade identifier
            asset_symbol: Asset being traded
            direction: Trade direction (CALL/PUT)
            stake_amount: Amount being staked
            expiry_time: When the trade expires
            strategy_id: Strategy that generated this trade
            signal_strength: Strength of the trading signal
            
        Raises:
            ValueError: If trade parameters are invalid
        """
        self._validate_trade_parameters(stake_amount, expiry_time)
        
        self._trade_id = trade_id
        self._asset_symbol = asset_symbol
        self._direction = direction
        self._stake_amount = stake_amount
        self._expiry_time = expiry_time
        self._strategy_id = strategy_id
        self._signal_strength = signal_strength
        
        self._status = TradeStatus.PENDING
        self._created_at = datetime.utcnow()
        self._execution: Optional[TradeExecution] = None
        self._closure: Optional[TradeClosure] = None
        self._entry_price: Optional[Decimal] = None
        
        # Domain events
        self._domain_events: List = []
        self._add_domain_event(
            TradeCreated(
                trade_id=self._trade_id,
                asset_symbol=self._asset_symbol,
                direction=self._direction,
                stake_amount=self._stake_amount,
                expiry_time=self._expiry_time,
                created_at=self._created_at
            )
        )
    
    @property
    def trade_id(self) -> TradeId:
        """Get trade ID."""
        return self._trade_id
    
    @property
    def asset_symbol(self) -> AssetSymbol:
        """Get asset symbol."""
        return self._asset_symbol
    
    @property
    def direction(self) -> TradeDirection:
        """Get trade direction."""
        return self._direction
    
    @property
    def stake_amount(self) -> Money:
        """Get stake amount."""
        return self._stake_amount
    
    @property
    def expiry_time(self) -> datetime:
        """Get expiry time."""
        return self._expiry_time
    
    @property
    def status(self) -> TradeStatus:
        """Get trade status."""
        return self._status
    
    @property
    def created_at(self) -> datetime:
        """Get creation timestamp."""
        return self._created_at
    
    @property
    def execution(self) -> Optional[TradeExecution]:
        """Get execution details."""
        return self._execution
    
    @property
    def closure(self) -> Optional[TradeClosure]:
        """Get closure details."""
        return self._closure
    
    @property
    def entry_price(self) -> Optional[Decimal]:
        """Get entry price."""
        return self._entry_price
    
    @property
    def is_open(self) -> bool:
        """Check if trade is open."""
        return self._status == TradeStatus.OPEN
    
    @property
    def is_closed(self) -> bool:
        """Check if trade is closed."""
        return self._status in [TradeStatus.CLOSED, TradeStatus.CANCELLED, TradeStatus.EXPIRED]
    
    @property
    def is_profitable(self) -> Optional[bool]:
        """Check if trade is profitable."""
        if not self._closure:
            return None
        return self._closure.result == TradeResult.WIN
    
    @property
    def duration_seconds(self) -> Optional[int]:
        """Get trade duration in seconds."""
        if not self._execution or not self._closure:
            return None
        return int((self._closure.closed_at - self._execution.executed_at).total_seconds())
    
    def execute(self, execution_price: Decimal, execution_id: str, platform_trade_id: Optional[str] = None) -> None:
        """Execute the trade.
        
        Args:
            execution_price: Price at which trade was executed
            execution_id: Unique execution identifier
            platform_trade_id: Platform-specific trade ID
            
        Raises:
            ValueError: If trade cannot be executed
        """
        if self._status != TradeStatus.PENDING:
            raise ValueError(f"Cannot execute trade in status: {self._status}")
        
        if execution_price <= 0:
            raise ValueError("Execution price must be positive")
        
        executed_at = datetime.utcnow()
        
        self._execution = TradeExecution(
            executed_at=executed_at,
            execution_price=execution_price,
            execution_id=execution_id,
            platform_trade_id=platform_trade_id
        )
        self._entry_price = execution_price
        self._status = TradeStatus.OPEN
        
        self._add_domain_event(
            TradeExecuted(
                trade_id=self._trade_id,
                execution_price=execution_price,
                executed_at=executed_at,
                execution_id=execution_id
            )
        )
    
    def close(self, closing_price: Decimal, result: TradeResult, payout_amount: Optional[Money] = None) -> None:
        """Close the trade.
        
        Args:
            closing_price: Price at which trade was closed
            result: Trade result (WIN/LOSS/TIE)
            payout_amount: Payout amount if trade won
            
        Raises:
            ValueError: If trade cannot be closed
        """
        if self._status != TradeStatus.OPEN:
            raise ValueError(f"Cannot close trade in status: {self._status}")
        
        if closing_price <= 0:
            raise ValueError("Closing price must be positive")
        
        closed_at = datetime.utcnow()
        
        # Calculate profit/loss
        profit_loss = self._calculate_profit_loss(result, payout_amount)
        
        self._closure = TradeClosure(
            closed_at=closed_at,
            closing_price=closing_price,
            result=result,
            payout_amount=payout_amount,
            profit_loss=profit_loss
        )
        self._status = TradeStatus.CLOSED
        
        self._add_domain_event(
            TradeClosed(
                trade_id=self._trade_id,
                closing_price=closing_price,
                result=result,
                closed_at=closed_at,
                profit_loss=profit_loss
            )
        )
    
    def cancel(self, reason: str) -> None:
        """Cancel the trade.
        
        Args:
            reason: Cancellation reason
            
        Raises:
            ValueError: If trade cannot be cancelled
        """
        if self._status not in [TradeStatus.PENDING, TradeStatus.OPEN]:
            raise ValueError(f"Cannot cancel trade in status: {self._status}")
        
        self._status = TradeStatus.CANCELLED
        
        # Add cancellation event
        # (Implementation would include a TradeCancelled event)
    
    def expire(self) -> None:
        """Mark trade as expired.
        
        Raises:
            ValueError: If trade cannot be expired
        """
        if self._status != TradeStatus.PENDING:
            raise ValueError(f"Cannot expire trade in status: {self._status}")
        
        if datetime.utcnow() < self._expiry_time:
            raise ValueError("Trade has not yet reached expiry time")
        
        self._status = TradeStatus.EXPIRED
    
    def modify_stake(self, new_stake_amount: Money) -> None:
        """Modify stake amount (only for pending trades).
        
        Args:
            new_stake_amount: New stake amount
            
        Raises:
            ValueError: If trade cannot be modified
        """
        if self._status != TradeStatus.PENDING:
            raise ValueError(f"Cannot modify trade in status: {self._status}")
        
        if new_stake_amount.amount <= 0:
            raise ValueError("Stake amount must be positive")
        
        old_stake = self._stake_amount
        self._stake_amount = new_stake_amount
        
        self._add_domain_event(
            TradeModified(
                trade_id=self._trade_id,
                field="stake_amount",
                old_value=old_stake,
                new_value=new_stake_amount,
                modified_at=datetime.utcnow()
            )
        )
    
    def get_domain_events(self) -> List:
        """Get domain events."""
        return self._domain_events.copy()
    
    def clear_domain_events(self) -> None:
        """Clear domain events."""
        self._domain_events.clear()
    
    def _validate_trade_parameters(self, stake_amount: Money, expiry_time: datetime) -> None:
        """Validate trade parameters.
        
        Args:
            stake_amount: Stake amount to validate
            expiry_time: Expiry time to validate
            
        Raises:
            ValueError: If parameters are invalid
        """
        if stake_amount.amount <= 0:
            raise ValueError("Stake amount must be positive")
        
        if expiry_time <= datetime.utcnow():
            raise ValueError("Expiry time must be in the future")
    
    def _calculate_profit_loss(self, result: TradeResult, payout_amount: Optional[Money]) -> Money:
        """Calculate profit/loss for the trade.
        
        Args:
            result: Trade result
            payout_amount: Payout amount if won
            
        Returns:
            Profit/loss amount
        """
        if result == TradeResult.WIN and payout_amount:
            return Money(payout_amount.amount - self._stake_amount.amount, self._stake_amount.currency)
        elif result == TradeResult.TIE:
            return Money(Decimal('0'), self._stake_amount.currency)
        else:  # LOSS
            return Money(-self._stake_amount.amount, self._stake_amount.currency)
    
    def _add_domain_event(self, event) -> None:
        """Add domain event.
        
        Args:
            event: Domain event to add
        """
        self._domain_events.append(event)
    
    def __eq__(self, other) -> bool:
        """Check equality based on trade ID."""
        if not isinstance(other, Trade):
            return False
        return self._trade_id == other._trade_id
    
    def __hash__(self) -> int:
        """Hash based on trade ID."""
        return hash(self._trade_id)
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Trade(id={self._trade_id}, asset={self._asset_symbol}, "
            f"direction={self._direction}, stake={self._stake_amount}, "
            f"status={self._status})"
        )