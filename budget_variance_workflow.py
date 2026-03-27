# Copyright (c) Microsoft. All rights reserved.

"""
Budget Variance Report Workflow — Five Sequential Agents
=========================================================

Pipeline:
  Agent 1  →  MCP Data Agent         (Responses API + FastMCP server)
               Retrieves approved budgets, historical actuals, and variance
               policy from the Budget Data MCP Server (localhost:8001).

  Agent 2  →  Web Search Agent       (Azure AI agent_reference: WebSearchAgent v13)
               Searches for macroeconomic context, inflation rates, and
               public-sector spending benchmarks relevant to the report period.

  Agent 3  →  Code Interpreter Agent (Azure AI Agent Service + code_interpreter tool)
               Calculates per-department variances, flags policy breaches,
               runs trend analysis against historical data, and produces
               structured JSON output.

  Agent 4  →  Summary Agent          (Responses API)
               Synthesises agents 1–3 into a professional Markdown report
               and converts it to a Word (.docx) document.

  Agent 5  →  Outlook Mail Agent     (Azure AI agent_reference: OutlookWorkIQAgent v7)
               Sends the final report to lananoor@microsoft.com via Outlook.

Prerequisites:
  - budget_mcp_server.py must be running on localhost:8001:
        python budget_mcp_server.py
  - Azure credentials configured (DefaultAzureCredential / AzureCliCredential)
  - Environment variables set (see .envsample)
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import os
from dotenv import load_dotenv
from pydantic import BaseModel

from agent_framework import Agent
from agent_framework.azure import AzureOpenAIResponsesClient, AzureAIAgentClient
from azure.ai.projects import AIProjectClient
from azure.identity.aio import DefaultAzureCredential, AzureCliCredential

# ---------------------------------------------------------------------------
# python-docx — optional; only needed for the Word executor
# ---------------------------------------------------------------------------
try:
    from docx import Document as WordDocument
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("[Warning] python-docx not installed — Word output will be skipped.")
    print("          Install with: pip install python-docx")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
load_dotenv()

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./output"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MCP_SERVER_URL       = os.getenv("MCP_SERVER_URL", "http://localhost:8001")
OUTLOOK_RECIPIENT    = os.getenv("OUTLOOK_RECIPIENT_EMAIL", "lananoor@microsoft.com")
WEB_SEARCH_AGENT     = os.getenv("WEB_SEARCH_AGENT_NAME", "WebSearchAgent")
WEB_SEARCH_VERSION   = os.getenv("WEB_SEARCH_AGENT_VERSION", "13")
OUTLOOK_AGENT        = os.getenv("OUTLOOK_AGENT_NAME", "OutlookWorkIQAgent")
OUTLOOK_VERSION      = os.getenv("OUTLOOK_AGENT_VERSION", "7")


# ---------------------------------------------------------------------------
# Pydantic structured-output model for Agent 3 (Code Interpreter)
# ---------------------------------------------------------------------------

class DepartmentVariance(BaseModel):
    department_code: str
    department_name: str
    approved_budget_aed: float
    actual_spend_aed: float
    variance_aed: float
    variance_pct: float
    policy_status: str          # ACCEPTABLE | MINOR | SIGNIFICANT | CRITICAL | UNDERSPEND_REVIEW
    required_action: str
    trend_vs_prior_year: Optional[str]   # IMPROVING | WORSENING | STABLE | INSUFFICIENT_DATA


class BudgetVarianceOutput(BaseModel):
    period: str                          # e.g. "Q1 2026"
    organisation: str
    total_approved_aed: float
    total_actual_aed: float
    total_variance_aed: float
    total_variance_pct: float
    overall_policy_status: str
    departments: List[DepartmentVariance]
    departments_requiring_cfo_approval: List[str]
    departments_requiring_board_notification: List[str]
    key_findings: List[str]
    data_quality_notes: List[str]


# ---------------------------------------------------------------------------
# Agent 1 — MCP Data Agent instructions
# ---------------------------------------------------------------------------
MCP_DATA_INSTRUCTIONS = """
You are a Budget Data Retrieval Agent for the Emirates Digital Authority (EDA).

YOUR TASK
You have access to the EDA Budget Data MCP Server. Use its tools to retrieve
authoritative data that will be used to cross-reference the submitted budget report.

REQUIRED STEPS
1. Call budget_list_departments() to confirm all department codes.
2. Call budget_get_period_approved_summary(fiscal_year=2026, quarter="Q1") to get
   the full approved budget for the reporting period.
