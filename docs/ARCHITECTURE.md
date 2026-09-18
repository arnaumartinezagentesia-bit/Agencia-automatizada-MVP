# Agencia Automatizada MVP — Architecture Specification

**Status:** Proposed for MVP-0
**Product:** Agencia Automatizada
**Department:** Trading
**Initial capability:** XAU/USD Market Analysis
**Primary user:** Project owner
**Repository:** `Agencia-automatizada-MVP`

---

## 1. Purpose

This document defines the technical architecture for MVP-0.

It translates the product scope defined in `docs/MVP_SCOPE.md` into concrete architectural responsibilities, boundaries, dependencies, runtime flows, data ownership and integration points.

This document is a foundation for implementation.

It does not define every field of every model. Detailed contracts belong in `DATA_CONTRACTS.md`.

It does not define every agent instruction. Agent behavior belongs in `AGENT_SPEC.md`.

It does not define detailed visual design. Frontend and interaction details belong in `UI_SPEC.md`.

---

## 2. Architectural objective

MVP-0 must prove one complete vertical slice:

```text
User
  ↓
Trading Desk
  ↓
Market Intelligence Agent
  ↓
Market Data Provider
  ↓
Structured Market Snapshot
  ↓
LLM reasoning
  ↓
Validated MarketAnalysis
  ↓
PostgreSQL
  ↓
API + WebSocket
  ↓
Frontend
```

The architecture must make this flow:

* understandable;
* testable;
* observable;
* replaceable at integration boundaries;
* resistant to fabricated results;
* extensible for future Trading agents.

The architecture must avoid premature distributed systems.

---

## 3. Core architectural principles

### 3.1 Backend is authoritative

The backend is the source of truth for:

* analysis state;
* market data used for an analysis;
* analysis results;
* timestamps;
* execution status;
* provider metadata;
* errors.

The frontend is never authoritative.

---

### 3.2 LLMs reason; deterministic code controls the system

LLMs may:

* interpret market information;
* summarize observations;
* organize qualitative reasoning;
* generate structured analysis.

LLMs may not:

* decide whether an operation was successfully persisted;
* invent market data;
* bypass validation;
* modify system state directly;
* execute trades;
* enforce financial risk controls;
* fabricate provider metadata;
* declare a failed process successful.

---

### 3.3 Explicit failures are preferable to fake success

Every important external dependency must expose failure explicitly.

Examples:

```text
market_data_unavailable
llm_unavailable
llm_invalid_output
database_unavailable
provider_timeout
provider_authentication_failed
analysis_timeout
```

No fallback may silently replace a real failure with fictional data.

---

### 3.4 Smallest useful architecture

MVP-0 intentionally excludes infrastructure that is not necessary yet.

Not required:

* Redis;
* LangGraph;
* Obsidian;
* message broker;
* distributed workers;
* microservices;
* Kubernetes;
* production authentication platform;
* multi-user tenancy.

These may be introduced later without changing the core domain boundaries.

---

### 3.5 Replaceable external providers

External systems must be accessed through application interfaces.

The application must not couple domain logic directly to:

* OpenRouter;
* a specific market-data vendor;
* a specific database client;
* browser APIs;
* Phaser internals.

---

### 3.6 No hidden business logic in the frontend

React and Phaser render state and capture user interactions.

They do not contain authoritative business rules.

---

## 4. Runtime architecture

MVP-0 is a modular monolith.

```text
                         ┌─────────────────────┐
                         │       Browser       │
                         │                     │
                         │ React / Next.js     │
                         │ Phaser              │
                         └──────────┬──────────┘
                                    │
                         HTTP / WebSocket
                                    │
                                    ▼
                    ┌────────────────────────────┐
                    │      FastAPI Backend       │
                    │                            │
                    │ API                        │
                    │ Application services       │
                    │ Agent                      │
                    │ Provider adapters           │
                    │ Persistence                 │
                    └───────┬───────────┬────────┘
                            │           │
                            │           │
                            ▼           ▼
                    ┌────────────┐   ┌──────────────┐
                    │ PostgreSQL │   │ External APIs│
                    │            │   │              │
                    │ persistent │   │ Market data  │
                    │ truth      │   │ OpenRouter   │
                    └────────────┘   └──────────────┘
```

