"""Execute trade use case.

This module implements the Execute Trade use case following Clean Architecture principles.
It orchestrates the execution of a trade through the domain layer and infrastructure.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Protocol
from dataclasses import dataclass
from uuid import UUID

from ....domain.trading.entities.trade import Trade, TradeDirection
from ....domain.trading.value_objects.trade_id import TradeId
from ....domain.trading.value_objects.asset_symbol import AssetSymbol
from ....domain.trading.value_objects.money import Money, Currency
from ....domain.trading.repositories.trade_repository import TradeRepository
from ....domain.trading.services.risk_management_service import RiskManagementService
from ....domain.market_data.services.price_service import PriceService
from ....domain.platform_integration.services.trading_platform_service import TradingPlatformService
from ...shared.events.event_bus import EventBus
from ...shared.logging.logger import Logger
from ...shared.exceptions import (
    ValidationError,
    BusinessRuleViolationError,
    InfrastructureError
)


@dataclass(frozen=True)
class ExecuteTradeCommand:
    """Command to execute a trade."""
    asset_symbol: str
    direction: str  # "call" or "put"
    stake_amount: Decimal
    stake_currency: str
    expiry_time: datetime
    strategy_id: Optional[str] = None
    signal_strength: Optional[str] = None
    user_id: Optional[str] = None


@dataclass(frozen=True)
class ExecuteTradeResult:
    """Result of trade execution."""
    trade_id: str
    success: bool
    execution_price: Optional[Decimal] = None
    execution_time: Optional[datetime] = None
    platform_trade_id: Optional[str] = None
    error_message: Optional[str] = None


class ExecuteTradeUseCase:
    """Use case for executing trades.
    
    This use case orchestrates the complete trade execution process:
    1. Validates the trade request
    2. Checks risk management rules
    3. Gets current market price
    4. Creates and persists the trade
    5. Executes the trade on the platform
    6. Updates trade status
    7. Publishes domain events
    """
    
    def __init__(
        self,
        trade_repository: TradeRepository,
        risk_management_service: RiskManagementService,
        price_service: PriceService,
        trading_platform_service: TradingPlatformService,
        event_bus: EventBus,
        logger: Logger
    ):
        """Initialize the use case with required dependencies.
        
        Args:
            trade_repository: Repository for trade persistence
            risk_management_service: Service for risk validation
            price_service: Service for market data
            trading_platform_service: Service for platform integration
            event_bus: Event bus for publishing domain events
            logger: Logger for audit trail
        """
        self._trade_repository = trade_repository
        self._risk_management_service = risk_management_service
        self._price_service = price_service
        self._trading_platform_service = trading_platform_service
        self._event_bus = event_bus
        self._logger = logger
    
    async def execute(self, command: ExecuteTradeCommand) -> ExecuteTradeResult:
        """Execute a trade based on the provided command.
        
        Args:
            command: Trade execution command
            
        Returns:
            Result of trade execution
            
        Raises:
            ValidationError: If command validation fails
            BusinessRuleViolationError: If business rules are violated
            InfrastructureError: If external service fails
        """
        try:
            self._logger.info(
                f"Starting trade execution for {command.asset_symbol} "
                f"{command.direction} {command.stake_amount} {command.stake_currency}"
            )
            
            # 1. Validate command
            self._validate_command(command)
            
            # 2. Create domain objects
            trade_id = TradeId.generate()
            asset_symbol = AssetSymbol(command.asset_symbol)
            direction = TradeDirection(command.direction.lower())
            stake_amount = Money(command.stake_amount, Currency(command.stake_currency))
            
            # 3. Check risk management rules
            await self._validate_risk_rules(stake_amount, command.user_id)
            
            # 4. Get current market price
            current_price = await self._get_current_price(asset_symbol)
            
            # 5. Create trade entity
            trade = Trade(
                trade_id=trade_id,
                asset_symbol=asset_symbol,
                direction=direction,
                stake_amount=stake_amount,
                expiry_time=command.expiry_time,
                strategy_id=command.strategy_id,
                signal_strength=command.signal_strength
            )
            
            # 6. Persist trade
            await self._trade_repository.save(trade)
            
            # 7. Execute trade on platform
            execution_result = await self._execute_on_platform(trade, current_price)
            
            # 8. Update trade with execution details
            trade.execute(
                execution_price=execution_result.execution_price,
                execution_id=execution_result.execution_id,
                platform_trade_id=execution_result.platform_trade_id
            )
            
            # 9. Update persisted trade
            await self._trade_repository.save(trade)
            
            # 10. Publish domain events
            await self._publish_domain_events(trade)
            
            self._logger.info(
                f"Trade executed successfully: {trade_id} at price {execution_result.execution_price}"
            )
            
            return ExecuteTradeResult(
                trade_id=str(trade_id),
                success=True,
                execution_price=execution_result.execution_price,
                execution_time=execution_result.execution_time,
                platform_trade_id=execution_result.platform_trade_id
            )
            
        except ValidationError as e:
            self._logger.warning(f"Trade execution validation failed: {e}")
            return ExecuteTradeResult(
                trade_id="",
                success=False,
                error_message=f"Validation error: {e}"
            )
            
        except BusinessRuleViolationError as e:
            self._logger.warning(f"Trade execution business rule violation: {e}")
            return ExecuteTradeResult(
                trade_id="",
                success=False,
                error_message=f"Business rule violation: {e}"
            )
            
        except InfrastructureError as e:
            self._logger.error(f"Trade execution infrastructure error: {e}")
            return ExecuteTradeResult(
                trade_id="",
                success=False,
                error_message=f"Infrastructure error: {e}"
            )
            
        except Exception as e:
            self._logger.error(f"Unexpected error during trade execution: {e}")
            return ExecuteTradeResult(
                trade_id="",
                success=False,
                error_message=f"Unexpected error: {e}"
            )
    
    def _validate_command(self, command: ExecuteTradeCommand) -> None:
        """Validate the execute trade command.
        
        Args:
            command: Command to validate
            
        Raises:
            ValidationError: If validation fails
        """
        if not command.asset_symbol:
            raise ValidationError("Asset symbol is required")
        
        if command.direction.lower() not in ["call", "put"]:
            raise ValidationError("Direction must be 'call' or 'put'")
        
        if command.stake_amount <= 0:
            raise ValidationError("Stake amount must be positive")
        
        if command.expiry_time <= datetime.utcnow():
            raise ValidationError("Expiry time must be in the future")
        
        try:
            Currency(command.stake_currency)
        except ValueError:
            raise ValidationError(f"Invalid currency: {command.stake_currency}")
    
    async def _validate_risk_rules(self, stake_amount: Money, user_id: Optional[str]) -> None:
        """Validate risk management rules.
        
        Args:
            stake_amount: Amount being staked
            user_id: User making the trade
            
        Raises:
            BusinessRuleViolationError: If risk rules are violated
        """
        # Check maximum stake amount
        if not await self._risk_management_service.is_stake_amount_allowed(stake_amount, user_id):
            raise BusinessRuleViolationError("Stake amount exceeds risk limits")
        
        # Check daily trading limits
        if not await self._risk_management_service.is_daily_limit_available(user_id):
            raise BusinessRuleViolationError("Daily trading limit exceeded")
        
        # Check concurrent trades limit
        if not await self._risk_management_service.is_concurrent_trades_allowed(user_id):
            raise BusinessRuleViolationError("Maximum concurrent trades exceeded")
    
    async def _get_current_price(self, asset_symbol: AssetSymbol) -> Decimal:
        """Get current market price for asset.
        
        Args:
            asset_symbol: Asset to get price for
            
        Returns:
            Current market price
            
        Raises:
            InfrastructureError: If price service fails
        """
        try:
            price = await self._price_service.get_current_price(asset_symbol)
            if price is None:
                raise InfrastructureError(f"No price available for {asset_symbol}")
            return price
        except Exception as e:
            raise InfrastructureError(f"Failed to get current price: {e}")
    
    async def _execute_on_platform(self, trade: Trade, current_price: Decimal) -> 'PlatformExecutionResult':
        """Execute trade on trading platform.
        
        Args:
            trade: Trade to execute
            current_price: Current market price
            
        Returns:
            Platform execution result
            
        Raises:
            InfrastructureError: If platform execution fails
        """
        try:
            result = await self._trading_platform_service.execute_trade(
                asset_symbol=trade.asset_symbol,
                direction=trade.direction,
                stake_amount=trade.stake_amount,
                expiry_time=trade.expiry_time,
                current_price=current_price
            )
            return result
        except Exception as e:
            raise InfrastructureError(f"Failed to execute trade on platform: {e}")
    
    async def _publish_domain_events(self, trade: Trade) -> None:
        """Publish domain events from the trade.
        
        Args:
            trade: Trade with domain events to publish
        """
        events = trade.get_domain_events()
        for event in events:
            await self._event_bus.publish(event)
        
        trade.clear_domain_events()


@dataclass(frozen=True)
class PlatformExecutionResult:
    """Result from platform trade execution."""
    execution_price: Decimal
    execution_time: datetime
    execution_id: str
    platform_trade_id: Optional[str] = None