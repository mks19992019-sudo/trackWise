from __future__ import annotations

import json
from contextvars import ContextVar, Token
from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from langchain_core.tools import tool
from pydantic import BaseModel

from finance_models import (
    BudgetCreate,
    BudgetUpdate,
    CategorySummaryRequest,
    ExpenseCreate,
    ExpenseListFilters,
    ExpenseSearchFilters,
    ExpenseUpdate,
    MonthlySummaryRequest,
)
from finance_repository import get_finance_repository

_active_user_id: ContextVar[str | None] = ContextVar("active_user_id", default=None)


def set_active_user_id(user_id: str) -> Token[str | None]:
    return _active_user_id.set(user_id.strip())


def reset_active_user_id(token: Token[str | None]) -> None:
    _active_user_id.reset(token)


def _require_active_user_id() -> str:
    user_id = _active_user_id.get()

    if not user_id:
        raise RuntimeError("No active user scope is set for finance tools.")

    return user_id


async def _repository():
    return await get_finance_repository()


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip()

    if not normalized or normalized.lower() in {"null", "none"}:
        return None

    return normalized


def _to_decimal(value: float | int | str | None) -> Decimal | None:
    if value is None:
        return None

    if isinstance(value, str):
        normalized = _optional_text(value)
        if normalized is None:
            return None
        return Decimal(normalized)

    return Decimal(str(value))


def _to_datetime(value: str | None) -> datetime | None:
    normalized = _optional_text(value)

    if normalized is None:
        return None

    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        parsed_date = date.fromisoformat(normalized)
        return datetime.combine(parsed_date, time.min, tzinfo=timezone.utc)


def _to_date(value: str | None) -> date | None:
    normalized = _optional_text(value)

    if normalized is None:
        return None

    try:
        return date.fromisoformat(normalized)
    except ValueError:
        return datetime.fromisoformat(normalized).date()


def _jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return {key: _jsonable(item) for key, item in value.model_dump().items()}
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


def _response(**payload: Any) -> str:
    return json.dumps(_jsonable(payload))


@tool
async def add_expense(
    description: str,
    category: str,
    amount: float,
    currency: str,
    spent_at: str | None = None,
    merchant: str | None = None,
    notes: str | None = None,
) -> str:
    """Create a new expense for the current user."""

    repo = await _repository()
    expense = await repo.add_expense(
        ExpenseCreate(
            user_id=_require_active_user_id(),
            description=description,
            category=category,
            amount=_to_decimal(amount),
            currency=currency,
            spent_at=_to_datetime(spent_at) or datetime.now(timezone.utc),
            merchant=_optional_text(merchant),
            notes=_optional_text(notes),
        )
    )
    return _response(ok=True, expense=expense)


@tool
async def update_expense(
    expense_id: str,
    description: str | None = None,
    category: str | None = None,
    amount: float | str | None = None,
    currency: str | None = None,
    spent_at: str | None = None,
    merchant: str | None = None,
    notes: str | None = None,
) -> str:
    """Update an existing expense for the current user."""

    repo = await _repository()
    expense = await repo.update_expense(
        _require_active_user_id(),
        UUID(expense_id),
        ExpenseUpdate(
            description=_optional_text(description),
            category=_optional_text(category),
            amount=_to_decimal(amount),
            currency=_optional_text(currency),
            spent_at=_to_datetime(spent_at),
            merchant=_optional_text(merchant),
            notes=_optional_text(notes),
        ),
    )

    if expense is None:
        return _response(ok=False, error="Expense not found.")

    return _response(ok=True, expense=expense)


@tool
async def delete_expense(expense_id: str) -> str:
    """Delete an expense for the current user."""

    repo = await _repository()
    deleted = await repo.delete_expense(_require_active_user_id(), UUID(expense_id))
    return _response(ok=deleted)