The backend is a single deployable application in MVP-0.

---

## 5. Repository architecture

The new repository must not reproduce the structure of the legacy repository.

Recommended structure:

```text
Agencia-automatizada-MVP/
│
├── docs/
│   ├── MVP_SCOPE.md
│   ├── ARCHITECTURE.md
│   ├── DATA_CONTRACTS.md
│   ├── AGENT_SPEC.md
│   ├── UI_SPEC.md
│   └── MASTER_DEVELOPMENT_PROMPT.md
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── agents/
│   │   ├── application/
│   │   ├── core/
│   │   ├── domain/
│   │   ├── persistence/
│   │   ├── providers/
│   │   ├── realtime/
│   │   └── main.py
│   │
│   └── tests/
│       ├── unit/
│       └── integration/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── game/
│   ├── lib/
│   ├── public/
│   └── tests/
│
├── infra/
│   └── docker/
│
├── scripts/
│
├── .env.example
├── .gitignore
├── README.md
└── docker-compose.yml
```

The final exact paths may be adjusted during implementation, but responsibilities must remain separated.

---

## 6. Backend layers

The backend should be organized by responsibility.

### 6.1 `api/`

Contains:

* HTTP route definitions;
* request/response handling;
* WebSocket entrypoints;
* translation between HTTP and application services.

API routes must remain thin.

Business logic must not be implemented directly inside route handlers.

---

### 6.2 `application/`

Contains application use cases.

Example:

```text
CreateMarketAnalysis
GetMarketAnalysis
ListMarketAnalyses
```

Application services coordinate domain objects, providers and persistence.

They represent actions the product can perform.

---

### 6.3 `domain/`

Contains business concepts independent from infrastructure.

Examples:

```text
MarketSnapshot
MarketAnalysis
AnalysisStatus
AnalysisRequest
ProviderMetadata
AnalysisError
```

Domain models must not import FastAPI, Phaser, OpenRouter clients or database-specific code.

---

### 6.4 `agents/`

Contains the agent implementation.

MVP-0 contains only:

```text
Market Intelligence Agent
```

The agent receives validated domain data and returns a structured output.

It does not own persistence.

It does not directly manipulate WebSockets.

It does not call the frontend.

---

### 6.5 `providers/`

Contains external integrations.

Recommended conceptual structure:

```text
providers/
├── market_data/
│   ├── base.py
│   ├── fixture.py
│   └── live.py
│
└── llm/
    ├── base.py
    ├── fake.py
    └── openrouter.py
```

The concrete provider names may change.

---

### 6.6 `persistence/`

Contains:

* database configuration;
* SQLAlchemy models;
* repositories;
* migrations;
* transaction handling.

Persistence must not leak into domain models.

---

### 6.7 `realtime/`

Contains:

* WebSocket connection management;
* event publication;
* event serialization.

The realtime layer publishes actual backend state.

It must not create fictional state transitions.

---

### 6.8 `core/`

Contains infrastructure-level concerns such as:

* configuration;
* logging;
* dependency wiring;
* application startup;
* shared technical utilities.

It must not become a miscellaneous business-logic folder.

---

## 7. Frontend architecture

The frontend has two layers.

```text
Frontend
│
├── React / Next.js
│   ├── application shell
│   ├── analysis panels
│   ├── history
│   ├── controls
│   └── error states
│
└── Phaser
    ├── Trading Desk
    ├── Market Intelligence Agent
    └── visual states
```

---

## 8. React responsibilities

React is responsible for:

* application layout;
* HTTP communication;
* WebSocket connection;
* analysis history;
* analysis panel;
* loading states;
* errors;
* data formatting;
* user controls.

React receives state from the backend.

---

## 9. Phaser responsibilities

Phaser is responsible for:

* visual Trading Desk environment;
* agent sprite;
* agent animation;
* interaction with the agent;
* visual state transitions;
* visual feedback.

Phaser must not independently determine whether an analysis succeeded.

For example:

```text
analysis.completed
        ↓
frontend state = completed
        ↓
Phaser agent = IDLE / SUCCESS animation
```

