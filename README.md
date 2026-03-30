# 🤖 Multi-Agent Budget Variance Analysis Workflow

> **A production-grade 6-agent sequential workflow** built with Azure AI Foundry Agent Service that automates budget variance analysis for government agencies using MCP, Web Search, Code Interpreter, Foundry IQ (AI Search), and Microsoft 365 integration.

[![Azure AI Foundry](https://img.shields.io/badge/Azure_AI_Foundry-0078D4?style=flat&logo=microsoft-azure&logoColor=white)](https://ai.azure.com)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [The 6 Agents](#-the-6-agents)
- [Prerequisites](#-prerequisites)
- [Deployment Guide](#-deployment-guide)
- [Running the Workflow](#-running-the-workflow)
- [Output Examples](#-output-examples)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)

---

## 🎯 Overview

This workflow demonstrates a **real-world enterprise use case**: automating quarterly budget variance analysis for the **Apex Digital Government Authority (ADGA)** using a 6-agent sequential pipeline.

### What It Does

**The workflow performs 3-way reconciliation:**
1. **Department Claims** (what departments SAY happened) → via MCP server
2. **Economic Validation** (external data confirms/contradicts) → via Web Search
3. **Official Data** (what ACTUALLY happened) → via CSV file analysis
4. **Policy Compliance** (what regulations REQUIRE) → via AI Search

**Output:** A comprehensive executive report (Markdown + Word) delivered via Outlook.

### Key Features

✅ **Model Context Protocol (MCP)** - Custom server deployed to Azure Container Apps  
✅ **Web Search Integration** - Real-time economic data validation  
✅ **Code Interpreter** - Python-based CSV analysis with file attachments  
✅ **Foundry IQ (AI Search)** - RAG over policy documents  
✅ **Microsoft 365** - Automated email delivery via Outlook  
✅ **Sequential Agent Orchestration** - Each agent builds on previous outputs  
✅ **Enterprise-Ready** - Handles real CSV data, generates audit-ready reports

---

## 🏗️ Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BUDGET VARIANCE WORKFLOW                         │
│                  (6 Sequential Agents + MCP Server)                 │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  📦 Azure Container Apps                                             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  MCP Server: budget-reports-mcp-server                         │ │
│  │  Serves: department_reports/*.md (narratives & justifications) │ │
│  └────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AGENT 1: BudgetReportsMCPAgent                                     │
│  Tool: MCP                                                          │
│  Output: Department claims & justifications (JSON)                 │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AGENT 2: WebSearchBudgetsAgent                                     │
│  Tool: Web Search (Bing Grounding)                                  │
│  Output: Economic validation data (inflation, cloud costs, etc.)   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AGENT 3: BudgetVarianceCodeIntAgent                                │
│  Tool: Code Interpreter                                             │
│  Files: approved_budgets.csv, historical_actuals.csv                │
│  Output: Reconciliation analysis (claims vs. reality) + policy check│
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AGENT 4: BudgetPolicyAgent                                         │
│  Tool: Azure AI Search (Foundry IQ)                                 │
│  Index: adga-budget-policies                                        │
│  Output: Compliance requirements, regulatory risks, timelines       │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AGENT 5: Summary Agent                                             │
│  Tool: Responses API (no agent_reference)                           │
│  Output: Executive Markdown report → Word document                  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AGENT 6: BudgetWorkIQMailAgent                                     │
│  Tool: Microsoft 365 (Outlook)                                      │
│  Output: Email sent to CFO/Board with report attached               │
└─────────────────────────────────────────────────────────────────────┘
```


