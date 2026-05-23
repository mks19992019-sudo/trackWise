import asyncio
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import sys
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database import close_db_pool
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


def test_expense_repository_crud_and_summaries() -> None:
    async def scenario() -> None:
        await close_db_pool()
        user_id = f"test-user-{uuid4()}"
        now = datetime.now(timezone.utc).replace(microsecond=0)
        repo = None
        repo = await get_finance_repository()

        try:
            expense_one = await repo.add_expense(
                ExpenseCreate(
                    user_id=user_id,
                    description="Weekly groceries",
                    category="groceries",
                    amount=Decimal("120.50"),
                    currency="usd",
                    spent_at=now,
                    merchant="Fresh Mart",
                    notes="vegetables and fruit",
                )
            )
            expense_two = await repo.add_expense(
                ExpenseCreate(
                    user_id=user_id,
                    description="Train pass",
                    category="transport",
                    amount=Decimal("60.00"),
                    currency="USD",
                    spent_at=now - timedelta(days=1),
                    merchant="Metro",
                )
            )
            expense_three = await repo.add_expense(
                ExpenseCreate(
                    user_id=user_id,
                    description="Extra groceries",
                    category="groceries",
                    amount=Decimal("30.00"),
                    currency="USD",
                    spent_at=now - timedelta(days=2),
                    merchant="Fresh Mart",
                )
            )

            listed = await repo.list_expenses(
                ExpenseListFilters(
                    user_id=user_id,
                    limit=10,
                )
            )
            assert [expense.id for expense in listed] == [
                expense_one.id,
                expense_two.id,
                expense_three.id,
            ]

            updated = await repo.update_expense(
                user_id,
                expense_one.id,
                ExpenseUpdate(
                    amount=Decimal("125.00"),
                    notes="weekly groceries refill",
                ),
            )
            assert updated is not None
            assert updated.amount == Decimal("125.00")
            assert updated.notes == "weekly groceries refill"

            searched = await repo.search_expenses(
                ExpenseSearchFilters(
                    user_id=user_id,
                    query="groceries",
                    limit=10,
                )
            )
            assert len(searched) == 2
            assert all(expense.category == "groceries" for expense in searched)

            monthly_summary = await repo.monthly_summary(
                MonthlySummaryRequest(
                    user_id=user_id,
                    year=now.year,
                    month=now.month,
                    currency="USD",
                )
            )
            assert monthly_summary.expense_count == 3
            assert monthly_summary.category_count == 2
            assert monthly_summary.top_category == "groceries"
            assert monthly_summary.totals_by_currency[0].total_amount == Decimal("215.00")

            category_summary = await repo.category_summary(
                CategorySummaryRequest(
                    user_id=user_id,
                    start_date=now.date() - timedelta(days=7),
                    end_date=now.date(),
                    currency="USD",
                )
            )
            assert category_summary[0].category == "groceries"
            assert category_summary[0].total_amount == Decimal("155.00")
            assert category_summary[0].expense_count == 2

            deleted = await repo.delete_expense(user_id, expense_two.id)
            assert deleted is True

            missing_delete = await repo.delete_expense("wrong-user", expense_three.id)
            assert missing_delete is False
        finally:
            if repo is not None:
                async with repo.pool.acquire() as connection:
                    await connection.execute("DELETE FROM budgets WHERE user_id = $1", user_id)
                    await connection.execute("DELETE FROM expenses WHERE user_id = $1", user_id)
            await close_db_pool()

    asyncio.run(scenario())


def test_budget_repository_status_and_analytics() -> None:
    async def scenario() -> None:
        await close_db_pool()
        user_id = f"test-user-{uuid4()}"
        today = date.today()
        period_start = today.replace(day=1)
        next_month = (period_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        period_end = next_month - timedelta(days=1)
        repo = None
        repo = await get_finance_repository()

        try:
            await repo.add_expense(
                ExpenseCreate(
                    user_id=user_id,
                    description="Groceries batch one",
                    category="groceries",
                    amount=Decimal("90.00"),
                    currency="USD",
                    spent_at=datetime.now(timezone.utc).replace(microsecond=0),
                    merchant="Fresh Mart",
                )
            )
            await repo.add_expense(
                ExpenseCreate(
                    user_id=user_id,
                    description="Groceries batch two",
                    category="groceries",
                    amount=Decimal("80.00"),
                    currency="USD",
                    spent_at=datetime.now(timezone.utc).replace(microsecond=0) - timedelta(days=1),
                    merchant="Fresh Mart",
                )
            )

            budget = await repo.create_budget(
                BudgetCreate(
                    user_id=user_id,
                    name="Monthly groceries",
                    category="groceries",
                    amount=Decimal("200.00"),
                    currency="USD",
                    period_start=period_start,
                    period_end=period_end,
                    notes="Primary grocery budget",
                )
            )

            budgets = await repo.list_budgets(user_id, today)
            assert len(budgets) == 1
            assert budgets[0].id == budget.id

            statuses = await repo.budget_status(user_id, today)
            assert len(statuses) == 1
            assert statuses[0].spent_amount == Decimal("170.00")
            assert statuses[0].remaining_amount == Decimal("30.00")
            assert statuses[0].status == "at_risk"

            analytics = await repo.budget_analytics(user_id, today)
            assert analytics.total_budgets == 1
            assert analytics.at_risk_count == 1
            assert analytics.over_budget_count == 0
            assert analytics.totals_by_currency[0].total_spent_amount == Decimal("170.00")

            updated_budget = await repo.update_budget(
                user_id,
                budget.id,
                BudgetUpdate(
                    amount=Decimal("160.00"),
                    notes="Adjusted down after review",
                ),
            )
            assert updated_budget is not None
            assert updated_budget.amount == Decimal("160.00")

            updated_statuses = await repo.budget_status(user_id, today)
            assert updated_statuses[0].status == "over_budget"

            deleted = await repo.delete_budget(user_id, budget.id)
            assert deleted is True
        finally:
            if repo is not None:
                async with repo.pool.acquire() as connection:
                    await connection.execute("DELETE FROM budgets WHERE user_id = $1", user_id)
                    await connection.execute("DELETE FROM expenses WHERE user_id = $1", user_id)
            await close_db_pool()

    asyncio.run(scenario())
