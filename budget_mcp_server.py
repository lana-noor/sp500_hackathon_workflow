"""
Budget Data MCP Server — Emirates Digital Authority
====================================================

A FastMCP server that exposes approved budget allocations, historical actuals,
department metadata, and variance policy as callable tools.

Run with:
    fastmcp run budget_mcp_server.py --transport streamable-http --port 8001

The budget_variance_workflow.py will call this server via the Azure OpenAI
Responses API MCP tool type:
    tools=[{"type": "mcp", "server_url": "http://localhost:8001", ...}]
"""

import csv
import json
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Server initialisation
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="BudgetDataServer",
    instructions=(
        "Provides authoritative budget allocation, historical actuals, "
        "department metadata, and variance policy data for Emirates Digital Authority (EDA). "
        "Use these tools to cross-reference submitted budget reports against approved figures."
    ),
)

# ---------------------------------------------------------------------------
# Data paths — resolved relative to this file
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).parent / "data"
_APPROVED_BUDGETS_CSV   = _DATA_DIR / "approved_budgets.csv"
_HISTORICAL_ACTUALS_CSV = _DATA_DIR / "historical_actuals.csv"
_DEPARTMENT_METADATA    = _DATA_DIR / "department_metadata.json"
_VARIANCE_POLICY        = _DATA_DIR / "variance_policy.json"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _read_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Tool 1 — List all departments
# ---------------------------------------------------------------------------

