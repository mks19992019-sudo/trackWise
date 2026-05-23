from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

CurrencyCode = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_upper=True,
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
    ),
]
TrimmedText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
AmountValue = Annotated[
    Decimal,
    Field(gt=Decimal("0"), max_digits=12, decimal_places=2),
]


class FinanceModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def _normalize_currency_code(value: str | None) -> str | None:
    if value is None:
        return None

    return value.strip().upper()


class ExpenseCreate(FinanceModel):
    user_id: TrimmedText
    description: TrimmedText
    category: TrimmedText
    amount: AmountValue
    currency: CurrencyCode
    spent_at: datetime
    merchant: str | None = None
    notes: str | None = None

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = _normalize_currency_code(value)
        assert normalized is not None
        return normalized

    @field_validator("spent_at")
    @classmethod
    def normalize_spent_at(cls, value: datetime) -> datetime:
        return _normalize_datetime(value)

    @field_validator("merchant", "notes")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None

        stripped = value.strip()
        return stripped or None


class ExpenseUpdate(FinanceModel):
    description: str | None = None
    category: str | None = None
    amount: AmountValue | None = None
    currency: CurrencyCode | None = None
    spent_at: datetime | None = None
    merchant: str | None = None
    notes: str | None = None

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return _normalize_currency_code(value)

    @field_validator("description", "category")
    @classmethod
    def validate_non_empty_strings(cls, value: str | None) -> str | None:
        if value is None:
            return value

        stripped = value.strip()
        if not stripped:
            raise ValueError("Value cannot be empty.")

        return stripped

    @field_validator("merchant", "notes")
    @classmethod
    def normalize_nullable_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None

        stripped = value.strip()
        return stripped or None

    @field_validator("spent_at")
    @classmethod
    def normalize_spent_at(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None

        return _normalize_datetime(value)

    @model_validator(mode="after")
    def validate_update_payload(self) -> ExpenseUpdate:
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided for an expense update.")

        for field_name in ("description", "category", "amount", "currency", "spent_at"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null.")

        return self


class ExpenseRecord(FinanceModel):
    id: UUID
    user_id: str
    description: str
    category: str
    amount: Decimal
    currency: str
    spent_at: datetime
    merchant: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ExpenseListFilters(FinanceModel):
    user_id: TrimmedText
    category: str | None = None
    currency: CurrencyCode | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    min_amount: AmountValue | None = None
    max_amount: AmountValue | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str | None) -> str | None:
        if value is None:
            return None

        stripped = value.strip()
        return stripped or None

    @field_validator("date_from", "date_to")
    @classmethod
    def normalize_range_datetimes(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None

        return _normalize_datetime(value)

    @model_validator(mode="after")
    def validate_ranges(self) -> ExpenseListFilters:
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be earlier than or equal to date_to.")

        if self.min_amount and self.max_amount and self.min_amount > self.max_amount:
            raise ValueError("min_amount must be less than or equal to max_amount.")

        return self


class ExpenseSearchFilters(ExpenseListFilters):
    query: str | None = None

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str | None) -> str | None:
        if value is None:
            return None

        stripped = value.strip()
        return stripped or None


class CurrencyTotal(FinanceModel):
    currency: str
    total_amount: Decimal
    average_amount: Decimal


class MonthlySummaryRequest(FinanceModel):
    user_id: TrimmedText
    year: int = Field(ge=2000, le=9999)
    month: int = Field(ge=1, le=12)
    currency: CurrencyCode | None = None

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return _normalize_currency_code(value)


class MonthlySummary(FinanceModel):
    year: int
    month: int
    expense_count: int
    category_count: int
    top_category: str | None
    totals_by_currency: list[CurrencyTotal]


class CategorySummaryRequest(FinanceModel):
    user_id: TrimmedText
    start_date: date
    end_date: date
    currency: CurrencyCode | None = None
    limit: int = Field(default=50, ge=1, le=200)

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return _normalize_currency_code(value)

    @model_validator(mode="after")
    def validate_dates(self) -> CategorySummaryRequest:
        if self.start_date > self.end_date:
            raise ValueError("start_date must be earlier than or equal to end_date.")

        return self


class CategorySummaryItem(FinanceModel):
    category: str
    currency: str
    total_amount: Decimal
    average_amount: Decimal
    expense_count: int
    first_spent_at: datetime
    last_spent_at: datetime


class BudgetCreate(FinanceModel):
    user_id: TrimmedText
    name: TrimmedText
    amount: AmountValue
    currency: CurrencyCode
    period_start: date
    period_end: date
    category: str | None = None
    notes: str | None = None

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = _normalize_currency_code(value)
        assert normalized is not None
        return normalized

    @field_validator("category", "notes")
    @classmethod
    def normalize_nullable_text(cls, value: str | None) -> str | None:
        if value is None:
            return None

        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def validate_budget_window(self) -> BudgetCreate:
        if self.period_end < self.period_start:
            raise ValueError("period_end must be later than or equal to period_start.")

        return self


class BudgetUpdate(FinanceModel):
    name: str | None = None
    amount: AmountValue | None = None
    currency: CurrencyCode | None = None
    period_start: date | None = None
    period_end: date | None = None
    category: str | None = None
    notes: str | None = None

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return _normalize_currency_code(value)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None

        stripped = value.strip()
        if not stripped:
            raise ValueError("name cannot be empty.")

        return stripped

    @field_validator("category", "notes")
    @classmethod
    def normalize_nullable_budget_text(cls, value: str | None) -> str | None:
        if value is None:
            return None

        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def validate_budget_update(self) -> BudgetUpdate:
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided for a budget update.")

        for field_name in ("name", "amount", "currency", "period_start", "period_end"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null.")

        if self.period_start and self.period_end and self.period_end < self.period_start:
            raise ValueError("period_end must be later than or equal to period_start.")

        return self


class BudgetRecord(FinanceModel):
    id: UUID
    user_id: str
    name: str
    amount: Decimal
    currency: str
    period_start: date
    period_end: date
    category: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class BudgetStatus(FinanceModel):
    budget_id: UUID
    user_id: str
    name: str
    category: str | None
    currency: str
    period_start: date
    period_end: date
    budget_amount: Decimal
    spent_amount: Decimal
    remaining_amount: Decimal
    usage_percentage: Decimal
    expense_count: int
    status: str


class BudgetCurrencyAnalytics(FinanceModel):
    currency: str
    total_budgeted_amount: Decimal
    total_spent_amount: Decimal
    total_remaining_amount: Decimal
    over_budget_count: int
    at_risk_count: int


class BudgetAnalytics(FinanceModel):
    total_budgets: int
    active_budgets: int
    over_budget_count: int
    at_risk_count: int
    on_track_count: int
    totals_by_currency: list[BudgetCurrencyAnalytics]
