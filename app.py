#!/usr/bin/env python3
"""
Expense Tracker CLI

Features:
- Add expenses
- List expenses
- Delete expenses
- Show summaries by category and date range
- Persistent storage in JSON

Run:
    python expense_tracker.py
"""

from __future__ import annotations

import json
import sys
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional


DATA_FILE = Path("expenses.json")
DATE_FMT = "%Y-%m-%d"


@dataclass
class Expense:
    id: str
    title: str
    amount: float
    category: str
    created_at: str  # YYYY-MM-DD


def load_expenses() -> List[Expense]:
    if not DATA_FILE.exists():
        return []

    try:
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        expenses = []
        for item in raw:
            expenses.append(
                Expense(
                    id=item["id"],
                    title=item["title"],
                    amount=float(item["amount"]),
                    category=item["category"],
                    created_at=item["created_at"],
                )
            )
        return expenses
    except Exception as e:
        print(f"Error loading data: {e}")
        return []


def save_expenses(expenses: List[Expense]) -> None:
    data = [asdict(expense) for expense in expenses]
    DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def parse_date(value: str) -> str:
    try:
        dt = datetime.strptime(value, DATE_FMT)
        return dt.strftime(DATE_FMT)
    except ValueError:
        raise ValueError(f"Invalid date format. Use {DATE_FMT}.")


def input_non_empty(prompt: str) -> str:
    value = input(prompt).strip()
    if not value:
        raise ValueError("Input cannot be empty.")
    return value


def input_float(prompt: str) -> float:
    value = input(prompt).strip()
    try:
        amount = float(value)
        if amount <= 0:
            raise ValueError
        return amount
    except ValueError:
        raise ValueError("Amount must be a positive number.")


def add_expense(expenses: List[Expense]) -> None:
    print("\nAdd Expense")
    print("-" * 20)

    title = input_non_empty("Title: ")
    amount = input_float("Amount: ")
    category = input_non_empty("Category: ")
    created_at_raw = input("Date (YYYY-MM-DD, blank for today): ").strip()

    if created_at_raw:
        created_at = parse_date(created_at_raw)
    else:
        created_at = date.today().strftime(DATE_FMT)

    expense = Expense(
        id=str(uuid.uuid4())[:8],
        title=title,
        amount=amount,
        category=category,
        created_at=created_at,
    )

    expenses.append(expense)
    save_expenses(expenses)
    print(f"Saved expense with ID: {expense.id}")


def list_expenses(expenses: List[Expense]) -> None:
    print("\nAll Expenses")
    print("-" * 60)

    if not expenses:
        print("No expenses found.")
        return

    print(f"{'ID':<10} {'Date':<12} {'Category':<15} {'Amount':<10} Title")
    print("-" * 60)
    for exp in sorted(expenses, key=lambda x: x.created_at, reverse=True):
        print(
            f"{exp.id:<10} {exp.created_at:<12} {exp.category:<15} "
            f"{exp.amount:<10.2f} {exp.title}"
        )


def delete_expense(expenses: List[Expense]) -> None:
    print("\nDelete Expense")
    print("-" * 20)

    if not expenses:
        print("No expenses to delete.")
        return

    expense_id = input_non_empty("Enter expense ID: ")
    before = len(expenses)
    expenses[:] = [exp for exp in expenses if exp.id != expense_id]

    if len(expenses) == before:
        print("Expense not found.")
    else:
        save_expenses(expenses)
        print("Expense deleted.")


def filter_by_date_range(expenses: List[Expense], start: str, end: str) -> List[Expense]:
    start_dt = datetime.strptime(start, DATE_FMT).date()
    end_dt = datetime.strptime(end, DATE_FMT).date()

    if start_dt > end_dt:
        raise ValueError("Start date cannot be after end date.")

    result = []
    for exp in expenses:
        exp_dt = datetime.strptime(exp.created_at, DATE_FMT).date()
        if start_dt <= exp_dt <= end_dt:
            result.append(exp)
    return result


