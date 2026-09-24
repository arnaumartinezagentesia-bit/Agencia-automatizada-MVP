# Agencia Automatizada MVP-0 — Master Development Prompt

**Status:** Approved for implementation
**Product:** Agencia Automatizada
**Department:** Trading
**Capability:** XAU/USD Market Analysis
**Repository:** `Agencia-automatizada-MVP`

---

## 1. Purpose

This document defines the **controlled implementation protocol** for MVP-0.

It is the bridge between approved specifications and implementation work.

It is NOT a vague "build the whole application" instruction.

It is a repeatable, verifiable, cost-conscious operating procedure that ensures:

* incremental development;
* contract-first implementation;
* test-first verification where practical;
* vertical slices that are independently reviewable;
* reversible changes;
* resistance to fabricated functionality;
* resistance to scope creep;
* explicit stop conditions when specifications conflict or are incomplete.

The implementation agent must never interpret the existence of this document as permission to implement future roadmap capabilities (Strategy Agent, Backtesting, Risk Engine, Director, Paper Trading, Obsidian, etc.).

---

## 2. Specification Hierarchy

This document is subordinate to all upstream specifications:

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

**Authority rules:**

* `MVP_SCOPE.md` defines WHAT is allowed (product scope, capabilities, boundaries).
* `ARCHITECTURE.md` defines HOW system responsibilities are separated (layers, interfaces, dependencies).
* `DATA_CONTRACTS.md` defines exact cross-layer schemas (request/response, persistence, events).
* `AGENT_SPEC.md` defines agent behavior and boundaries (candidate output, non-responsibilities).
* `UI_SPEC.md` defines presentation and interaction (states, controls, error handling).
* This document defines HOW implementation work must be organized, verified and controlled.

**Conflict resolution:**

When this document and an upstream document appear to conflict, the upstream document prevails. The implementation must be corrected, not the specification.

When an upstream document is ambiguous or incomplete, the implementation agent must STOP and report the exact specification section, not invent a solution.

---

## 3. MVP-0 Implementation Target

The implementation target is exactly one vertical slice:

```text
User
  ↓
Trading Desk (Phaser environment)
  ↓
Market Intelligence Agent (interaction point)
  ↓
AnalysisRequest (validated)
  ↓
MarketDataProvider (FixtureMarketDataProvider initially)
  ↓
MarketSnapshot (validated)
  ↓
LLMProvider (FakeLLMProvider initially)
  ↓
candidate analytical output
  ↓
Application Layer validation/enrichment
  ↓
authoritative MarketAnalysis
  ↓
PostgreSQL (persistent operational source of truth)
  ↓
HTTP API + WebSocket notifications
  ↓
React / Phaser frontend
  ↓
Analysis result panel
  ↓
History retrieval
```

**Success milestone:**

A user can:

1. Enter the Trading Desk.
2. Activate the Market Intelligence Agent.
3. Request a qualitative XAU/USD analysis.
4. Observe the real backend execution lifecycle (pending → running → completed).
5. Receive the validated structured `MarketAnalysis` result.
6. Retrieve the same result later from persistent storage.

**Explicit non-scope:**

The implementation must NOT expand into:

* strategy generation;
* trading signals or BUY/SELL recommendations;
* order entry or execution;
* risk management or risk enforcement;
* broker integration;
* portfolio management;
* paper trading;
* multi-agent orchestration;
* Director;
* backtesting;
* autonomous position management;
* future departments;
* multi-user authentication beyond local development.

---

## 4. Implementation Principles

### 4.1 Specification before code

No implementation should introduce a new behavior that requires a new contract without first updating the appropriate specification.

If a coding task discovers that a specification is incomplete or ambiguous, the task must STOP and report the issue rather than invent a solution.

### 4.2 Backend authority

Backend state is authoritative for:

* analysis lifecycle;
* market data used;
* analysis results;
* timestamps;
* provider metadata;
* model metadata;
* error state.

Frontend state is never authoritative.

Frontend may cache or present backend state; it must never contradict or overwrite it.

### 4.3 Contract-first implementation

Implement exact upstream contracts rather than approximations.

Do not create "temporary" JSON structures that later become accidental contracts.

Do not invent convenience fields that are not in the specification.

### 4.4 LLM boundary

LLMs reason and generate interpretive content.

Deterministic application code controls:

* validation;
* lifecycle state transitions;
* identifiers (analysis_id, request_id, event_id);
* timestamps (created_at, started_at, completed_at, failed_at);
* persistence (database writes, transaction commit/rollback);
* provenance (data_sources, model_metadata);
* error handling and error codes.

The LLM does not own or decide any of these.

### 4.5 Explicit failure