@tool
async def list_expenses(
    category: str | None = None,
    currency: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    min_amount: float | str | None = None,
    max_amount: float | str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> str:
    """List expenses for the current user with optional filters."""

    repo = await _repository()
    expenses = await repo.list_expenses(
        ExpenseListFilters(
            user_id=_require_active_user_id(),
            category=_optional_text(category),
            currency=_optional_text(currency),
            date_from=_to_datetime(date_from),
            date_to=_to_datetime(date_to),
            min_amount=_to_decimal(min_amount),
            max_amount=_to_decimal(max_amount),
            limit=limit,
            offset=offset,
        )
    )
    return _response(ok=True, count=len(expenses), expenses=expenses)


@tool
async def search_expenses(
    query: str | None = None,
    category: str | None = None,
    currency: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    min_amount: float | str | None = None,
    max_amount: float | str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> str:
    """Search expenses for the current user."""

    repo = await _repository()
    expenses = await repo.search_expenses(
        ExpenseSearchFilters(
            user_id=_require_active_user_id(),
            query=_optional_text(query),
            category=_optional_text(category),
            currency=_optional_text(currency),
            date_from=_to_datetime(date_from),
            date_to=_to_datetime(date_to),
            min_amount=_to_decimal(min_amount),
            max_amount=_to_decimal(max_amount),
            limit=limit,
            offset=offset,
        )
    )
    return _response(ok=True, count=len(expenses), expenses=expenses)


@tool
async def monthly_summary(
    year: int,
    month: int,
    currency: str | None = None,
) -> str:
    """Return a monthly spending summary for the current user."""

    repo = await _repository()
    summary = await repo.monthly_summary(
        MonthlySummaryRequest(
            user_id=_require_active_user_id(),
            year=year,
            month=month,
            currency=_optional_text(currency),
        )
    )
    return _response(ok=True, summary=summary)


@tool
async def category_summary(
    start_date: str,
    end_date: str,
    currency: str | None = None,
    limit: int = 50,
) -> str:
    """Return spending totals grouped by category for the current user."""

    repo = await _repository()
    summary = await repo.category_summary(
        CategorySummaryRequest(
            user_id=_require_active_user_id(),
            start_date=_to_date(start_date),
            end_date=_to_date(end_date),
            currency=_optional_text(currency),
            limit=limit,
        )
    )
    return _response(ok=True, count=len(summary), categories=summary)


@tool
async def create_budget(
    name: str,
    amount: float,
    currency: str,
    period_start: str,
    period_end: str,
    category: str | None = None,
    notes: str | None = None,
) -> str:
    """Create a new budget for the current user."""

    repo = await _repository()
    budget = await repo.create_budget(
        BudgetCreate(
            user_id=_require_active_user_id(),
            name=name,
            category=_optional_text(category),
            amount=_to_decimal(amount),
            currency=currency,
            period_start=_to_date(period_start),
            period_end=_to_date(period_end),
            notes=_optional_text(notes),
        )
    )
    return _response(ok=True, budget=budget)


@tool
async def update_budget(
    budget_id: str,
    name: str | None = None,
    amount: float | str | None = None,
    currency: str | None = None,
    period_start: str | None = None,
    period_end: str | None = None,
    category: str | None = None,
    notes: str | None = None,
) -> str:
    """Update an existing budget for the current user."""

    repo = await _repository()
    budget = await repo.update_budget(
        _require_active_user_id(),
        UUID(budget_id),
        BudgetUpdate(
            name=_optional_text(name),
            amount=_to_decimal(amount),
            currency=_optional_text(currency),
            period_start=_to_date(period_start),
            period_end=_to_date(period_end),
            category=_optional_text(category),
            notes=_optional_text(notes),
        ),
    )

    if budget is None:
        return _response(ok=False, error="Budget not found.")

    return _response(ok=True, budget=budget)


@tool
async def delete_budget(budget_id: str) -> str:
    """Delete a budget for the current user."""

    repo = await _repository()
    deleted = await repo.delete_budget(_require_active_user_id(), UUID(budget_id))
    return _response(ok=deleted)


@tool
async def budget_status(reference_date: str | None = None) -> str:
    """Return current budget statuses and high-level analytics for the current user."""

    repo = await _repository()
    user_id = _require_active_user_id()
    resolved_reference_date = _to_date(reference_date)
    statuses = await repo.budget_status(user_id, resolved_reference_date)
    analytics = await repo.budget_analytics(user_id, resolved_reference_date)
    return _response(
        ok=True,
        count=len(statuses),
        statuses=statuses,
        analytics=analytics,
    )


def get_finance_tools():
    return [
        add_expense,
        update_expense,
        delete_expense,
        list_expenses,
        search_expenses,
        monthly_summary,
        category_summary,
        create_budget,
        update_budget,
        delete_budget,
        budget_status,
    ]