Not:

```text
Phaser animation finishes
        ↓
frontend assumes analysis succeeded
```

---

## 10. Frontend state model

The frontend should represent analysis lifecycle explicitly:

```text
idle
  ↓
submitting
  ↓
running
  ├───────────────┐
  ↓               ↓
completed        failed
```

The frontend must never skip directly from:

```text
submitting → completed
```

without backend confirmation.

---

## 11. Market data architecture

Market data enters the system through `MarketDataProvider`.

Conceptually:

```text
MarketDataProvider
        │
        ├── FixtureMarketDataProvider
        │
        └── LiveMarketDataProvider
```

---

### 11.1 Fixture provider

The fixture provider is deterministic.

Given the same fixture and request parameters:

```text
same input
    ↓
same snapshot
```

It must not generate random values.

It must be explicitly marked:

```text
source_mode = fixture
```

---

### 11.2 Live provider

The live provider translates vendor-specific data into the internal `MarketSnapshot` contract.

Vendor terminology must not leak into the domain layer.

For example:

```text
Vendor API
   ↓
adapter
   ↓
MarketSnapshot
   ↓
agent
```

The agent must never need to know how the vendor names candles, symbols or timestamps internally.

---

## 12. Market data normalization

The internal normalized market data must define:

* symbol;
* timeframe;
* observation timestamp;
* source;
* source mode;
* bars/observations;
* provider metadata;
* data quality information.

All timestamps must be stored in UTC.

The normalization layer must detect malformed provider responses.

Examples:

```text
missing timestamp
invalid OHLC values
unsupported symbol
empty response
unexpected response shape
```

These conditions become explicit failures.

---

## 13. LLM architecture

The application uses an `LLMProvider` abstraction.

```text
LLMProvider
    │
    ├── FakeLLMProvider
    │
    └── OpenRouterProvider
```

The provider is responsible for:

* sending the prompt;
* sending structured input;
* receiving the model output;
* exposing provider/model metadata;
* exposing provider failures.

The provider is not responsible for business validation.

---

## 14. Runtime model configuration

The model used by the product must be configurable.

Conceptually:

```text
LLM_MODEL=...
LLM_PROVIDER=openrouter
```

No model identifier should be hardcoded throughout the application.

This allows model replacement without rewriting the agent.

---

## 15. Development models vs product models

The model used by Cline for software development is a development-tool decision.

It is not automatically the model used by the product.

Therefore:

```text
Cline
  ↓
GLM 5.2 Free
  ↓
software implementation
```

is separate from:

```text
Market Intelligence Agent
  ↓
LLMProvider
  ↓
configured runtime model
```

The initial runtime model may use one of the configured OpenRouter models, but the architecture must not couple the product to Cline.

---

## 16. Agent execution flow

The canonical MVP-0 execution flow is:

```text
1. User requests XAU/USD analysis
        ↓
2. API validates request
        ↓
3. Application creates analysis record
        ↓
4. status = running
        ↓
5. emit analysis.started
        ↓
6. MarketDataProvider obtains snapshot
        ↓
7. snapshot is validated
        ↓
8. Market Intelligence Agent receives snapshot
        ↓
9. LLMProvider generates structured output
        ↓
10. output is validated
        ↓
11. analysis is persisted
        ↓
12. status = completed
        ↓
13. emit analysis.completed
        ↓
14. API returns result
```

Failure at any step must produce:

```text
status = failed
```

and emit:

```text
analysis.failed
```

---

## 17. HTTP API

The API should use a versioned namespace:

```text
/api/v1/
```

Initial conceptual routes:

```text
POST /api/v1/market-analyses
GET  /api/v1/market-analyses/{analysis_id}
GET  /api/v1/market-analyses
```

---

### 17.1 Create analysis

```text
POST /api/v1/market-analyses
```

Input contains the minimum information required to perform the analysis.

At MVP-0 this is expected to include:

* symbol;
* timeframe;
* data mode.

The server validates allowed values.

---

### 17.2 Retrieve analysis

```text
GET /api/v1/market-analyses/{analysis_id}
```

Returns the persisted analysis.

