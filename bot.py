import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from config import (
    PRIVATE_KEY, TRADE_AMOUNT, TRADE_INTERVAL,
    STRATEGY, MIN_PROFIT_PERCENT, TRADING_PAIR,
    MAX_DAILY_LOSS_PERCENT, STOP_LOSS_PERCENT
)
from exchange_connector import ExchangeConnector
from strategies import StrategyFactory
from portfolio import Portfolio
from alerts import alert_manager
from logger import logger

class TradingBot:
    """Main trading bot orchestrator"""
    
    def __init__(self):
        logger.info("🤖 Initializing Trading Bot...")
        
        # Initialize components
        self.exchange = ExchangeConnector(PRIVATE_KEY)
        self.portfolio = Portfolio()
        self.strategy = StrategyFactory.create_strategy(
            STRATEGY,
            self.exchange,
            interval_seconds=TRADE_INTERVAL,
            min_profit_percent=MIN_PROFIT_PERCENT
        )
        
        # Trading state
        self.is_running = False
        self.daily_loss = 0
        self.last_reset = datetime.now()
        self.trade_count = 0
        self.scheduler = BackgroundScheduler()
        
        # Parse trading pair
        self.from_token, self.to_token = TRADING_PAIR.split('/')
        
        logger.info(f"✅ Bot initialized with {STRATEGY} strategy")
        logger.info(f"📊 Trading pair: {self.from_token} → {self.to_token}")
        logger.info(f"💰 Trade amount: {TRADE_AMOUNT} {self.from_token}")
    
    def start(self):
        """Start the trading bot"""
        if self.is_running:
            logger.warning("Bot is already running")
            return
        
        self.is_running = True
        logger.info("🚀 Starting bot...")
        
        # Schedule trading
        self.scheduler.add_job(
            self.execute_trade_cycle,
            'interval',
            seconds=TRADE_INTERVAL,
            id='trading_job'
        )
        
        # Schedule health check
        self.scheduler.add_job(
            self.health_check,
            'interval',
            seconds=300,  # Every 5 minutes
            id='health_check'
        )
        
        # Schedule daily reset
        self.scheduler.add_job(
            self.reset_daily_limits,
            'cron',
            hour=0,
            minute=0,
            id='daily_reset'
        )
        
        self.scheduler.start()
        alert_manager.send_alert(
            "🤖 Bot Started",
            f"Trading bot started with {STRATEGY} strategy\nPair: {TRADING_PAIR}\nAmount: {TRADE_AMOUNT}",
            "info"
        )
        
        try:
            # Keep the bot running
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the trading bot"""
        logger.info("⛔ Stopping bot...")
        self.is_running = False
        
        if self.scheduler.running:
            self.scheduler.shutdown()
        
        alert_manager.send_alert(
            "🛑 Bot Stopped",
            f"Trading bot stopped\nTotal trades: {self.trade_count}",
            "info"
        )
        logger.info(f"✅ Bot stopped. Total trades: {self.trade_count}")
    
    def execute_trade_cycle(self):
        """Execute one trading cycle"""
        try:
            logger.info("🔄 Executing trade cycle...")
            
            # Check daily loss limit
            if self.daily_loss > 0 and self.daily_loss >= (self.portfolio.calculate_total_spent() * MAX_DAILY_LOSS_PERCENT / 100):
                logger.error(f"❌ Daily loss limit reached ({self.daily_loss})")
                alert_manager.send_alert(
                    "⚠️  Daily Loss Limit",
                    f"Daily loss limit reached: ${self.daily_loss:.2f}",
                    "warning"
                )
                return
            
            # Check if strategy says to trade
            should_trade, reason = self.strategy.should_trade(
                self.from_token,
                self.to_token,
                TRADE_AMOUNT
            )
            
            if not should_trade:
                logger.debug(f"⏭️  Trade skipped: {reason}")
                return
            
            # Get price estimate
            estimate = self.exchange.estimate_swap(
                self.from_token,
                self.to_token,
                TRADE_AMOUNT
            )
            
            if not estimate:
                logger.error("Failed to estimate swap")
                return
            
            # Check profitability
            if not self.exchange.is_profitable(
                TRADE_AMOUNT,
                estimate['output_amount'],
                estimate['gas_cost_usd'],
                MIN_PROFIT_PERCENT
            ):
                logger.info("Trade not profitable, skipping")
                return
            
            # Check slippage
            if not self.exchange.check_slippage(estimate):
                logger.warning("Slippage too high, skipping trade")
                return
            
            # Execute trade (in production, this would send actual transaction)
            self.execute_trade(estimate)
            
            self.trade_count += 1
            
        except Exception as e:
            logger.error(f"Trade cycle failed: {str(e)}", exc_info=True)
            alert_manager.send_alert(
                "❌ Trade Error",
                f"Trade cycle failed: {str(e)}",
                "error"
            )
    
    def execute_trade(self, estimate: dict):
        """Execute a trade"""
        try:
            logger.info("💹 Executing trade...")
            
            # In production: Send actual transaction to blockchain
            # For now: Log and update portfolio
            
            # Update portfolio
            self.portfolio.remove_holding(self.from_token, estimate['input_amount'])
            self.portfolio.add_holding(self.to_token, estimate['output_amount'])
            
            # Log transaction
            self.portfolio.log_transaction(
                tx_type='swap',
                from_token=self.from_token,
                to_token=self.to_token,
                from_amount=estimate['input_amount'],
                to_amount=estimate['output_amount'],
                price=estimate['output_amount'] / estimate['input_amount'],
                gas_fee=estimate['gas_cost_usd'],
                tx_hash="0xDEMO_" + str(self.trade_count)
            )
            
            # Calculate profit/loss
            profit = estimate['output_amount'] - estimate['input_amount'] - estimate['gas_cost_usd']
            profit_percent = (profit / estimate['input_amount'] * 100) if estimate['input_amount'] > 0 else 0
            
            if profit < 0:
                self.daily_loss += abs(profit)
            
            # Send alert
            alert_manager.send_alert(
                "💹 Trade Executed",
                f"Bought {estimate['output_amount']:.6f} {self.to_token}\n"
                f"Spent: {estimate['input_amount']} {self.from_token}\n"
                f"Gas: ${estimate['gas_cost_usd']:.2f}\n"
                f"Profit: ${profit:.2f} ({profit_percent:.2f}%)",
                "trade"
            )
            
            logger.info(f"✅ Trade executed successfully. Profit: ${profit:.2f}")
        
        except Exception as e:
            logger.error(f"Trade execution failed: {str(e)}", exc_info=True)
            raise
    
    def health_check(self):
        """Perform health check"""
        try:
            # Check connection
            if not self.exchange.web3.is_connected():
                logger.error("❌ RPC connection lost!")
                alert_manager.send_alert(
                    "⚠️  Connection Lost",
                    "RPC connection lost. Bot may not function.",
                    "warning"
                )
                return
            
            # Get current prices
            prices = self.exchange.get_prices([self.from_token, self.to_token])
            
            # Get portfolio stats
            stats = self.portfolio.get_statistics(prices)
            
            logger.info(
                f"💚 Health check OK\n"
                f"  Holdings: {stats['holdings']}\n"
                f"  Portfolio value: ${stats['total_value']:.2f}\n"
                f"  P&L: ${stats['profit_loss']:.2f} ({stats['profit_loss_percent']:.2f}%)"
            )
        
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
    
    def reset_daily_limits(self):
        """Reset daily loss counter"""
        logger.info("🔄 Resetting daily limits...")
        self.daily_loss = 0
        self.last_reset = datetime.now()
    
    def get_status(self) -> dict:
        """Get bot status"""
        try:
            prices = self.exchange.get_prices([self.from_token, self.to_token])
            stats = self.portfolio.get_statistics(prices)
            
            return {
                "is_running": self.is_running,
                "strategy": STRATEGY,
                "trading_pair": TRADING_PAIR,
                "trade_amount": TRADE_AMOUNT,
                "total_trades": self.trade_count,
                "daily_loss": self.daily_loss,
                "portfolio": stats,
                "prices": prices,
                "last_reset": self.last_reset.isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get status: {str(e)}")
            return {}

if __name__ == "__main__":
    bot = TradingBot()
    bot.start()