@mcp.tool(
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def budget_list_departments() -> dict:
    """
    Return all EDA departments with their codes, names, heads, cost centres,
    budget categories, and variance escalation thresholds.
    Use this first to discover valid department codes for other tools.
    """
    meta = _read_json(_DEPARTMENT_METADATA)
    return {
        "organisation": meta["organisation"],
        "currency": meta["currency"],
        "departments": meta["departments"],
    }


# ---------------------------------------------------------------------------
# Tool 2 — Get approved budget for a specific department / period
# ---------------------------------------------------------------------------

@mcp.tool(
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def budget_get_approved_allocation(
    department_code: str,
    fiscal_year: int,
    quarter: str,
) -> dict:
    """
    Return the approved budget allocation for a specific department and quarter.

    Args:
        department_code: Department code, e.g. 'IT', 'HR', 'INF', 'COM', 'POL', 'FIN'.
        fiscal_year: Four-digit fiscal year, e.g. 2026.
        quarter: Quarter string, e.g. 'Q1', 'Q2', 'Q3', 'Q4'.

    Returns a dict with approved_budget_aed, approval_date, approved_by, and budget_version.
    Returns an error message if no matching record is found.
    """
    rows = _read_csv(_APPROVED_BUDGETS_CSV)
    matches = [
        r for r in rows
        if r["department_code"].upper() == department_code.upper()
        and r["fiscal_year"] == str(fiscal_year)
        and r["quarter"].upper() == quarter.upper()
    ]
    if not matches:
        return {
            "error": (
                f"No approved budget found for department_code='{department_code}', "
                f"fiscal_year={fiscal_year}, quarter='{quarter}'. "
                f"Use budget_list_departments() to see valid codes."
            )
        }
    row = matches[0]
    return {
        "department_code": row["department_code"],
        "department_name": row["department_name"],
        "fiscal_year": int(row["fiscal_year"]),
        "quarter": row["quarter"],
        "approved_budget_aed": float(row["approved_budget_aed"]),
        "approval_date": row["approval_date"],
        "approved_by": row["approved_by"],
        "budget_version": row["budget_version"],
    }


# ---------------------------------------------------------------------------
# Tool 3 — Get historical actuals for a department
# ---------------------------------------------------------------------------

@mcp.tool(
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def budget_get_historical_actuals(
    department_code: str,
    num_quarters: int = 4,
) -> dict:
    """
    Return the most recent historical actual spend records for a department.

    Args:
        department_code: Department code, e.g. 'IT', 'HR', 'INF', 'COM', 'POL', 'FIN'.
        num_quarters: Number of most-recent quarters to return (default 4, max 8).

    Returns a list of quarterly actuals sorted newest-first, including variance
    against approved budget and any notes from finance.
    """
    num_quarters = min(max(num_quarters, 1), 8)
    rows = _read_csv(_HISTORICAL_ACTUALS_CSV)
    dept_rows = [
        r for r in rows
        if r["department_code"].upper() == department_code.upper()
    ]
    if not dept_rows:
        return {
            "error": (
                f"No historical actuals found for department_code='{department_code}'. "
                f"Use budget_list_departments() to see valid codes."
            )
        }

    # Sort by fiscal_year desc, then quarter desc
    def _sort_key(r):
        q_order = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}
        return (int(r["fiscal_year"]), q_order.get(r["quarter"].upper(), 0))

    dept_rows_sorted = sorted(dept_rows, key=_sort_key, reverse=True)
    recent = dept_rows_sorted[:num_quarters]

    records = []
    for r in recent:
        records.append({
            "fiscal_year": int(r["fiscal_year"]),
            "quarter": r["quarter"],
            "actual_spend_aed": float(r["actual_spend_aed"]),
            "approved_budget_aed": float(r["approved_budget_aed"]),
            "variance_aed": float(r["variance_aed"]),
            "variance_pct": float(r["variance_pct"]),
            "report_date": r["report_date"],
            "notes": r["notes"],
        })

    avg_variance_pct = sum(r["variance_pct"] for r in records) / len(records)

    return {
        "department_code": department_code.upper(),
        "department_name": dept_rows[0]["department_name"],
        "num_quarters_returned": len(records),
        "average_variance_pct_over_period": round(avg_variance_pct, 2),
        "actuals": records,
    }


# ---------------------------------------------------------------------------
# Tool 4 — Get full period summary across all departments
# ---------------------------------------------------------------------------

@mcp.tool(
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def budget_get_period_approved_summary(
    fiscal_year: int,
    quarter: str,
) -> dict:
    """
    Return approved budget allocations for ALL departments for a given fiscal year
    and quarter. Use this to get a full cross-organisation budget picture for a period.

    Args:
        fiscal_year: Four-digit fiscal year, e.g. 2026.
        quarter: Quarter string, e.g. 'Q1'.

    Returns total approved budget, per-department breakdown, and organisation metadata.
    """
    rows = _read_csv(_APPROVED_BUDGETS_CSV)
    period_rows = [
        r for r in rows
        if r["fiscal_year"] == str(fiscal_year)
        and r["quarter"].upper() == quarter.upper()
    ]
    if not period_rows:
        return {
            "error": (
                f"No approved budgets found for fiscal_year={fiscal_year}, "
                f"quarter='{quarter}'."
            )
        }

    total = sum(float(r["approved_budget_aed"]) for r in period_rows)
    departments = [
        {
            "department_code": r["department_code"],
            "department_name": r["department_name"],
            "approved_budget_aed": float(r["approved_budget_aed"]),
            "approved_by": r["approved_by"],
            "approval_date": r["approval_date"],
        }
        for r in period_rows
    ]

    return {
        "organisation": "Emirates Digital Authority",
        "fiscal_year": fiscal_year,
        "quarter": quarter.upper(),
        "total_approved_budget_aed": total,
        "num_departments": len(departments),
        "departments": departments,
    }


# ---------------------------------------------------------------------------
# Tool 5 — Get variance policy
# ---------------------------------------------------------------------------

@mcp.tool(
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def budget_get_variance_policy() -> dict:
    """
    Return the EDA Budget Variance Management Policy including:
    - Variance threshold bands (acceptable / minor / significant / critical)
    - Required actions and escalation approvers per band
    - Board notification thresholds
    - Reporting requirements and reallocation rules

    Use this to determine the correct policy status and required actions
    for any department variance identified in the submitted report.
    """
    return _read_json(_VARIANCE_POLICY)


# ---------------------------------------------------------------------------
# Tool 6 — Get department metadata
# ---------------------------------------------------------------------------

@mcp.tool(
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def budget_get_department_detail(department_code: str) -> dict:
    """
    Return detailed metadata for a single department including head of department,
    cost centre code, budget category, headcount, location, and variance thresholds.

    Args:
        department_code: Department code, e.g. 'IT', 'HR', 'INF', 'COM', 'POL', 'FIN'.
    """
    meta = _read_json(_DEPARTMENT_METADATA)
    matches = [
        d for d in meta["departments"]
        if d["code"].upper() == department_code.upper()
    ]
    if not matches:
        return {
            "error": (
                f"Department '{department_code}' not found. "
                f"Use budget_list_departments() to see valid codes."
            )
        }
    return matches[0]


# ---------------------------------------------------------------------------
# Entry point — run as streamable-http MCP server on port 8001
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8001)
