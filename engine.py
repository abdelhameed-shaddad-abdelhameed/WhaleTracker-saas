import time
import json
import traceback
from decimal import Decimal
from typing import Dict, Any

# استدعاء مكتبات النظام
from whaletracker import BlockchainService
import config
import db
import analysis  # تحليل النوايا (Intent AI)
import notifier  # موزع التنبيهات الذكي (Dispatcher)

# حد أدنى لتجاهل غبار الغاز (Dust)
MIN_CHANGE_THRESHOLD = Decimal("0.0001") 

def check_thresholds(user_settings: dict, asset: str, change_amount: Decimal, new_balance: Decimal, delta_pct: Decimal) -> bool:
    """
    فلتر ذكي: يقرر هل نرسل تنبيهاً للمستخدم بناءً على باقته وإعداداته.
    """
    if not user_settings:
        return False
        
    # البحث عن إعدادات العملة، أو استخدام الافتراضي
    asset_rules = user_settings.get(asset) or user_settings.get("DEFAULT")
    
    if not asset_rules:
        return False

    # 1. فحص الحد الأدنى للرصيد
    min_bal = Decimal(str(asset_rules.get("min_balance", 0)))
    if new_balance < min_bal:
        return False

    # 2. فحص نسبة التغير
    min_delta = Decimal(str(asset_rules.get("min_delta_pct", 0)))
    if abs(delta_pct) < min_delta:
        return False

    return True

def scan_once():
    """
    دورة المسح الشاملة:
    1. تجلب كل الشبكات (العامة والخاصة) من DB.
    2. تجلب المحافظ النشطة.
    3. تحلل وتوزع التنبيهات.
    """
    
    # --- 1. تجهيز الاتصال بالشبكات (All System + Custom Chains) ---
    try:
        # هذه الدالة الجديدة تجلب كل الشبكات بغض النظر عن المالك
        db_chains = db.get_all_chains_for_engine()
    except Exception as e:
        print(f"⚠️ DB Error loading chains: {e}")
        return

    providers = {}
    for c in db_chains:
        if c.rpc_url:
            try:
                # نمرر (RPC URL) و (اسم الشبكة) و (قائمة التوكنز JSON)
                providers[c.name] = BlockchainService(c.rpc_url, c.name, c.tokens_json)
            except Exception as e:
                # طباعة خطأ بسيط وتجاهل الشبكة المعطلة (قد تكون شبكة خاصة لمستخدم وتوقفت)
                print(f"⚠️ Failed to connect to chain '{c.name}': {e}")

    # --- 2. جلب المحافظ المستهدفة ---
    active_wallets = db.get_all_active_wallets()
    if not active_wallets:
        return

    # --- 3. بدء المسح ---
    for w in active_wallets:
        svc = providers.get(w.chain)
        
        # إذا كانت المحفظة على شبكة غير متصلة (أو محذوفة)، تجاوزها
        if not svc:
            continue

        # === A. فحص العملة الأساسية (Native Coin: ETH/BNB/MATIC) ===
        current_eth = None
        try:
            current_eth = svc.get_eth_balance(w.address)
            
            if current_eth is not None:
                last_eth = w.last_eth_balance or Decimal(0)
                change = current_eth - last_eth
                
                # إذا حدث تغيير حقيقي
                if abs(change) >= MIN_CHANGE_THRESHOLD:
                    # تحليل الحركة
                    delta = analysis.calculate_delta(last_eth, current_eth)
                    intent = analysis.classify_intent("ETH", change, current_eth)
                    
                    # تسجيل الحدث (Log)
                    db.log_event(
                        address=w.address,
                        chain=w.chain,
                        asset="ETH", # أو رمز الشبكة مثل BNB
                        change=change,
                        new_bal=current_eth,
                        delta_pct=delta,
                        tx_type=intent
                    )
                    
                    # توزيع التنبيهات للمستخدمين (Watchers)
                    for watchlist_item in w.watchers:
                        user = watchlist_item.user
                        
                        # تحقق إضافي: هل هذا المستخدم مسموح له برؤية هذه الشبكة؟
                      
                        
                        if check_thresholds(watchlist_item.alert_settings, "ETH", change, current_eth, delta):
                            # رسالة للمستخدم (Human Readable)
                            msg = (
                                f"🚨 *{watchlist_item.user_label}* | {intent}\n"
                                f"Chain: {w.chain.upper()}\n"
                                f"Change: `{change:+.4f}`\n"
                                f"New Balance: `{current_eth:.4f}` ({delta:+.2f}%)"
                            )
                            
                            # بيانات للمبرمجين (Webhook Payload)
                            event_data = {
                                "event": "whale_move",
                                "address": w.address,
                                "label": watchlist_item.user_label,
                                "asset": "ETH",
                                "change": float(change),
                                "balance": float(current_eth),
                                "delta_pct": float(delta),
                                "intent": intent
                            }

                            notifier.dispatch_alert(user.settings_json, msg, event_data)

        except Exception as e:
            print(f"❌ Error scanning Native Coin for {w.address}: {e}")

        # === B. فحص التوكنز (USDT, WBTC, etc.) ===
        # جلب الأرصدة القديمة
        current_token_balances = dict(w.last_token_balances) if w.last_token_balances else {}
        
        # نستخدم svc.token_services التي تم بناؤها ديناميكياً من الـ DB Chain
        for sym, tsvc in svc.token_services.items():
            try:
                bal = tsvc.balance(w.address)
                if bal is None: 
                    continue

                last_bal = Decimal(str(current_token_balances.get(sym, 0)))
                change = bal - last_bal
                
                if abs(change) > 0:
                    delta = analysis.calculate_delta(last_bal, bal)
                    intent = analysis.classify_intent(sym, change, bal)
                    
                    # تحديث القاموس المحلي
                    current_token_balances[sym] = float(bal)
                    
                    # تسجيل وتنبيه
                    db.log_event(w.address, w.chain, sym, change, bal, delta, intent)
                    
                    for watchlist_item in w.watchers:
                        if check_thresholds(watchlist_item.alert_settings, sym, change, bal, delta):
                            msg = (
                                f"🔔 *{watchlist_item.user_label}* | {intent}\n"
                                f"Asset: *{sym}*\n"
                                f"Change: `{change:+,.2f}`\n"
                                f"Balance: `{bal:,.2f}` ({delta:+.2f}%)"
                            )
                            
                            event_data = {
                                "event": "token_move",
                                "address": w.address,
                                "asset": sym,
                                "change": float(change),
                                "balance": float(bal),
                                "intent": intent
                            }
                            
                            notifier.dispatch_alert(watchlist_item.user.settings_json, msg, event_data)

            except Exception as e:
                # خطأ في توكن معين لا يوقف باقي التوكنز
                print(f"⚠️ Error scanning token {sym} for {w.address}: {e}")

        # === C. حفظ الحالة النهائية ===
        if current_eth is not None:
            db.update_wallet_state(w.address, current_eth, current_token_balances)

def run_loop():
    print("🚀 WhaleHunter SaaS Engine Started (Background)...")
    while True:
        try:
            scan_once()
        except Exception as e:
            print(f"🔥 Critical Loop Error: {e}")
            traceback.print_exc()
            
        time.sleep(config.SCAN_INTERVAL_SECONDS)

# ==========================================
# نقطة الدخول (Entry Point) لتشغيل الملف
# ==========================================
if __name__ == "__main__":
    # تهيئة قاعدة البيانات أولاً
    try:
        db.init_db()
        print("✅ Database connection initialized.")
    except Exception as e:
        print(f"⚠️ Database warning: {e}")
        
    # تشغيل المحرك
    run_loop()