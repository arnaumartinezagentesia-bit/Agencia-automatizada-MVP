# Agencia Automatizada MVP — Scope Specification

**Status:** Proposed for MVP-0
**Product:** Agencia Automatizada
**Department:** Trading
**Initial instrument:** XAU/USD
**Primary user:** Project owner
**Repository:** Agencia-automatizada-MVP

---

## 1. Product vision

Agencia Automatizada is a multi-agent AI platform organized around autonomous business departments.

The first department is **Trading**.

The long-term Trading vision is a controlled team of specialized agents capable of:

* market intelligence;
* strategy generation;
* deterministic backtesting;
* risk evaluation;
* paper trading;
* decision journaling;
* curated memory;
* multi-agent orchestration.

The platform must be designed so that future departments can reuse its technical foundations.

The system must never confuse an LLM-generated analysis with deterministic financial truth.

---

## 2. MVP strategy

The product will not be built as one large system.

Development will proceed through small, independently verifiable vertical slices.

The first slice is called **MVP-0**.

MVP-0 must prove that one user can interact with one department, one agent and one business capability from the frontend through the backend to a persistent result.

### MVP-0 vertical slice

```text
Trading Desk
    │
    └── Market Intelligence Agent
            │
            └── Analyze XAU/USD
                    │
                    ├── obtain market snapshot
                    ├── validate input
                    ├── analyze market context
                    ├── produce structured result
                    ├── persist result
                    └── display result in frontend
```

The objective is to validate the complete product loop, not to build the final trading system.

---

## 3. MVP-0 business capability

### Capability

**Analyze XAU/USD market conditions.**

The user selects or requests an analysis of XAU/USD.

The system obtains a market snapshot and asks the Market Intelligence Agent to produce a structured analytical report.

The result must be traceable to the input data used.

### MVP-0 analysis areas

The agent may describe:

* current market context;
* observed trend structure;
* volatility context;
* relevant price levels;
* notable market characteristics;
* supporting observations;
* uncertainties and limitations;
* data provenance.

The agent must not produce:

* BUY orders;
* SELL orders;
* broker instructions;
* trade execution;
* autonomous position management;
* claims of guaranteed profitability.

The first version is an **analysis product**, not a trading execution product.

---

## 4. Data strategy

MVP-0 will support two data modes behind the same interface.

### 4.1 Deterministic fixture data

Used for:

* automated tests;
* development without external APIs;
* reproducible demonstrations;
* failure testing.

The fixture must be explicitly identifiable as test data.

The frontend must never present fixture data as live market data.

### 4.2 Live market data provider

A real market-data provider will be integrated behind the same abstraction.

The concrete provider will be selected during implementation after confirming:

* XAU/USD support;
* available historical/intraday data;
* free-tier limits;
* licensing/usage restrictions;
* reliability;
* authentication mechanism.

The provider must be replaceable without changing the agent contract.

### 4.3 Provider abstraction

Conceptually:

```text
MarketDataProvider
    ├── FixtureMarketDataProvider
    └── LiveMarketDataProvider
```

The agent must depend on the interface, not on a concrete provider.

---

## 5. LLM strategy

MVP-0 uses an LLM for interpretation and natural-language analysis.

The LLM must not be responsible for:

* validating critical system state;
* financial calculations;
* persistence;
* authentication;
* authorization;
* execution;
* risk enforcement.

### LLM abstraction

```text
LLMProvider
    ├── OpenRouterProvider
    └── future providers
```

The provider must be replaceable.

Automated tests must not depend on live LLM availability.

A deterministic fake/stub provider will therefore be available for testing.

---

## 6. Agent definition

### Agent

**Market Intelligence Agent**

### Initial identifier

`trading_market_intelligence_agent`

### Purpose

Transform validated market information into a structured analytical report.

### Inputs

The agent receives:

* instrument;
* analysis timestamp;
* timeframe;
* validated market snapshot;
* data provenance;
* model configuration when applicable.

### Outputs

The agent returns a validated `MarketAnalysis` object.

The agent is not allowed to return arbitrary operational JSON as its canonical output.

### Initial conceptual contract

