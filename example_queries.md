# Example User Queries — S&P 500 Research Workflow

```bash
python portfolio_risk_workflow.py --query "<your question here>"
```

**Dataset:** 505 actual S&P 500 companies · 11 GICS sectors · January 2017 – December 2021

---

## What each run produces

For every query the workflow runs 5 agents and outputs two files:

| File | Contents |
|---|---|
| `output/sp500_analysis_<id>.json` | Full checkpoint with all agent outputs |
| `output/sp500_analysis_<id>.pptx` | PowerPoint deck with exec summary, comparison tables, narrative slides, and sources |

**Agent 2** computes real numbers from the CSV files: cumulative returns, annual returns year-by-year, max drawdown, Sharpe ratio, annualised volatility, correlations.

**Agent 4** searches the web via Tavily (one search per query, loops through all queries from Agent 3) and returns sourced evidence with URLs — requires `TAVILY_API_KEY` in your `.env`.

---

## Intent types Agent 1 recognises

Phrase your query naturally — Agent 1 will classify the intent automatically:

| Intent | Example phrasing |
|---|---|
| `single_stock_deep_dive` | "Analyze Apple from 2017 to 2021" |
| `sector_comparison` | "Compare IT versus Energy" |
| `ranking` | "Rank all sectors by Sharpe ratio" |
| `risk_analysis` | "Which stocks had the worst drawdown in 2020?" |
| `correlation_study` | "How correlated were the 11 sectors?" |
| `general` | Broad exploratory questions |

---

## Apple

```bash
python portfolio_risk_workflow.py --query "Give me a full analysis of Apple from 2017 to 2021 — cumulative return, annual performance, max drawdown, Sharpe ratio, and how it compared to the rest of the Information Technology sector."
```
> AAPL went from ~$40 to ~$180 over this period. Agent 2 will compute exact annual returns, drawdown, and Sharpe from the CSV data.

```bash
python portfolio_risk_workflow.py --query "How did Apple perform year by year from 2017 to 2021? Which year was its best and worst, and how deep was its drawdown during the March 2020 COVID crash?"
```

```bash
python portfolio_risk_workflow.py --query "How did Apple compare to the FAANG group — Facebook, Alphabet, Amazon, and Netflix — from 2017 to 2021? Rank by total return, Sharpe ratio, and max drawdown."
```

---

## Microsoft

```bash
python portfolio_risk_workflow.py --query "Analyze Microsoft's performance from 2017 to 2021 — total return, annual breakdown, max drawdown, Sharpe ratio, and how it ranked among Information Technology peers."
```
> MSFT compounded steadily across all 5 years with relatively low volatility — one of the best risk-adjusted stories in the dataset.

```bash
python portfolio_risk_workflow.py --query "Compare Microsoft against enterprise software peers — Salesforce, Adobe, ServiceNow, and Oracle — from 2017 to 2021. Who had the best total return and who had the best Sharpe ratio?"
```

```bash
python portfolio_risk_workflow.py --query "Compare Apple and Microsoft from 2017 to 2021 — total return, Sharpe ratio, annualised volatility, and max drawdown. Which was the better risk-adjusted investment?"
```

---

## Big Banks

```bash
python portfolio_risk_workflow.py --query "Rank JPMorgan, Bank of America, Wells Fargo, Citigroup, Goldman Sachs, and Morgan Stanley by total return from 2017 to 2021. Which big bank was the best investment and which was the worst?"
```
> WFC was under a Fed asset cap from 2018 — the return gap versus JPM and MS is clearly visible in the data.

```bash
python portfolio_risk_workflow.py --query "Analyze JPMorgan Chase from 2017 to 2021 — total return, annual performance, max drawdown in 2020, and how it compared to the Financials sector average."
```

```bash
python portfolio_risk_workflow.py --query "Compare Goldman Sachs and Morgan Stanley against regional banks — Charles Schwab, PNC, U.S. Bancorp, and Truist — from 2017 to 2021. Did Wall Street banks or regional banks deliver better returns?"
```

```bash
python portfolio_risk_workflow.py --query "Analyze Berkshire Hathaway (BRK-B) versus JPMorgan and Goldman Sachs from 2017 to 2021 — total return, Sharpe ratio, and drawdown comparison."
```

```bash
python portfolio_risk_workflow.py --query "Compare Visa and Mastercard against the big banks JPMorgan and Goldman Sachs from 2017 to 2021. Which sub-sector of Financials had the best risk-adjusted returns?"
```

---

## Bank vs Tech

```bash
python portfolio_risk_workflow.py --query "Which was the better investment from 2017 to 2021 — Apple or JPMorgan? Compare total return, Sharpe ratio, max drawdown, and year-by-year performance."
```

