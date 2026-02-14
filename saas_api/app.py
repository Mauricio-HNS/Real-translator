from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime

import stripe
from deep_translator import GoogleTranslator
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, SessionLocal, engine
from .models import ApiKey, Company, Plan
from .schemas import CompanyCreate, CompanyOut, TranslateIn, TranslateOut, UsageOut
from .service import active_subscription_with_plan, add_usage, create_company_with_subscription, current_period, ensure_default_plans, get_or_create_usage


stripe.api_key = settings.stripe_secret_key

app = FastAPI(title=settings.app_name, version="1.0.0")


@contextmanager
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db():
    with db_session() as db:
        yield db


def get_company_by_api_key(
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Company:
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-API-Key.")
    key = db.scalar(select(ApiKey).where(ApiKey.key == x_api_key, ApiKey.active.is_(True)))
    if key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key.")
    company = db.scalar(select(Company).where(Company.id == key.company_id))
    if company is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Company not found.")
    return company


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with db_session() as db:
        ensure_default_plans(db)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "time": datetime.utcnow().isoformat()}


@app.post("/v1/admin/companies", response_model=CompanyOut)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)) -> CompanyOut:
    try:
        company, sub, api_key = create_company_with_subscription(db, payload.name, payload.email, payload.plan_code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    plan_row = db.scalar(select(Plan).where(Plan.id == sub.plan_id))
    return CompanyOut(
        id=company.id,
        name=company.name,
        email=company.email,
        plan_code=plan_row.code if plan_row else payload.plan_code,
        subscription_status=sub.status,
        api_key=api_key.key,
    )


@app.get("/v1/usage", response_model=UsageOut)
def usage(company: Company = Depends(get_company_by_api_key), db: Session = Depends(get_db)) -> UsageOut:
    try:
        sub, plan = active_subscription_with_plan(db, company.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    usage_row = get_or_create_usage(db, company.id, current_period())
    remaining = max(0, plan.included_minutes - usage_row.used_minutes)
    return UsageOut(
        plan_code=plan.code,
        included_minutes=plan.included_minutes,
        used_minutes=usage_row.used_minutes,
        used_requests=usage_row.used_requests,
        remaining_minutes=remaining,
        status=sub.status,
    )


@app.post("/v1/translate", response_model=TranslateOut)
def translate(payload: TranslateIn, company: Company = Depends(get_company_by_api_key), db: Session = Depends(get_db)) -> TranslateOut:
    try:
        sub, plan = active_subscription_with_plan(db, company.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if sub.status != "active":
        raise HTTPException(status_code=403, detail="Subscription inactive.")

    usage_row = get_or_create_usage(db, company.id, current_period())
    estimated_minutes = max(0, int(payload.estimated_minutes))
    projected = usage_row.used_minutes + estimated_minutes
    if plan.included_minutes > 0 and projected > plan.included_minutes:
        raise HTTPException(status_code=402, detail="Monthly limit exceeded.")

    translator = GoogleTranslator(source=payload.source, target=payload.target)
    translated = translator.translate(payload.text)
    add_usage(db, company.id, estimated_minutes, 1)
    return TranslateOut(translated_text=translated)


@app.post("/v1/billing/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured.")
    payload = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    try:
        event = stripe.Webhook.construct_event(payload=payload, sig_header=signature, secret=settings.stripe_webhook_secret)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Invalid webhook: {exc}") from exc

    event_type = event.get("type", "")
    obj = event.get("data", {}).get("object", {})
    sub_id = obj.get("id")
    customer_id = obj.get("customer")
    if event_type.startswith("customer.subscription.") and (sub_id or customer_id):
        company = None
        if customer_id:
            company = db.scalar(select(Company).where(Company.stripe_customer_id == customer_id))
        if company and sub_id:
            from .models import Subscription

            sub = db.scalar(select(Subscription).where(Subscription.company_id == company.id).order_by(Subscription.created_at.desc()))
            if sub:
                status_val = str(obj.get("status", "active"))
                sub.status = "active" if status_val in {"active", "trialing"} else "inactive"
                company.stripe_subscription_id = sub_id
                db.commit()

    return {"status": "ok"}
