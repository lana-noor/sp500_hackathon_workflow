"""
Budget Variance Narrative Reports MCP Server — ADGA
====================================================

A FastMCP server that serves department-submitted variance narrative reports.

This server provides access to department-submitted quarterly variance reports
containing justifications, explanations, and supporting narratives for budget
variances. These narratives represent "what departments claim happened."

The actual financial data (CSV files) will be attached directly to the Code
Interpreter agent for analysis and reconciliation.

Run with:
    fastmcp run budget-reports-mcp-server.py --transport streamable-http --port 8001

Or from the digital_transformation_demo directory:
    cd digital_transformation_demo
    fastmcp run budget-reports-mcp-server.py --transport streamable-http --port 8001

Deployed to Azure Container Apps at:
    https://budget-reports-mcp-server.<random-id>.eastus.azurecontainerapps.io/mcp
"""

import json
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Server initialisation
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="BudgetVarianceNarrativeServer",
    instructions=(
        "Provides access to department-submitted quarterly budget variance reports "
        "for the Apex Digital Government Authority (ADGA). These reports contain "
        "narrative justifications, explanations, and supporting documentation for "
        "budget variances. Use these tools to retrieve department claims and "
        "justifications for reconciliation against official financial data."
    ),
)

# ---------------------------------------------------------------------------
# Data paths — resolved relative to this file
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).parent / "data"
_REPORTS_DIR = _DATA_DIR / "department_reports"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _read_report(path: Path) -> str:
    """Read a markdown report file and return its content."""
    return path.read_text(encoding="utf-8")


def _list_reports_for_quarter(quarter: str, fiscal_year: int) -> list[dict]:
    """List all available department reports for a given quarter."""
    reports = []
    if not _REPORTS_DIR.exists():
        return reports

    # Pattern: DEPT_Q1_2026_variance_report.md
    pattern = f"*_{quarter}_{fiscal_year}_variance_report.md"
    for report_path in _REPORTS_DIR.glob(pattern):
        dept_code = report_path.stem.split("_")[0]
        reports.append({
            "department_code": dept_code,
            "quarter": quarter,
            "fiscal_year": fiscal_year,
            "filename": report_path.name,
        })
    return reports


# ---------------------------------------------------------------------------
# Tool 1 — List available department reports
# ---------------------------------------------------------------------------

