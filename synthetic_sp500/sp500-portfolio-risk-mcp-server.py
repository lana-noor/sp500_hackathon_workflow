"""
S&P 500 Portfolio Risk MCP Server
===================================

A FastMCP server that serves synthetic S&P 500-like portfolio data for
investment risk analysis demos.

Portfolio assumptions:
  - 500 synthetic public companies modeled after the S&P 500 index
  - Equal investment of $1,000,000 per company ($500M total)
  - Each company has: sector, industry, description, market cap, revenue, beta, P/E
  - Data is synthetic and for demonstration purposes only

Run locally with:
    fastmcp run sp500-portfolio-risk-mcp-server.py --transport streamable-http --port 8001

Deployed to Azure Container Apps at:
    https://sp500-portfolio-risk-mcp-server.<random-id>.eastus.azurecontainerapps.io/mcp
"""

import csv
import json
import random
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Server initialisation
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="SP500PortfolioRiskServer",
    instructions=(
        "Provides access to a synthetic S&P 500-like investment portfolio for risk analysis. "
        "The portfolio contains 500 companies with equal $1,000,000 investments each ($500M total). "
        "Use these tools to retrieve company data, sector holdings, and portfolio statistics "
        "for investment risk and exposure analysis. All data is synthetic and for demo use only."
    ),
)

# ---------------------------------------------------------------------------
# Synthetic data generation — deterministic (seed=42)
# ---------------------------------------------------------------------------