```text
MarketAnalysis
├── schema_version
├── analysis_id
├── timestamp_utc
├── symbol
├── timeframe
├── market_snapshot
├── trend_context
├── volatility_context
├── key_levels
├── market_observations
├── uncertainties
├── data_sources
└── model_metadata
```

The exact Pydantic fields will be finalized in `DATA_CONTRACTS.md`.

---

## 7. Persistence

PostgreSQL is the operational source of truth from MVP-0 onward.

MVP-0 must persist, at minimum:

* analysis request;
* analysis status;
* market snapshot reference/data;
* final structured analysis;
* timestamps;
* provider metadata;
* model metadata;
* error state when execution fails.

The system must distinguish clearly between:

```text
pending
running
completed
failed
```

A failed analysis must never be persisted or displayed as a successful analysis.

---

## 8. Backend responsibilities

The backend is authoritative.

The backend must:

1. accept analysis requests;
2. validate requests;
3. retrieve market data;
4. invoke the Market Intelligence Agent;
5. validate the agent output;
6. persist the result;
7. expose the result through the API;
8. emit minimal real-time status events;
9. report failures explicitly.

The frontend must never fabricate:

* agent state;
* analysis results;
* market data;
* timestamps;
* successful execution status.

---

## 9. API scope

MVP-0 requires a minimal HTTP API.

Conceptually:

```text
POST /api/market-analysis
GET  /api/market-analysis/{analysis_id}
GET  /api/market-analysis
```

The exact route names may be adjusted during architecture work.

The API must return structured error responses.

A successful HTTP response must only be returned when the backend has actually completed the requested operation.

---

## 10. Real-time events

MVP-0 uses a deliberately small WebSocket protocol.

Required events:

```text
analysis.started
analysis.completed
analysis.failed
```

The purpose is to demonstrate that frontend activity is driven by real backend execution.

No general-purpose event bus or complex distributed orchestration is required yet.

Redis is therefore excluded from MVP-0.

---

## 11. Frontend scope

The frontend represents one Trading department.

It contains:

### Trading Desk

A visual Pixel Art environment representing the Trading department.

It does not need to simulate an entire company.

### Market Intelligence Agent

Exactly one active agent is required for MVP-0.

The user can interact with the agent.

### Analysis panel

A professional information panel displays:

* instrument;
* timestamp;
* analysis status;
* market context;
* observations;
* key levels;
* uncertainties;
* data source;
* model metadata.

### Primary action

The main user action is:

**Analyze XAU/USD**

The UI must clearly indicate whether the displayed data is:

* fixture/test data;
* live data;
* unavailable.

---

## 12. Visual architecture

The visual layer is divided into two responsibilities.

### Pixel Art / Phaser

Responsible for:

* Trading Desk environment;
* agent representation;
* simple agent state animation;
* interaction point;
* visual status.

### Conventional React UI

Responsible for:

* analysis panels;
* controls;
* status;
* history;
* errors;
* structured information.

The Pixel Art environment is not the source of truth for application state.

It is a visual representation of backend state.

---

## 13. Reuse from the legacy repository

The old repository may be mined selectively.

### Candidates for reuse or adaptation

* Phaser initialization concept;
* Pixel Art rendering configuration;
* Trading office visual concept;
* `GameContainer` approach;
* `OfficeScene` design concepts;
* `AgentEntity` visual concepts;
* office assets located under the previous frontend asset tree;
* general UI composition ideas.

### Components explicitly not reused as business logic

* mock market-data service;
* simulated agent-state loop;
* mock backtesting engine;
* heuristic Director;
* hardcoded trading verdicts;
* hardcoded market claims;
* fabricated performance metrics;
* legacy persistence/state shortcuts.

Any reused code must be reviewed and adapted to the new architecture.

No large directory copy from the old repository is permitted.

---

## 14. Architecture constraints for MVP-0

### Required

* Type-safe backend contracts;
* FastAPI;
* PostgreSQL;
* React/Next.js;
* Phaser for the visual environment;
* structured validation;
* deterministic tests;
* provider abstractions;
* explicit error states;
* Git-based feature development.

### Deliberately postponed