```bash
python portfolio_risk_workflow.py --query "Compare Microsoft against the entire Financials sector average from 2017 to 2021 on total return, Sharpe ratio, and max drawdown."
```

```bash
python portfolio_risk_workflow.py --query "Compare the Information Technology sector versus the Financials sector from 2017 to 2021 — cumulative return, annual returns, Sharpe ratio, and max drawdown."
```

---

## Semiconductors

```bash
python portfolio_risk_workflow.py --query "Compare NVIDIA, AMD, and Intel from 2017 to 2021 — total return, annual breakdown, Sharpe ratio, and max drawdown. Who won the semiconductor race?"
```
> NVDA ~+900%, AMD ~+1200%, INTC nearly flat. One of the sharpest divergences in the dataset.

```bash
python portfolio_risk_workflow.py --query "How did semiconductor equipment companies — Lam Research, Applied Materials, and KLA Corporation — perform versus the broader Information Technology sector from 2017 to 2021?"
```

```bash
python portfolio_risk_workflow.py --query "Rank the top 10 best-performing Information Technology stocks from 2017 to 2021 by total return. Include their Sharpe ratios and max drawdowns."
```

---

## COVID Crash — Winners and Losers

```bash
python portfolio_risk_workflow.py --query "How badly were the airlines — Delta, United, American Airlines, and Southwest — hit in the 2020 COVID crash? Compute max drawdown, 2020 annual return, and recovery by end of 2021."
```
> DAL, UAL, AAL, LUV all in the dataset. Max drawdowns were -60% to -70% in Q1 2020.

```bash
python portfolio_risk_workflow.py --query "Compare the COVID crash and recovery for Carnival, Royal Caribbean, and Norwegian Cruise Line from 2017 to 2021. Rank by max drawdown and 2021 recovery return."
```

```bash
python portfolio_risk_workflow.py --query "Which Consumer Staples stocks — Walmart, Costco, Procter and Gamble, and Clorox — were most resilient during the March 2020 crash? Compare their 2020 drawdowns and annual returns."
```
> CLX surged on cleaning product demand and had one of the mildest drawdowns in the entire dataset.

```bash
python portfolio_risk_workflow.py --query "Compare the 2020 COVID drawdown and recovery speed across all 11 S&P 500 sectors. Which sectors recovered to new highs fastest?"
```

---

## Big Tech

```bash
python portfolio_risk_workflow.py --query "Rank Apple, Microsoft, Alphabet, Facebook, and Amazon by Sharpe ratio from 2017 to 2021. Which delivered the best return per unit of risk?"
```

```bash
python portfolio_risk_workflow.py --query "Compare cloud and SaaS stocks — Salesforce, Adobe, ServiceNow, and Intuit — against legacy IT names like IBM, HP, and Hewlett Packard Enterprise from 2017 to 2021."
```
> Cloud vs legacy is one of the starkest performance gaps in the dataset.

```bash
python portfolio_risk_workflow.py --query "How much did Tesla distort the Consumer Discretionary sector returns from 2017 to 2021? Compare Tesla's individual return and volatility against the sector average excluding Tesla."
```
> TSLA's surge in 2020–2021 heavily influenced the sector average — worth quantifying explicitly.

---

## Healthcare

```bash
python portfolio_risk_workflow.py --query "Compare Moderna, Pfizer, and Johnson and Johnson from 2017 to 2021 — total return, annual breakdown, and max drawdown. When did Moderna's breakout begin?"
```
> MRNA is in the dataset — it went from ~$20 to over $400. The annual return data will show exactly when.

```bash
python portfolio_risk_workflow.py --query "Compare managed care companies — UnitedHealth, Anthem, Cigna, and Humana — against pharmaceutical companies — AbbVie, Eli Lilly, and Merck — from 2017 to 2021 on Sharpe ratio and total return."
```

```bash
python portfolio_risk_workflow.py --query "How did medical device and diagnostics companies — Thermo Fisher, Danaher, Intuitive Surgical, and DexCom — perform versus the Health Care sector average from 2017 to 2021?"
```

---

## Energy

```bash
python portfolio_risk_workflow.py --query "Analyze the Energy sector from 2017 to 2021 — annual returns year by year, max drawdown, Sharpe ratio, and which individual companies had the worst and best performance."
```

```bash
python portfolio_risk_workflow.py --query "Compare Exxon, Chevron, and ConocoPhillips against oilfield services companies Schlumberger, Halliburton, and Baker Hughes from 2017 to 2021. Which group held up better?"
```

