import asyncio
import json
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
import sys
from uuid import UUID, uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import agent as agent_module
import tool as tool_module
from finance_models import BudgetAnalytics, BudgetCurrencyAnalytics, BudgetStatus, ExpenseRecord


def test_add_expense_tool_uses_active_user_context(monkeypatch) -> None:
    captured = {}
    expense_id = uuid4()

    class FakeRepository:
        async def add_expense(self, payload):
            captured["payload"] = payload
            return ExpenseRecord(
                id=expense_id,
                user_id=payload.user_id,
                description=payload.description,
                category=payload.category,
                amount=payload.amount,
                currency=payload.currency,
                spent_at=payload.spent_at,
                merchant=payload.merchant,
                notes=payload.notes,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

    async def fake_repository():
        return FakeRepository()

    monkeypatch.setattr(tool_module, "_repository", fake_repository)
    token = tool_module.set_active_user_id("user-123")

    try:
        response = asyncio.run(
            tool_module.add_expense.ainvoke(
                {
                    "description": "Coffee",
                    "category": "dining",
                    "amount": "4.50",
                    "currency": "usd",
                    "merchant": "Cafe",
                }
            )
        )
    finally:
        tool_module.reset_active_user_id(token)

    parsed = json.loads(response)
    assert parsed["ok"] is True
    assert parsed["expense"]["user_id"] == "user-123"
    assert parsed["expense"]["currency"] == "USD"
    assert captured["payload"].user_id == "user-123"
    assert captured["payload"].currency == "USD"


def test_budget_status_tool_returns_statuses_and_analytics(monkeypatch) -> None:
    budget_id = uuid4()

    class FakeRepository:
        async def budget_status(self, user_id: str, reference_date: date | None):
            assert user_id == "user-123"
            assert reference_date == date(2026, 5, 1)
            return [
                BudgetStatus(
                    budget_id=budget_id,
                    user_id=user_id,
                    name="Groceries",
                    category="groceries",
                    currency="USD",
                    period_start=date(2026, 5, 1),
                    period_end=date(2026, 5, 31),
                    budget_amount=Decimal("200.00"),
                    spent_amount=Decimal("170.00"),
                    remaining_amount=Decimal("30.00"),
                    usage_percentage=Decimal("85.00"),
                    expense_count=4,
                    status="at_risk",
                )
            ]

        async def budget_analytics(self, user_id: str, reference_date: date | None):
            assert user_id == "user-123"
            assert reference_date == date(2026, 5, 1)
            return BudgetAnalytics(
                total_budgets=1,
                active_budgets=1,
                over_budget_count=0,
                at_risk_count=1,
                on_track_count=0,
                totals_by_currency=[
                    BudgetCurrencyAnalytics(
                        currency="USD",
                        total_budgeted_amount=Decimal("200.00"),
                        total_spent_amount=Decimal("170.00"),
                        total_remaining_amount=Decimal("30.00"),
                        over_budget_count=0,
                        at_risk_count=1,
                    )
                ],
            )

    async def fake_repository():
        return FakeRepository()

    monkeypatch.setattr(tool_module, "_repository", fake_repository)
    token = tool_module.set_active_user_id("user-123")

    try:
        response = asyncio.run(
            tool_module.budget_status.ainvoke(
                {
                    "reference_date": "2026-05-01",
                }
            )
        )
    finally:
        tool_module.reset_active_user_id(token)

    parsed = json.loads(response)
    assert parsed["ok"] is True
    assert parsed["count"] == 1
    assert parsed["statuses"][0]["budget_id"] == str(budget_id)
    assert parsed["analytics"]["at_risk_count"] == 1


def test_get_finance_tools_exposes_required_tool_names() -> None:
    tool_names = [tool.name for tool in tool_module.get_finance_tools()]

    assert tool_names == [
        "add_expense",
        "update_expense",
        "delete_expense",
        "list_expenses",
        "search_expenses",
        "monthly_summary",
        "category_summary",
        "create_budget",
        "update_budget",
        "delete_budget",
        "budget_status",
    ]


def test_agent_registers_finance_tools(monkeypatch) -> None:
    captured = {}

    def fake_create_agent(*, model, tools, system_prompt):
        captured["model"] = model
        captured["tools"] = tools
        captured["system_prompt"] = system_prompt
        return object()

    monkeypatch.setattr(agent_module, "create_agent", fake_create_agent)
    agent_module.get_expense_agent.cache_clear()

    try:
        expense_agent = agent_module.get_expense_agent()
    finally:
        agent_module.get_expense_agent.cache_clear()

    assert expense_agent is not None
    assert [tool.name for tool in captured["tools"]] == [
        "add_expense",
        "update_expense",
        "delete_expense",
        "list_expenses",
        "search_expenses",
        "monthly_summary",
        "category_summary",
        "create_budget",
        "update_budget",
        "delete_budget",
        "budget_status",
    ]
    assert "Never ask the user for a user_id or thread_id" in captured["system_prompt"]
