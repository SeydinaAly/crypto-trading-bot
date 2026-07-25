from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import pandas as pd
from logger import logger
from config import MIN_PROFIT_PERCENT, STOP_LOSS_PERCENT, MAX_DAILY_LOSS_PERCENT

class TradingStrategy:
    """Base trading strategy class"""
    
    def __init__(self, exchange_connector):
        self.exchange = exchange_connector
        self.trade_history = []
        self.daily_loss = 0
    
    def should_trade(self, from_token: str, to_token: str, amount: float) -> Tuple[bool, str]:
        """Determine if a trade should be executed"""
        raise NotImplementedError

class DCAStrategy(TradingStrategy):
    """Dollar Cost Averaging Strategy"""
    
    def __init__(self, exchange_connector, interval_seconds: int = 3600):
        super().__init__(exchange_connector)
        self.last_trade_time = None
        self.interval = timedelta(seconds=interval_seconds)
        self.strategy_name = "DCA"
    
    def should_trade(self, from_token: str, to_token: str, amount: float) -> Tuple[bool, str]:
        """Check if enough time has passed since last trade"""
        now = datetime.now()
        
        if self.last_trade_time is None:
            self.last_trade_time = now
            logger.info(f"📊 {self.strategy_name}: First trade initiated")
            return True, "First trade"
        
        time_since_last = now - self.last_trade_time
        
        if time_since_last >= self.interval:
            self.last_trade_time = now
            logger.info(f"📊 {self.strategy_name}: Interval reached ({time_since_last.seconds}s)")
            return True, f"Interval reached ({time_since_last.seconds}s)"
        
        minutes_remaining = ((self.interval - time_since_last).total_seconds() / 60)
        return False, f"Wait {minutes_remaining:.1f} minutes"

class ArbitrageStrategy(TradingStrategy):
    """Arbitrage Strategy - Exploit price differences"""
    
    def __init__(self, exchange_connector, min_profit_percent: float = 2):
        super().__init__(exchange_connector)
        self.min_profit = min_profit_percent
        self.strategy_name = "Arbitrage"
    
    def should_trade(self, from_token: str, to_token: str, amount: float) -> Tuple[bool, str]:
        """Check if arbitrage opportunity exists"""
        try:
            # Estimate the swap
            estimate = self.exchange.estimate_swap(from_token, to_token, amount)
            
            if not estimate:
                return False, "Cannot estimate swap"
            
            # Calculate potential profit
            output = estimate.get('output_amount', 0)
            gas_cost = estimate.get('gas_cost_usd', 0)
            profit = output - amount - gas_cost
            profit_percent = (profit / amount * 100) if amount > 0 else 0
            
            if profit_percent >= self.min_profit:
                logger.info(f"📊 {self.strategy_name}: Opportunity found! Profit: {profit_percent:.2f}%")
                return True, f"Profit: {profit_percent:.2f}%"
            
            logger.debug(f"📊 {self.strategy_name}: Not profitable ({profit_percent:.2f}%)")
            return False, f"Profit too low ({profit_percent:.2f}%)"
        
        except Exception as e:
            logger.error(f"Arbitrage check failed: {str(e)}")
            return False, str(e)

class TechnicalAnalysisStrategy(TradingStrategy):
    """Technical Analysis Strategy - Based on price movements"""
    
    def __init__(self, exchange_connector, lookback_hours: int = 24):
        super().__init__(exchange_connector)
        self.lookback = timedelta(hours=lookback_hours)
        self.price_history = {}
        self.strategy_name = "Technical Analysis"
    
    def should_trade(self, from_token: str, to_token: str, amount: float) -> Tuple[bool, str]:
        """
        Check if technical indicators suggest a trade
        Simplified: Buy if price has fallen 5% in last 24h
        """
        try:
            # This would normally use actual price history
            # For demo, we'll use a simplified approach
            logger.info(f"📊 {self.strategy_name}: Checking indicators")
            
            # In production, integrate with:
            # - Moving averages (MA50, MA200)
            # - RSI (Relative Strength Index)
            # - MACD
            # - Bollinger Bands
            # - Volume analysis
            
            return False, "Demo mode - implement TA indicators"
        
        except Exception as e:
            logger.error(f"Technical analysis failed: {str(e)}")
            return False, str(e)

class HybridStrategy(TradingStrategy):
    """Hybrid Strategy - Combine multiple strategies"""
    
    def __init__(self, exchange_connector, strategies: List[TradingStrategy]):
        super().__init__(exchange_connector)
        self.strategies = strategies
        self.strategy_name = "Hybrid"
    
    def should_trade(self, from_token: str, to_token: str, amount: float) -> Tuple[bool, str]:
        """Execute trade only if all strategies agree"""
        results = []
        
        for strategy in self.strategies:
            should_trade, reason = strategy.should_trade(from_token, to_token, amount)
            results.append((strategy.strategy_name, should_trade, reason))
        
        all_agree = all(result[1] for result in results)
        
        reasons = " | ".join([f"{r[0]}: {r[2]}" for r in results])
        logger.info(f"📊 {self.strategy_name}: {reasons}")
        
        return all_agree, reasons

class StrategyFactory:
    """Factory to create trading strategies"""
    
    @staticmethod
    def create_strategy(strategy_type: str, exchange_connector, **kwargs) -> TradingStrategy:
        """Create a trading strategy by type"""
        
        if strategy_type.lower() == "dca":
            interval = kwargs.get('interval_seconds', 3600)
            return DCAStrategy(exchange_connector, interval)
        
        elif strategy_type.lower() == "arbitrage":
            min_profit = kwargs.get('min_profit_percent', 2)
            return ArbitrageStrategy(exchange_connector, min_profit)
        
        elif strategy_type.lower() == "technical_analysis":
            lookback = kwargs.get('lookback_hours', 24)
            return TechnicalAnalysisStrategy(exchange_connector, lookback)
        
        elif strategy_type.lower() == "hybrid":
            strategies = kwargs.get('strategies', [])
            return HybridStrategy(exchange_connector, strategies)
        
        else:
            logger.error(f"Unknown strategy: {strategy_type}")
            raise ValueError(f"Unknown strategy: {strategy_type}")

if __name__ == "__main__":
    # Test strategies
    from exchange_connector import ExchangeConnector
    
    connector = ExchangeConnector()
    
    # DCA Strategy
    dca = StrategyFactory.create_strategy("dca", connector, interval_seconds=60)
    should_trade, reason = dca.should_trade("USDC", "ETH", 100)
    print(f"DCA - Should trade: {should_trade} ({reason})")
    
    # Arbitrage Strategy
    arb = StrategyFactory.create_strategy("arbitrage", connector, min_profit_percent=2)
    should_trade, reason = arb.should_trade("USDC", "ETH", 100)
    print(f"Arbitrage - Should trade: {should_trade} ({reason})")
