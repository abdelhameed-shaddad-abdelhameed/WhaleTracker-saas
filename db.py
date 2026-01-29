import json
import secrets
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import (
    Column, String, Integer, Numeric, DateTime, 
    create_engine, select, delete, update, ForeignKey, Boolean, JSON
)
# ✅ تم إضافة joinedload هنا للإصلاح
from sqlalchemy.orm import declarative_base, Session, relationship, joinedload
import config

Base = declarative_base()
engine = create_engine(config.POSTGRES_DSN, future=True)

# ---------------------------------------------------------
# 1. Chain Management
# ---------------------------------------------------------
class Chain(Base):
    __tablename__ = "chains"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    rpc_url = Column(String, nullable=False)
    min_tier = Column(String, default="free") 
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    tokens_json = Column(JSON, default={})

# ---------------------------------------------------------
# 2. User Management
# ---------------------------------------------------------
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    api_key = Column(String, unique=True, nullable=False)
    tier = Column(String, default="free")
    is_admin = Column(Boolean, default=False)
    settings_json = Column(JSON, default={})
    wallets = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")

# ---------------------------------------------------------
# 3. Tracking Tables
# ---------------------------------------------------------
class Wallet(Base):
    __tablename__ = "wallets"
    
    address = Column(String, primary_key=True)
    chain = Column(String, default="ethereum")
    label = Column(String)
    last_eth_balance = Column(Numeric, default=0)
    last_token_balances = Column(JSON, default={})
    
    watchers = relationship("Watchlist", back_populates="wallet")

class Watchlist(Base):
    __tablename__ = "watchlist"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    wallet_address = Column(String, ForeignKey("wallets.address"))
    user_label = Column(String)
    alert_settings = Column(JSON, default={}) 
    
    user = relationship("User", back_populates="wallets")
    wallet = relationship("Wallet", back_populates="watchers")

class Log(Base):
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    address = Column(String)
    chain = Column(String)
    asset = Column(String)
    amount_change = Column(Numeric)
    new_balance = Column(Numeric)
    delta_percentage = Column(Numeric, nullable=True)
    tx_type = Column(String, nullable=True)

# ---------------------------------------------------------
# Functions
# ---------------------------------------------------------

def init_db() -> None:
    Base.metadata.create_all(engine)
    seed_default_chains()

def seed_default_chains():
    with Session(engine) as s:
        if s.query(Chain).filter(Chain.user_id == None).first() is None:
            defaults = [
                Chain(name="ethereum", rpc_url=config.INFURA_URL, min_tier="free", user_id=None, tokens_json=config.CHAIN_TOKENS.get("ethereum", {})),
                Chain(name="bsc", rpc_url=config.BSC_RPC, min_tier="pro", user_id=None, tokens_json=config.CHAIN_TOKENS.get("bsc", {})),
                Chain(name="polygon", rpc_url=config.POLYGON_RPC, min_tier="pro", user_id=None, tokens_json=config.CHAIN_TOKENS.get("polygon", {}))
            ]
            s.add_all(defaults)
            s.commit()

# --- Auth Functions ---

def create_user(username: str, password: str, tier: str = "free", is_admin: bool = False) -> User:
    auto_api_key = secrets.token_urlsafe(24)
    with Session(engine) as s:
        if s.scalars(select(User).where(User.username == username)).first():
            raise ValueError("Username already taken")
        user = User(username=username, password=password, api_key=auto_api_key, tier=tier, is_admin=is_admin)
        s.add(user)
        s.commit()
        s.refresh(user)
        return user

def login_user(username: str, password: str) -> Optional[User]:
    with Session(engine) as s:
        user = s.scalars(select(User).where(User.username == username)).first()
        if user and user.password == password:
            return user
        return None

def get_user_by_api_key(api_key: str) -> Optional[User]:
    with Session(engine) as s:
        return s.scalars(select(User).where(User.api_key == api_key)).first()

def get_user_count() -> int:
    with Session(engine) as s:
        return s.query(User).count()