A real failure must remain a failure.

Never produce fake success to keep the UI looking functional.

Never silently substitute fixture data when live was requested.

Never convert a system failure into an analytical ambiguity.

Never convert an analytical ambiguity into a system failure.

### 4.6 Minimal architecture

Do not introduce infrastructure that MVP-0 explicitly excludes.

Do not add:

* Redis;
* message queues (Celery, RabbitMQ, etc.);
* distributed workers;
* microservices;
* LangGraph;
* Obsidian;
* Kubernetes;
* production orchestration platforms;
* unnecessary observability platforms (Datadog, New Relic, etc.).

These are not rejected permanently. They are deferred until a later MVP requires them.

### 4.7 Replaceable providers

External providers must remain behind interfaces.

The codebase must not couple domain/application logic directly to:

* OpenRouter (or any specific LLM provider);
* a particular market-data vendor;
* database clients;
* browser APIs;
* Phaser internals.

Providers must be replaceable without changing agent contracts or application use cases.

### 4.8 Synchronous MVP-0 execution

MVP-0 uses synchronous execution inside the FastAPI application process.

The `POST /api/v1/market-analyses` request returns only after the analysis has completed or failed.

WebSocket events are notifications only; they do not establish authoritative state.

The final HTTP response reflects the authoritative persisted state.

This is intentionally a development-scale execution model. The architecture must isolate the application use case so that future execution can move to a queue/worker model without changing API contracts or domain models.

---

## 5. Implementation Phases

The recommended implementation sequence is:

```text
Phase 0   Repository / development foundation
Phase 1   Backend + frontend project foundation
Phase 2   Domain models and exact data contracts
Phase 3   PostgreSQL persistence + migrations
Phase 4   FixtureMarketDataProvider
Phase 5   LLMProvider abstraction + FakeLLMProvider
Phase 6   Market Intelligence Agent
Phase 7   CreateMarketAnalysis application use case
Phase 8   HTTP API
Phase 9   WebSocket notifications
Phase 10  Frontend React application shell
Phase 11  Trading Desk / Phaser environment
Phase 12  Analysis workflow + result UI
Phase 13  History + reconciliation + error UX
Phase 14  End-to-end fixture vertical slice (happy path + one representative failure path)
Phase 15  OpenRouter runtime integration
Phase 16  Final MVP-0 verification
```

**Adjustment rule:**

The exact implementation order may be adjusted only when a documented dependency requires it.

Do NOT collapse all phases into one implementation task.

Do NOT skip phases.

**Phase 7 / Phase 9 dependency note:**

Phase 7 (`CreateMarketAnalysis` application use case) needs to emit lifecycle notifications (`analysis.started`, `analysis.completed`, `analysis.failed`) before the WebSocket transport exists (Phase 9).

This is resolved without reordering phases: Phase 7 defines a `NotificationPort` interface owned by the application layer, with an in-memory/test implementation used for Phase 7's automated tests. Phase 9 implements the real WebSocket adapter behind that same port and wires it in place of the test implementation. The application use case must not be rewritten when Phase 9 lands — only the adapter changes.

---

## 6. Phase Gates

Every phase must have:

* **objective** — what is being implemented;
* **allowed scope** — what is in scope, what is explicitly out of scope;
* **inputs/dependencies** — what must be complete before this phase starts;
* **expected outputs** — what artifacts/code/tests are produced;
* **automated tests** — what test coverage is required;
* **manual verification** — what must be verified by human review;
* **acceptance criteria** — explicit pass/fail conditions;
* **explicit stop condition** — when to halt and report a blocker.

**A phase is not complete merely because code compiles.**

The next phase may begin only after the current phase passes its gate.

**Gate authorship:**