The result must come from backend state, not frontend cache.

---

### 17.3 History

```text
GET /api/v1/market-analyses
```

Returns historical analysis summaries.

Pagination should exist even if only a small amount of data is expected locally.

---

## 18. HTTP status principles

The API should distinguish common classes of errors.

Examples:

```text
400 → invalid request
404 → analysis not found
409 → conflicting/idempotency condition
422 → validation failure where appropriate
502/503 → upstream provider/service unavailable
500 → unexpected internal failure
```

The exact mapping should be centralized rather than invented independently by each endpoint.

---

## 19. WebSocket architecture

MVP-0 uses one WebSocket endpoint:

```text
/api/v1/ws
```

The frontend establishes a persistent connection while the Trading Desk is open.

Events are server-originated.

Required event types:

```text
analysis.started
analysis.completed
analysis.failed
```

Conceptually:

```text
WebSocketEvent
├── event_id
├── event_type
├── occurred_at
├── analysis_id
└── payload
```

The exact contract belongs in `DATA_CONTRACTS.md`.

---

## 20. WebSocket guarantees

WebSocket delivery is not the source of truth.

If the frontend disconnects:

```text
WebSocket lost
       ↓
HTTP GET /analysis/{id}
       ↓
PostgreSQL-backed state
       ↓
frontend reconciles
```

Therefore:

* events are notifications;
* HTTP/database state is authoritative;
* reconnect logic is required;
* frontend state can always be reconstructed.

---

## 21. PostgreSQL architecture

PostgreSQL is the persistent operational source of truth.

MVP-0 should use:

* SQLAlchemy;
* Alembic;
* explicit migrations;
* transactions.

---

## 22. Minimal persistence model

MVP-0 should minimize the number of tables.

A primary concept is:

```text
analysis_runs
```

It represents one analysis execution.

It should contain or reference:

* analysis ID;
* symbol;
* timeframe;
* status;
* request metadata;
* timestamps;
* market snapshot;
* provider metadata;
* model metadata;
* structured result;
* error information.

JSON/JSONB may be used where appropriate for versioned structured payloads.

Relational columns should be used for fields that are frequently queried.

The exact schema belongs in the implementation and is constrained by `DATA_CONTRACTS.md`.

---

## 23. Persistence lifecycle

When an analysis begins:

```text
analysis_runs.status = running
```

When successful:

```text
analysis_runs.status = completed
```

When unsuccessful:

```text
analysis_runs.status = failed
```

A failed record may retain diagnostic information.

It must never contain a fake successful result.

---

## 24. Transaction principle

The persistence operation for a completed analysis must be atomic.

The backend must not expose:

```text
completed
```

before the corresponding persistent result has been committed successfully.

---

## 25. Current MVP execution model

MVP-0 does not require a distributed worker system.

The initial execution can occur inside the FastAPI application process.

This is intentionally a development-scale execution model.

The architecture must isolate the application use case so that future execution can move to:

```text
API
  ↓
queue
  ↓
worker
  ↓
agent
```

without changing:

* API contracts;
* domain models;
* agent contracts;
* persistence semantics.

---

## 26. Concurrency

MVP-0 should assume that more than one analysis can be requested.

The system must therefore:

* create unique analysis IDs;
* avoid shared mutable global analysis state;
* avoid singleton agent execution state;
* associate every event with an `analysis_id`;
* persist every analysis independently.

The frontend may still expose only one active analysis at a time in the initial UI.

---

## 27. Configuration

Configuration must come from environment variables or a configuration layer.

Example conceptual variables:

```text
APP_ENV
DATABASE_URL

LLM_PROVIDER
LLM_MODEL
OPENROUTER_API_KEY

MARKET_DATA_PROVIDER
MARKET_DATA_API_KEY
MARKET_DATA_MODE
```

Secret values must only exist in:

```text
.env
```

or another secret mechanism.

Only safe placeholders belong in Git:

```text
.env.example
```

---

## 28. Secret handling

The application must never:

* commit secrets;
* log API keys;
* store provider secrets in PostgreSQL;
* return provider credentials through the API;
* place credentials in Obsidian;
* expose credentials to the frontend.

