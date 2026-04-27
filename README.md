# S&P 500 Quantitative Research Workflow

> A **5-agent sequential research workflow** built on Microsoft Agent Framework that answers natural language investment questions using real S&P 500 price and return data — computing exact metrics from CSV files, sourcing qualitative context from the web, and assembling everything into a PowerPoint deck.

---

## What It Does

Ask any research question about S&P 500 performance between 2017 and 2021. The workflow:

1. Plans the analysis (Agent 1)
2. Runs Python code against the real CSV data to compute exact numbers (Agent 2)
3. Generates targeted web search queries from those findings (Agent 3)
4. Searches the web via Tavily and extracts sourced evidence (Agent 4)
5. Merges quantitative findings and web evidence into a slide deck spec (Agent 5)
6. Renders the PowerPoint file from that spec (deterministic Python function)

---

## Dataset

| File | Contents |
|---|---|
| `sp500_sample_data/tickerlist.csv` | 505 S&P 500 constituents — name, ticker, 11 GICS sectors |
| `sp500_sample_data/returns.csv` | 60 monthly decimal returns, January 2017 – December 2021, one column per ticker |
| `sp500_sample_data/prices.csv` | ~62 monthly price snapshots, one column per ticker |

All data is real S&P 500 constituent data. No synthetic values.

---

## Example Queries

```bash
python portfolio_risk_workflow.py --query "Compare NVIDIA, AMD, and Intel from 2017 to 2021 — total return, Sharpe ratio, and max drawdown."

python portfolio_risk_workflow.py --query "Rank all 11 S&P 500 sectors by Sharpe ratio from 2017 to 2021."

python portfolio_risk_workflow.py --query "How badly were airlines hit in the 2020 COVID crash? Compute max drawdown and 2020 annual return."

python portfolio_risk_workflow.py --query "Give me a full analysis of Apple from 2017 to 2021 — cumulative return, annual performance, max drawdown, and Sharpe ratio."
```

See [`example_queries.md`](example_queries.md) for 40+ ready-to-run queries across every sector.

---

## Architecture Diagram

Open [`workflow_architecture_sp500.html`](workflow_architecture_sp500.html) in a browser for the full interactive architecture diagram.

---

## Agent Pipeline

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│         S&P 500 RESEARCH WORKFLOW  (5 Sequential Agents)            │
└─────────────────────────────────────────────────────────────────────┘

Agent 1: Query Planner  (FoundryChatClient — no portal agent needed)
  ├─ Input:  natural language research question
  ├─ Task:   classify intent, resolve tickers/sectors in scope,
  │          generate 3–5 analytical questions (answerable from CSVs)
  │          and 2–3 qualitative questions (for web research)
  └─ Output: structured research plan JSON

Agent 2: Quantitative Analyst  (FoundryAgent + Code Interpreter)
  ├─ Tool:   Code Interpreter — Python sandbox (pandas / numpy)
  ├─ Files:  tickerlist.csv, prices.csv, returns.csv (attached in Foundry portal)
  ├─ Task:   execute every analytical question with real computed values —
  │          cumulative return, year-by-year annual returns, max drawdown,
  │          Sharpe ratio, annualised volatility, correlations, rankings
  ├─ Guard:  output validated on return — rejects hallucinated templates
  └─ Output: findings JSON with real computed numbers

Agent 3: Search Query Expander  (FoundryChatClient — no portal agent needed)
  ├─ Input:  research plan (Agent 1) + findings summary (Agent 2)
  ├─ Task:   generate 5–8 precise web search query strings grounded in
  │          the quantitative findings — business drivers and events,
  │          not raw percentages
  └─ Output: query list JSON

Agent 4: Web Researcher  (FoundryChatClient + Tavily, one call per query)
  ├─ Tool:   Tavily Search API  (requires TAVILY_API_KEY in .env)
  ├─ Task:   loop through every query from Agent 3;
  │          call Tavily, then extract 2–4 factual claims per result;
  │          record coverage_gap: true when no relevant sources found
  └─ Output: evidence pack JSON with sourced claims and URLs