# Sector configuration: name → {count, industries, beta, pe, market_cap, revenue, supply_chain_sensitivity}
_SECTOR_CONFIG = {
    "Information Technology": {
        "count": 75,
        "industries": ["Software", "Semiconductors", "Hardware & Equipment", "IT Services", "Cloud Infrastructure"],
        "beta_mean": 1.40, "beta_std": 0.30,
        "pe_mean": 38.0,   "pe_std": 18.0,
        "mc_mean": 80.0,   "mc_std": 200.0,
        "rev_mean": 20.0,  "rev_std": 50.0,
        "sc_weights": {"HIGH": 0.55, "MEDIUM": 0.35, "LOW": 0.10},
        "descriptions": [
            "develops enterprise SaaS platforms for workflow automation",
            "designs high-performance GPU and CPU semiconductor chips",
            "manufactures networking hardware and switching equipment",
            "provides managed cloud and IT outsourcing services",
            "operates hyperscale data centre infrastructure",
            "builds AI-powered analytics and business intelligence tools",
            "supplies semiconductor fabrication equipment",
            "develops cybersecurity software and threat detection systems",
            "provides ERP and supply chain management software",
            "designs mobile processors and system-on-chip solutions",
        ],
    },
    "Health Care": {
        "count": 65,
        "industries": ["Pharmaceuticals", "Biotechnology", "Medical Devices", "Health Services", "Diagnostics & Tools"],
        "beta_mean": 0.80, "beta_std": 0.25,
        "pe_mean": 24.0,   "pe_std": 12.0,
        "mc_mean": 40.0,   "mc_std": 80.0,
        "rev_mean": 12.0,  "rev_std": 25.0,
        "sc_weights": {"HIGH": 0.20, "MEDIUM": 0.45, "LOW": 0.35},
        "descriptions": [
            "develops and commercialises oncology therapeutics",
            "manufactures surgical robotics and minimally invasive devices",
            "operates a national network of diagnostic imaging centres",
            "produces generic and branded pharmaceutical formulations",
            "provides clinical research and drug development services",
            "develops mRNA-based vaccine platforms",
            "manufactures continuous glucose monitoring devices",
            "provides pharmacy benefit management services",
            "develops gene therapy treatments for rare diseases",
            "supplies laboratory diagnostics equipment and reagents",
        ],
    },
    "Financials": {
        "count": 70,
        "industries": ["Banks", "Insurance", "Asset Management", "Diversified Financials", "Payment Processing"],
        "beta_mean": 1.05, "beta_std": 0.20,
        "pe_mean": 13.0,   "pe_std": 4.0,
        "mc_mean": 60.0,   "mc_std": 120.0,
        "rev_mean": 25.0,  "rev_std": 50.0,
        "sc_weights": {"HIGH": 0.05, "MEDIUM": 0.25, "LOW": 0.70},
        "descriptions": [
            "operates a diversified retail and commercial banking network",
            "provides property and casualty insurance products",
            "manages institutional and retail investment funds",
            "processes electronic payments and card transactions",
            "provides investment banking and capital markets services",
            "operates a consumer credit and personal loan platform",
            "provides mortgage origination and servicing",
            "manages private equity and alternative investments",
            "provides financial data and analytics to institutions",
            "operates a digital-first neobank and payments platform",
        ],
    },
    "Consumer Discretionary": {
        "count": 55,
        "industries": ["Retail", "Automotive", "Hospitality & Travel", "Media & Entertainment", "E-Commerce"],
        "beta_mean": 1.25, "beta_std": 0.30,
        "pe_mean": 28.0,   "pe_std": 14.0,
        "mc_mean": 35.0,   "mc_std": 100.0,
        "rev_mean": 20.0,  "rev_std": 60.0,
        "sc_weights": {"HIGH": 0.50, "MEDIUM": 0.35, "LOW": 0.15},
        "descriptions": [
            "operates a global e-commerce marketplace and fulfilment network",
            "designs and manufactures electric passenger vehicles",
            "operates a chain of luxury department stores",
            "provides on-demand video streaming entertainment",
            "franchises and operates quick-service restaurant brands",
            "manufactures premium athletic footwear and apparel",
            "operates hotel and resort properties worldwide",
            "provides online travel booking and accommodation services",
            "designs and retails consumer furniture and home goods",
            "operates a subscription-based fitness equipment platform",
        ],
    },
    "Communication Services": {
        "count": 25,
        "industries": ["Telecom Services", "Media", "Interactive Media & Services", "Wireless Services"],
        "beta_mean": 0.90, "beta_std": 0.20,
        "pe_mean": 22.0,   "pe_std": 10.0,
        "mc_mean": 100.0,  "mc_std": 300.0,
        "rev_mean": 40.0,  "rev_std": 80.0,
        "sc_weights": {"HIGH": 0.10, "MEDIUM": 0.30, "LOW": 0.60},
        "descriptions": [
            "operates a global social media and digital advertising platform",
            "provides nationwide 5G wireless and broadband services",
            "produces and distributes film and television content",
            "operates a music and podcast streaming platform",
            "provides satellite internet and direct-to-home TV services",
            "operates a digital search engine and advertising network",
            "provides enterprise unified communications and video conferencing",
        ],
    },
    "Industrials": {
        "count": 70,
        "industries": ["Aerospace & Defense", "Machinery", "Transportation & Logistics", "Construction & Engineering", "Business Services"],
        "beta_mean": 1.05, "beta_std": 0.25,
        "pe_mean": 22.0,   "pe_std": 8.0,
        "mc_mean": 25.0,   "mc_std": 60.0,
        "rev_mean": 12.0,  "rev_std": 25.0,
        "sc_weights": {"HIGH": 0.45, "MEDIUM": 0.40, "LOW": 0.15},
        "descriptions": [
            "manufactures commercial aircraft and aviation components",
            "produces industrial robots and factory automation systems",
            "operates express parcel delivery and freight logistics",
            "engineers and constructs large-scale infrastructure projects",
            "provides staffing, payroll, and workforce management services",
            "manufactures gas turbines and power generation equipment",
            "operates a rail freight transportation network",
            "designs and builds HVAC and building systems",
            "provides defence electronics and military communication systems",
            "manufactures precision measurement and testing instruments",
        ],
    },
    "Consumer Staples": {
        "count": 35,
        "industries": ["Food & Beverages", "Personal Products", "Household Products", "Food Retail"],
        "beta_mean": 0.55, "beta_std": 0.15,
        "pe_mean": 22.0,   "pe_std": 6.0,
        "mc_mean": 50.0,   "mc_std": 100.0,
        "rev_mean": 30.0,  "rev_std": 60.0,
        "sc_weights": {"HIGH": 0.20, "MEDIUM": 0.50, "LOW": 0.30},
        "descriptions": [
            "produces and distributes packaged food and snack brands",
            "manufactures personal care and grooming products",
            "brews and markets global beer and beverage brands",
            "operates a nationwide grocery and supermarket chain",
            "produces cleaning and household maintenance products",
            "distributes premium coffee and hot beverage products",
            "manufactures infant nutrition and health food products",
        ],
    },
    "Energy": {
        "count": 25,
        "industries": ["Oil & Gas Exploration", "Renewable Energy", "Energy Equipment & Services", "Oil Refining & Marketing"],
        "beta_mean": 1.20, "beta_std": 0.30,
        "pe_mean": 14.0,   "pe_std": 6.0,
        "mc_mean": 50.0,   "mc_std": 120.0,
        "rev_mean": 30.0,  "rev_std": 80.0,
        "sc_weights": {"HIGH": 0.30, "MEDIUM": 0.45, "LOW": 0.25},
        "descriptions": [
            "explores, produces, and markets crude oil and natural gas",
            "develops and operates utility-scale solar and wind farms",
            "provides oilfield drilling and completion services",
            "refines crude oil into petroleum products and chemicals",
            "builds and operates LNG export terminals and pipelines",
            "manufactures wind turbines and renewable energy components",
        ],
    },
    "Utilities": {
        "count": 30,
        "industries": ["Electric Utilities", "Gas Utilities", "Water Utilities", "Renewable Power Generation"],
        "beta_mean": 0.45, "beta_std": 0.15,
        "pe_mean": 17.0,   "pe_std": 4.0,
        "mc_mean": 20.0,   "mc_std": 40.0,
        "rev_mean": 8.0,   "rev_std": 12.0,
        "sc_weights": {"HIGH": 0.05, "MEDIUM": 0.25, "LOW": 0.70},
        "descriptions": [
            "operates regulated electric transmission and distribution",
            "distributes natural gas to residential and commercial customers",
            "operates water treatment and municipal water supply infrastructure",
            "generates electricity from solar, wind, and hydro sources",
            "operates a nuclear power generation fleet",
        ],
    },
    "Real Estate": {
        "count": 30,
        "industries": ["Commercial REITs", "Residential REITs", "Industrial & Logistics REITs", "Diversified Real Estate"],
        "beta_mean": 0.85, "beta_std": 0.20,
        "pe_mean": 28.0,   "pe_std": 10.0,
        "mc_mean": 15.0,   "mc_std": 30.0,
        "rev_mean": 4.0,   "rev_std": 8.0,
        "sc_weights": {"HIGH": 0.05, "MEDIUM": 0.20, "LOW": 0.75},
        "descriptions": [
            "owns and manages Class A commercial office properties",
            "owns and operates apartment communities in major metros",
            "owns a portfolio of industrial and logistics warehouses",
            "develops and leases retail shopping centre properties",
            "operates data centre facilities and co-location services",
            "manages senior housing and healthcare facility properties",
        ],
    },
    "Materials": {
        "count": 20,
        "industries": ["Specialty Chemicals", "Mining & Metals", "Steel & Aluminium", "Paper & Packaging"],
        "beta_mean": 1.10, "beta_std": 0.25,
        "pe_mean": 16.0,   "pe_std": 6.0,
        "mc_mean": 20.0,   "mc_std": 50.0,
        "rev_mean": 10.0,  "rev_std": 20.0,
        "sc_weights": {"HIGH": 0.40, "MEDIUM": 0.40, "LOW": 0.20},
        "descriptions": [
            "produces specialty chemicals for industrial and agricultural use",
            "mines and refines copper, lithium, and rare earth metals",
            "manufactures flat-rolled steel products for automotive use",
            "produces aluminium sheet and extrusions for aerospace",
            "manufactures sustainable paper-based packaging solutions",
        ],
    },
}

