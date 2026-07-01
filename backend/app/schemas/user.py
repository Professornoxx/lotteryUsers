from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    # Core profile
    user_id: Optional[int] = None        # auto-assigned if None
    username: str
    gender: Optional[int] = 0
    phone: Optional[str] = None
    email: Optional[str] = None
    birth_date: Optional[datetime] = None
    city: Optional[str] = None
    register_ip: Optional[str] = None
    user_status: Optional[int] = 0
    is_test: Optional[int] = 0
    app_version: Optional[str] = None
    reg_version: Optional[str] = None
    reg_source: Optional[str] = None
    reg_channel: Optional[str] = None
    package_id: Optional[int] = None
    mark: Optional[str] = None
    tag: Optional[str] = None

    # Financials
    balance: Optional[float] = 0
    user_balance: Optional[float] = 0
    total_deposits: Optional[float] = 0
    total_withdrawals: Optional[float] = 0
    frozen_amount: Optional[float] = 0
    withdraw_limit: Optional[float] = 0
    recharge_count: Optional[int] = 0

    # Agent
    agent_status: Optional[int] = None
    agent_user_id: Optional[int] = None
    parent_user_id: Optional[int] = None
    direct_parent: Optional[int] = None
    agent_level1: Optional[int] = None
    agent_level2: Optional[int] = None
    agent_level3: Optional[int] = None
    agent_level4: Optional[int] = None
    agent_level: Optional[int] = None
    inviter_user_id: Optional[int] = None
    member_level: Optional[int] = 0

    # Device
    register_device: Optional[str] = None
    login_device: Optional[str] = None
    last_login_device: Optional[str] = None
    device_id: Optional[str] = None
    push_token: Optional[str] = None
    last_active_time: Optional[datetime] = None

    # IM
    im_user_id: Optional[str] = None
    im_user_status: Optional[str] = None
    im_customer: Optional[str] = None
    group_name: Optional[str] = None
    adjust_adid: Optional[str] = None

    # Follow-up
    flow_up_time: Optional[datetime] = None
    next_flow_up_time: Optional[datetime] = None


class UserUpdate(UserCreate):
    username: Optional[str] = None
