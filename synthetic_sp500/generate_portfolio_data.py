"""
Generate Synthetic S&P 500 Portfolio CSV
=========================================

Run this script once to export the synthetic portfolio data to CSV.
The same deterministic data is also generated in-memory by the MCP server
(seed=42 ensures both produce identical data).

Usage:
    python data/generate_portfolio_data.py

Output:
    data/synthetic_sp500_portfolio.csv
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import the MCP server's data generator
sys.path.insert(0, str(Path(__file__).parent.parent))

# The MCP server exports the CSV automatically on first run.
# This script just triggers that export explicitly.
import importlib.util as _ilu

_spec = _ilu.spec_from_file_location(
    "sp500_portfolio_risk_mcp_server",
    Path(__file__).parent.parent / "sp500-portfolio-risk-mcp-server.py",
)
mcp_server = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(mcp_server)  # noqa: E402


def main() -> None:
    portfolio = mcp_server._PORTFOLIO
    csv_path = mcp_server._CSV_PATH

    if csv_path.exists():
        print(f"CSV already exists at: {csv_path}")
        print(f"  Companies: {len(portfolio)}")
        print(f"  Total investment: ${len(portfolio):,}M")
        return

    # Force export
    mcp_server._export_csv_if_missing()
    print(f"Generated: {csv_path}")
    print(f"  Companies: {len(portfolio)}")
    print(f"  Sectors: {len(set(c['sector'] for c in portfolio))}")
    print(f"  Total investment: ${len(portfolio):,}M")

    # Print sector breakdown
    from collections import Counter
    sector_counts = Counter(c["sector"] for c in portfolio)
    print("\nSector breakdown:")
    for sector, count in sector_counts.most_common():
        print(f"  {sector:<35} {count:>3} companies  ${count}M")


if __name__ == "__main__":
    main()