* Redis;
* LangGraph;
* Obsidian;
* multi-agent orchestration;
* Director;
* Strategy Agent;
* Backtesting Engine;
* Risk Engine;
* paper trading;
* broker integrations;
* Telegram;
* multi-user support;
* authentication system beyond what is strictly necessary for local MVP development;
* background worker infrastructure;
* production-scale observability.

These are not rejected permanently. They are intentionally deferred until they solve a demonstrated product need.

---

## 15. Financial safety boundaries

MVP-0 is an analytical system.

It must not:

* connect to a real broker;
* submit orders;
* manage real positions;
* store broker credentials;
* claim financial profitability;
* label a generated hypothesis as a validated trading strategy;
* treat LLM output as deterministic financial truth.

The architecture must make these future capabilities difficult to enable accidentally.

---

## 16. Error philosophy

The system must prefer an explicit failure over a convincing fake.

Examples:

```text
Market data unavailable
LLM unavailable
Invalid agent output
Database unavailable
Analysis timeout
Provider authentication failure
```

These errors must be represented as actual failures.

The frontend must never convert them into:

```text
Analysis completed
```

---

## 17. History

MVP-0 includes minimal analysis history.

The user must be able to see previously completed analyses and distinguish them by:

* analysis ID;
* timestamp;
* symbol;
* timeframe;
* status.

A historical result must be loaded from the backend/database rather than reconstructed from frontend memory.

---

## 18. Testing requirements

MVP-0 is complete only when automated tests cover at least:

### Contract tests

Valid and invalid `MarketAnalysis` structures.

### Service tests

Market-data provider success and failure.

### Agent tests

Valid agent output and malformed output handling.

### API tests

Successful analysis request.

Failed analysis request.

Historical analysis retrieval.

### Persistence tests

Successful persistence.

Failure persistence/state.

### Frontend integration

The main analysis flow must be testable without requiring a real LLM.

---

## 19. Definition of Done

MVP-0 is complete when all of the following are true:

* [ ] The application starts locally.
* [ ] PostgreSQL is available locally.
* [ ] The Trading Desk is visible.
* [ ] The Market Intelligence Agent is visible/interactable.
* [ ] The user can request XAU/USD analysis.
* [ ] A deterministic fixture can execute the complete flow.
* [ ] A real provider can be integrated without changing the agent contract.
* [ ] The backend validates the request.
* [ ] The agent output is schema validated.
* [ ] The result is persisted.
* [ ] The frontend receives real execution events.
* [ ] Analysis history is available.
* [ ] Failures are explicitly represented.
* [ ] No fake market data is presented as live data.
* [ ] No trading execution capability exists.
* [ ] Tests pass.
* [ ] No secrets are committed.
* [ ] The implementation is reviewed before merging to `main`.

---

## 20. MVP-0 success criterion

The first real milestone is not:

> "We have an AI trading company."

It is:

> "A user can enter the Trading Desk, activate the Market Intelligence Agent, request an XAU/USD analysis, observe the real execution lifecycle, receive a validated structured result, and later retrieve that same result from persistent storage."

Once this works reliably, the architecture has earned the right to grow.

---

## 21. Roadmap after MVP-0

```text
MVP-0
Market Intelligence
        │
        ▼
MVP-1
Strategy Agent
        │
        ▼
MVP-2
Deterministic Backtesting
        │
        ▼
MVP-2.5
Deterministic Risk Engine
        │
        ▼
MVP-3
Director + Multi-Agent Committee
        │
        ▼
MVP-4
Paper Trading
        │
        ▼
MVP-5
Curated Memory / Obsidian
        │
        ▼
MVP-6
Advanced Observability
        │
        ▼
Future
Additional departments
```

The architecture must evolve only when a new capability requires it.

---

## 22. Source of truth

For the new repository:

```text
MVP_SCOPE.md
    ↓
ARCHITECTURE.md
    ↓
DATA_CONTRACTS.md
    ↓
AGENT_SPEC.md
    ↓
UI_SPEC.md
    ↓
MASTER_DEVELOPMENT_PROMPT.md
    ↓
implementation
```

Conflicts must be resolved against the newest approved architectural decision.

The legacy repository is not a source of truth for the new implementation.
