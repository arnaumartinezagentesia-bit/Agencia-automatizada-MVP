# Agencia Automatizada — MVP-0

**Project:** Agencia Automatizada
**Department:** Trading
**Initial Capability:** XAU/USD Market Analysis
**MVP Slice:** Market Intelligence Agent → Analyze XAU/USD

---

## Purpose

MVP-0 establishes the minimum viable vertical slice for the Trading department: a user can interact with the Market Intelligence Agent to request a structured qualitative analysis of XAU/USD market conditions. The analysis is obtained through a market-data provider, processed by an LLM, validated, persisted, and displayed in the frontend.

**This is an analysis product, not a trading execution system.**
The agent produces qualitative market interpretation (trend context, volatility regime, key levels, observations, uncertainties). It does **not** generate BUY/SELL orders, execute trades, manage positions, or make financial recommendations.

---

## Current Implementation Status

**Repository foundation / specification approved**
No application code has been implemented yet. The repository contains only the canonical specification documents in `docs/` and this foundation.

---

## Specification Documents (Source of Truth)

All implementation must follow the approved specifications in `docs/`:

- [`MVP_SCOPE.md`](docs/MVP_SCOPE.md) — Product scope, MVP strategy, business capability, data strategy
- [`ARCHITECTURE.md`](docs/ARCHITECTURE.md) — Technical architecture, layers, interfaces, runtime flows
- [`DATA_CONTRACTS.md`](docs/DATA_CONTRACTS.md) — Canonical data schemas, request/response, persistence, WebSocket events
- [`AGENT_SPEC.md`](docs/AGENT_SPEC.md) — Market Intelligence Agent behavior, input/output contracts, boundaries
- [`UI_SPEC.md`](docs/UI_SPEC.md) — Frontend UX, visual responsibilities, interaction behavior, states
- [`MASTER_DEVELOPMENT_PROMPT.md`](docs/MASTER_DEVELOPMENT_PROMPT.md) — Controlled implementation protocol, phase gates, verification

**The legacy repository is not the source of truth for this implementation.**

---

## Technology Stack (Planned)

| Layer | Technology |
|-------|------------|
| Backend | FastAPI (Python) |
| Validation | Pydantic |
| Persistence | PostgreSQL + SQLAlchemy + Alembic |
| Frontend | Next.js + React |
| Visual Layer | Phaser |
| Realtime | FastAPI WebSocket |
| Market Data | Provider abstraction (fixture → live) |
| LLM | Provider abstraction (OpenRouter gateway) |
| Tests | Pytest + frontend test framework |

---

## Repository Foundation

This phase establishes only:
- `.gitignore` — repository-level ignore rules for Python, Node, IDE, OS artifacts
- `.env.example` — safe environment variable template (no real credentials)
- `README.md` — this file

No backend, frontend, database, provider, agent, API, or WebSocket code exists yet.
