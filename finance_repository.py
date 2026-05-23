from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import asyncpg

from database import initialize_database
from finance_models import (
    BudgetAnalytics,
    BudgetCreate,
    BudgetCurrencyAnalytics,
    BudgetRecord,
    BudgetStatus,
    BudgetUpdate,
    CategorySummaryItem,
    CategorySummaryRequest,
    CurrencyTotal,
    ExpenseCreate,
    ExpenseListFilters,
    ExpenseRecord,
    ExpenseSearchFilters,
    ExpenseUpdate,
    MonthlySummary,
    MonthlySummaryRequest,
)

AT_RISK_PERCENTAGE = Decimal("80")
HUNDRED = Decimal("100")
ZERO = Decimal("0")
EXPENSE_SEARCH_VECTOR_SQL = (
    "to_tsvector("
    "'simple', "
    "coalesce(description, '') || ' ' || category || ' ' || "
    "coalesce(merchant, '') || ' ' || coalesce(notes, '')"
    ")"
)


def _month_window(year: int, month: int) -> tuple[datetime, datetime]:
    start = datetime(year, month, 1, tzinfo=timezone.utc)

    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)

    return start, end


def _day_start(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def _day_end_exclusive(value: date) -> datetime:
    return datetime.combine(value + timedelta(days=1), time.min, tzinfo=timezone.utc)


def _decimal_or_zero(value: Decimal | None) -> Decimal:
    return value if value is not None else ZERO


def _usage_percentage(spent_amount: Decimal, budget_amount: Decimal) -> Decimal:
    if budget_amount == ZERO:
        return ZERO

    return (spent_amount / budget_amount * HUNDRED).quantize(Decimal("0.01"))


def _budget_status_label(spent_amount: Decimal, budget_amount: Decimal) -> str:
    usage = _usage_percentage(spent_amount, budget_amount)

    if spent_amount > budget_amount:
        return "over_budget"

    if usage >= AT_RISK_PERCENTAGE:
        return "at_risk"

    return "on_track"


def _expense_record(row: asyncpg.Record) -> ExpenseRecord:
    return ExpenseRecord.model_validate(dict(row))


def _budget_record(row: asyncpg.Record) -> BudgetRecord:
    return BudgetRecord.model_validate(dict(row))


@dataclass(slots=True)
class FinanceRepository:
    pool: asyncpg.Pool

    async def add_expense(self, payload: ExpenseCreate) -> ExpenseRecord:
        expense_id = uuid4()
        row = await self.pool.fetchrow(
            """
            INSERT INTO expenses (
                id,
                user_id,
                description,
                category,
                amount,
                currency,
                spent_at,
                merchant,
                notes
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING
                id,
                user_id,
                description,
                category,
                amount,
                currency,
                spent_at,
                merchant,
                notes,
                created_at,
                updated_at
            """,
            expense_id,
            payload.user_id,
            payload.description,
            payload.category,
            payload.amount,
            payload.currency,
            payload.spent_at,
            payload.merchant,
            payload.notes,
        )
        assert row is not None
        return _expense_record(row)

    async def update_expense(
        self,
        user_id: str,
        expense_id: UUID,
        payload: ExpenseUpdate,
    ) -> ExpenseRecord | None:
        updates = payload.model_dump(exclude_unset=True)
        assignments: list[str] = []
        args: list[Any] = [expense_id, user_id]

        for field_name, value in updates.items():
            args.append(value)
            assignments.append(f"{field_name} = ${len(args)}")

        args.append(datetime.now(timezone.utc))
        assignments.append(f"updated_at = ${len(args)}")

        row = await self.pool.fetchrow(
            f"""
            UPDATE expenses
            SET {", ".join(assignments)}
            WHERE id = $1 AND user_id = $2
            RETURNING
                id,
                user_id,
                description,
                category,
                amount,
                currency,
                spent_at,
                merchant,
                notes,
                created_at,
                updated_at
            """,
            *args,
        )

        if row is None:
            return None

        return _expense_record(row)

    async def delete_expense(self, user_id: str, expense_id: UUID) -> bool:
        result = await self.pool.execute(
            """
            DELETE FROM expenses
            WHERE id = $1 AND user_id = $2
            """,
            expense_id,
            user_id,
        )
        return result.endswith("1")

    async def list_expenses(self, filters: ExpenseListFilters) -> list[ExpenseRecord]:
        where_clauses = ["user_id = $1"]
        args: list[Any] = [filters.user_id]

        def add_clause(clause: str, value: Any) -> None:
            args.append(value)
            where_clauses.append(clause.format(index=len(args)))

        if filters.category:
            add_clause("category = ${index}", filters.category)
        if filters.currency:
            add_clause("currency = ${index}", filters.currency)
        if filters.date_from:
            add_clause("spent_at >= ${index}", filters.date_from)
        if filters.date_to:
            add_clause("spent_at <= ${index}", filters.date_to)
        if filters.min_amount:
            add_clause("amount >= ${index}", filters.min_amount)
        if filters.max_amount:
            add_clause("amount <= ${index}", filters.max_amount)

        args.extend([filters.limit, filters.offset])
        rows = await self.pool.fetch(
            f"""
            SELECT
                id,
                user_id,
                description,
                category,
                amount,
                currency,
                spent_at,
                merchant,
                notes,
                created_at,
                updated_at
            FROM expenses
            WHERE {" AND ".join(where_clauses)}
            ORDER BY spent_at DESC, created_at DESC
            LIMIT ${len(args) - 1}
            OFFSET ${len(args)}
            """,
            *args,
        )
        return [_expense_record(row) for row in rows]

    async def search_expenses(self, filters: ExpenseSearchFilters) -> list[ExpenseRecord]:
        if not filters.query:
            return await self.list_expenses(filters)

        where_clauses = ["user_id = $1"]
        args: list[Any] = [filters.user_id]

        def add_clause(clause: str, value: Any) -> None:
            args.append(value)
            where_clauses.append(clause.format(index=len(args)))

        if filters.category:
            add_clause("category = ${index}", filters.category)
        if filters.currency:
            add_clause("currency = ${index}", filters.currency)
        if filters.date_from:
            add_clause("spent_at >= ${index}", filters.date_from)
        if filters.date_to:
            add_clause("spent_at <= ${index}", filters.date_to)
        if filters.min_amount:
            add_clause("amount >= ${index}", filters.min_amount)
        if filters.max_amount:
            add_clause("amount <= ${index}", filters.max_amount)

        args.append(filters.query)
        tsquery_index = len(args)
        args.append(f"%{filters.query}%")
        ilike_index = len(args)
        where_clauses.append(
            "("
            f"{EXPENSE_SEARCH_VECTOR_SQL} @@ websearch_to_tsquery('simple', ${tsquery_index}) "
            f"OR description ILIKE ${ilike_index} "
            f"OR merchant ILIKE ${ilike_index} "
            f"OR notes ILIKE ${ilike_index}"
            ")"
        )

        args.extend([filters.limit, filters.offset])
        rows = await self.pool.fetch(
            f"""
            SELECT
                id,
                user_id,
                description,
                category,
                amount,
                currency,
                spent_at,
                merchant,
                notes,
                created_at,
                updated_at
            FROM expenses
            WHERE {" AND ".join(where_clauses)}
            ORDER BY
                ts_rank({EXPENSE_SEARCH_VECTOR_SQL}, websearch_to_tsquery('simple', ${tsquery_index})) DESC,
                spent_at DESC,
                created_at DESC
            LIMIT ${len(args) - 1}
            OFFSET ${len(args)}
            """,
            *args,
        )
        return [_expense_record(row) for row in rows]

    async def monthly_summary(self, request: MonthlySummaryRequest) -> MonthlySummary:
        start, end = _month_window(request.year, request.month)
        filters = [request.user_id, start, end]
        currency_condition = ""

        if request.currency:
            filters.append(request.currency)
            currency_condition = f" AND currency = ${len(filters)}"

        aggregate_row = await self.pool.fetchrow(
            f"""
            SELECT
                COUNT(*)::INT AS expense_count,
                COUNT(DISTINCT category)::INT AS category_count
            FROM expenses
            WHERE user_id = $1
              AND spent_at >= $2
              AND spent_at < $3
              {currency_condition}
            """,
            *filters,
        )

        totals_rows = await self.pool.fetch(
            f"""
            SELECT
                currency,
                COALESCE(SUM(amount), 0)::NUMERIC(12, 2) AS total_amount,
                COALESCE(AVG(amount), 0)::NUMERIC(12, 2) AS average_amount
            FROM expenses
            WHERE user_id = $1
              AND spent_at >= $2
              AND spent_at < $3
              {currency_condition}
            GROUP BY currency
            ORDER BY currency
            """,
            *filters,
        )

        top_category_row = await self.pool.fetchrow(
            f"""
            SELECT category
            FROM expenses
            WHERE user_id = $1
              AND spent_at >= $2
              AND spent_at < $3
              {currency_condition}
            GROUP BY category
            ORDER BY SUM(amount) DESC, COUNT(*) DESC, category ASC
            LIMIT 1
            """,
            *filters,
        )

        return MonthlySummary(
            year=request.year,
            month=request.month,
            expense_count=(aggregate_row["expense_count"] if aggregate_row else 0),
            category_count=(aggregate_row["category_count"] if aggregate_row else 0),
            top_category=(top_category_row["category"] if top_category_row else None),
            totals_by_currency=[
                CurrencyTotal.model_validate(dict(row))
                for row in totals_rows
            ],
        )

    async def category_summary(
        self,
        request: CategorySummaryRequest,
    ) -> list[CategorySummaryItem]:
        start = _day_start(request.start_date)
        end = _day_end_exclusive(request.end_date)
        args: list[Any] = [request.user_id, start, end]
        currency_condition = ""

        if request.currency:
            args.append(request.currency)
            currency_condition = f" AND currency = ${len(args)}"

        args.append(request.limit)
        rows = await self.pool.fetch(
            f"""
            SELECT
                category,
                currency,
                COALESCE(SUM(amount), 0)::NUMERIC(12, 2) AS total_amount,
                COALESCE(AVG(amount), 0)::NUMERIC(12, 2) AS average_amount,
                COUNT(*)::INT AS expense_count,
                MIN(spent_at) AS first_spent_at,
                MAX(spent_at) AS last_spent_at
            FROM expenses
            WHERE user_id = $1
              AND spent_at >= $2
              AND spent_at < $3
              {currency_condition}
            GROUP BY category, currency
            ORDER BY total_amount DESC, expense_count DESC, category ASC
            LIMIT ${len(args)}
            """,
            *args,
        )
        return [CategorySummaryItem.model_validate(dict(row)) for row in rows]

    async def create_budget(self, payload: BudgetCreate) -> BudgetRecord:
        budget_id = uuid4()
        row = await self.pool.fetchrow(
            """
            INSERT INTO budgets (
                id,
                user_id,
                name,
                category,
                amount,
                currency,
                period_start,
                period_end,
                notes
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING
                id,
                user_id,
                name,
                category,
                amount,
                currency,
                period_start,
                period_end,
                notes,
                created_at,
                updated_at
            """,
            budget_id,
            payload.user_id,
            payload.name,
            payload.category,
            payload.amount,
            payload.currency,
            payload.period_start,
            payload.period_end,
            payload.notes,
        )
        assert row is not None
        return _budget_record(row)

    async def update_budget(
        self,
        user_id: str,
        budget_id: UUID,
        payload: BudgetUpdate,
    ) -> BudgetRecord | None:
        current_row = await self.pool.fetchrow(
            """
            SELECT period_start, period_end
            FROM budgets
            WHERE id = $1 AND user_id = $2
            """,
            budget_id,
            user_id,
        )

        if current_row is None:
            return None

        updates = payload.model_dump(exclude_unset=True)
        period_start = updates.get("period_start", current_row["period_start"])
        period_end = updates.get("period_end", current_row["period_end"])

        if period_end < period_start:
            raise ValueError("period_end must be later than or equal to period_start.")

        assignments: list[str] = []
        args: list[Any] = [budget_id, user_id]

        for field_name, value in updates.items():
            args.append(value)
            assignments.append(f"{field_name} = ${len(args)}")

        args.append(datetime.now(timezone.utc))
        assignments.append(f"updated_at = ${len(args)}")

        row = await self.pool.fetchrow(
            f"""
            UPDATE budgets
            SET {", ".join(assignments)}
            WHERE id = $1 AND user_id = $2
            RETURNING
                id,
                user_id,
                name,
                category,
                amount,
                currency,
                period_start,
                period_end,
                notes,
                created_at,
                updated_at
            """,
            *args,
        )

        if row is None:
            return None

        return _budget_record(row)

    async def delete_budget(self, user_id: str, budget_id: UUID) -> bool:
        result = await self.pool.execute(
            """
            DELETE FROM budgets
            WHERE id = $1 AND user_id = $2
            """,
            budget_id,
            user_id,
        )
        return result.endswith("1")

    async def list_budgets(
        self,
        user_id: str,
        reference_date: date | None = None,
    ) -> list[BudgetRecord]:
        args: list[Any] = [user_id]
        date_condition = ""

        if reference_date is not None:
            args.append(reference_date)
            date_condition = f" AND ${len(args)} BETWEEN period_start AND period_end"

        rows = await self.pool.fetch(
            f"""
            SELECT
                id,
                user_id,
                name,
                category,
                amount,
                currency,
                period_start,
                period_end,
                notes,
                created_at,
                updated_at
            FROM budgets
            WHERE user_id = $1
              {date_condition}
            ORDER BY period_start DESC, created_at DESC
            """,
            *args,
        )
        return [_budget_record(row) for row in rows]

    async def budget_status(
        self,
        user_id: str,
        reference_date: date | None = None,
    ) -> list[BudgetStatus]:
        effective_date = reference_date or date.today()
        rows = await self.pool.fetch(
            """
            SELECT
                b.id AS budget_id,
                b.user_id,
                b.name,
                b.category,
                b.currency,
                b.period_start,
                b.period_end,
                b.amount AS budget_amount,
                COALESCE(SUM(e.amount), 0)::NUMERIC(12, 2) AS spent_amount,
                COUNT(e.id)::INT AS expense_count
            FROM budgets AS b
            LEFT JOIN expenses AS e
                ON e.user_id = b.user_id
               AND e.currency = b.currency
               AND (b.category IS NULL OR e.category = b.category)
               AND e.spent_at >= b.period_start::TIMESTAMPTZ
               AND e.spent_at < (b.period_end + INTERVAL '1 day')::TIMESTAMPTZ
            WHERE b.user_id = $1
              AND $2 BETWEEN b.period_start AND b.period_end
            GROUP BY
                b.id,
                b.user_id,
                b.name,
                b.category,
                b.currency,
                b.period_start,
                b.period_end,
                b.amount
            ORDER BY b.period_start DESC, b.created_at DESC
            """,
            user_id,
            effective_date,
        )

        statuses: list[BudgetStatus] = []
        for row in rows:
            spent_amount = _decimal_or_zero(row["spent_amount"])
            budget_amount = row["budget_amount"]
            remaining_amount = (budget_amount - spent_amount).quantize(Decimal("0.01"))
            usage_percentage = _usage_percentage(spent_amount, budget_amount)

            statuses.append(
                BudgetStatus(
                    budget_id=row["budget_id"],
                    user_id=row["user_id"],
                    name=row["name"],
                    category=row["category"],
                    currency=row["currency"],
                    period_start=row["period_start"],
                    period_end=row["period_end"],
                    budget_amount=budget_amount,
                    spent_amount=spent_amount,
                    remaining_amount=remaining_amount,
                    usage_percentage=usage_percentage,
                    expense_count=row["expense_count"],
                    status=_budget_status_label(spent_amount, budget_amount),
                )
            )

        return statuses

    async def budget_analytics(
        self,
        user_id: str,
        reference_date: date | None = None,
    ) -> BudgetAnalytics:
        statuses = await self.budget_status(user_id, reference_date)
        totals: dict[str, dict[str, Decimal | int]] = {}
        over_budget_count = 0
        at_risk_count = 0
        on_track_count = 0

        for status in statuses:
            currency_totals = totals.setdefault(
                status.currency,
                {
                    "total_budgeted_amount": ZERO,
                    "total_spent_amount": ZERO,
                    "total_remaining_amount": ZERO,
                    "over_budget_count": 0,
                    "at_risk_count": 0,
                },
            )
            currency_totals["total_budgeted_amount"] += status.budget_amount
            currency_totals["total_spent_amount"] += status.spent_amount
            currency_totals["total_remaining_amount"] += status.remaining_amount

            if status.status == "over_budget":
                over_budget_count += 1
                currency_totals["over_budget_count"] += 1
            elif status.status == "at_risk":
                at_risk_count += 1
                currency_totals["at_risk_count"] += 1
            else:
                on_track_count += 1

        return BudgetAnalytics(
            total_budgets=len(statuses),
            active_budgets=len(statuses),
            over_budget_count=over_budget_count,
            at_risk_count=at_risk_count,
            on_track_count=on_track_count,
            totals_by_currency=[
                BudgetCurrencyAnalytics(
                    currency=currency,
                    total_budgeted_amount=values["total_budgeted_amount"],
                    total_spent_amount=values["total_spent_amount"],
                    total_remaining_amount=values["total_remaining_amount"],
                    over_budget_count=values["over_budget_count"],
                    at_risk_count=values["at_risk_count"],
                )
                for currency, values in sorted(totals.items())
            ],
        )


async def get_finance_repository() -> FinanceRepository:
    pool = await initialize_database()
    return FinanceRepository(pool=pool)
