# 🤖 Crypto Trading Bot - Setup Guide

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/SeydinaAly/crypto-trading-bot.git
cd crypto-trading-bot
```

### 2. Setup Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
# Copy example config
cp .env.example .env

# Edit with your settings
nano .env  # or open in your editor
```

## Configuration

### Required Settings

**Blockchain RPC:**
```env
BLOCKCHAIN=ethereum
RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY
PRIVATE_KEY=0x...  # Your Ethereum private key (WITHOUT 0x prefix in some cases)
```

Get free RPC endpoints:
- **Alchemy**: https://www.alchemy.com/
- **Infura**: https://infura.io/
- **QuickNode**: https://www.quicknode.com/

**Trading Configuration:**
```env
STRATEGY=dca              # Strategy type
TRADING_PAIR=USDC/ETH     # What to trade
TRADE_AMOUNT=100          # Amount per trade
TRADE_INTERVAL=3600       # Interval in seconds
```

### Optional - Alerts (Pick One or More)

**Telegram:**
1. Create bot: Message [@BotFather](https://t.me/BotFather) on Telegram
2. Get chat ID: Message bot, then visit `https://api.telegram.org/bot{TOKEN}/getUpdates`

```env
ALERT_TYPE=telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=987654321
```

**Discord:**
1. Create webhook in server settings
2. Copy webhook URL

```env
ALERT_TYPE=discord
DISCORD_WEBHOOK=https://discord.com/api/webhooks/123456789/...
```

**Email (Gmail):**
1. Enable 2FA on Gmail
2. Create app password: https://myaccount.google.com/apppasswords

```env
ALERT_TYPE=email
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=app_password_here
EMAIL_RECIPIENT=recipient@gmail.com
```

**All Alerts:**
```env
ALERT_TYPE=all
# Configure all three above
```

### Safety Settings

```env
MAX_DAILY_LOSS_PERCENT=5      # Stop trading if daily loss exceeds this
MAX_TRANSACTION_AMOUNT=10000  # Max USD per transaction
STOP_LOSS_PERCENT=3           # Stop loss trigger
```

## Running the Bot

### Start Everything
```bash
python main.py
```

This will:
1. Initialize the bot ✅
2. Start the dashboard 🎨
3. Begin trading according to strategy 💹

### Dashboard
Open browser: **http://localhost:5000**

Features:
- 📊 Real-time portfolio value
- 💹 Trading history
- 🔔 Recent alerts
- ⛽ Gas prices
- 💰 Token prices
- ✅ Start/Stop controls

### Monitor Logs
```bash
tail -f logs/bot.log
```

## Strategies Explained

### DCA (Dollar Cost Averaging)
- Buys at **fixed intervals** (e.g., every hour)
- Works in any market condition
- Great for beginners
- **Settings:**
  ```env
  STRATEGY=dca
  TRADE_INTERVAL=3600  # Buy every hour
  TRADE_AMOUNT=100     # $100 per trade
  ```

### Arbitrage
- Exploits **price differences** between DEXes
- Only trades when **profitable**
- Requires fast execution
- **Settings:**
  ```env
  STRATEGY=arbitrage
  MIN_PROFIT_PERCENT=2  # Only if >2% profit
  ```

### Technical Analysis
- Uses **indicators** (RSI, MACD, etc.)
- Customizable strategies
- Requires tuning
- **Status:** Framework ready, indicators need implementation

## API Endpoints

Base: `http://localhost:5000/api`

### Bot Control
- `POST /api/start` - Start trading
- `POST /api/stop` - Stop trading
- `GET /api/status` - Current status
- `GET /api/health` - Health check

### Data
- `GET /api/portfolio` - Holdings & stats
- `GET /api/trades` - Trade history
- `GET /api/prices?tokens=ETH,USDC` - Token prices
- `GET /api/gas` - Gas prices
- `GET /api/alerts` - Alert history
- `GET /api/logs` - Recent logs

### Trading
- `POST /api/estimate` - Estimate a trade
  ```json
  {
    "from_token": "USDC",
    "to_token": "ETH",
    "amount": 100
  }
  ```

## Testing

### Test Mode (Recommended First)
```bash
# Create test environment
cp .env.example .env.test

# Use testnet
nano .env.test
# Set: BLOCKCHAIN=sepolia
# Set: RPC_URL=https://sepolia.g.alchemy.com/v2/YOUR_KEY

# Run with test env
export ENV_FILE=.env.test
python main.py
```

### Check Configuration
```python
python -c "from config import *; print('Config loaded!')"
```

## Troubleshooting

### "Failed to connect to RPC"
```
✓ Check RPC_URL is valid
✓ Check internet connection
✓ Try another RPC provider
```

### "Invalid private key"
```
✓ Remove '0x' prefix if present
✓ Use 64 character hex string
✓ Check no spaces or special chars
```

### "Insufficient balance"
```
✓ Send funds to your wallet address
✓ Check address is correct: 
  python -c "from web3 import Account; print(Account.from_key('YOUR_KEY').address)"
```

### "Gas price too high"
```
✓ Wait for lower gas prices
✓ Check https://ethgasstation.info/
✓ Reduce TRADE_AMOUNT
```

### Telegram not working
```
✓ Verify TELEGRAM_BOT_TOKEN
✓ Verify TELEGRAM_CHAT_ID
✓ Send message to bot first
✓ Check: https://api.telegram.org/botYOUR_TOKEN/getMe
```

## Security Tips

1. **Never commit .env**
   ```bash
   # Already in .gitignore, but verify
   echo ".env" >> .gitignore
   ```

2. **Use testnet first**
   - Sepolia, Goerli, Mumbai
   - Small amounts

3. **Monitor transactions**
   - Check etherscan
   - Verify gas prices
   - Review logs

4. **Set appropriate limits**
   - MAX_DAILY_LOSS_PERCENT
   - MAX_TRANSACTION_AMOUNT
   - STOP_LOSS_PERCENT

5. **Backup portfolio data**
   ```bash
   cp data/portfolio.json data/portfolio_backup.json
   ```

## Next Steps

1. ✅ Configure .env
2. ✅ Test on testnet
3. ✅ Monitor logs and dashboard
4. ✅ Start with small amounts
5. ✅ Scale up once comfortable

## Support

- 📖 Check README.md for full documentation
- 📊 View logs: `tail -f logs/bot.log`
- 🐛 Report issues on GitHub
- 💬 Join community Discord

## Important Reminders

⚠️ **This is NOT financial advice**

- Trading crypto has **high risk**
- Past performance ≠ Future results
- Only trade **money you can afford to lose**
- Start small and scale up
- Always use **risk management**
- Monitor your bot **regularly**

**Happy trading! 🚀**
