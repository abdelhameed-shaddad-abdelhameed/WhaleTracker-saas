from decimal import Decimal

# تصنيف العملات المستقرة لتحليل التدفقات
STABLECOINS = {"USDT", "USDC", "DAI", "BUSD"}

def calculate_delta(old_val: Decimal, new_val: Decimal) -> Decimal:
    """حساب نسبة التغير المئوية"""
    if old_val == 0:
        return Decimal(100) if new_val > 0 else Decimal(0)
    
    delta = ((new_val - old_val) / old_val) * 100
    return delta

def classify_intent(asset: str, change: Decimal, current_balance: Decimal) -> str:
    """
    Whale Intent Engine: تحديد نية الحوت بناءً على الحركة
    """
    is_positive = change > 0
    
    # 1. تحليل العملات المستقرة (Risk-On / Risk-Off)
    if asset in STABLECOINS:
        if is_positive:
            # زيادة الكاش تعني الخروج من السوق (خوف) أو التحضير للشراء
            return "💰 Stablecoin Accumulation (Dry Powder)"
        else:
            # نقص الكاش يعني غالباً الشراء (دخول السوق)
            return "🚀 Buying Power Deployed (Risk-On)"

    # 2. تحليل العملات العادية (ETH, WBTC, Tokens)
    else:
        if is_positive:
            return "📥 Accumulation (Buying/Inflow)"
        else:
            # إذا باع الحوت كل شيء أو جزء كبير
            if current_balance == 0 or (abs(change) / (current_balance + abs(change)) > 0.8):
                return "🚨 Panic Dump (Exit)"
            return "📤 Distribution (Selling/Outflow)"

def get_risk_level(delta_pct: Decimal, asset_usd_value: float = 0) -> str:
    """تحديد خطورة الحركة بناءً على النسبة المئوية"""
    abs_delta = abs(delta_pct)
    
    if abs_delta >= 50:
        return "CRITICAL"
    elif abs_delta >= 20:
        return "HIGH"
    elif abs_delta >= 5:
        return "MEDIUM"
    else:
        return "LOW"
