"""Money value object for the trading domain.

This module defines the Money value object following Domain-Driven Design principles.
Money represents a monetary amount with currency, ensuring type safety and business rules.
"""

from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Union
from dataclasses import dataclass


class Currency(Enum):
    """Supported currencies."""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CHF = "CHF"
    CAD = "CAD"
    AUD = "AUD"
    NZD = "NZD"
    BTC = "BTC"
    ETH = "ETH"


@dataclass(frozen=True)
class Money:
    """Money value object.
    
    Represents a monetary amount with currency.
    Immutable and ensures monetary arithmetic follows business rules.
    """
    
    amount: Decimal
    currency: Currency
    
    def __post_init__(self):
        """Validate money object after initialization."""
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, 'amount', Decimal(str(self.amount)))
        
        if not isinstance(self.currency, Currency):
            if isinstance(self.currency, str):
                object.__setattr__(self, 'currency', Currency(self.currency))
            else:
                raise ValueError(f"Invalid currency type: {type(self.currency)}")
        
        # Round to appropriate decimal places based on currency
        precision = self._get_currency_precision()
        rounded_amount = self.amount.quantize(Decimal('0.1') ** precision, rounding=ROUND_HALF_UP)
        object.__setattr__(self, 'amount', rounded_amount)
    
    @classmethod
    def zero(cls, currency: Union[Currency, str]) -> 'Money':
        """Create zero money amount.
        
        Args:
            currency: Currency for zero amount
            
        Returns:
            Money object with zero amount
        """
        if isinstance(currency, str):
            currency = Currency(currency)
        return cls(Decimal('0'), currency)
    
    @classmethod
    def from_float(cls, amount: float, currency: Union[Currency, str]) -> 'Money':
        """Create money from float amount.
        
        Args:
            amount: Float amount
            currency: Currency
            
        Returns:
            Money object
            
        Note:
            Use with caution due to floating-point precision issues.
        """
        if isinstance(currency, str):
            currency = Currency(currency)
        return cls(Decimal(str(amount)), currency)
    
    @classmethod
    def from_string(cls, amount: str, currency: Union[Currency, str]) -> 'Money':
        """Create money from string amount.
        
        Args:
            amount: String representation of amount
            currency: Currency
            
        Returns:
            Money object
        """
        if isinstance(currency, str):
            currency = Currency(currency)
        return cls(Decimal(amount), currency)
    
    def add(self, other: 'Money') -> 'Money':
        """Add two money amounts.
        
        Args:
            other: Money to add
            
        Returns:
            Sum of money amounts
            
        Raises:
            ValueError: If currencies don't match
        """
        self._validate_same_currency(other)
        return Money(self.amount + other.amount, self.currency)
    
    def subtract(self, other: 'Money') -> 'Money':
        """Subtract money amount.
        
        Args:
            other: Money to subtract
            
        Returns:
            Difference of money amounts
            
        Raises:
            ValueError: If currencies don't match
        """
        self._validate_same_currency(other)
        return Money(self.amount - other.amount, self.currency)
    
    def multiply(self, factor: Union[Decimal, int, float]) -> 'Money':
        """Multiply money by a factor.
        
        Args:
            factor: Multiplication factor
            
        Returns:
            Multiplied money amount
        """
        if not isinstance(factor, Decimal):
            factor = Decimal(str(factor))
        return Money(self.amount * factor, self.currency)
    
    def divide(self, divisor: Union[Decimal, int, float]) -> 'Money':
        """Divide money by a divisor.
        
        Args:
            divisor: Division divisor
            
        Returns:
            Divided money amount
            
        Raises:
            ValueError: If divisor is zero
        """
        if not isinstance(divisor, Decimal):
            divisor = Decimal(str(divisor))
        
        if divisor == 0:
            raise ValueError("Cannot divide by zero")
        
        return Money(self.amount / divisor, self.currency)
    
    def percentage(self, percent: Union[Decimal, int, float]) -> 'Money':
        """Calculate percentage of money amount.
        
        Args:
            percent: Percentage (e.g., 10 for 10%)
            
        Returns:
            Percentage of money amount
        """
        if not isinstance(percent, Decimal):
            percent = Decimal(str(percent))
        
        return self.multiply(percent / Decimal('100'))
    
    def abs(self) -> 'Money':
        """Get absolute value.
        
        Returns:
            Absolute money amount
        """
        return Money(abs(self.amount), self.currency)
    
    def negate(self) -> 'Money':
        """Negate money amount.
        
        Returns:
            Negated money amount
        """
        return Money(-self.amount, self.currency)
    
    def is_positive(self) -> bool:
        """Check if amount is positive.
        
        Returns:
            True if amount is positive
        """
        return self.amount > 0
    
    def is_negative(self) -> bool:
        """Check if amount is negative.
        
        Returns:
            True if amount is negative
        """
        return self.amount < 0
    
    def is_zero(self) -> bool:
        """Check if amount is zero.
        
        Returns:
            True if amount is zero
        """
        return self.amount == 0
    
    def compare_to(self, other: 'Money') -> int:
        """Compare money amounts.
        
        Args:
            other: Money to compare with
            
        Returns:
            -1 if less than, 0 if equal, 1 if greater than
            
        Raises:
            ValueError: If currencies don't match
        """
        self._validate_same_currency(other)
        
        if self.amount < other.amount:
            return -1
        elif self.amount > other.amount:
            return 1
        else:
            return 0
    
    def to_float(self) -> float:
        """Convert to float.
        
        Returns:
            Float representation of amount
            
        Note:
            Use with caution due to floating-point precision issues.
        """
        return float(self.amount)
    
    def to_string(self, include_currency: bool = True) -> str:
        """Convert to string representation.
        
        Args:
            include_currency: Whether to include currency symbol
            
        Returns:
            String representation
        """
        if include_currency:
            return f"{self.amount} {self.currency.value}"
        else:
            return str(self.amount)
    
    def format(self, decimal_places: int = None) -> str:
        """Format money with specific decimal places.
        
        Args:
            decimal_places: Number of decimal places (defaults to currency precision)
            
        Returns:
            Formatted string
        """
        if decimal_places is None:
            decimal_places = self._get_currency_precision()
        
        format_str = f"{{:.{decimal_places}f}} {{}}"
        return format_str.format(self.amount, self.currency.value)
    
    def _validate_same_currency(self, other: 'Money') -> None:
        """Validate that two money objects have the same currency.
        
        Args:
            other: Money object to compare currency with
            
        Raises:
            ValueError: If currencies don't match
        """
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot perform operation on different currencies: "
                f"{self.currency.value} and {other.currency.value}"
            )
    
    def _get_currency_precision(self) -> int:
        """Get decimal precision for currency.
        
        Returns:
            Number of decimal places for currency
        """
        # Most fiat currencies use 2 decimal places
        if self.currency in [Currency.USD, Currency.EUR, Currency.GBP, 
                           Currency.CHF, Currency.CAD, Currency.AUD, Currency.NZD]:
            return 2
        # Japanese Yen typically doesn't use decimal places
        elif self.currency == Currency.JPY:
            return 0
        # Cryptocurrencies typically use 8 decimal places
        elif self.currency in [Currency.BTC, Currency.ETH]:
            return 8
        else:
            return 2  # Default
    
    def __add__(self, other: 'Money') -> 'Money':
        """Add operator overload."""
        return self.add(other)
    
    def __sub__(self, other: 'Money') -> 'Money':
        """Subtract operator overload."""
        return self.subtract(other)
    
    def __mul__(self, factor: Union[Decimal, int, float]) -> 'Money':
        """Multiply operator overload."""
        return self.multiply(factor)
    
    def __rmul__(self, factor: Union[Decimal, int, float]) -> 'Money':
        """Right multiply operator overload."""
        return self.multiply(factor)
    
    def __truediv__(self, divisor: Union[Decimal, int, float]) -> 'Money':
        """Divide operator overload."""
        return self.divide(divisor)
    
    def __neg__(self) -> 'Money':
        """Negate operator overload."""
        return self.negate()
    
    def __abs__(self) -> 'Money':
        """Absolute value operator overload."""
        return self.abs()
    
    def __lt__(self, other: 'Money') -> bool:
        """Less than operator overload."""
        return self.compare_to(other) < 0
    
    def __le__(self, other: 'Money') -> bool:
        """Less than or equal operator overload."""
        return self.compare_to(other) <= 0
    
    def __gt__(self, other: 'Money') -> bool:
        """Greater than operator overload."""
        return self.compare_to(other) > 0
    
    def __ge__(self, other: 'Money') -> bool:
        """Greater than or equal operator overload."""
        return self.compare_to(other) >= 0
    
    def __eq__(self, other) -> bool:
        """Equality operator overload."""
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount and self.currency == other.currency
    
    def __hash__(self) -> int:
        """Hash function."""
        return hash((self.amount, self.currency))
    
    def __str__(self) -> str:
        """String representation."""
        return self.to_string()
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Money(amount={self.amount}, currency={self.currency.value})"