Agent 5: Synthesizer  (FoundryChatClient — no portal agent needed)
  ├─ Input:  research plan + findings (Agent 2) + evidence pack (Agent 4)
  ├─ Task:   design 5–8 slides — every claim cites a number from Agent 2
  │          or a URL from Agent 4; year-by-year returns always get a
  │          dedicated comparison_table slide
  └─ Output: slide_deck_spec JSON

generate_pptx()  [deterministic Python function — not an LLM]
  ├─ Input:  slide_deck_spec from Agent 5
  └─ Output: dark-navy PowerPoint presentation saved to ./output/
```

---

## The 5 Agents in Detail

### Agent 1 — Query Planner
**Type:** `FoundryChatClient` — no portal agent required  
**Prompt:** `prompts/query_planner_agent.txt`

Reads the user's question and produces a structured research plan. Classifies the query intent, resolves which tickers and sectors are in scope, and splits the work into:
- **Analytical questions** (3–5): answerable from the CSV data — cumulative return, annual breakdown, max drawdown, Sharpe ratio, volatility, correlations, rankings
- **Qualitative questions** (2–3): require web search — macro drivers, industry dynamics, events

**Intent types recognised:**

| Intent | Example phrasing |
|---|---|
| `single_stock_deep_dive` | "Analyze Apple from 2017 to 2021" |
| `sector_comparison` | "Compare IT versus Energy" |
| `ranking` | "Rank all sectors by Sharpe ratio" |
| `risk_analysis` | "Which stocks had the worst drawdown in 2020?" |
| `correlation_study` | "How correlated were the 11 sectors?" |
| `general` | Broad exploratory questions |

---

### Agent 2 — Quantitative Analyst
**Type:** `FoundryAgent` with Code Interpreter tool — must be created in the Foundry portal  
**Prompt:** `prompts/quantitative_analyst_agent.txt` (set as the agent's system prompt in the portal)

The only agent in this workflow that requires a portal deployment. Runs Python code inside a sandbox against the three attached CSV files. Computes real values — no estimates, no simulated data.

**Metrics computed:**
- Cumulative total return over the full period
- Year-by-year annual returns (2017, 2018, 2019, 2020, 2021)
- Max drawdown (peak-to-trough on cumulative curve)
- Sharpe ratio (annualised, 0% risk-free rate)
- Annualised volatility
- Pairwise correlations
- Rankings by any metric

**Output validation:** the workflow validates Agent 2's response immediately on return. If the output contains placeholder text (`[value]`, `calculated value`, `INSERT`, etc.) or is missing the `findings` key, a `ValueError` is raised and the run stops rather than passing bad data downstream.

---

### Agent 3 — Search Query Expander
**Type:** `FoundryChatClient` — no portal agent required  
**Prompt:** `prompts/search_query_expander_agent.txt`

Takes the research plan and Agent 2's findings and generates 5–8 web search query strings. Queries describe business drivers, macro events, and industry themes — not raw statistics. Embedding exact return percentages in query strings is explicitly prohibited because it degrades search result quality.

---

### Agent 4 — Web Researcher
**Type:** `FoundryChatClient` + Tavily Search API  
**Prompt:** `prompts/web_researcher_agent.txt`

Loops through each query from Agent 3. For every query:
1. Calls the Tavily Search API (one call, max 3 results)
2. Passes the raw results to a `FoundryChatClient` call that extracts 2–4 specific factual claims with full source URLs
3. Skips paywalled, promotional, or off-topic sources
4. Records `coverage_gap: true` when no relevant sources are found — never fabricates

If `TAVILY_API_KEY` is not set, Agent 4 is skipped entirely and the deck is built from quantitative findings only.

---

### Agent 5 — Synthesizer
**Type:** `FoundryChatClient` — no portal agent required  
**Prompt:** `prompts/synthesizer_agent.txt`

Merges Agent 2's findings and Agent 4's evidence pack into a `slide_deck_spec` JSON that `generate_pptx()` renders directly. Every factual claim must cite either a real number from Agent 2 or a URL from Agent 4 — uncited claims are omitted.

**Slide structure:**
1. **Title** — deck title, user query, analysis period
2. **Executive Summary** — 3–5 bullets with real computed numbers
3. **Comparison Table** — total return, max drawdown, Sharpe ratio, annualised volatility
4. **Annual Returns Table** — year-by-year breakdown per ticker or sector (dedicated `comparison_table` slide whenever Agent 2 provides annual return data)
5. **Narrative** — qualitative context with URL citations from Agent 4
6. **Sources** — all unique URLs from the evidence pack

---

### generate_pptx() — Presentation Builder
**Type:** Deterministic Python function — no LLM call  
**Library:** `python-pptx`

Reads the `slide_deck_spec` from Agent 5 and renders each slide type using a dark-navy / gold design theme. Makes no model calls — pure Python.

---

## How the Numbers Flow into the Deck

Agent 2 runs Python code against the CSV files inside the Code Interpreter sandbox. The agent reads its own code outputs and writes a final JSON response containing the real computed values. That JSON (`findings`) is:

1. **Validated on return** — any hallucinated template or placeholder text raises an error immediately
2. **Passed verbatim to Agent 5** as `=== QUANTITATIVE FINDINGS (Agent 2) ===`
3. **Written into `slide_deck_spec`** by Agent 5 with exact numbers in bullets and table rows
4. **Rendered into the PPTX** by `generate_pptx()` — a deterministic function that makes no LLM calls

---

## Key Files

| File | Purpose |
|---|---|
| `portfolio_risk_workflow.py` | Main workflow — run this |
| `sp500_sample_data/` | `tickerlist.csv`, `returns.csv`, `prices.csv` |
| `prompts/query_planner_agent.txt` | Agent 1 system prompt |
| `prompts/quantitative_analyst_agent.txt` | Agent 2 system prompt (set in Foundry portal) |
| `prompts/search_query_expander_agent.txt` | Agent 3 system prompt |
| `prompts/web_researcher_agent.txt` | Agent 4 system prompt |
| `prompts/synthesizer_agent.txt` | Agent 5 system prompt |
| `example_queries.md` | 40+ ready-to-run example queries |
| `workflow_architecture_sp500.html` | Interactive architecture diagram |
| `output/` | JSON checkpoints and PPTX files |
| `.envsample` | Environment variable template |

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
pip install python-pptx   # required for PPTX generation
pip install httpx         # required for Tavily API calls
```