3. For each department, call budget_get_historical_actuals(department_code, num_quarters=4)
   to retrieve the last 4 quarters of actual spend.
4. Call budget_get_variance_policy() to retrieve the policy thresholds and actions.

OUTPUT FORMAT
Return a structured JSON object with the following keys:
{
  "period": "Q1 2026",
  "approved_totals": { <department_code>: <approved_budget_aed>, ... },
  "historical_actuals": { <department_code>: [ { "quarter": "...", "actual": ..., "variance_pct": ... }, ... ] },
  "variance_policy": { ... },
  "data_retrieval_notes": [ "..." ]
}

Return ONLY valid JSON — no prose, no markdown fences.
""".strip()


# ---------------------------------------------------------------------------
# Agent 2 — Web Search Agent instructions (sent as the user prompt)
# ---------------------------------------------------------------------------
WEB_SEARCH_PROMPT_TEMPLATE = """
You are a macroeconomic research assistant. A UAE public sector budget variance report
for Q1 2026 (January–March 2026) has been submitted by the Emirates Digital Authority (EDA).

Please search for and provide concise, factual context on the following:

1. UAE inflation rate for Q1 2026 (Jan–Mar 2026) — CPI change vs prior year
2. UAE government / public sector IT spending benchmarks or trends for 2025-2026
3. Construction / facilities cost index changes in the UAE for 2025-2026
   (relevant to infrastructure overspend)
4. Any significant cybersecurity incidents in the UAE public sector in early 2026
   (relevant to IT emergency procurement)
5. UAE public sector HR / recruitment market conditions in Q1 2026

Return a concise JSON object:
{
  "uae_inflation_q1_2026_pct": <number or null>,
  "it_spending_context": "...",
  "construction_cost_context": "...",
  "cybersecurity_context": "...",
  "hr_market_context": "...",
  "search_notes": ["..."]
}

Return ONLY valid JSON.
""".strip()


# ---------------------------------------------------------------------------
# Agent 3 — Code Interpreter Agent instructions
# ---------------------------------------------------------------------------
CODE_INTERPRETER_INSTRUCTIONS = """
You are a Budget Variance Analysis Agent with Code Interpreter enabled.

You will receive three inputs:
  1. The submitted budget variance report (Markdown).
  2. Authoritative MCP data: approved budgets, historical actuals, variance policy (JSON).
  3. Macroeconomic web research context (JSON).

TASK — Use Python code to:

1. Parse the submitted report to extract per-department actual spend figures.
2. Cross-reference against MCP approved budgets to compute:
   - Variance (AED) = actual - approved
   - Variance (%) = (variance / approved) * 100
3. Apply the variance policy thresholds to assign a policy_status to each department:
   - |variance_pct| <= 5%     → ACCEPTABLE
   - 5% < |variance_pct| <= 10% → MINOR (overspend) or UNDERSPEND_REVIEW if negative
   - 10% < |variance_pct| <= 25% AND overspend → SIGNIFICANT (CFO approval required)
   - variance_pct > 25% (overspend) → CRITICAL (Board notification required)
   - variance_pct < -15% → UNDERSPEND_REVIEW
4. Compare Q1 2026 variance_pct to the department's average variance_pct over the
   last 4 quarters from historical actuals:
   - If Q1 2026 variance_pct > avg_historical + 5pp → WORSENING
   - If Q1 2026 variance_pct < avg_historical - 5pp → IMPROVING
   - Otherwise → STABLE
   - If < 2 historical quarters available → INSUFFICIENT_DATA
5. Identify:
   - Departments requiring CFO approval (SIGNIFICANT or CRITICAL)
   - Departments requiring Board notification (CRITICAL only)
6. Produce 3–5 key findings as bullet points.

OUTPUT — Return ONLY valid JSON matching this schema exactly:
{
  "period": "Q1 2026",
  "organisation": "Emirates Digital Authority",
  "total_approved_aed": <number>,
  "total_actual_aed": <number>,
  "total_variance_aed": <number>,
  "total_variance_pct": <number>,
  "overall_policy_status": "ACCEPTABLE|MINOR|SIGNIFICANT|CRITICAL",
  "departments": [
    {
      "department_code": "...",
      "department_name": "...",
      "approved_budget_aed": <number>,
      "actual_spend_aed": <number>,
      "variance_aed": <number>,
      "variance_pct": <number>,
      "policy_status": "ACCEPTABLE|MINOR|SIGNIFICANT|CRITICAL|UNDERSPEND_REVIEW",
      "required_action": "...",
      "trend_vs_prior_year": "IMPROVING|WORSENING|STABLE|INSUFFICIENT_DATA"
    }
  ],
  "departments_requiring_cfo_approval": ["...", "..."],
  "departments_requiring_board_notification": ["..."],
  "key_findings": ["...", "..."],
  "data_quality_notes": ["..."]
}