# Adjective/noun patterns for generating synthetic company names
_NAME_PARTS = {
    "prefixes": [
        "Apex", "Atlas", "Beacon", "Blue", "Bright", "Crest", "Crown", "Delta",
        "Eagle", "Echo", "Edge", "Ember", "Evolve", "First", "Forge", "Global",
        "Golden", "Green", "Hawk", "High", "Horizon", "Hyper", "Ideal", "Insight",
        "Ion", "Iron", "Jade", "Keystone", "Laser", "Liberty", "Link", "Lumen",
        "Macro", "Main", "Metro", "Micro", "Mid", "Milestone", "Modern", "Mono",
        "New", "Next", "Nord", "North", "Nova", "Omni", "Open", "Optimal", "Orbit",
        "Pacific", "Peak", "Pinnacle", "Pioneer", "Pivot", "Prime", "Pro", "Pulse",
        "Quantum", "Quest", "Rapid", "Red", "Ridge", "Rise", "Rock", "Royal",
        "Safe", "Scale", "Silver", "Smart", "Solid", "South", "Spark", "Star",
        "Steel", "Sterling", "Summit", "Swift", "Titan", "True", "Trust", "Ultra",
        "Union", "United", "Vector", "Vertex", "Vibe", "Vision", "Vital", "West",
        "White", "Wide", "Wind", "Wise", "World", "Zenith", "Zero",
    ],
    "suffixes": [
        "Analytics", "Bio", "Capital", "Care", "Cast", "Cloud", "Corp", "Crest",
        "Data", "Dynamics", "Edge", "Energy", "Enterprises", "Equities", "Finance",
        "Flow", "Force", "Global", "Group", "Health", "Holdings", "Hub", "IQ",
        "Labs", "Link", "Logic", "Matrix", "Media", "Net", "Networks", "One",
        "Optima", "Partners", "Path", "Point", "Power", "Pro", "Reach", "Resources",
        "Sciences", "Secure", "Select", "Services", "Shield", "Signal", "Smart",
        "Solutions", "Source", "Sphere", "Stream", "Systems", "Tech", "Technologies",
        "Therapeutics", "Tower", "Track", "Trust", "Ventures", "Vision", "Wave",
        "Works", "World",
    ],
}


