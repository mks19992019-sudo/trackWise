from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated
from fastapi import FastAPI, HTTPException, Query
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, ConfigDict, StringConstraints
from redis.asyncio import Redis

from database import close_db_pool, initialize_database, get_db_pool
from finance_repository import get_finance_repository
from graph import close_graph_resources, get_checkpointer, get_workflow

SESSION_TTL_SECONDS = 20
TrimmedText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

Redis_client = Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
)


class ChatMessage(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    message: TrimmedText
    thread_id: TrimmedText


class ExpenseSummary(BaseModel):
    """Summary of expenses for the UI dashboard"""
    total_amount: float
    total_count: int
    currency: str
    date_range: dict


class CategoryBreakdown(BaseModel):
    """Expense breakdown by category"""
    category: str
    amount: float
    count: int
    percentage: float


@asynccontextmanager
async def lifespan(_: FastAPI):
    # start server
    await initialize_database()

    try:
        yield
    finally:
        # shutdown the server
        await Redis_client.aclose()
        await close_graph_resources()
        await close_db_pool()


app = FastAPI(
    title="Finance AI System",
    description="AI-powered personal finance management",
    lifespan=lifespan
)


# ============================================================================
# AGENTIC ENDPOINTS (Main Focus)
# ============================================================================

@app.get("/")
async def home():
    """Health check endpoint"""
    return {"message": "Finance AI System is running"}


@app.post("/chat")
async def chat(payload: ChatMessage):
    """Main chat endpoint - AI agent processes user messages"""
    thread_id = payload.thread_id
    user_message = payload.message
    session_key = f"session:{thread_id}"
    
    if not await Redis_client.exists(session_key):
        checkpointer = await get_checkpointer()
        await checkpointer.adelete_thread(thread_id)

    await Redis_client.set(session_key, "active", ex=SESSION_TTL_SECONDS)

    workflow = await get_workflow()
    result = await workflow.ainvoke(
        {
            "messages": [HumanMessage(content=user_message)],
            "thread_id": thread_id,
        },
        {"configurable": {"thread_id": thread_id}},
    )

    response_messages = result.get("messages", [])

    if not response_messages:
        raise HTTPException(status_code=500, detail="Workflow returned no messages.")

    return response_messages[-1].content


# ============================================================================
# DATABASE QUERY ENDPOINTS (UI Support)
# ============================================================================

@app.get("/api/expenses/summary", response_model=ExpenseSummary)
async def get_expense_summary(
    user_id: str = Query(..., description="User ID"),
    limit_days: int = Query(30, ge=1, le=365, description="Number of days to look back")
):
    """Get total expense summary for the UI dashboard"""
    try:
        pool = await get_db_pool()
        repo = await get_finance_repository()
        
        # Get expenses from the past N days
        cutoff_date = datetime.now(timezone.utc)
        start_date = cutoff_date.date()
        
        from finance_models import ExpenseListFilters
        filters = ExpenseListFilters(
            user_id=user_id,
            limit=1000,
        )
        
        expenses = await repo.list_expenses(filters)
        
        if not expenses:
            return ExpenseSummary(
                total_amount=0.0,
                total_count=0,
                currency="USD",
                date_range={"from": start_date.isoformat(), "to": cutoff_date.date().isoformat()}
            )
        
        total = sum(float(exp.amount) for exp in expenses)
        currency = expenses[0].currency if expenses else "USD"
        
        return ExpenseSummary(
            total_amount=total,
            total_count=len(expenses),
            currency=currency,
            date_range={
                "from": min(exp.spent_at.date() for exp in expenses).isoformat(),
                "to": max(exp.spent_at.date() for exp in expenses).isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching summary: {str(e)}")


@app.get("/api/expenses/by-category", response_model=list[CategoryBreakdown])
async def get_expenses_by_category(
    user_id: str = Query(..., description="User ID"),
):
    """Get expense breakdown by category for UI charts"""
    try:
        repo = await get_finance_repository()
        
        from finance_models import ExpenseListFilters
        filters = ExpenseListFilters(user_id=user_id, limit=1000)
        expenses = await repo.list_expenses(filters)
        
        if not expenses:
            return []
        
        # Group by category
        category_map = {}
        total_amount = 0
        
        for exp in expenses:
            category = exp.category or "Uncategorized"
            if category not in category_map:
                category_map[category] = {"amount": 0.0, "count": 0}
            
            category_map[category]["amount"] += float(exp.amount)
            category_map[category]["count"] += 1
            total_amount += float(exp.amount)
        
        # Convert to response format
        result = []
        for category, data in sorted(category_map.items(), key=lambda x: x[1]["amount"], reverse=True):
            percentage = (data["amount"] / total_amount * 100) if total_amount > 0 else 0
            result.append(CategoryBreakdown(
                category=category,
                amount=data["amount"],
                count=data["count"],
                percentage=round(percentage, 2)
            ))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")


@app.get("/api/expenses/recent")
async def get_recent_expenses(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(10, ge=1, le=100, description="Number of recent expenses to fetch")
):
    """Get recent expenses for UI list view"""
    try:
        repo = await get_finance_repository()
        
        from finance_models import ExpenseListFilters
        filters = ExpenseListFilters(user_id=user_id, limit=limit)
        expenses = await repo.list_expenses(filters)
        
        return [
            {
                "id": str(exp.id),
                "description": exp.description,
                "category": exp.category,
                "amount": float(exp.amount),
                "currency": exp.currency,
                "merchant": exp.merchant,
                "spent_at": exp.spent_at.isoformat(),
            }
            for exp in expenses
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching expenses: {str(e)}")


@app.get("/api/expenses/monthly")
async def get_monthly_summary(
    user_id: str = Query(..., description="User ID"),
    year: int = Query(..., ge=2000, le=2100, description="Year"),
    month: int = Query(..., ge=1, le=12, description="Month")
):
    """Get monthly expense summary"""
    try:
        repo = await get_finance_repository()
        
        from finance_models import MonthlySummaryRequest
        request = MonthlySummaryRequest(user_id=user_id, year=year, month=month)
        summary = await repo.monthly_summary(request)
        
        return {
            "year": year,
            "month": month,
            "total_amount": float(summary.total_amount),
            "total_count": summary.total_count,
            "currency_totals": [
                {"currency": ct.currency, "amount": float(ct.amount)}
                for ct in summary.currency_totals
            ],
            "category_summaries": [
                {
                    "category": cs.category,
                    "amount": float(cs.amount),
                    "count": cs.count,
                }
                for cs in summary.category_summaries
            ] if summary.category_summaries else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching monthly summary: {str(e)}")


@app.get("/api/budgets")
async def get_budgets(
    user_id: str = Query(..., description="User ID"),
):
    """Get all budgets for the user"""
    try:
        repo = await get_finance_repository()
        budgets = await repo.list_budgets(user_id=user_id)
        
        return [
            {
                "id": str(budget.id),
                "category": budget.category,
                "amount": float(budget.amount),
                "currency": budget.currency,
                "start_date": budget.start_date.isoformat() if budget.start_date else None,
                "end_date": budget.end_date.isoformat() if budget.end_date else None,
            }
            for budget in budgets
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching budgets: {str(e)}")


@app.get("/api/budgets/status")
async def get_budget_status(
    user_id: str = Query(..., description="User ID"),
    category: str = Query(..., description="Budget category"),
):
    """Get budget status for a specific category"""
    try:
        repo = await get_finance_repository()
        
        from finance_models import BudgetAnalytics
        status = await repo.budget_status(user_id=user_id, category=category)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"No budget found for category: {category}")
        
        return {
            "category": status.category,
            "budget_amount": float(status.budget_amount),
            "spent_amount": float(status.spent_amount),
            "remaining": float(status.budget_amount - status.spent_amount),
            "usage_percentage": float((status.spent_amount / status.budget_amount * 100) if status.budget_amount > 0 else 0),
            "status": "over_budget" if status.spent_amount > status.budget_amount else (
                "at_risk" if (status.spent_amount / status.budget_amount * 100 if status.budget_amount > 0 else 0) >= 80 else "on_track"
            ),
            "currency": status.currency,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching budget status: {str(e)}")


@app.get("/api/stats/quick")
async def get_quick_stats(
    user_id: str = Query(..., description="User ID"),
):
    """Get quick statistics for UI dashboard cards"""
    try:
        repo = await get_finance_repository()
        
        # Get all expenses
        from finance_models import ExpenseListFilters
        filters = ExpenseListFilters(user_id=user_id, limit=10000)
        expenses = await repo.list_expenses(filters)
        
        if not expenses:
            return {
                "total_expenses": 0.0,
                "average_expense": 0.0,
                "highest_expense": 0.0,
                "transaction_count": 0,
            }
        
        amounts = [float(exp.amount) for exp in expenses]
        
        return {
            "total_expenses": sum(amounts),
            "average_expense": sum(amounts) / len(amounts) if amounts else 0,
            "highest_expense": max(amounts),
            "transaction_count": len(amounts),
            "currency": expenses[0].currency if expenses else "USD",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")