### 2. Create the Quantitative Analyst agent in the Azure AI Foundry portal

This is the **only** agent that needs to be created in the portal. Agents 1, 3, 4, and 5 run as `FoundryChatClient` — no portal setup required for them.

```
Name:    SP500QuantAgent            (must match QUANT_AGENT_NAME in .env)
Version: 1                          (must match QUANT_AGENT_VERSION in .env)
Model:   gpt-4o (or your deployment)
Tools:   ✅ Code Interpreter

File Attachments — upload all three from sp500_sample_data/:
  ✅ tickerlist.csv
  ✅ returns.csv
  ✅ prices.csv

System Prompt:
  Copy the full content of: prompts/quantitative_analyst_agent.txt
```

The three CSV files must be attached directly to the agent in the Foundry portal. The Code Interpreter loads them at runtime — they are not sent through the API message.

### 3. Get a Tavily API key

Agent 4 calls the Tavily Search API (free tier available at [tavily.com](https://tavily.com)). If `TAVILY_API_KEY` is left blank, Agent 4 is skipped and the deck is built from quantitative findings only — no web citations.

### 4. Configure environment variables

Copy `.envsample` to `.env` and fill in:

```bash
AZURE_AI_PROJECT_ENDPOINT=https://<your-project>.services.ai.azure.com/api/projects/<project>
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2025-03-01-preview

SP500_DATA_DIR=./sp500_sample_data

QUANT_AGENT_NAME=SP500QuantAgent
QUANT_AGENT_VERSION=1

TAVILY_API_KEY=tvly-your-key-here

OUTPUT_DIR=./output
```

### 5. Authenticate to Azure

```bash
az login
# or
azd auth login
```

---

## Running the Workflow

```bash
# Default query
python portfolio_risk_workflow.py

# Custom query
python portfolio_risk_workflow.py --query "Compare Apple and Microsoft from 2017 to 2021."

# Resume an interrupted run automatically — same query finds the latest checkpoint
python portfolio_risk_workflow.py --query "Compare Apple and Microsoft from 2017 to 2021."

# Resume a specific run by ID (printed at the start of every run)
python portfolio_risk_workflow.py --run-id 20260427_143022

# Delete checkpoint and restart from Agent 1
python portfolio_risk_workflow.py --query "Compare Apple and Microsoft from 2017 to 2021." --reset

# Delete a specific run by ID and restart
python portfolio_risk_workflow.py --run-id 20260427_143022 --reset
```

### Expected Console Output

```
=================================================================
  S&P 500 RESEARCH WORKFLOW — START (5 AGENTS)
=================================================================
  Query:      Compare Apple and Microsoft from 2017 to 2021.
  Run ID:     20260427_143022
  Checkpoint: ./output/sp500_analysis_20260427_143022.json

[Agent 1] Query Planner (FoundryChatClient)...
[Agent 1] Done. Research plan produced.

[Agent 2] Quantitative Analyst — calling SP500QuantAgent v1...
[Agent 2] Running Python analysis against tickerlist, prices, returns CSVs...
[Agent 2 Validation] OK — 4 finding(s) validated.
[Agent 2] Done. Quantitative analysis complete.

[Agent 3] Search Query Expander (FoundryChatClient)...
[Agent 3] Done. Search queries generated.

[Agent 4] Web Researcher (FoundryChatClient + Tavily, per-query loop)...
[Agent 4] Query 1/6: Microsoft cloud revenue growth Azure 2017 2021...
[Agent 4] Query 2/6: Apple iPhone services revenue transition 2017 2021...
...
[Agent 4] Done. 6 evidence entries, 1 coverage gap(s).

[Agent 5] Synthesizer (FoundryChatClient)...
[Agent 5] Done. Slide deck spec generated.

[Executor] PPTX saved -> ./output/sp500_analysis_20260427_143022.pptx

=================================================================
  WORKFLOW COMPLETE
=================================================================
  Output JSON -> ./output/sp500_analysis_20260427_143022.json
  Output PPTX -> ./output/sp500_analysis_20260427_143022.pptx
```

---

## Output

Every run saves two files to `./output/`:

| File | Contents |
|---|---|
| `sp500_analysis_<id>.json` | Full checkpoint — all five agent outputs. Re-running with the same query automatically resumes from the last completed step. |
| `sp500_analysis_<id>.pptx` | PowerPoint deck with real computed metrics from Agent 2 and web-sourced narrative from Agent 4 |

### Checkpoint / Resume

The JSON file is both the output record and the resume checkpoint. If a run is interrupted at any agent, re-running with the same query string automatically finds the latest checkpoint and skips completed steps. Use `--reset` to force a fresh run from Agent 1.

---

## Agent Framework Classes Used

| Class | Used By | Description |
|---|---|---|
| `FoundryChatClient` | Agents 1, 3, 4, 5 | Inline agent — model, instructions, and tools set in code at runtime. No portal resource created. |
| `FoundryAgent` | Agent 2 | Server-managed agent created in the Foundry portal. Persistent versioning, Code Interpreter tool, file attachments. |

```python
# FoundryChatClient — used for Agents 1, 3, 4, 5
from agent_framework.foundry import FoundryChatClient

client = FoundryChatClient(
    project_endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT"),
    model=os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME"),
    credential=DefaultAzureCredential(),
)

# FoundryAgent — used for Agent 2 (Code Interpreter)
from agent_framework.foundry import FoundryAgent

agent = FoundryAgent(
    project_endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT"),
    agent_name="SP500QuantAgent",
    agent_version="1",
    credential=DefaultAzureCredential(),
)
```

Install the framework:

```bash
pip install agent-framework>=1.0.1
pip install agent-framework-foundry>=1.0.1
```
