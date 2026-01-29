import time
from decimal import Decimal
from typing import Optional, Dict
from web3 import Web3
from web3.exceptions import Web3Exception
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import config

# ABI قياسي لجلب رصيد أي توكن ERC20
ERC20_BALANCEOF_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    }
]

class TokenService:
    def __init__(self, w3: Web3, address: str, decimals: int):
        self.w3 = w3
        self.decimals = decimals
        # تحويل العنوان لصيغة Checksum (حروف كبيرة وصغيرة) لتجنب أخطاء Web3
        self.contract = w3.eth.contract(address=Web3.to_checksum_address(address), abi=ERC20_BALANCEOF_ABI)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(Exception))
    def balance(self, owner: str) -> Optional[Decimal]:
        try:
            # إضافة تأخير بسيط لتخفيف الحمل على RPC
            time.sleep(0.1)
            raw = self.contract.functions.balanceOf(Web3.to_checksum_address(owner)).call()
            return Decimal(raw) / Decimal(10 ** self.decimals)
        except Exception as e:
            # طباعة الخطأ ولكن عدم إيقاف البرنامج
            print(f"⚠️ Token read error: {e}")
            raise e

class BlockchainService:
    def __init__(self, provider_url: str, chain: str, tokens_config: Dict = None):
        """
        خدمة الاتصال بالبلوكتشين.
        
        :param provider_url: رابط RPC (مثل Infura/Alchemy)
        :param chain: اسم الشبكة (للتسجيل)
        :param tokens_config: قاموس يحتوي على التوكنز وعناوينها (يأتي من قاعدة البيانات)
                              Format: {"USDT": ["0xAddress...", 6], ...}
        """
        # إضافة timeout لمنع تعليق البرنامج إذا انقطع النت
        self.w3 = Web3(Web3.HTTPProvider(provider_url, request_kwargs={'timeout': 15}))
        self.chain = chain
        
        # تجهيز خدمات التوكنز بناءً على البيانات الديناميكية
        self.token_services = {}
        
        if tokens_config:
            for sym, data in tokens_config.items():
                try:
                    # data[0] = address, data[1] = decimals
                    addr = data[0]
                    dec = int(data[1])
                    self.token_services[sym] = TokenService(self.w3, addr, dec)
                except Exception as e:
                    print(f"⚠️ Error loading token {sym} on {chain}: {e}")

    def is_connected(self) -> bool:
        try:
            return self.w3.is_connected()
        except Web3Exception:
            return False

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(Exception))
    def get_eth_balance(self, address: str) -> Optional[Decimal]:
        """
        جلب رصيد العملة الأساسية (ETH, BNB, MATIC, etc.)
        """
        # انتظار بسيط لتجنب Rate Limit
        time.sleep(0.2)
        try:
            wei = self.w3.eth.get_balance(Web3.to_checksum_address(address))
            return Decimal(self.w3.from_wei(wei, "ether"))
        except Exception as e:
            print(f"⚠️ Native Balance Error ({self.chain}): {e}")
            raise e