def update_user_settings(user_id: int, settings: dict):
    with Session(engine) as s:
        s.execute(update(User).where(User.id == user_id).values(settings_json=settings))
        s.commit()

# --- Chain Functions ---

def add_chain(name: str, rpc: str, tier: str, tokens: dict, user_id: int = None):
    with Session(engine) as s:
        if s.scalars(select(Chain).where(Chain.name == name)).first():
            raise ValueError("Chain name already exists.")
        s.add(Chain(name=name, rpc_url=rpc, min_tier=tier, tokens_json=tokens, user_id=user_id))
        s.commit()

def delete_chain(name: str, user_id: int = None):
    with Session(engine) as s:
        stmt = delete(Chain).where(Chain.name == name)
        if user_id: stmt = stmt.where(Chain.user_id == user_id)
        s.execute(stmt)
        s.commit()

def get_all_chains_for_engine():
    with Session(engine) as s:
        return s.scalars(select(Chain)).all()

def get_all_system_chains():
    with Session(engine) as s:
        return s.scalars(select(Chain).filter(Chain.user_id == None)).all()

def get_user_custom_chains(user_id: int):
    with Session(engine) as s:
        return s.scalars(select(Chain).filter(Chain.user_id == user_id)).all()

def get_available_chains_for_user(user: User):
    tiers_map = {"free": 1, "pro": 2, "enterprise": 3}
    user_rank = tiers_map.get(user.tier, 1)
    with Session(engine) as s:
        sys_chains = s.scalars(select(Chain).filter(Chain.user_id == None)).all()
        allowed = [c for c in sys_chains if tiers_map.get(c.min_tier, 1) <= user_rank]
        if user_rank >= 2:
            custom = s.scalars(select(Chain).filter(Chain.user_id == user.id)).all()
            allowed.extend(custom)
        return allowed

# --- Wallet & Watchlist Functions (Fixed Here) ---

def get_user_watchlist(user_id: int):
    """
    ✅ FIX: Added joinedload(Watchlist.wallet) to prevent DetachedInstanceError
    """
    with Session(engine) as s:
        stmt = select(Watchlist).where(Watchlist.user_id == user_id).options(joinedload(Watchlist.wallet))
        return s.scalars(stmt).all()

def get_all_active_wallets():
    with Session(engine) as s:
        # Also fix here to be safe for the engine
        stmt = select(Wallet).options(joinedload(Wallet.watchers).joinedload(Watchlist.user))
        return s.scalars(stmt).unique().all()

def add_wallet_to_watchlist(user_id: int, address: str, chain: str, label: str, settings: dict):
    with Session(engine) as s:
        wallet = s.get(Wallet, address)
        if not wallet:
            wallet = Wallet(address=address, chain=chain, label=label)
            s.add(wallet)
        
        existing = s.scalars(select(Watchlist).where(Watchlist.user_id==user_id, Watchlist.wallet_address==address)).first()
        if not existing:
            s.add(Watchlist(user_id=user_id, wallet_address=address, user_label=label, alert_settings=settings))
        s.commit()

def update_wallet_state(address: str, eth_bal: Decimal, token_bals: dict):
    with Session(engine) as s:
        s.execute(update(Wallet).where(Wallet.address == address).values(last_eth_balance=eth_bal, last_token_balances=token_bals))
        s.commit()

# --- Logging Functions ---

def log_event(address, chain, asset, change, new_bal, delta_pct=None, tx_type="move"):
    with Session(engine) as s:
        s.add(Log(address=address, chain=chain, asset=asset, amount_change=change, new_balance=new_bal, delta_percentage=delta_pct, tx_type=tx_type))
        s.commit()

def get_logs(limit: int = 100):
    with Session(engine) as s:
        stmt = select(Log.timestamp, Log.address, Log.chain, Log.asset, Log.amount_change, Log.new_balance, Log.delta_percentage, Log.tx_type).order_by(Log.timestamp.desc()).limit(limit)
        return s.execute(stmt).all()