def _pick_supply_chain(rng: random.Random, weights: dict) -> str:
    levels = list(weights.keys())
    probs = list(weights.values())
    return rng.choices(levels, weights=probs, k=1)[0]


def _generate_portfolio(seed: int = 42) -> list[dict]:
    """Generate 500 synthetic portfolio companies deterministically."""
    rng = random.Random(seed)
    portfolio = []
    company_id = 1
    used_tickers: set[str] = set()

    for sector, cfg in _SECTOR_CONFIG.items():
        industries = cfg["industries"]
        descriptions = cfg["descriptions"]

        for i in range(cfg["count"]):
            industry = industries[i % len(industries)]
            description = descriptions[i % len(descriptions)]

            # Generate unique ticker (3–4 letters)
            while True:
                length = rng.choice([3, 4])
                ticker = "".join(rng.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=length))
                if ticker not in used_tickers:
                    used_tickers.add(ticker)
                    break

            # Generate company name
            prefix = rng.choice(_NAME_PARTS["prefixes"])
            suffix = rng.choice(_NAME_PARTS["suffixes"])
            company_name = f"{prefix} {suffix} Inc."

            # Financial attributes — clipped to realistic ranges
            beta = round(max(0.1, rng.gauss(cfg["beta_mean"], cfg["beta_std"])), 2)
            pe = round(max(5.0, rng.gauss(cfg["pe_mean"], cfg["pe_std"])), 1)
            market_cap = round(max(0.5, rng.gauss(cfg["mc_mean"], cfg["mc_std"])), 2)
            revenue = round(max(0.1, rng.gauss(cfg["rev_mean"], cfg["rev_std"])), 2)
            sc_sensitivity = _pick_supply_chain(rng, cfg["sc_weights"])

            portfolio.append({
                "company_id": company_id,
                "ticker": ticker,
                "company_name": company_name,
                "sector": sector,
                "industry": industry,
                "description": f"{company_name[:-5]} {description}",
                "market_cap_b": market_cap,
                "revenue_b": revenue,
                "beta": beta,
                "pe_ratio": pe,
                "supply_chain_sensitivity": sc_sensitivity,
                "investment_usd": 1_000_000,
            })
            company_id += 1

    return portfolio


# ---------------------------------------------------------------------------
# Build the in-memory portfolio at module load time
# ---------------------------------------------------------------------------

_PORTFOLIO: list[dict] = _generate_portfolio(seed=42)

# Index by ticker and sector for fast lookup
_BY_TICKER: dict[str, dict] = {c["ticker"]: c for c in _PORTFOLIO}
_BY_SECTOR: dict[str, list[dict]] = {}
for _company in _PORTFOLIO:
    _BY_SECTOR.setdefault(_company["sector"], []).append(_company)

# ---------------------------------------------------------------------------
# Optionally persist to CSV on startup (for reference / Code Interpreter)
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).parent / "data"
_CSV_PATH = _DATA_DIR / "synthetic_sp500_portfolio.csv"