Before a phase begins, the orchestrator/human defines and approves the concrete gate for that phase (the eight elements above, instantiated for the phase's actual scope). The coding agent implementing the phase does not author or self-approve its own acceptance criteria — it implements against the gate it was given and reports against it. If no gate has been defined for a phase, the phase is not ready to start (see §24).

**Recommended workflow per phase:**

```text
implement
    ↓
test (automated + manual)
    ↓
inspect diff (git diff)
    ↓
review (code review)
    ↓
commit (small, meaningful commits)
    ↓
merge feature branch into main
    ↓
next phase
```

Do not allow implementation to accumulate a large unreviewed batch of unrelated changes.

---

## 7. Git Workflow

### 7.1 Branch discipline

* `main` represents the latest approved stable state.
* Never implement directly on `main`.
* Every logical implementation unit gets a dedicated feature branch.
* Branch names follow the pattern: `feat/phase-description` (e.g., `feat/fixture-market-data`, `feat/http-api`).
* Before starting a new phase, verify `git status` is clean and the feature branch is created from an up-to-date `main`. Starting a phase from a stale `main` or on top of uncommitted, unrelated changes is not permitted.

### 7.2 Commit discipline

* Keep commits small and meaningful.
* Each commit should represent one logical change.
* Avoid mixing documentation changes with implementation changes unless explicitly required.
* Run `git diff --check` before committing (no trailing whitespace, no mixed line endings).
* Review `git diff` before committing (understand what you're committing).

### 7.3 Testing before merge

* All automated tests must pass before merging.
* Manual verification must be documented in the PR.
* No merge without passing tests.

### 7.4 PR requirements

* Clear scope (one phase, one feature, one responsibility).
* Acceptance evidence (test results, manual verification notes).
* Reference to the specification section being implemented.
* No unrelated changes.

### 7.5 Recommended branch names

```text
feat/backend-foundation
feat/frontend-foundation
feat/domain-contracts
feat/persistence-migrations
feat/fixture-market-data
feat/llm-provider-abstraction
feat/market-intelligence-agent
feat/create-market-analysis-usecase
feat/http-api
feat/websocket-notifications
feat/frontend-shell
feat/trading-desk-phaser
feat/analysis-workflow-ui
feat/history-reconciliation
feat/e2e-fixture-flow
feat/openrouter-runtime
feat/final-verification
```

---

## 8. Testing Strategy

### 8.1 Contract tests

Validate exact schema compliance:

* `AnalysisRequest` — valid and invalid structures.
* `MarketSnapshot` — valid and invalid market data.
* `MarketBar` — OHLCV validation, timestamp ordering.
* `DataSource` — provenance fields.
* `MarketAnalysis` — complete structure, required fields, enum values.
* `ModelMetadata` — provider, model, prompt_version, timestamp.
* `AnalysisRun` — lifecycle states, field invariants.
* `AnalysisSummary` — history list item structure.
* `WebSocketEvent` — envelope structure, event types.
* Error envelope — code, message, details, meta.request_id.

### 8.2 Unit tests

Cover:

* `FixtureMarketDataProvider` — deterministic snapshot generation, validation.
* `FakeLLMProvider` — deterministic candidate output generation.
* `MarketSnapshot` validation — OHLCV relationships, timestamp ordering, price invariants.
* `MarketAnalysis` validation — schema, enums, field constraints, qualitative safety (no trading instructions).
* Application service (`CreateMarketAnalysis`) — request validation, lifecycle transitions, error handling.
* Persistence operations — create, retrieve, list, transaction handling.
* Error mapping — provider errors → API error codes.

### 8.3 Integration tests

Cover:

* PostgreSQL persistence — create analysis, retrieve by ID, list with pagination.
* Provider/application integration — snapshot validation, agent invocation, result validation.
* HTTP API behavior — POST request/response, GET retrieval, list pagination, error responses.
* WebSocket behavior — event emission, event structure, reconnection.

### 8.4 Frontend tests

Cover:

* Analysis controls — timeframe selection, data-mode selection, primary action.
* Lifecycle states — idle, submitting, pending, running, completed, failed.
* Result rendering — all required fields from `MarketAnalysis`.
* Failure states — error display, retry capability.
* History — list rendering, pagination, selection, retrieval.
* Fixture/live labeling — visible everywhere data is displayed.
* Reconciliation — GET after completion, after reconnection, after unknown outcome.
* WebSocket integration — event handling, disconnect behavior.

### 8.5 End-to-end test

The end-to-end suite must prove both the happy path and at least one representative failure path — the fixture vertical slice (Phase 14) is not done on the happy path alone.

**Happy path** — prove the complete vertical slice:

```text
UI (React)
  ↓
POST /api/v1/market-analyses
  ↓
backend (FastAPI)
  ↓
FixtureMarketDataProvider
  ↓
MarketSnapshot (validated)
  ↓
FakeLLMProvider
  ↓
candidate analytical output
  ↓
Application Layer validation
  ↓
MarketAnalysis (authoritative)
  ↓
PostgreSQL (persisted)
  ↓
backend emits analysis.completed
  +
backend returns HTTP 201 with analysis_id
  ↓
frontend obtains analysis_id
  ↓
GET /api/v1/market-analyses/{analysis_id}
  ↓
UI result panel
  ↓
GET /api/v1/market-analyses (history)
  ↓
UI history list
  ↓
page reload
  ↓
GET /api/v1/market-analyses/{analysis_id}
  ↓
same persisted result retrievable
```

The WebSocket notification and the HTTP 201 response are independent delivery paths. The frontend must remain correct regardless of which arrives first, and must not implement an accidental dependency between the two channels.

**Representative failure path** — prove at least one full failure traversal end to end, e.g. a `MarketDataProvider` configured to fail deterministically (`PROVIDER_ERROR`):

```text
UI (React)
  ↓
POST /api/v1/market-analyses
  ↓
backend (FastAPI)
  ↓
MarketDataProvider fails deterministically
  ↓
Application Layer maps failure to PROVIDER_ERROR
  ↓
status = failed, error persisted (best effort, per §13.2)
  ↓
HTTP error response (non-2xx, error envelope)
  ↓
UI failure state rendered (explicit, non-fabricated, per UI_SPEC.md §15)
```

This does not require a large failure-path test matrix for Phase 14 — one representative, deterministic failure traversed end to end is sufficient to prove the failure contract holds across all layers. Additional failure paths are covered by the unit/integration/contract tests in §8.1–§8.3.

**Tests must NOT depend on a real OpenRouter request.**

---

## 9. Deterministic Development Baseline

The first complete vertical slice must use:

```text
FixtureMarketDataProvider
+
FakeLLMProvider
+
PostgreSQL (local)
```

**Purpose:**

Make the entire system reproducible without external API availability.

Enable cost-conscious development (no paid API calls during development).

Enable deterministic automated testing.

**Rules:**

* The fixture provider is deterministic: same input → same snapshot.
* The fake LLM is deterministic: same input → same candidate output.
* The fixture must never be presented as live data.
* The fake LLM must never be used by the production runtime path unless explicitly configured for development/testing.
* Fixture data is explicitly marked as test data everywhere it appears.

---

## 10. Live Data Implementation

Live market data must be implemented behind the existing `MarketDataProvider` abstraction.

**Sequence:**

1. Fixture implementation comes first.
2. Live integration comes later (Phase 15).
3. Provider selection must not change agent contracts.
4. Live availability cannot silently fall back to fixture.
5. Provider failures must remain explicit.

**Provider selection criteria:**

Before implementing a live provider, verify:

* XAU/USD support;
* required timeframe support (1m, 5m, 15m, 1h, 4h, 1d);
* historical and intraday data availability;
* free-tier limits and cost;
* licensing and usage restrictions;
* authentication mechanism;
* reliability and uptime SLA;
* rate limiting and throttling behavior.

**Implementation rule:**

The implementation specification must not prematurely hard-code a vendor if the upstream architecture intentionally leaves the choice open.

---

## 11. LLM Implementation

### 11.1 Provider abstraction

Implement:

```text
LLMProvider (interface)
├── FakeLLMProvider (deterministic test implementation)
└── OpenRouterProvider (production implementation)
```

### 11.2 Market Intelligence Agent

The agent consumes `LLMProvider`.

The agent receives validated `MarketSnapshot` and returns candidate analytical output.

The agent does NOT own persistence, lifecycle, identifiers, timestamps or provenance.

### 11.3 Model configuration

The runtime LLM model must be configurable:

```text
LLM_PROVIDER=openrouter
LLM_MODEL=<configured-model-identifier>
```

No model identifier should be hardcoded throughout the application.

### 11.4 Development vs. product model

The model used by Cline (or any coding assistant) for software development is a development-tool decision.

It is NOT automatically the model used by the product runtime.

Therefore:

```text
Cline
  ↓
development model (e.g., Claude, GLM, etc.)
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

Do not couple the product runtime model to:

* Cline;
* Claude;
* Abacus;
* any specific coding assistant.

Runtime model configuration belongs to application configuration, not to the implementation.

---

## 12. Agent Implementation Boundary

The implementation protocol must explicitly preserve the distinction established in `AGENT_SPEC.md`.

### 12.1 Agent responsibility

The agent returns candidate structured analytical content:

```text
trend_context
volatility_context
key_levels
market_observations
uncertainties
```

### 12.2 Agent non-responsibility

The agent does NOT own or generate authoritative:

```text
analysis_id
timestamp_utc
schema_version
market_snapshot
model_metadata
data_sources
status
lifecycle
```

### 12.3 Application Layer responsibility

The Application Layer:

1. Validates the candidate output.
2. Constructs the authoritative `MarketAnalysis` by combining:
   - candidate analytical fields (from agent);
   - authoritative backend fields (analysis_id, timestamp_utc, schema_version, market_snapshot, model_metadata, data_sources).
3. Persists the authoritative result.
4. Manages lifecycle state.

**The coding agent must not collapse these layers for convenience.**

---

## 13. Application Use Case

The implementation must contain a clear application-level orchestration for the MVP-0 analysis operation.

### 13.1 Use case: CreateMarketAnalysis

Conceptually:

```text
validate request (AnalysisRequest)
    ↓
create analysis record (status = pending)
    ↓
transition to running
    ↓
emit analysis.started (status = running)
    ↓
obtain MarketSnapshot (MarketDataProvider)
    ↓
validate snapshot
    ↓
invoke Market Intelligence Agent (LLMProvider)
    ↓
validate candidate output
    ↓
construct authoritative MarketAnalysis
    ↓
persist atomically (PostgreSQL)
    ↓
emit analysis.completed (status = completed)
    ↓
return HTTP 201 + analysis_id
```

### 13.2 Failure handling

Failure handling is split by whether the `AnalysisRun` record already exists, because `analysis_id`, lifecycle state and WebSocket events cannot exist before the record is created.

**Pre-creation failures** (request validation, before the `AnalysisRun` is created — no `analysis_id` yet):

```text
HTTP error (non-2xx) with the error envelope
```

No lifecycle state, no `analysis_id`, no WebSocket event: there is nothing yet to attach them to. This matches `UI_SPEC.md` §15.1 (`VALIDATION_ERROR` presented near the analysis controls, not as a run failure).

**Post-creation failures** (any step after the `AnalysisRun` exists — snapshot retrieval, agent invocation, candidate validation, construction of the authoritative `MarketAnalysis`):

```text
status = failed
error = ErrorDetail (code, message, details)
persist the failed state (best effort — see below)
emit analysis.failed only when the failed terminal state is durably confirmed persisted
return HTTP error (non-2xx)
```

**Persistence-failure rule (`PERSISTENCE_ERROR`):**

If persistence itself is what failed, the use case must not claim that the `failed` state was durably saved — a database that just failed to write cannot be trusted to have written the very record describing its own failure. Concretely:

* The HTTP error response is the authoritative signal of failure in this case; it does not depend on the write having succeeded.
* `analysis.failed` is emitted only if the run's terminal state was confirmed persisted (i.e., persistence failures that prevent writing the `failed` state must not trigger the event, since there would be nothing for a later `GET` to confirm).
* The UI must never be told, directly or implicitly, that a `failed` state exists in the database unless that can be confirmed. An unconfirmed outcome after a persistence failure is presented as unknown/failed-to-persist, not as a confirmed `failed` run (`UI_SPEC.md` §8.2, §15.1).
* No fabricated durability: "best effort" persistence of the failure record is attempted once; its outcome (succeeded or not) must be reflected honestly, never assumed.

### 13.3 Lifecycle ownership

Do not implement lifecycle logic inside:

* React;
* Phaser;
* the LLM;
* the market provider.

Lifecycle is owned by the Application Layer.

---

## 14. HTTP API Implementation

Implement only the routes defined in `ARCHITECTURE.md` §17 and `DATA_CONTRACTS.md` §14:

```text
POST /api/v1/market-analyses
GET  /api/v1/market-analyses/{analysis_id}
GET  /api/v1/market-analyses
```

### 14.1 POST /api/v1/market-analyses

* Input: `AnalysisRequest` (symbol, timeframe, data_mode).
* Execution: synchronous (returns only after completion or failure).
* Success response: HTTP 201 + `{"data": {"analysis_id": "...", "status": "completed"}, "meta": {"request_id": "..."}}`
* Failure response: HTTP non-2xx + error envelope.

### 14.2 GET /api/v1/market-analyses/{analysis_id}

* Returns the persisted analysis and lifecycle state.
* Discriminated union on `status`:
  - `pending` / `running` → `analysis = null`, `error = null`
  - `completed` → `analysis = MarketAnalysis`, `error = null`
  - `failed` → `analysis = null`, `error = ErrorDetail`

### 14.3 GET /api/v1/market-analyses

* Returns historical analyses using server-side pagination.
* Response: `{"data": {"items": [AnalysisSummary, ...], "pagination": {...}}, "meta": {...}}`
* Pagination: `limit`, `offset`, `has_more`.

### 14.4 Error envelope

All errors use the common contract:

```text
{
  "error": {
    "code": "ERROR_CODE",
    "message": "safe message",
    "details": {...}
  },
  "meta": {
    "request_id": "UUID"
  }
}
```

### 14.5 Rules

* Do not invent additional API endpoints for convenience.
* Respect synchronous MVP-0 execution.
* HTTP 201 only after successful persistence.
* Non-2xx on execution failure.
* Server-side history pagination (no unbounded responses).
* Authoritative backend results (no frontend fabrication).

---

## 15. WebSocket Implementation

Implement only:

```text
/api/v1/ws
```

and the defined event types:

```text
analysis.started
analysis.completed
analysis.failed
```

### 15.1 Event structure

Each event is a `WebSocketEvent` envelope (`DATA_CONTRACTS.md` §12):

```text
{
  "event_id": "UUID",
  "event_type": "analysis.started | analysis.completed | analysis.failed",
  "occurred_at": "ISO-8601 UTC",
  "analysis_id": "UUID",
  "payload": {...}
}
```

### 15.2 Payload content

* `analysis.started`: `{"status": "running"}`
* `analysis.completed`: `{"status": "completed"}`
* `analysis.failed`: `{"status": "failed", "error": {...}}`

The payload contains only lifecycle notification content — never analysis content.

### 15.3 Semantics

WebSocket events are notifications only.

The frontend must reconcile authoritative state through HTTP GET.

### 15.4 Rules

* Do not introduce event buses, Redis, message brokers or distributed event infrastructure.
* Events are server-originated.
* Delivery is not guaranteed; HTTP GET is the authoritative reconciliation path.
* Do not create additional event types beyond the three defined.

---

## 16. Frontend Implementation

The frontend implementation must respect the approved UI specification (`UI_SPEC.md`).

### 16.1 Responsibility split

```text
React
    ↓
conventional information UI
    - analysis controls (symbol, timeframe, data_mode)
    - status area (lifecycle, transport)
    - analysis result panel (all MarketAnalysis fields)
    - history list (AnalysisSummary items)
    - error display
    - provenance display (fixture/live, provider, timestamps, model)

Phaser
    ↓
visual Trading Desk
    - environment (office scene)
    - agent representation (sprite)
    - backend-derived visual state (idle, working, completed, failed)
    - interaction point (select agent)
```

### 16.2 State model

Frontend state may cache or present information.

Phaser state is derived visual state.

Neither is authoritative.

Backend state is authoritative.

### 16.3 Forbidden behavior

No UI implementation may invent:

* market data or prices;
* analysis results or analysis content;
* progress percentages or simulated steps;
* agent autonomy or self-initiated work;
* lifecycle completion from animation finishing;
* fake success to keep the UI looking functional.

### 16.4 Required behavior

* Lifecycle states are always visible as text.
* Fixture/live distinction is visible everywhere data is displayed.
* Uncertainties and `unclear` values are visible and rendered as valid analysis.
* Provenance is visible (data source mode, provider, timestamps, model metadata).
* Errors are explicit and use the safe backend error contract.
* WebSocket disconnect is shown as a transport status, not as analysis failure.
* History is backend-backed via `GET /api/v1/market-analyses`.
* Reconciliation through GET happens after completion, failure, reconnection and unknown outcomes.

---

## 17. Accessibility Requirements

Preserve the UI specification's minimum accessibility guarantees:

* **Semantic controls:** real buttons, real selects, real links — not pixel-only hotspots.
* **Keyboard operation:** all interactive elements reachable and operable by keyboard.
* **Visible focus:** clear focus indicator on every interactive element.
* **Text + non-color-only state:** every state communicated by text plus icon/shape; color is secondary.
* **Assistive technology:** lifecycle changes announced to screen readers (live regions).
* **Error communication:** errors are text, associated with relevant control, mention safe message and error code.
* **Loading communication:** loading states are text + indeterminate indicator; never animation alone.
* **Pixel Art redundancy:** Pixel Art never carries information exclusively; all backend states also represented textually.

Do not treat Pixel Art interaction as exempt from accessibility.

---

## 18. Legacy Repository Policy

The implementation may selectively reuse visual concepts and assets from the legacy repository only.

### 18.1 Potential reuse

* Trading office visual concept.
* Phaser initialization concepts.
* `GameContainer` approach.
* `OfficeScene` concepts.
* `AgentEntity` visual concepts.
* Visual assets (office/agent sprite art) where appropriate.

### 18.2 Never reuse

* Fake market data or mock market-data services.
* Simulated agent state or autonomous agent-state loops.
* Heuristic Director logic.
* Fake analysis generation or fake backtesting.
* Hardcoded trading claims or profitability statements.
* Fabricated performance metrics.
* Legacy persistence shortcuts or global mutable state.

### 18.3 Adaptation rule

Any reused code must be reviewed against the new architecture before adoption.

No large directory copy from the old repository is permitted.

---

## 19. Secrets and Configuration

### 19.1 Never commit

* API keys;
* credentials;
* tokens;
* `.env` secrets;
* provider secrets;
* authentication headers;
* private reasoning traces.

### 19.2 Use environment configuration

Configuration must come from environment variables or a configuration layer:

```text
APP_ENV
DATABASE_URL
LLM_PROVIDER
LLM_MODEL
OPENROUTER_API_KEY
MARKET_DATA_PROVIDER
MARKET_DATA_API_KEY
```

### 19.3 Safe placeholders

Only safe placeholders belong in Git:

```text
.env.example
```

### 19.4 Frontend security

Frontend must never receive server-side provider credentials.

### 19.5 Failure behavior

The runtime should fail explicitly when required provider configuration is missing.

Never silently fall back from live provider to fixture.

---

## 20. Cost Control

Because this project initially operates under constrained budget, the implementation protocol must prefer:

* Fixture data during development (no paid API calls).
* `FakeLLMProvider` for tests (no OpenRouter calls).
* Minimal external API usage.
* No unnecessary repeated LLM calls.
* No unnecessary infrastructure.
* Local PostgreSQL.
* Deterministic automated tests.

Real OpenRouter calls should be introduced only after the fixture vertical slice is stable (Phase 15).

Do not make paid external services a prerequisite for basic development.

---

## 21. Observability

MVP-0 requires only the observability defined upstream.

### 21.1 Support

* Structured logs (JSON format preferred).
* Request correlation (`request_id`).
* Analysis correlation (`analysis_id`).
* Provider identity (provider_name, provider_version).
* Lifecycle visibility (status transitions).
* Explicit validation/error codes.

### 21.2 Never log

* API keys;
* credentials;
* authentication headers;
* private reasoning traces;
* unnecessary secrets;
* full prompts (only prompt_version).

### 21.3 No new platforms

Do not introduce a new observability platform in MVP-0.

---

## 22. Failure / Stop Conditions

The coding agent must STOP and report rather than improvising when it encounters:

* Conflicting specifications.
* Missing required contract.
* Ambiguous domain behavior.
* Need for a new API endpoint.
* Need for a new cross-layer field.
* Need for a new lifecycle state.
* Need for a new external dependency.
* Architecture requiring Redis, queues, workers, etc.
* Trading execution requirements.
* Inability to preserve backend authority.
* Inability to preserve agent candidate-output boundary.
* Inability to preserve synchronous execution.
* Inability to preserve fixture/live separation.

**Correct behavior:**

```text
STOP
  ↓
identify conflict
  ↓
report exact specification section
  ↓
do not invent solution
```

Do not "temporarily" violate the contract.

---

## 23. Implementation Task Format

Every coding task generated from this master prompt must be structured as:

```text
Task
Objective
Scope
Allowed files
Forbidden changes
Dependencies
Implementation requirements
Tests
Manual verification
Acceptance criteria
Git/PR requirements
Stop conditions
```

**Example:**

```text
Task: Implement FixtureMarketDataProvider

Objective:
Provide a deterministic market-data provider for development and testing.

Scope:
- Implement FixtureMarketDataProvider class
- Implement deterministic snapshot generation
- Add unit tests for snapshot generation
- Add contract tests for MarketSnapshot validation

Allowed files:
- backend/app/providers/market_data/fixture.py
- backend/tests/unit/providers/test_fixture_market_data.py
- backend/tests/contract/test_market_snapshot.py

Forbidden changes:
- Do not modify MarketDataProvider interface
- Do not modify MarketSnapshot contract
- Do not add new fields to MarketSnapshot
- Do not modify any other provider

Dependencies:
- MarketDataProvider interface must exist
- MarketSnapshot contract must be defined

Implementation requirements:
- Implement MarketDataProvider interface
- Generate deterministic snapshot for XAUUSD
- Support the full contract timeframe enum: 1m, 5m, 15m, 1h, 4h, 1d
- Validate snapshot against contract
- Mark data as fixture mode

Tests:
- Unit tests for snapshot generation, covering every timeframe in the
  contract enum
- Contract tests for MarketSnapshot schema
- Determinism test: same input → same output, for each timeframe

Manual verification:
- Inspect generated snapshot
- Verify fixture mode is set
- Verify prices satisfy the MarketSnapshot contract and match the
  expected deterministic fixture output

Acceptance criteria:
- All tests pass
- Snapshot matches contract
- Fixture mode is explicit
- No secrets in code
- No hardcoded API keys

Git/PR requirements:
- Branch: feat/fixture-market-data
- Commit message: "feat: implement FixtureMarketDataProvider"
- PR description: scope, tests, verification

Stop conditions:
- If MarketSnapshot contract is incomplete
- If MarketDataProvider interface is missing
- If fixture data cannot be marked as test data
```

The task must be small enough to review independently.

Avoid prompts such as: "Build the entire MVP."

---

## 24. Definition of Ready

A task is READY only when:

* The relevant specification exists and is complete.
* Dependencies are known and available.
* Exact contracts are clear.
* Scope is bounded.
* Tests are identifiable.
* Forbidden changes are known.
* Stop conditions are explicit.

If these conditions are not true, the task is not ready for implementation.

---

## 25. Definition of Done

An implementation task is DONE only when:

* Implementation matches upstream contracts exactly.
* Automated tests pass.
* Relevant manual verification passes.
* No unrelated changes are present.
* `git diff --check` passes (no trailing whitespace, no mixed line endings).
* No secrets are introduced.
* No fake behavior is introduced.
* No undocumented contract is introduced.
* Branch/commit is reviewable (small, focused changes).
* PR description explains scope and verification.

**MVP-0 as a whole is DONE only when the definition of done in `MVP_SCOPE.md` §19 is satisfied.**

---

## 26. Final MVP-0 Implementation Gate

Before declaring MVP-0 complete, verify the complete chain:

### 26.1 Happy path

```text
Trading Desk (visible)
    ↓
Market Intelligence Agent (visible, interactive)
    ↓
Analyze XAU/USD (primary action)
    ↓
AnalysisRequest validation
    ↓
MarketSnapshot (obtained, validated)
    ↓
LLMProvider (invoked)
    ↓
candidate analytical output (validated)
    ↓
MarketAnalysis (authoritative, constructed)
    ↓
PostgreSQL (persisted atomically)
    ↓
backend emits analysis.completed
    +
backend returns HTTP 201 (with analysis_id) — independent delivery paths
    ↓
frontend obtains analysis_id
    ↓
GET /api/v1/market-analyses/{analysis_id} (authoritative result)
    ↓
frontend result panel (rendered from GET)
    ↓
GET /api/v1/market-analyses (history)
    ↓
frontend history list (rendered)
    ↓
page reload
    ↓
same persisted result retrievable
```

### 26.2 Failure paths

Verify explicit failure handling:

* Provider failure (market data unavailable).
* LLM failure (LLM unavailable or timeout).
* Invalid LLM output (schema violation, forbidden content).
* Persistence failure (database unavailable).
* API failure (HTTP error).
* WebSocket disconnect (transport failure).
* Unknown POST outcome (network failure during submission).

In every case, the UI must remain truthful and never fabricate success.

### 26.3 Verification checklist

* [ ] Trading Desk is visible and interactive.
* [ ] Market Intelligence Agent is visible and interactive.
* [ ] XAU/USD analysis is the primary workflow.
* [ ] Fixture data is explicitly marked as test data.
* [ ] Live data mode is available (even if not configured).
* [ ] Lifecycle states are visible as text.
* [ ] Analysis result panel shows all required fields.
* [ ] Uncertainties and `unclear` values are visible.
* [ ] Provenance is visible (data source, provider, timestamps, model).
* [ ] History is backend-backed and retrievable.
* [ ] Failures are explicit and use the error contract.
* [ ] WebSocket disconnect is shown as transport status.
* [ ] No trading execution UI exists.
* [ ] No secrets are committed.
* [ ] No fake behavior is present.
* [ ] All tests pass.
* [ ] Code is reviewed.

---

## 27. Document Hierarchy / Source of Truth

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

**Authority rules:**

* This document does not override upstream specifications.
* Implementation must follow the latest approved contract.
* Undocumented behavior must not be invented.
* Future roadmap functionality requires a separate specification.
* The legacy repository is not a source of truth.

**Conflict resolution:**

When this document and an upstream document appear to conflict, the upstream document prevails.

When an upstream document is ambiguous or incomplete, the implementation agent must STOP and report the issue, not invent a solution.

---

## 28. Quality Checklist

Before writing implementation code, verify this document satisfies all quality criteria:

* [ ] Does not create new product scope.
* [ ] Does not create new domain contracts.
* [ ] Does not introduce new API routes.
* [ ] Preserves backend authority.
* [ ] Preserves the agent candidate-output boundary.
* [ ] Preserves synchronous MVP-0 execution.
* [ ] Preserves WebSocket notification semantics.
* [ ] Preserves fixture/live separation.
* [ ] Preserves deterministic testing.
* [ ] Preserves PostgreSQL as operational source of truth.
* [ ] Preserves React/Phaser responsibility boundaries.
* [ ] Preserves financial safety boundaries.
* [ ] Preserves explicit failure behavior.
* [ ] Does not require paid services for the first deterministic vertical slice.
* [ ] Does not turn the master prompt into an uncontrolled "build everything" instruction.
* [ ] Defines clear implementation gates and stop conditions.
* [ ] Keeps coding-agent model/provider separate from product runtime model/provider.
* [ ] Does not modify any upstream specification.
* [ ] Does not modify any implementation file.
