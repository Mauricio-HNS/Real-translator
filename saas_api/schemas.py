from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class CompanyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    email: EmailStr
    plan_code: str = Field(default="starter", max_length=40)


class CompanyOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    plan_code: str
    subscription_status: str
    api_key: str


class TranslateIn(BaseModel):
    text: str = Field(min_length=1)
    source: str = "en"
    target: str = "pt"
    estimated_minutes: int = 0


class TranslateOut(BaseModel):
    translated_text: str


class UsageOut(BaseModel):
    plan_code: str
    included_minutes: int
    used_minutes: int
    used_requests: int
    remaining_minutes: int
    status: str

