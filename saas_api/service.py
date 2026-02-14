from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import ApiKey, Company, Plan, Subscription, UsageRecord


def current_period() -> str:
    now = datetime.utcnow()
    return f"{now.year:04d}{now.month:02d}"


def ensure_default_plans(db: Session) -> None:
    existing = {p.code for p in db.scalars(select(Plan)).all()}
    defaults = [
        ("starter", "Starter", 4900, 1000),
        ("business", "Business", 19900, 6000),
        ("enterprise", "Enterprise", 0, 0),
    ]
    for code, name, price, minutes in defaults:
        if code in existing:
            continue
        db.add(Plan(code=code, name=name, monthly_price_cents=price, included_minutes=minutes, active=True))
    db.commit()


def create_company_with_subscription(db: Session, name: str, email: str, plan_code: str) -> tuple[Company, Subscription, ApiKey]:
    plan = db.scalar(select(Plan).where(Plan.code == plan_code, Plan.active.is_(True)))
    if plan is None:
        raise ValueError(f"Plan '{plan_code}' not found.")

    company = Company(name=name, email=email)
    db.add(company)
    db.flush()

    start = datetime.utcnow()
    end = start + timedelta(days=30)
    subscription = Subscription(company_id=company.id, plan_id=plan.id, status="active", period_start=start, period_end=end)
    api_key = ApiKey(company_id=company.id, name="default")
    db.add(subscription)
    db.add(api_key)
    db.commit()
    db.refresh(company)
    db.refresh(subscription)
    db.refresh(api_key)
    return company, subscription, api_key


def get_or_create_usage(db: Session, company_id: int, period: str) -> UsageRecord:
    usage = db.scalar(select(UsageRecord).where(UsageRecord.company_id == company_id, UsageRecord.period_yyyymm == period))
    if usage:
        return usage
    usage = UsageRecord(company_id=company_id, period_yyyymm=period, used_minutes=0, used_requests=0)
    db.add(usage)
    db.commit()
    db.refresh(usage)
    return usage


def add_usage(db: Session, company_id: int, used_minutes: int, used_requests: int = 1) -> UsageRecord:
    usage = get_or_create_usage(db, company_id, current_period())
    usage.used_minutes += max(0, int(used_minutes))
    usage.used_requests += max(0, int(used_requests))
    db.commit()
    db.refresh(usage)
    return usage


def active_subscription_with_plan(db: Session, company_id: int) -> tuple[Subscription, Plan]:
    sub = db.scalar(
        select(Subscription).where(Subscription.company_id == company_id).order_by(Subscription.created_at.desc())
    )
    if sub is None:
        raise ValueError("Subscription not found.")
    plan = db.scalar(select(Plan).where(Plan.id == sub.plan_id))
    if plan is None:
        raise ValueError("Plan not found.")
    return sub, plan