def _export_csv_if_missing() -> None:
    if _CSV_PATH.exists():
        return
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "company_id", "ticker", "company_name", "sector", "industry",
        "description", "market_cap_b", "revenue_b", "beta", "pe_ratio",
        "supply_chain_sensitivity", "investment_usd",
    ]
    with open(_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(_PORTFOLIO)
    print(f"[MCP] Exported portfolio CSV -> {_CSV_PATH}")


_export_csv_if_missing()


# ---------------------------------------------------------------------------
# Tool 1 — Portfolio-level summary
# ---------------------------------------------------------------------------

@mcp.tool(annotations={"readOnlyHint": True, "idempotentHint": True})
def get_portfolio_summary() -> dict:
    """
    Return a high-level summary of the synthetic S&P 500-like portfolio.

    Includes total company count, total investment, sector breakdown with
    company counts and aggregate investment, and supply chain sensitivity distribution.
    Use this first to understand the portfolio composition before drilling into sectors.
    """
    sector_breakdown = []
    for sector, companies in _BY_SECTOR.items():
        sc_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for c in companies:
            sc_counts[c["supply_chain_sensitivity"]] += 1
        sector_breakdown.append({
            "sector": sector,
            "company_count": len(companies),
            "total_investment_usd": len(companies) * 1_000_000,
            "avg_beta": round(sum(c["beta"] for c in companies) / len(companies), 2),
            "supply_chain_high_count": sc_counts["HIGH"],
            "supply_chain_medium_count": sc_counts["MEDIUM"],
            "supply_chain_low_count": sc_counts["LOW"],
        })

    sector_breakdown.sort(key=lambda x: x["company_count"], reverse=True)

    return {
        "portfolio_name": "Synthetic S&P 500-like Portfolio",
        "data_note": "All data is synthetic — for demonstration purposes only",
        "total_companies": len(_PORTFOLIO),
        "total_investment_usd": len(_PORTFOLIO) * 1_000_000,
        "investment_per_company_usd": 1_000_000,
        "total_sectors": len(_BY_SECTOR),
        "sectors": sector_breakdown,
    }


# ---------------------------------------------------------------------------
# Tool 2 — Get all companies in a sector
# ---------------------------------------------------------------------------

@mcp.tool(annotations={"readOnlyHint": True, "idempotentHint": True})
def get_sector_holdings(sector: str) -> dict:
    """
    Retrieve all portfolio companies in a given GICS sector.

    Args:
        sector: Full sector name, e.g. 'Information Technology', 'Health Care',
                'Financials', 'Consumer Discretionary', 'Communication Services',
                'Industrials', 'Consumer Staples', 'Energy', 'Utilities',
                'Real Estate', 'Materials'.

    Returns all companies in that sector with their full financial attributes,
    including ticker, industry, description, beta, market cap, revenue, and
    supply chain sensitivity.
    """
    # Case-insensitive match
    matched_sector = None
    for s in _BY_SECTOR:
        if s.lower() == sector.lower():
            matched_sector = s
            break

    if matched_sector is None:
        return {
            "error": f"Sector '{sector}' not found.",
            "available_sectors": list(_BY_SECTOR.keys()),
        }

    companies = _BY_SECTOR[matched_sector]
    industries = {}
    for c in companies:
        industries.setdefault(c["industry"], 0)
        industries[c["industry"]] += 1

    return {
        "sector": matched_sector,
        "total_companies": len(companies),
        "total_sector_investment_usd": len(companies) * 1_000_000,
        "industry_breakdown": industries,
        "companies": companies,
    }


# ---------------------------------------------------------------------------
# Tool 3 — Get a specific company by ticker
# ---------------------------------------------------------------------------

@mcp.tool(annotations={"readOnlyHint": True, "idempotentHint": True})
def get_company_details(ticker: str) -> dict:
    """
    Retrieve full details for a specific company by its ticker symbol.

    Args:
        ticker: The company's ticker symbol (e.g. 'AAPL', 'NVDA'). Case-insensitive.
                Note: tickers in this portfolio are synthetic 3-4 letter codes.

    Returns full company profile including sector, industry, financial attributes,
    supply chain sensitivity, and investment details.
    """
    company = _BY_TICKER.get(ticker.upper())
    if company is None:
        return {
            "error": f"Ticker '{ticker}' not found in portfolio.",
            "note": "Portfolio contains 500 synthetic companies with randomly generated tickers.",
        }
    return company


# ---------------------------------------------------------------------------
# Tool 4 — Search companies by criteria
# ---------------------------------------------------------------------------

@mcp.tool(annotations={"readOnlyHint": True, "idempotentHint": True})
def search_companies_by_criteria(
    sector: Optional[str] = None,
    industry: Optional[str] = None,
    supply_chain_sensitivity: Optional[str] = None,
    min_beta: Optional[float] = None,
    max_beta: Optional[float] = None,
    min_market_cap_b: Optional[float] = None,
    limit: int = 50,
) -> dict:
    """
    Search portfolio companies using one or more filter criteria.

    Args:
        sector: Filter by GICS sector name (partial match, case-insensitive).
        industry: Filter by industry name (partial match, case-insensitive).
        supply_chain_sensitivity: Filter by supply chain sensitivity: 'HIGH', 'MEDIUM', or 'LOW'.
        min_beta: Minimum beta value (e.g. 1.5 for high market-sensitivity companies).
        max_beta: Maximum beta value.
        min_market_cap_b: Minimum market cap in USD billions.
        limit: Maximum number of results to return (default 50, max 200).

    Returns matching companies sorted by market cap descending.
    Use this to find companies fitting specific risk profiles for analysis.
    """
    limit = min(limit, 200)
    results = _PORTFOLIO[:]

    if sector:
        results = [c for c in results if sector.lower() in c["sector"].lower()]
    if industry:
        results = [c for c in results if industry.lower() in c["industry"].lower()]
    if supply_chain_sensitivity:
        sc = supply_chain_sensitivity.upper()
        results = [c for c in results if c["supply_chain_sensitivity"] == sc]
    if min_beta is not None:
        results = [c for c in results if c["beta"] >= min_beta]
    if max_beta is not None:
        results = [c for c in results if c["beta"] <= max_beta]
    if min_market_cap_b is not None:
        results = [c for c in results if c["market_cap_b"] >= min_market_cap_b]

    results.sort(key=lambda x: x["market_cap_b"], reverse=True)
    results = results[:limit]

    return {
        "total_matches": len(results),
        "filters_applied": {
            "sector": sector,
            "industry": industry,
            "supply_chain_sensitivity": supply_chain_sensitivity,
            "min_beta": min_beta,
            "max_beta": max_beta,
            "min_market_cap_b": min_market_cap_b,
        },
        "companies": results,
    }


# ---------------------------------------------------------------------------
# Tool 5 — List all sectors and industries
# ---------------------------------------------------------------------------

@mcp.tool(annotations={"readOnlyHint": True, "idempotentHint": True})
def list_sectors_and_industries() -> dict:
    """
    List all sectors and their industries in the synthetic portfolio.

    Returns a complete taxonomy of sectors and industries available in the
    portfolio. Use this to understand the data structure before querying
    specific sectors or industries.
    """
    taxonomy = {}
    for sector, companies in _BY_SECTOR.items():
        industries = sorted(set(c["industry"] for c in companies))
        taxonomy[sector] = {
            "company_count": len(companies),
            "industries": industries,
        }
    return {
        "total_sectors": len(taxonomy),
        "total_companies": len(_PORTFOLIO),
        "sectors": taxonomy,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("S&P 500 Portfolio Risk MCP Server")
    print("Synthetic S&P 500-like Portfolio — Demo Data Only")
    print("=" * 70)
    print(f"Portfolio: {len(_PORTFOLIO)} companies, ${len(_PORTFOLIO):,}M total investment")
    print(f"Sectors: {len(_BY_SECTOR)}")
    print(f"CSV export: {_CSV_PATH}")
    print()
    print("Available tools:")
    print("  1. get_portfolio_summary()         — Portfolio-level overview")
    print("  2. get_sector_holdings(sector)     — All companies in a sector")
    print("  3. get_company_details(ticker)     — Single company details")
    print("  4. search_companies_by_criteria()  — Filter by sector/industry/beta/etc.")
    print("  5. list_sectors_and_industries()   — Full taxonomy")
    print("=" * 70)
    print("Starting server on http://127.0.0.1:8001")
    print("=" * 70)
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8001)
