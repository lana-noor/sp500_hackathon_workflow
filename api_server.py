"""
FastAPI backend with Server-Sent Events for the Budget Variance Report UI.

Run with:
    uvicorn api_server:app --reload --port 8000

Prerequisites:
    The Budget Data MCP Server must also be running:
        python budget_mcp_server.py
"""
import asyncio
import json
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel

from budget_variance_workflow import (
    BudgetVarianceWorkflowExecutor,
    SAMPLE_BUDGET_REPORT_MARKDOWN,
)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Budget Variance Report API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Holds the path to the most-recently generated Word document
_last_word_doc: dict = {"path": None}


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    budget_report: str = SAMPLE_BUDGET_REPORT_MARKDOWN


# ---------------------------------------------------------------------------
# Streaming executor — subclasses the workflow to inject SSE events
# ---------------------------------------------------------------------------

class StreamingWorkflowExecutor(BudgetVarianceWorkflowExecutor):
    """Overrides agent runner methods to emit progress events into a queue."""

    def __init__(self, queue: asyncio.Queue) -> None:
        super().__init__()
        self._q = queue

    async def _emit(self, data: dict) -> None:
        await self._q.put(data)

    # Agent 1 — MCP Data Agent
    async def _run_mcp_data(self, budget_report_input: str) -> str:
        await self._emit({"event": "agent_start", "agent": 1})
        result = await super()._run_mcp_data(budget_report_input)
        await self._emit({"event": "agent_complete", "agent": 1, "output": result})
        return result

    # Agent 2 — Web Search Agent
    async def _run_web_search(self, budget_report_input: str) -> str:
        await self._emit({"event": "agent_start", "agent": 2})
        result = await super()._run_web_search(budget_report_input)
        await self._emit({"event": "agent_complete", "agent": 2, "output": result})
        return result

    # Agent 3 — Code Interpreter Agent
    async def _run_code_analysis(
        self, budget_report_input: str, mcp_data_text: str, web_context_text: str
    ) -> str:
        await self._emit({"event": "agent_start", "agent": 3})
        result = await super()._run_code_analysis(
            budget_report_input, mcp_data_text, web_context_text
        )
        await self._emit({"event": "agent_complete", "agent": 3, "output": result})
        return result

    # Agent 4 — Summary Agent (also signals executor_start on return)
    async def _run_summary(
        self,
        budget_report_input: str,
        mcp_data_text: str,
        web_context_text: str,
        analysis_text: str,
    ) -> str:
        await self._emit({"event": "agent_start", "agent": 4})
        result = await super()._run_summary(
            budget_report_input, mcp_data_text, web_context_text, analysis_text
        )
        await self._emit({"event": "agent_complete", "agent": 4, "output": result})
        await self._emit({"event": "executor_start"})  # Word doc conversion is next
        return result

    # Agent 5 — Outlook Mail Agent
    async def _run_outlook_mail(self, summary_markdown: str, word_doc_path) -> str:
        await self._emit({"event": "agent_start", "agent": 5})
        result = await super()._run_outlook_mail(summary_markdown, word_doc_path)
        await self._emit({"event": "agent_complete", "agent": 5, "output": result})
        return result

    # Full workflow — wraps super().execute() and emits completion events
    async def execute(self, budget_report_input: str) -> dict:
        result = await super().execute(budget_report_input)
        await self._emit({
            "event": "executor_complete",
            "markdown": result["summary"],
            "word_doc_path": result.get("word_doc_path") or "",
            "mail_result": result.get("mail_result") or "",
        })
        await self._emit({"event": "done"})
        return result


# ---------------------------------------------------------------------------
# SSE endpoint
# ---------------------------------------------------------------------------

@app.post("/api/run")
async def run_workflow(body: RunRequest) -> StreamingResponse:
    """
    Run the budget variance workflow and stream progress as SSE events.

    Event types emitted:
      agent_start       { agent: 1|2|3|4|5 }
      agent_complete    { agent: 1|2|3|4|5, output: str }
      executor_start    {}
      executor_complete { markdown: str, word_doc_path: str, mail_result: str }
      done              {}
      error             { message: str }
    """

    async def generate() -> AsyncIterator[str]:
        queue: asyncio.Queue = asyncio.Queue()
        executor = StreamingWorkflowExecutor(queue)

        async def run_task() -> None:
            try:
                result = await executor.execute(body.budget_report)
                _last_word_doc["path"] = result.get("word_doc_path")
            except Exception as exc:
                await queue.put({"event": "error", "message": str(exc)})
                await queue.put({"event": "done"})

        task = asyncio.create_task(run_task())

        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("event") in ("done", "error"):
                    break
        finally:
            await task

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# Word doc download endpoint
# ---------------------------------------------------------------------------

@app.get("/api/download")
async def download_word() -> FileResponse:
    path = _last_word_doc.get("path")
    if not path or not Path(path).exists():
        raise HTTPException(status_code=404, detail="Word document not yet generated")
    return FileResponse(
        path=path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=Path(path).name,
    )


# ---------------------------------------------------------------------------
# Sample report endpoint — used to pre-fill the React textarea
# ---------------------------------------------------------------------------

@app.get("/api/sample")
async def get_sample() -> dict:
    return {"content": SAMPLE_BUDGET_REPORT_MARKDOWN}