@mcp.tool(
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def list_submitted_variance_reports(
    fiscal_year: int = 2026,
    quarter: str = "Q1"
) -> dict:
    """
    List all department variance reports submitted for a given quarter.

    Args:
        fiscal_year: Four-digit fiscal year, e.g. 2026 (default: 2026).
        quarter: Quarter string, e.g. 'Q1', 'Q2', 'Q3', 'Q4' (default: Q1).

    Returns a list of available reports with department codes and filenames.
    Use this first to discover which departments have submitted reports.
    """
    reports = _list_reports_for_quarter(quarter, fiscal_year)

    return {
        "organisation": "Apex Digital Government Authority",
        "fiscal_year": fiscal_year,
        "quarter": quarter.upper(),
        "num_reports_submitted": len(reports),
        "reports": reports,
    }


# ---------------------------------------------------------------------------
# Tool 2 — Get a specific department's variance report
# ---------------------------------------------------------------------------

@mcp.tool(
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def get_department_variance_report(
    department_code: str,
    fiscal_year: int = 2026,
    quarter: str = "Q1",
) -> dict:
    """
    Retrieve the full narrative variance report submitted by a department.

    Args:
        department_code: Department code, e.g. 'IT', 'HR', 'INF', 'COM', 'POL', 'FIN'.
        fiscal_year: Four-digit fiscal year, e.g. 2026 (default: 2026).
        quarter: Quarter string, e.g. 'Q1', 'Q2', 'Q3', 'Q4' (default: Q1).

    Returns the full markdown content of the department's submitted variance report,
    including justifications, supporting evidence, remediation plans, and sign-offs.

    This represents what the department CLAIMS happened. For actual financial data,
    use the CSV files attached to the Code Interpreter agent.
    """
    dept_code_upper = department_code.upper()
    quarter_upper = quarter.upper()

    # Pattern: IT_Q1_2026_variance_report.md
    filename = f"{dept_code_upper}_{quarter_upper}_{fiscal_year}_variance_report.md"
    report_path = _REPORTS_DIR / filename

    if not report_path.exists():
        # Try to list what reports are available
        available = _list_reports_for_quarter(quarter_upper, fiscal_year)
        available_codes = [r["department_code"] for r in available]

        return {
            "error": (
                f"No variance report found for department '{dept_code_upper}' "
                f"in {quarter_upper} {fiscal_year}.\n"
                f"Available department codes for this quarter: {', '.join(available_codes) if available_codes else 'None'}\n"
                f"Use list_submitted_variance_reports() to see all available reports."
            )
        }

    report_content = _read_report(report_path)

    return {
        "department_code": dept_code_upper,
        "fiscal_year": fiscal_year,
        "quarter": quarter_upper,
        "filename": filename,
        "report_content": report_content,
        "note": (
            "This is the department's narrative justification. "
            "Reconcile this against official CSV data for variance analysis."
        ),
    }


# ---------------------------------------------------------------------------
# Tool 3 — Get all reports for a quarter (convenience method)
# ---------------------------------------------------------------------------

@mcp.tool(
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def get_all_variance_reports_for_quarter(
    fiscal_year: int = 2026,
    quarter: str = "Q1",
) -> dict:
    """
    Retrieve ALL department variance reports for a given quarter as a consolidated response.

    Args:
        fiscal_year: Four-digit fiscal year, e.g. 2026 (default: 2026).
        quarter: Quarter string, e.g. 'Q1', 'Q2', 'Q3', 'Q4' (default: Q1).

    Returns a dictionary with all submitted reports for the quarter.
    Each report contains the full markdown content with justifications and supporting evidence.

    Use this when you need to analyze multiple departments at once.
    """
    quarter_upper = quarter.upper()
    reports = _list_reports_for_quarter(quarter_upper, fiscal_year)

    if not reports:
        return {
            "error": f"No variance reports found for {quarter_upper} {fiscal_year}.",
            "organisation": "Apex Digital Government Authority",
            "fiscal_year": fiscal_year,
            "quarter": quarter_upper,
            "num_reports": 0,
            "reports": [],
        }

    full_reports = []
    for report_info in reports:
        dept_code = report_info["department_code"]
        filename = report_info["filename"]
        report_path = _REPORTS_DIR / filename

        if report_path.exists():
            content = _read_report(report_path)
            full_reports.append({
                "department_code": dept_code,
                "filename": filename,
                "report_content": content,
            })

    return {
        "organisation": "Apex Digital Government Authority",
        "fiscal_year": fiscal_year,
        "quarter": quarter_upper,
        "num_reports": len(full_reports),
        "reports": full_reports,
        "note": (
            "These are department-submitted narrative justifications. "
            "Reconcile against official CSV data attached to the Code Interpreter agent."
        ),
    }


# ---------------------------------------------------------------------------
# Entry point — run as streamable-http MCP server on port 8001
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("Budget Variance Narrative Reports MCP Server")
    print("Apex Digital Government Authority (ADGA)")
    print("=" * 70)
    print(f"Reports directory: {_REPORTS_DIR}")
    print("Available tools:")
    print("  1. list_submitted_variance_reports() - List all available reports")
    print("  2. get_department_variance_report() - Get a specific department report")
    print("  3. get_all_variance_reports_for_quarter() - Get all reports for a quarter")
    print("=" * 70)
    print("Starting server on http://127.0.0.1:8001")
    print("=" * 70)
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8001)
