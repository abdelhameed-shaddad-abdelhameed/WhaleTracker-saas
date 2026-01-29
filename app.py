import streamlit as st
import pandas as pd
import time
import plotly.express as px
from decimal import Decimal
import json

import db
from db import User, Watchlist
import engine
import config

st.set_page_config(page_title="WhaleHunter SaaS", page_icon="🐋", layout="wide")

st.markdown("""
<style>
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    div[data-testid="stMetric"] { background-color: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155; }
    .intent-buy { color: #4ade80; font-weight: bold; }
    .intent-sell { color: #f87171; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def get_session_user():
    return st.session_state.get("user", None)

def login(username, password):
    # التعديل: الدخول بالاسم والباسورد
    user = db.login_user(username, password)
    if user:
        st.session_state["user"] = user
        st.success(f"Welcome back, {user.username}!")
        time.sleep(0.5)
        st.rerun()
    else:
        st.error("Invalid Username or Password")

def logout():
    st.session_state["user"] = None
    st.rerun()

# --- Pages ---

def render_setup_wizard():
    st.warning("⚠️ System is empty. Please create the Root Admin.")
    with st.form("setup_admin"):
        u_name = st.text_input("Admin Username", value="admin")
        u_pass = st.text_input("Admin Password", type="password")
        
        if st.form_submit_button("Initialize System"):
            if u_name and u_pass:
                try:
                    # إنشاء الأدمن
                    db.create_user(u_name, u_pass, "enterprise", is_admin=True)
                    db.seed_default_chains()
                    st.success("✅ System Initialized! Please login.")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

def render_dashboard(user):
    st.title(f"📊 Dashboard: {user.username}")
    
    watchlist = db.get_user_watchlist(user.id)
    logs = db.get_logs(limit=100) 
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tracked Wallets", len(watchlist))
    col2.metric("Tier Plan", user.tier.upper())
    col3.metric("Recent Alerts", len(logs))
    col4.metric("System Status", "🟢 Online")

    st.subheader("📈 Activity Analysis")
    if logs:
        df = pd.DataFrame(logs, columns=["ts", "addr", "chain", "asset", "change", "bal", "delta", "intent"])
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(df, names='intent', hole=0.4), use_container_width=True)
        with c2:
            st.plotly_chart(px.bar(df, x='chain', y='change', color='asset'), use_container_width=True)
    else:
        st.info("No activity logs found yet.")

def render_watchlist_manager(user):
    st.title("🎯 Target Management")
    LIMITS = {"free": 1, "pro": 20, "enterprise": 1000}
    watchlist = db.get_user_watchlist(user.id)
    
    if watchlist:
        data = [{"Label": w.user_label, "Chain": w.wallet.chain if w.wallet else "N/A", "Address": w.wallet_address} for w in watchlist]
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("No targets yet.")

    st.divider()
    if len(watchlist) >= LIMITS.get(user.tier, 1):
        st.error("Limit Reached. Upgrade plan.")
    else:
        with st.form("add"):
            c1, c2 = st.columns(2)
            addr = c1.text_input("Address")
            lbl = c2.text_input("Label")
            chains = [c.name for c in db.get_available_chains_for_user(user)]
            ch = st.selectbox("Chain", chains) if chains else None
            
            if st.form_submit_button("Track"):
                if ch and addr:
                    try:
                        db.add_wallet_to_watchlist(user.id, addr, ch, lbl, {"ETH": {"min_balance": 1, "min_delta_pct": 5}})
                        st.success("Added!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e: st.error(str(e))

def render_live_feed():
    st.title("📡 Live Market Feed")
    if st.button("⚡ Force Scan"):
        engine.scan_once()
        st.success("Scanned!")
    
    logs = db.get_logs(50)
    if logs:
        df = pd.DataFrame(logs, columns=["Time", "Address", "Chain", "Asset", "Change", "New Balance", "Delta %", "Intent"])
        st.dataframe(df, use_container_width=True)

def render_settings_page(user):
    st.title("⚙️ Settings & API")
    
    # 1. عرض مفتاح الـ API الخاص بالمستخدم
    st.subheader("🔑 Your API Key")
    st.code(user.api_key, language="text")
    st.caption("Use this key to authenticate with our REST API (Enterprise Only).")
    
    st.divider()

    if user.tier == "free":
        st.warning("Integrations locked for Free Tier.")
        return

    curr = user.settings_json or {}
    with st.form("set"):
        st.subheader("Telegram")
        tid = st.text_input("Chat ID", value=curr.get("telegram", {}).get("chat_id", ""))
        ttok = st.text_input("Bot Token", value=curr.get("telegram", {}).get("bot_token", ""), type="password")
        
        st.subheader("Webhook")
        wh = st.text_input("URL", value=curr.get("webhook_url", ""))
        
        if st.form_submit_button("Save"):
            new_s = curr.copy()
            new_s["telegram"] = {"chat_id": tid, "bot_token": ttok}
            if user.tier == "enterprise": new_s["webhook_url"] = wh
            db.update_user_settings(user.id, new_s)
            user.settings_json = new_s
            st.session_state["user"] = user
            st.success("Saved!")

def render_custom_chains_page(user):
    st.title("🔗 Custom Networks")
    if user.tier == "free": return st.warning("Pro Feature.")
    
    my = db.get_user_custom_chains(user.id)
    if my: st.dataframe(pd.DataFrame([{"Name": c.name, "RPC": c.rpc_url} for c in my]))
    
    if len(my) < 5:
        with st.form("add_c"):
            n = st.text_input("Name")
            r = st.text_input("RPC")
            if st.form_submit_button("Add"):
                try:
                    db.add_chain(n.lower(), r, user.tier, {}, user_id=user.id)
                    st.success("Added!")
                    st.rerun()
                except Exception as e: st.error(str(e))

def render_admin_panel(user):
    st.title("🛠️ Admin Panel")
    t1, t2 = st.tabs(["Users", "Chains"])
    
    with t1:
        st.subheader("Create User")
        with st.form("nu"):
            u = st.text_input("Username")
            # الأدمن يضع باسورد للدخول
            p = st.text_input("Password", type="password") 
            t = st.selectbox("Tier", ["free", "pro", "enterprise"])
            ia = st.checkbox("Is Admin?")
            
            if st.form_submit_button("Create"):
                try:
                    # النظام سيولد API Key تلقائياً
                    new_u = db.create_user(u, p, t, is_admin=ia)
                    st.success(f"User Created! API Key: {new_u.api_key}")
                except Exception as e: st.error(str(e))
                
    with t2:
        st.info("Manage Global Chains here...")
        # (نفس كود إدارة الشبكات السابق)

def main():
    try: cnt = db.get_user_count()
    except: cnt = 0

    if cnt == 0:
        render_setup_wizard()
        return

    user = get_session_user()
    
    with st.sidebar:
        st.title("🐋 WhaleHunter")
        if not user:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Login"): login(u, p)
        else:
            st.success(f"👤 {user.username}")
            st.caption(f"Tier: {user.tier}")
            
            opts = ["📊 Dashboard", "🎯 Watchlist", "📡 Live Feed", "⚙️ Settings"]
            if user.tier != "free": opts.append("🔗 Custom Networks")
            if user.is_admin: opts.append("🛠️ Admin")
            
            page = st.radio("Menu", opts)
            st.divider()
            if st.button("Logout"): logout()

    if user:
        if page == "📊 Dashboard": render_dashboard(user)
        elif page == "🎯 Watchlist": render_watchlist_manager(user)
        elif page == "📡 Live Feed": render_live_feed()
        elif page == "⚙️ Settings": render_settings_page(user)
        elif page == "🔗 Custom Networks": render_custom_chains_page(user)
        elif page == "🛠️ Admin": 
            if user.is_admin: render_admin_panel(user)
            else: st.error("Unauthorized")

if __name__ == "__main__":
    try: db.init_db()
    except: pass
    main()