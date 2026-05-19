"""ChatService — AI-powered financial assistant with tool-calling."""

import os
from datetime import datetime, timedelta
from typing import Any

from beanie import PydanticObjectId
from openai import AsyncOpenAI

from app.core.config import get_settings
from app.modules.chat.application.dtos import ChatMessage, ChatRequest, ChatResponse, FinancialSummaryRequest
from app.modules.transactions.infrastructure.models import Transaction
from app.modules.budgets.infrastructure.models import Budget


class ChatService:
    def __init__(self) -> None:
        settings = get_settings()
        # Use Groq if available, fallback to OpenAI
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            self.client = AsyncOpenAI(
                api_key=groq_api_key,
                base_url="https://api.groq.com/openai/v1",
            )
            self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        elif settings.openai_api_key:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            self.model = settings.openai_model
        else:
            self.client = None
            self.model = None

    async def chat(self, request: ChatRequest, user_id: PydanticObjectId) -> ChatResponse:
        if not self.client:
            raise ValueError("Groq or OpenAI API key not configured")

        # Build conversation history
        messages = [
            {
                "role": "system",
                "content": f"""You are a helpful financial assistant for FinTrack. You can help users:
- Understand their spending patterns
- Track budgets
- Get summaries of transactions
- Answer questions about their finances

Current date: {datetime.now().strftime("%Y-%m-%d")}
Current month: {datetime.now().strftime("%Y-%m")}

CRITICAL: All currency values are in Indian Rupees (INR). You MUST use the ₹ symbol for all currency amounts. Never use dollars ($), USD, or any other currency. Always write amounts as "₹31,000" not "$31,000".

When the user asks about "this month", use the current month ({datetime.now().strftime("%Y-%m")}).
When the user asks about "this week", calculate dates from the current date.

Use the available tools to fetch real financial data when needed.
Be concise and helpful. Always format currency as ₹ (INR).""",
            }
        ]

        # Add history
        for msg in request.conversation_history:
            messages.append({"role": msg.role, "content": msg.content})

        # Add current message
        messages.append({"role": "user", "content": request.message})

        # Define tools
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_transactions_summary",
                    "description": "Get summary of transactions for a date range",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date_from": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                            "date_to": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                        },
                        "required": ["date_from", "date_to"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_category_breakdown",
                    "description": "Get spending breakdown by category for a date range",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date_from": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                            "date_to": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                        },
                        "required": ["date_from", "date_to"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_budget_progress",
                    "description": "Get budget progress for a specific month",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "month": {"type": "string", "description": "Month in YYYY-MM format"},
                        },
                        "required": ["month"],
                    },
                },
            },
        ]

        # Call OpenAI with tools
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        message = response.choices[0].message

        # Handle tool calls
        if message.tool_calls:
            tool_results = []
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_args = eval(tool_call.function.arguments)

                if function_name == "get_transactions_summary":
                    result = await self._get_transactions_summary(user_id, function_args)
                elif function_name == "get_category_breakdown":
                    result = await self._get_category_breakdown(user_id, function_args)
                elif function_name == "get_budget_progress":
                    result = await self._get_budget_progress(user_id, function_args)
                else:
                    result = "Unknown function"

                tool_results.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": str(result),
                    }
                )

            # Get final response with tool results
            messages.append(message.model_dump(exclude_none=True))
            messages.extend(tool_results)

            final_response = await self.client.chat.completions.create(
                model=self.model, messages=messages
            )
            assistant_message = final_response.choices[0].message.content
        else:
            assistant_message = message.content or "I couldn't process that request."

        # Update conversation history
        updated_history = [
            ChatMessage(role=msg.role, content=msg.content) for msg in request.conversation_history
        ]
        updated_history.append(ChatMessage(role="user", content=request.message))
        updated_history.append(ChatMessage(role="assistant", content=assistant_message))

        return ChatResponse(message=assistant_message, conversation_history=updated_history)

    async def generate_summary(self, request: FinancialSummaryRequest, user_id: PydanticObjectId) -> str:
        if not self.client:
            raise ValueError("Groq or OpenAI API key not configured")

        # Determine date range
        now = datetime.utcnow()
        if request.period == "week":
            date_from = now - timedelta(days=7)
        elif request.period == "month":
            date_from = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif request.period == "quarter":
            quarter = (now.month - 1) // 3 + 1
            date_from = now.replace(month=(quarter - 1) * 3 + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:  # year
            date_from = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        date_to = now

        # Fetch data
        transactions_summary = await self._get_transactions_summary(
            user_id, {"date_from": date_from.isoformat(), "date_to": date_to.isoformat()}
        )
        category_breakdown = await self._get_category_breakdown(
            user_id, {"date_from": date_from.isoformat(), "date_to": date_to.isoformat()}
        )
        budget_progress = await self._get_budget_progress(
            user_id, {"month": now.strftime("%Y-%m")}
        )

        print(f"DEBUG generate_summary: transactions_summary={transactions_summary}")
        print(f"DEBUG generate_summary: category_breakdown={category_breakdown}")
        print(f"DEBUG generate_summary: budget_progress={budget_progress}")

        # Generate summary
        prompt = f"""Generate a concise financial summary for the {request.period}:

Transaction Summary:
{transactions_summary}

Category Breakdown:
{category_breakdown}

Budget Progress:
{budget_progress}

IMPORTANT: All currency values are in Indian Rupees (INR). Use ₹ symbol. Never use dollars ($).

Provide insights on:
1. Overall spending vs income
2. Top spending categories
3. Budget adherence
4. Recommendations for improvement

Keep it under 200 words."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.choices[0].message.content or "Could not generate summary."

    async def _get_transactions_summary(
        self, user_id: PydanticObjectId, args: dict[str, Any]
    ) -> dict[str, Any]:
        print(f"DEBUG _get_transactions_summary ENTRY: args={args}")
        
        # Handle both YYYY-MM-DD and ISO format dates
        date_from_str = args["date_from"]
        date_to_str = args["date_to"]
        
        if len(date_from_str) == 10:  # YYYY-MM-DD
            date_from = datetime.strptime(date_from_str, "%Y-%m-%d")
            date_to = datetime.strptime(date_to_str, "%Y-%m-%d")
            # Set end of day for date_to
            date_to = date_to.replace(hour=23, minute=59, second=59)
        else:
            date_from = datetime.fromisoformat(date_from_str)
            date_to = datetime.fromisoformat(date_to_str)

        transactions = await Transaction.find(
            Transaction.user_id == user_id,
            Transaction.date >= date_from,
            Transaction.date <= date_to,
        ).to_list()

        print(f"DEBUG _get_transactions_summary: date_from={date_from}, date_to={date_to}")
        print(f"DEBUG _get_transactions_summary: found {len(transactions)} transactions")
        for t in transactions:
            print(f"DEBUG _get_transactions_summary: transaction - date={t.date}, type={t.type}, amount={t.amount}")

        income = sum(t.amount for t in transactions if t.type == "income")
        expense = sum(t.amount for t in transactions if t.type == "expense")

        print(f"DEBUG _get_transactions_summary: income={income}, expense={expense}")

        result = {
            "period": f"{date_from.date()} to {date_to.date()}",
            "total_income": f"₹{income:,.2f}",
            "total_expense": f"₹{expense:,.2f}",
            "net": f"₹{income - expense:,.2f}",
            "transaction_count": len(transactions),
        }
        return result

    async def _get_category_breakdown(
        self, user_id: PydanticObjectId, args: dict[str, Any]
    ) -> dict[str, Any]:
        # Handle both YYYY-MM-DD and ISO format dates
        date_from_str = args["date_from"]
        date_to_str = args["date_to"]
        
        if len(date_from_str) == 10:  # YYYY-MM-DD
            date_from = datetime.strptime(date_from_str, "%Y-%m-%d")
            date_to = datetime.strptime(date_to_str, "%Y-%m-%d")
            # Set end of day for date_to
            date_to = date_to.replace(hour=23, minute=59, second=59)
        else:
            date_from = datetime.fromisoformat(date_from_str)
            date_to = datetime.fromisoformat(date_to_str)

        transactions = await Transaction.find(
            Transaction.user_id == user_id,
            Transaction.date >= date_from,
            Transaction.date <= date_to,
        ).to_list()

        by_category: dict[str, dict[str, Any]] = {}
        for t in transactions:
            cat_id = str(t.category_id)
            if cat_id not in by_category:
                by_category[cat_id] = {
                    "category_name": t.category_name,
                    "total": 0,
                    "count": 0,
                }
            by_category[cat_id]["total"] += t.amount
            by_category[cat_id]["count"] += 1

        result = {
            "categories": [
                {
                    "category_name": cat["category_name"],
                    "total": f"₹{cat['total']:,.2f}",
                    "count": cat["count"],
                }
                for cat in by_category.values()
            ]
        }
        return result

    async def _get_budget_progress(self, user_id: PydanticObjectId, args: dict[str, Any]) -> dict[str, Any]:
        month = args["month"]
        budgets = await Budget.find(Budget.user_id == user_id, Budget.month == month).to_list()

        # Calculate spending per category
        year, mon = month.split("-")
        date_from = datetime(int(year), int(mon), 1)
        if mon == "12":
            date_to = datetime(int(year) + 1, 1, 1)
        else:
            date_to = datetime(int(year), int(mon) + 1, 1)

        transactions = await Transaction.find(
            Transaction.user_id == user_id,
            Transaction.date >= date_from,
            Transaction.date < date_to,
        ).to_list()

        spent_by_cat: dict[str, float] = {}
        for t in transactions:
            cat_id = str(t.category_id)
            spent_by_cat[cat_id] = spent_by_cat.get(cat_id, 0) + t.amount

        progress = []
        for b in budgets:
            spent = spent_by_cat.get(str(b.category_id), 0)
            progress.append({
                "category_id": str(b.category_id),
                "limit": f"₹{b.limit:,.2f}",
                "spent": f"₹{spent:,.2f}",
                "remaining": f"₹{b.limit - spent:,.2f}",
                "percent": (spent / b.limit * 100) if b.limit > 0 else 0,
            })

        result = {"month": month, "budgets": progress}
        return result