Return ONLY valid JSON — no prose, no markdown fences.
""".strip()


# ---------------------------------------------------------------------------
# Agent 4 — Summary Agent instructions
# ---------------------------------------------------------------------------
SUMMARY_INSTRUCTIONS = """
You are a Budget Report Summary Agent. Synthesise the outputs of a budget variance
analysis into a professional Markdown report suitable for senior government finance officials.

You will receive:
  1. The original submitted budget report (Markdown).
  2. MCP Data retrieval results (JSON from Agent 1).
  3. Web research context (JSON from Agent 2).
  4. Structured variance analysis (JSON from Agent 3).

Generate a Markdown report following this EXACT structure:

---

# Budget Variance Analysis Report — Q1 2026

**Organisation:** Emirates Digital Authority (EDA)
**Period:** January – March 2026
**Report Date:** {today's date}
**Prepared by:** Budget Analysis Workflow (AI-Assisted)
**Classification:** Internal — Finance & Senior Leadership

---

## Executive Summary

{2–3 sentence summary of overall position, key concerns, and recommended actions}

---

## Overall Budget Position

| Metric | Value |
|---|---|
| Total Approved Budget (Q1) | AED {total_approved:,.0f} |
| Total Actual Spend (Q1) | AED {total_actual:,.0f} |
| Total Variance | AED {total_variance:+,.0f} ({total_variance_pct:+.1f}%) |
| Overall Policy Status | {status with emoji} |
| Departments Over Budget | {count} |
| Departments Under Budget | {count} |

---

## Department Variance Summary

| Department | Approved (AED) | Actual (AED) | Variance (AED) | Variance % | Status | Trend |
|---|---|---|---|---|---|---|
{one row per department, with emoji status indicators}

Status legend: ✅ Acceptable · ⚠️ Minor · 🔶 Significant (CFO) · 🚨 Critical (Board) · 🔵 Underspend Review

---

## Macroeconomic Context

{Summarise the web research findings: inflation, IT sector trends, construction costs,
cybersecurity environment — 2–3 sentences each, with source context where available}

---

## Detailed Department Analysis

### {Department Name} — {Status emoji}

{For each department with SIGNIFICANT or CRITICAL status, provide a dedicated subsection:
 - Approved vs actual table
 - Variance drivers from the submitted report
 - Historical trend (IMPROVING/WORSENING/STABLE)
 - Required action under EDA variance policy}

---

## Required Actions & Escalations

| Department | Variance % | Policy Status | Required Action | Deadline |
|---|---|---|---|---|
{rows only for departments with variance_pct > 5% or < -15%}

---

## Historical Trend Analysis

{2–3 sentences summarising whether the overall overspend pattern is new or recurring,
referencing the last 4 quarters of historical data}

---

## Recommendations

{3–5 numbered recommendations based on the analysis}

---

## Data Notes

{Any data quality issues, caveats, or limitations noted by the analysis agents}

---

*Report generated by EDA Budget Variance Workflow · Powered by Azure AI Agent Service*

---

DECISION RULES:
- Use 🚨 for CRITICAL (>25% overspend — Board notification required)
- Use 🔶 for SIGNIFICANT (10–25% overspend — CFO approval required)
- Use ⚠️ for MINOR (5–10% variance)
- Use ✅ for ACCEPTABLE (<5% variance)
- Use 🔵 for UNDERSPEND_REVIEW (< -15% underspend)
""".strip()


# ---------------------------------------------------------------------------
# Executor — Markdown → Word Document (reused from payslip workflow)
# ---------------------------------------------------------------------------

def markdown_to_word_executor(markdown_content: str, output_path: Path) -> Path:
    """Convert a Markdown string to a formatted Word (.docx) document."""
    if not DOCX_AVAILABLE:
        raise RuntimeError("python-docx not installed. Run: pip install python-docx")

    doc = WordDocument()
    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Calibri"
    normal_style.font.size = Pt(11)

    lines = markdown_content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("#### "):
            doc.add_heading(stripped[5:].strip(), level=4)
        elif stripped.startswith("### "):
            doc.add_heading(stripped[4:].strip(), level=3)
        elif stripped.startswith("## "):
            doc.add_heading(stripped[3:].strip(), level=2)
        elif stripped.startswith("# "):
            doc.add_heading(stripped[2:].strip(), level=1)
        elif stripped in ("---", "***", "___"):
            doc.add_paragraph("─" * 60)
        elif stripped.startswith("|"):
            table_lines: list[str] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            data_rows = [
                tl for tl in table_lines
                if not re.fullmatch(r"[\|\-\: ]+", tl.strip())
            ]
            if data_rows:
                parsed: list[list[str]] = []
                for tl in data_rows:
                    cells = [
                        re.sub(r"\*\*(.+?)\*\*", r"\1", c.strip())
                        for c in tl.strip().strip("|").split("|")
                    ]
                    parsed.append(cells)
                num_cols = max(len(r) for r in parsed)
                table = doc.add_table(rows=len(parsed), cols=num_cols)
                table.style = "Table Grid"
                for ri, row_data in enumerate(parsed):
                    for ci in range(num_cols):
                        cell_text = row_data[ci] if ci < len(row_data) else ""
                        cell = table.rows[ri].cells[ci]
                        cell.text = cell_text
                        if ri == 0:
                            for run in cell.paragraphs[0].runs:
                                run.bold = True
            continue
        elif re.match(r"^[\-\*] ", stripped):
            text = re.sub(r"\*\*(.+?)\*\*", r"\1", stripped[2:])
            text = re.sub(r"\*(.+?)\*", r"\1", text)
            doc.add_paragraph(text, style="List Bullet")
        elif re.match(r"^\d+\. ", stripped):
            text = re.sub(r"^\d+\. ", "", stripped)
            text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
            doc.add_paragraph(text, style="List Number")
        elif stripped.startswith("**") and stripped.endswith("**") and stripped.count("**") == 2:
            p = doc.add_paragraph()
            run = p.add_run(stripped.strip("*"))
            run.bold = True
        else:
            text = re.sub(r"\*\*(.+?)\*\*", r"\1", stripped)
            text = re.sub(r"\*(.+?)\*", r"\1", text)
            if text:
                doc.add_paragraph(text)
        i += 1

    doc.save(str(output_path))
    return output_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_text_from_result(result) -> str:
    """Pull the final assistant text from an agent result."""
    try:
        if hasattr(result, "messages") and result.messages:
            for message in reversed(result.messages):
                if hasattr(message, "contents"):
                    for content in message.contents:
                        if getattr(content, "type", None) == "text":
                            if hasattr(content, "text") and content.text:
                                return content.text
    except Exception:
        pass
    return str(result)


def _banner(title: str) -> None:
    bar = "=" * 65
    print(f"\n{bar}")
    print(f"  {title}")
    print(bar)


# ---------------------------------------------------------------------------
# Workflow Executor
# ---------------------------------------------------------------------------

class BudgetVarianceWorkflowExecutor:
    """
    Sequential five-agent workflow executor for Budget Variance Report analysis.

    Step 1  — MCP Data Agent
              Calls the Budget Data MCP Server (FastMCP, localhost:8001) via the
              Azure OpenAI Responses API MCP tool type to retrieve authoritative
              approved budgets, historical actuals, and variance policy.

    Step 2  — Web Search Agent
              Uses the Azure AI Foundry WebSearchAgent (agent_reference) to pull
              macroeconomic context: UAE inflation, sector benchmarks, news.

    Step 3  — Code Interpreter Agent
              Azure AI Agent Service with code_interpreter tool. Computes
              per-department variances, applies policy thresholds, trend analysis.
              Returns structured JSON (BudgetVarianceOutput schema).

    Step 4  — Summary Agent
              Synthesises steps 1–3 into a professional Markdown report,
              then converts to Word (.docx).

    Step 5  — Outlook Mail Agent
              Uses the Azure AI Foundry OutlookWorkIQAgent (agent_reference) to
              send the final report to lananoor@microsoft.com.
    """

    def __init__(self) -> None:
        self.responses_client = AzureOpenAIResponsesClient(
            credential=DefaultAzureCredential(),
            project_endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT"),
            deployment_name=os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME"),
        )
        self.project_client = AIProjectClient(
            endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT"),
            credential=DefaultAzureCredential(),
        )
        self.openai_client = self.project_client.get_openai_client()

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def execute(self, budget_report_input: str) -> dict:
        """
        Run the full budget variance workflow.

        Args:
            budget_report_input: Budget variance report in Markdown format.

        Returns:
            dict with keys: mcp_data, web_context, analysis, summary,
                            markdown_report_path, word_doc_path, mail_result.
        """
        _banner("BUDGET VARIANCE WORKFLOW — START")

        # ── Step 1: MCP Data Retrieval ───────────────────────────────────
        mcp_data_text = await self._run_mcp_data(budget_report_input)

        # ── Step 2: Web Search Context ───────────────────────────────────
        web_context_text = await self._run_web_search(budget_report_input)

        # ── Step 3: Code Interpreter Analysis ───────────────────────────
        analysis_text = await self._run_code_analysis(
            budget_report_input, mcp_data_text, web_context_text
        )

        # ── Step 4: Summary → Markdown + Word ───────────────────────────
        summary_markdown = await self._run_summary(
            budget_report_input, mcp_data_text, web_context_text, analysis_text
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        md_path = OUTPUT_DIR / f"budget_variance_report_{timestamp}.md"
        md_path.write_text(summary_markdown, encoding="utf-8")
        print(f"\n[Executor] Markdown saved → {md_path}")

        word_path: Optional[Path] = None
        word_doc_path = OUTPUT_DIR / f"budget_variance_report_{timestamp}.docx"
        try:
            markdown_to_word_executor(summary_markdown, word_doc_path)
            word_path = word_doc_path
            print(f"[Executor] Word document saved → {word_path}")
        except RuntimeError as exc:
            print(f"[Executor] Word conversion skipped: {exc}")

        # ── Step 5: Outlook Mail ─────────────────────────────────────────
        mail_result = await self._run_outlook_mail(summary_markdown, word_path)

        _banner("WORKFLOW COMPLETE")

        return {
            "mcp_data": mcp_data_text,
            "web_context": web_context_text,
            "analysis": analysis_text,
            "summary": summary_markdown,
            "markdown_report_path": str(md_path),
            "word_doc_path": str(word_path) if word_path else None,
            "mail_result": mail_result,
        }

    # ------------------------------------------------------------------
    # Agent 1 — MCP Data Agent (Responses API + FastMCP server)
    # ------------------------------------------------------------------

    async def _run_mcp_data(self, budget_report_input: str) -> str:
        print(f"\n[Agent 1] MCP Data Agent — connecting to {MCP_SERVER_URL}...")
        response = self.openai_client.responses.create(
            model=os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME"),
            input=[
                {
                    "role": "user",
                    "content": (
                        "Retrieve all relevant budget data for the report below "
                        "and return a structured JSON summary.\n\n"
                        f"=== SUBMITTED REPORT ===\n{budget_report_input}"
                    ),
                }
            ],
            instructions=MCP_DATA_INSTRUCTIONS,
            tools=[
                {
                    "type": "mcp",
                    "server_label": "budget_data_server",
                    "server_url": MCP_SERVER_URL,
                    "require_approval": "never",
                }
            ],
        )
        text = response.output_text
        print(f"[Agent 1] Done.\n{text[:200]}...\n")
        return text

    # ------------------------------------------------------------------
    # Agent 2 — Web Search Agent (agent_reference)
    # ------------------------------------------------------------------

    async def _run_web_search(self, budget_report_input: str) -> str:
        print("\n[Agent 2] Web Search Agent (WebSearchAgent) — running...")
        response = self.openai_client.responses.create(
            input=[{"role": "user", "content": WEB_SEARCH_PROMPT_TEMPLATE}],
            extra_body={
                "agent_reference": {
                    "name": WEB_SEARCH_AGENT,
                    "version": WEB_SEARCH_VERSION,
                    "type": "agent_reference",
                }
            },
        )
        text = response.output_text
        print(f"[Agent 2] Done.\n{text[:200]}...\n")
        return text

    # ------------------------------------------------------------------
    # Agent 3 — Code Interpreter Agent (Azure AI Agent Service)
    # ------------------------------------------------------------------

    async def _run_code_analysis(
        self,
        budget_report_input: str,
        mcp_data_text: str,
        web_context_text: str,
    ) -> str:
        print("\n[Agent 3] Code Interpreter Agent — running...")
        query = (
            "Use code interpreter to complete the variance analysis.\n\n"
            "=== SUBMITTED BUDGET REPORT ===\n"
            f"{budget_report_input}\n\n"
            "=== MCP DATA (approved budgets + historical actuals + policy) ===\n"
            f"{mcp_data_text}\n\n"
            "=== WEB RESEARCH CONTEXT ===\n"
            f"{web_context_text}\n\n"
            "Return ONLY valid JSON matching the required output schema."
        )
        async with AzureCliCredential() as credential:
            async with AzureAIAgentClient(
                credential=credential,
                project_endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT"),
            ).as_agent(
                name="BudgetCodeInterpreterAgent",
                instructions=CODE_INTERPRETER_INSTRUCTIONS,
                tools=[AzureAIAgentClient.get_code_interpreter_tool()],
            ) as agent:
                result = await agent.run(query)
        text = _extract_text_from_result(result)
        print(f"[Agent 3] Done.\n{text[:200]}...\n")
        return text

    # ------------------------------------------------------------------
    # Agent 4 — Summary Agent (Responses API)
    # ------------------------------------------------------------------

    async def _run_summary(
        self,
        budget_report_input: str,
        mcp_data_text: str,
        web_context_text: str,
        analysis_text: str,
    ) -> str:
        print("\n[Agent 4] Summary Agent — running...")
        agent = Agent(
            client=self.responses_client,
            instructions=SUMMARY_INSTRUCTIONS,
        )
        query = (
            "Generate the full Markdown budget variance report using these inputs.\n\n"
            "=== ORIGINAL SUBMITTED REPORT ===\n"
            f"{budget_report_input}\n\n"
            "=== MCP DATA RETRIEVAL RESULT ===\n"
            f"{mcp_data_text}\n\n"
            "=== WEB RESEARCH CONTEXT ===\n"
            f"{web_context_text}\n\n"
            "=== VARIANCE ANALYSIS RESULT ===\n"
            f"{analysis_text}"
        )
        result = await agent.run(query)
        text = _extract_text_from_result(result)
        print("[Agent 4] Done.\n")
        return text

    # ------------------------------------------------------------------
    # Agent 5 — Outlook Mail Agent (agent_reference)
    # ------------------------------------------------------------------

    async def _run_outlook_mail(
        self, summary_markdown: str, word_doc_path: Optional[Path]
    ) -> str:
        print(f"\n[Agent 5] Outlook Mail Agent — sending to {OUTLOOK_RECIPIENT}...")

        word_note = (
            f"A Word document version of this report has been saved to: {word_doc_path}"
            if word_doc_path
            else "Note: Word document generation was skipped (python-docx not available)."
        )

        email_prompt = f"""
Please compose and send a professional email with the following details:

To: {OUTLOOK_RECIPIENT}
Subject: Budget Variance Analysis Report — EDA Q1 2026

Email body should:
1. Open with a brief professional introduction (2-3 sentences) explaining this is an
   AI-assisted budget variance analysis for the Emirates Digital Authority Q1 2026.
2. Include a short summary of the headline findings (total overspend, departments flagged).
3. State that the full analysis report is included below.
4. Close professionally.

Then append the full report content below the email closing:

{summary_markdown}

---
{word_note}
This email was generated automatically by the EDA Budget Variance Workflow.
""".strip()

        response = self.openai_client.responses.create(
            input=[{"role": "user", "content": email_prompt}],
            extra_body={
                "agent_reference": {
                    "name": OUTLOOK_AGENT,
                    "version": OUTLOOK_VERSION,
                    "type": "agent_reference",
                }
            },
        )
        text = response.output_text
        print(f"[Agent 5] Done. Mail result: {text[:150]}...\n")
        return text


# ---------------------------------------------------------------------------
# Synthetic sample report — used when the script is run directly
# ---------------------------------------------------------------------------

def _load_sample_report() -> str:
    sample_path = Path(__file__).parent / "sample_budget_report.md"
    if sample_path.exists():
        return sample_path.read_text(encoding="utf-8")
    return "# Budget Variance Report\n\n(sample_budget_report.md not found)"


SAMPLE_BUDGET_REPORT_MARKDOWN = _load_sample_report()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    """Run the budget variance workflow on the sample report."""
    executor = BudgetVarianceWorkflowExecutor()
    result = await executor.execute(SAMPLE_BUDGET_REPORT_MARKDOWN)

    _banner("OUTPUT PATHS")
    print(f"Markdown  → {result['markdown_report_path']}")
    print(f"Word Doc  → {result['word_doc_path'] or 'Not generated'}")
    print(f"Mail Sent → {result['mail_result'][:100]}...")

    print("\n--- SUMMARY PREVIEW (first 1000 chars) ---")
    print(result["summary"][:1000])


if __name__ == "__main__":
    asyncio.run(main())