Frontend code must never receive server-side API keys.

---

## 29. Logging

MVP-0 requires structured application logging.

Each analysis-related log should include enough correlation information to identify the execution.

At minimum:

```text
analysis_id
request_id
component
event
timestamp
status
```

Logs must not contain:

* API keys;
* passwords;
* authentication headers;
* private reasoning traces;
* unnecessary full prompts;
* sensitive credentials.

---

## 30. Error architecture

Errors must be classified.

Conceptually:

```text
DomainError
ProviderError
ValidationError
PersistenceError
ConfigurationError
UnexpectedError
```

Each error should have:

* stable internal error code;
* human-readable safe message;
* optional internal diagnostic details.

Internal diagnostics remain server-side.

---

## 31. Testing architecture

The project must have multiple test layers.

### Unit tests

Test:

* domain models;
* validation;
* provider adapters;
* agent parsing;
* application services.

---

### Integration tests

Test:

* FastAPI endpoints;
* PostgreSQL persistence;
* WebSocket lifecycle;
* provider integration boundaries.

---

### Contract tests

Test:

```text
API request
API response
MarketSnapshot
MarketAnalysis
WebSocketEvent
```

against their defined schemas.

---

## 32. LLM testing

Automated tests must not depend on a real OpenRouter request.

The default test path is:

```text
Application
   ↓
FakeLLMProvider
   ↓
deterministic structured output
```

This allows tests to verify:

* valid output;
* invalid output;
* provider timeout;
* provider failure;
* schema validation.

---

## 33. Market data testing

The fixture provider is the deterministic baseline for tests.

Tests should verify:

```text
same fixture + same request
        =
same MarketSnapshot
```

The live provider should have adapter-level tests where possible, but the complete application test suite must remain independent from external API availability.

---

## 34. Frontend testing

The frontend must test at least:

* initial idle state;
* submitting state;
* running state;
* completed state;
* failed state;
* historical analysis rendering;
* WebSocket reconnection/reconciliation;
* fixture/live/unavailable indicators.

The frontend test suite must not require a live LLM.

---

## 35. Security boundaries

Even though MVP-0 is local/single-user oriented, the architecture must enforce basic boundaries.

The server must validate:

* symbols;
* timeframes;
* input sizes;
* allowed modes;
* response schemas.

The server must not trust:

* frontend state;
* frontend timestamps;
* frontend status;
* client-provided provider metadata.

---

## 36. Financial safety boundary

MVP-0 contains no trading engine.

There must be no runtime path from:

```text
MarketAnalysis
```

to:

```text
broker order
```

or:

```text
position execution
```

The architecture intentionally stops at analysis.

---

## 37. Legacy repository reuse policy

The legacy repository can serve as:

* design reference;
* source of visual inspiration;
* source of potentially reusable assets;
* source of architectural lessons.

It must not be treated as the implementation base.

### Reusable candidates

* Phaser initialization pattern;
* Trading Desk visual concept;
* `GameContainer` concept;
* `OfficeScene` concepts;
* `AgentEntity` visual concepts;
* selected office assets;
* visual interaction ideas.

### Not reusable as-is

* mock market-data service;
* random agent-state simulation;
* fabricated backtest engine;
* hardcoded Director;
* simulated verdict logic;
* legacy global state shortcuts;
* mock Telegram flows;
* hardcoded financial claims.

Every reused component must pass review against this architecture.

---

## 38. Dependency direction

Dependencies should flow inward:

```text
API
 ↓
Application
 ↓
Domain
```

Infrastructure dependencies point toward application/domain interfaces:

```text
OpenRouter adapter
      ↓
   LLMProvider
      ↑
  Application
```

```text
Market vendor adapter
      ↓
MarketDataProvider
      ↑
Application
```

The domain layer must remain infrastructure-independent.

---

## 39. Anti-patterns explicitly prohibited

The MVP must not introduce:

### Fake operational data

Examples:

```text
random prices
random agent states
fabricated news
fabricated metrics
fabricated analysis completion
```

---

### Global mutable business state

No global dictionary should act as the database for analyses.

---

### Frontend-generated truth

