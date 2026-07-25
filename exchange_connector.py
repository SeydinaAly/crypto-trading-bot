import time
from typing import Dict, Tuple
from web3 import Web3
from config import (
    RPC_URL, BLOCKCHAIN, EXCHANGE_TYPE, DEX_TYPE,
    UNISWAP_V3_ROUTER, UNISWAP_V2_ROUTER, TOKEN_ADDRESSES
)
from logger import logger

class ExchangeConnector:
    """Handle connections to DEX and CEX"""
    
    def __init__(self, private_key=None):
        self.web3 = Web3(Web3.HTTPProvider(RPC_URL))
        self.private_key = private_key
        self.exchange_type = EXCHANGE_TYPE
        self.dex_type = DEX_TYPE
        
        if not self.web3.is_connected():
            raise ConnectionError("❌ Failed to connect to blockchain RPC")
        logger.info(f"✅ Connected to {BLOCKCHAIN}")
    
    def get_token_balance(self, account: str, token_symbol: str) -> float:
        """Get token balance for account"""
        if token_symbol not in TOKEN_ADDRESSES:
            logger.warning(f"Token {token_symbol} not found")
            return 0
        
        token_address = TOKEN_ADDRESSES[token_symbol]
        
        # ERC20 ABI minimal
        erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            }
        ]
        
        try:
            contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=erc20_abi
            )
            balance = contract.functions.balanceOf(
                Web3.to_checksum_address(account)
            ).call()
            decimals = contract.functions.decimals().call()
            
            return balance / (10 ** decimals)
        except Exception as e:
            logger.error(f"Failed to get balance: {str(e)}")
            return 0
    
    def get_token_price(self, token_symbol: str) -> float:
        """Get current token price from DEX"""
        # This is a simplified version - in production use Chainlink price feeds
        try:
            import requests
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={token_symbol.lower()}&vs_currencies=usd"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            price_key = {
                "ETH": "ethereum",
                "USDC": "usd-coin",
                "DAI": "dai",
                "USDT": "tether"
            }.get(token_symbol)
            
            if price_key and price_key in data:
                return data[price_key].get("usd", 0)
            return 0
        except Exception as e:
            logger.error(f"Failed to get price for {token_symbol}: {str(e)}")
            return 0
    
    def get_prices(self, tokens: list) -> Dict[str, float]:
        """Get prices for multiple tokens"""
        prices = {}
        for token in tokens:
            prices[token] = self.get_token_price(token)
        return prices
    
    def estimate_swap(self, from_token: str, to_token: str, amount: float) -> Dict:
        """Estimate swap output amount and gas"""
        try:
            from_price = self.get_token_price(from_token)
            to_price = self.get_token_price(to_token)
            
            if from_price == 0 or to_price == 0:
                logger.error("Cannot estimate swap - missing price data")
                return {}
            
            output_amount = (amount * from_price) / to_price
            
            # Estimate gas (~150-300k wei for uniswap swap)
            gas_limit = 200000
            gas_price = self.web3.eth.gas_price
            gas_cost_eth = gas_limit * gas_price / 10**18
            gas_cost_usd = gas_cost_eth * self.get_token_price("ETH")
            
            return {
                "input_amount": amount,
                "input_token": from_token,
                "output_amount": output_amount,
                "output_token": to_token,
                "price_impact": 0.3,  # 0.3% for uniswap
                "gas_limit": gas_limit,
                "gas_price": gas_price,
                "gas_cost_eth": gas_cost_eth,
                "gas_cost_usd": gas_cost_usd
            }
        except Exception as e:
            logger.error(f"Swap estimation failed: {str(e)}")
            return {}
    
    def get_current_gas_price(self) -> Dict:
        """Get current gas prices"""
        try:
            gas_price_wei = self.web3.eth.gas_price
            gas_price_gwei = gas_price_wei / 10**9
            gas_price_eth = gas_price_wei / 10**18
            
            return {
                "wei": gas_price_wei,
                "gwei": gas_price_gwei,
                "eth": gas_price_eth
            }
        except Exception as e:
            logger.error(f"Failed to get gas price: {str(e)}")
            return {}
    
    def is_profitable(self, from_amount: float, to_amount: float, gas_cost_usd: float, min_profit_percent: float) -> bool:
        """Check if trade is profitable"""
        profit = to_amount - from_amount - gas_cost_usd
        profit_percent = (profit / from_amount * 100) if from_amount > 0 else 0
        
        is_profit = profit_percent >= min_profit_percent
        logger.info(f"Profit: ${profit:.2f} ({profit_percent:.2f}%) - Profitable: {is_profit}")
        
        return is_profit
    
    def check_slippage(self, estimated: Dict, max_slippage_percent: float = 1) -> bool:
        """Check if estimated slippage is acceptable"""
        if "price_impact" not in estimated:
            return False
        
        acceptable = estimated["price_impact"] <= max_slippage_percent
        logger.info(f"Slippage: {estimated['price_impact']:.2f}% - Acceptable: {acceptable}")
        return acceptable

if __name__ == "__main__":
    connector = ExchangeConnector()
    
    # Test balance
    test_addr = "0xd456feaee6e1c252a77594d0b6c567ba481e2c4c"
    balance = connector.get_token_balance(test_addr, "USDC")
    print(f"USDC Balance: {balance}")
    
    # Test prices
    prices = connector.get_prices(["ETH", "USDC", "DAI"])
    print(f"Prices: {prices}")
    
    # Test swap estimation
    swap = connector.estimate_swap("USDC", "ETH", 1000)
    print(f"Swap estimate: {swap}")