def show_summary(expenses: List[Expense]) -> None:
    print("\nSummary")
    print("-" * 20)

    if not expenses:
        print("No expenses found.")
        return

    total = sum(exp.amount for exp in expenses)
    print(f"Total expenses: {total:.2f}")

    by_category: Dict[str, float] = {}
    for exp in expenses:
        by_category[exp.category] = by_category.get(exp.category, 0.0) + exp.amount

    print("\nBy category:")
    for category, amount in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category:<15} {amount:.2f}")

    print("\nOptional date range summary")
    choice = input("Show filtered summary by date range? (y/n): ").strip().lower()
    if choice == "y":
        try:
            start = parse_date(input("Start date (YYYY-MM-DD): ").strip())
            end = parse_date(input("End date   (YYYY-MM-DD): ").strip())
            filtered = filter_by_date_range(expenses, start, end)
            filtered_total = sum(exp.amount for exp in filtered)
            print(f"\nExpenses between {start} and {end}: {filtered_total:.2f}")
            if filtered:
                by_cat: Dict[str, float] = {}
                for exp in filtered:
                    by_cat[exp.category] = by_cat.get(exp.category, 0.0) + exp.amount
                for category, amount in sorted(by_cat.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {category:<15} {amount:.2f}")
            else:
                print("No expenses in this range.")
        except Exception as e:
            print(f"Error: {e}")


def search_expenses(expenses: List[Expense]) -> None:
    print("\nSearch Expenses")
    print("-" * 20)

    if not expenses:
        print("No expenses found.")
        return

    keyword = input_non_empty("Enter keyword: ").lower()
    matched = [
        exp for exp in expenses
        if keyword in exp.title.lower() or keyword in exp.category.lower()
    ]

    if not matched:
        print("No matching expenses.")
        return

    print(f"{'ID':<10} {'Date':<12} {'Category':<15} {'Amount':<10} Title")
    print("-" * 60)
    for exp in matched:
        print(
            f"{exp.id:<10} {exp.created_at:<12} {exp.category:<15} "
            f"{exp.amount:<10.2f} {exp.title}"
        )


def edit_expense(expenses: List[Expense]) -> None:
    print("\nEdit Expense")
    print("-" * 20)

    if not expenses:
        print("No expenses to edit.")
        return

    expense_id = input_non_empty("Enter expense ID: ")
    expense: Optional[Expense] = next((exp for exp in expenses if exp.id == expense_id), None)

    if expense is None:
        print("Expense not found.")
        return

    print("Press Enter to keep the current value.")

    new_title = input(f"Title [{expense.title}]: ").strip()
    new_amount = input(f"Amount [{expense.amount:.2f}]: ").strip()
    new_category = input(f"Category [{expense.category}]: ").strip()
    new_date = input(f"Date [{expense.created_at}]: ").strip()

    if new_title:
        expense.title = new_title

    if new_amount:
        try:
            amount = float(new_amount)
            if amount <= 0:
                raise ValueError
            expense.amount = amount
        except ValueError:
            print("Invalid amount. Keeping old value.")

    if new_category:
        expense.category = new_category

    if new_date:
        try:
            expense.created_at = parse_date(new_date)
        except ValueError:
            print("Invalid date. Keeping old value.")

    save_expenses(expenses)
    print("Expense updated.")


def show_menu() -> None:
    print("\nExpense Tracker")
    print("=" * 20)
    print("1. Add expense")
    print("2. List expenses")
    print("3. Edit expense")
    print("4. Delete expense")
    print("5. Search expenses")
    print("6. Summary")
    print("7. Exit")


def main() -> None:
    expenses = load_expenses()

    while True:
        show_menu()
        choice = input("Choose an option: ").strip()

        try:
            if choice == "1":
                add_expense(expenses)
            elif choice == "2":
                list_expenses(expenses)
            elif choice == "3":
                edit_expense(expenses)
            elif choice == "4":
                delete_expense(expenses)
            elif choice == "5":
                search_expenses(expenses)
            elif choice == "6":
                show_summary(expenses)
            elif choice == "7":
                print("Goodbye.")
                sys.exit(0)
            else:
                print("Invalid option.")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