No frontend-only:

```text
analysis.status = completed
```

may be considered authoritative.

---

### LLM-generated business state

The LLM may output an analysis.

It may not decide:

```text
database transaction succeeded
provider succeeded
analysis is officially completed
```

---

### Premature infrastructure

Do not add:

```text
Redis
Kafka
Celery
Kubernetes
LangGraph
Obsidian
```

unless a later requirement justifies them.

---

## 40. Future evolution points

The architecture is intentionally prepared for future capabilities.

### MVP-1

```text
Strategy Agent
```

can use the same:

```text
LLMProvider
Application services
PostgreSQL
Realtime events
```

---

### MVP-2

Backtesting can become another application service:

```text
BacktestEngine
```

using deterministic calculations.

---

### MVP-2.5

Risk can be introduced as:

```text
RiskCalculatorEngine
```

without giving the LLM authority over risk limits.

---

### MVP-3

Multi-agent coordination can later be introduced through:

```text
Director
LangGraph
workflow state
```

without forcing MVP-0 to depend on LangGraph.

---

### MVP-4

Paper trading can later add:

```text
PaperExecutionEngine
```

while keeping the current analysis contracts intact.

---

## 41. Architecture decision summary

MVP-0 intentionally chooses:

```text
Application type:
Modular monolith

Backend:
FastAPI

Language:
Python

Validation:
Pydantic

Persistence:
PostgreSQL

ORM:
SQLAlchemy

Migrations:
Alembic

Frontend:
Next.js + React

Visual layer:
Phaser

Realtime:
FastAPI WebSocket

Market data:
Provider abstraction

LLM:
Provider abstraction

Initial LLM gateway:
OpenRouter

Tests:
Pytest + frontend test framework

Deployment target:
Local development first
```

---

## 42. Deferred technology decisions

The following must remain open until their corresponding phase requires them:

```text
Redis
LangGraph
Celery / worker system
Obsidian integration
Authentication
Cloud deployment architecture
Advanced observability
Broker integration
Paper execution infrastructure
```

An implementation agent must not introduce one of these technologies merely because it is familiar or available.

---

## 43. End-to-end ownership model

The definitive responsibility chain is:

```text
USER
 │
 ▼
FRONTEND
 │
 │ HTTP / WebSocket
 ▼
FASTAPI API
 │
 ▼
APPLICATION SERVICE
 │
 ├───────────────┐
 ▼               ▼
MARKET DATA    AGENT
PROVIDER         │
 │               ▼
 ▼           LLM PROVIDER
MARKET           │
SNAPSHOT         ▼
 │          STRUCTURED OUTPUT
 └──────────────┬┘
                ▼
          VALIDATION
                │
                ▼
           POSTGRESQL
                │
                ├── HTTP response
                └── WebSocket event
```

The system should have one authoritative source of truth for each stage.

---

## 44. MVP-0 architectural acceptance criteria

This architecture is considered implemented correctly when:

* [ ] frontend and backend are separate modules;
* [ ] backend is a modular monolith;
* [ ] domain models do not depend on framework infrastructure;
* [ ] market data is accessed through `MarketDataProvider`;
* [ ] LLM access is performed through `LLMProvider`;
* [ ] fixture providers exist for deterministic tests;
* [ ] PostgreSQL stores analysis execution state;
* [ ] migrations are version controlled;
* [ ] analysis lifecycle is explicit;
* [ ] WebSocket events reflect actual backend lifecycle;
* [ ] frontend can recover state through HTTP;
* [ ] fake data is explicitly marked;
* [ ] failures cannot appear as successful analyses;
* [ ] secrets stay outside source control;
* [ ] no trading execution path exists;
* [ ] automated tests do not require a live LLM;
* [ ] the implementation does not require Redis, LangGraph or Obsidian.

---

## 45. Final architectural rule

The MVP must be allowed to be small.

A technically simpler implementation that satisfies this document is preferable to a more sophisticated implementation that introduces unnecessary infrastructure.

The first objective is not maximum autonomy.

The first objective is a trustworthy, observable and extensible vertical slice.

Once that foundation works, additional agents and infrastructure can be introduced one capability at a time.