```bash
python portfolio_risk_workflow.py --query "How did Occidental Petroleum compare to Exxon and Chevron from 2017 to 2021? Compute total return, max drawdown, and year-by-year annual returns."
```
> OXY had one of the worst drawdowns in the entire S&P 500 in 2020 — the data makes this vivid.

---

## Real Estate

```bash
python portfolio_risk_workflow.py --query "Compare digital infrastructure REITs — American Tower, Crown Castle, Equinix, and Digital Realty — against traditional retail REITs like Simon Property Group from 2017 to 2021 on total return and Sharpe ratio."
```
> Tower/data center REITs versus mall REITs — one of the clearest structural divergences in the dataset.

```bash
python portfolio_risk_workflow.py --query "Rank all Real Estate sector stocks by total return from 2017 to 2021. Which sub-types performed best — towers, data centers, industrial, residential, or retail?"
```

---

## Industrials & Aerospace

```bash
python portfolio_risk_workflow.py --query "Compare Boeing and Lockheed Martin from 2017 to 2021 — total return, annual performance, and max drawdown. How did Boeing's 737 MAX crisis in 2019 and COVID in 2020 show up in the data?"
```
> BA had two consecutive disasters — the year-by-year breakdown makes the double hit clear.

```bash
python portfolio_risk_workflow.py --query "How did UPS, FedEx, and Old Dominion Freight perform versus the broader Industrials sector from 2017 to 2021? Did the COVID e-commerce surge show up in their returns?"
```

---

## Materials

```bash
python portfolio_risk_workflow.py --query "Compare Newmont, Freeport-McMoRan, and Nucor from 2017 to 2021 — total return, annual breakdown, and max drawdown. Which benefited most from commodity price cycles?"
```

```bash
python portfolio_risk_workflow.py --query "How did Albemarle perform from 2017 to 2021 versus the broader Materials sector? Compute annual returns and identify when EV-driven lithium demand started showing up in the stock."
```
> ALB surged in 2021 — the annual return data will show the inflection point.

---

## Communication Services

```bash
python portfolio_risk_workflow.py --query "Compare Netflix and Disney from 2017 to 2021 — total return, annual performance, max drawdown, and Sharpe ratio. Did Disney's streaming launch in 2019 close the gap with Netflix?"
```

```bash
python portfolio_risk_workflow.py --query "How did gaming stocks — Activision Blizzard, Electronic Arts, and Take-Two Interactive — perform from 2017 to 2021? Compute their returns during 2020 specifically to see the COVID lockdown effect."
```

---

## Sector Rankings & Correlations

```bash
python portfolio_risk_workflow.py --query "Rank all 11 S&P 500 sectors by Sharpe ratio from 2017 to 2021. Include total return, annualised volatility, and max drawdown for each."
```

```bash
python portfolio_risk_workflow.py --query "Compute the pairwise correlation matrix of all 11 S&P 500 sector returns from 2017 to 2021. Which sector pairs were most and least correlated?"
```

```bash
python portfolio_risk_workflow.py --query "How did defensive sectors — Utilities, Consumer Staples, and Health Care — perform versus cyclicals — Energy, Financials, and Industrials — from 2017 to 2021 on return, volatility, and drawdown?"
```

---

## Consumer Discretionary

```bash
python portfolio_risk_workflow.py --query "Compare Amazon, Home Depot, Target, and TJX from 2017 to 2021 — total return, Sharpe ratio, and max drawdown. Did traditional retailers keep up with Amazon?"
```

```bash
python portfolio_risk_workflow.py --query "How did homebuilders — D.R. Horton, Lennar, NVR, and PulteGroup — perform from 2017 to 2021? Compute annual returns to see when the housing boom showed up."
```

```bash
python portfolio_risk_workflow.py --query "Compare Nike, Under Armour, Gap, and Ralph Lauren from 2017 to 2021 on total return and max drawdown. Which apparel brand was the best and worst investment?"
```
> Nike surged while Gap and Under Armour lagged — the return gap is large and the data tells the story clearly.

---

## Reset & Resume

```bash
# Delete checkpoint and start over
python portfolio_risk_workflow.py --query "Compare NVIDIA, AMD, and Intel from 2017 to 2021?" --reset

# Resume automatically — re-running the same query finds the latest checkpoint
python portfolio_risk_workflow.py --query "Compare NVIDIA, AMD, and Intel from 2017 to 2021?"

# Resume a specific run by ID (printed at the start of every run)
python portfolio_risk_workflow.py --run-id 20260427_143022

# Delete a specific run by ID and restart
python portfolio_risk_workflow.py --run-id 20260427_143022 --reset
```
