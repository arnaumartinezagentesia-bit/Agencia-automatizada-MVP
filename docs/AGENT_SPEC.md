# Agencia Automatizada MVP — Agent Specification

**Status:** Proposed for MVP-0
**Product:** Agencia Automatizada
**Department:** Trading
**Primary agent:** Market Intelligence Agent
**Identifier:** `trading_market_intelligence_agent`
**Repository:** `Agencia-automatizada-MVP`

---

## 1. Purpose

The Market Intelligence Agent is the sole agent in MVP-0. Its purpose is to transform a validated `MarketSnapshot` into candidate structured analytical content containing qualitative interpretation of market context, trend structure, volatility context, relevant price levels, observations, and uncertainties.

The agent produces candidate structured analytical content. It does not produce trading decisions, execution instructions, or financial recommendations. The Application Layer validates the candidate content, assigns/enriches authoritative fields (`analysis_id`, `timestamp_utc`, `schema_version`, `market_snapshot`, `model_metadata`, `data_sources`), and the accepted result becomes a `MarketAnalysis` object as defined in `DATA_CONTRACTS.md`.

---

## 2. Identity

| Property | Value |
|----------|-------|
| **Name** | Market Intelligence Agent |
| **Identifier** | `trading_market_intelligence_agent` |
| **Department** | Trading |
| **Capability** | Structured qualitative market analysis of XAU/USD |
| **Lifecycle role** | Invoked during `running` state of an `AnalysisRun`; returns candidate structured output for application-layer validation |

---

## 3. Responsibilities

The agent MUST:

* Interpret market context from the supplied `MarketSnapshot`
* Describe trend structure via `TrendContext` (direction, strength, description)
* Describe volatility context via `VolatilityContext` (regime, description)
* Identify relevant price levels via `KeyLevel[]` (type: support | resistance, price, description)
* Generate concise qualitative `market_observations` grounded in the snapshot
* Record explicit `uncertainties` and limitations of the analysis
* Preserve traceability to the input `MarketSnapshot` and its `DataSource`
* Return candidate analytical/interpretive content compatible with the interpretive fields of `MarketAnalysis` (`trend_context`, `volatility_context`, `key_levels`, `market_observations`, `uncertainties`); the Application Layer constructs the authoritative `MarketAnalysis` by combining this candidate content with authoritative fields (`analysis_id`, `timestamp_utc`, `schema_version`, `market_snapshot`, `model_metadata`, `data_sources`)

---

## 4. Non-responsibilities

The agent MUST NOT:

* Emit BUY/SELL instructions or any trading signal
* Generate order instructions (entry, exit, stop-loss, take-profit, position sizing)
* Execute trades or interact with any broker interface
* Control or manage positions
* Decide or enforce financial risk limits
* Invent market data, prices, bars, volume, or events
* Determine whether an analysis operation succeeded or failed
* Control persistence (database writes, transaction commit/rollback)
* Control WebSocket emission or lifecycle events
* Select or override the market data provider
* Modify system state directly (analysis status, timestamps, identifiers)
* Produce `MarketAnalysis` fields that are authoritative backend concerns (`analysis_id`, `timestamp_utc`, `schema_version`, `market_snapshot`, `model_metadata`, `data_sources`, lifecycle/status fields)

---

## 5. Input Contract

The agent receives the following conceptual input (already validated by the application/provider layer):

| Input | Source | Description |
|-------|--------|-------------|
| `instrument` | `AnalysisRequest.symbol` | Canonical symbol: `XAUUSD` |
| `timeframe` | `AnalysisRequest.timeframe` | Requested timeframe (e.g., `1h`) |
| `market_observation_timestamp` | `MarketSnapshot.as_of_utc` | Market-data observation timestamp (the moment the market data represents) |
| `validated_market_snapshot` | `MarketSnapshot` | Validated snapshot containing bid, ask, mid, bars, and `DataSource` |
| `data_provenance` | `MarketSnapshot.data_source` | Provenance of the snapshot (mode, provider, timestamps). This is a reference to the single authoritative `MarketSnapshot.data_source`; it does not constitute a second source of truth. |
| `model_configuration` | Application config | `LLMProvider`, model identifier, prompt version |

`MarketSnapshot.as_of_utc` is a market-data observation timestamp.
`MarketAnalysis.timestamp_utc` is assigned by the backend when the validated analysis is finalized.

The agent MUST NOT receive unvalidated data. The input snapshot has passed provider validation and market snapshot consistency validation per `DATA_CONTRACTS.md` §15.

---

## 6. Input Validation Assumptions

The agent operates under the following assumptions:

* The `MarketSnapshot` has passed all provider validations (symbol, timeframe, timestamps, OHLC relationships, positive prices, non-negative volume, bar ordering)
* The snapshot `symbol` and `timeframe` match the request
* Bars belong to the requested symbol and timeframe
* Latest bar timestamp ≤ `snapshot.as_of_utc`
* `DataSource` is present and valid
* Price invariants hold (bid > 0, ask > 0, mid > 0, ask ≥ bid)

The agent MUST NOT attempt to repair invalid data. Invalid provider data results in explicit `PROVIDER_ERROR` or `VALIDATION_ERROR` before the agent is invoked.

---

## 7. Output Contract

The agent produces a candidate structured output that, after application-layer validation and enrichment, becomes a `MarketAnalysis` per `DATA_CONTRACTS.md` §9.

### 7.1 Candidate Output Shape

The agent candidate output contains exactly these interpretive fields:

* `trend_context`
* `volatility_context`
* `key_levels`
* `market_observations`
* `uncertainties`

These are **candidate values only**. The candidate output does **NOT** contain authoritative backend fields such as:

* `analysis_id`
* `timestamp_utc`
* `schema_version`
* `market_snapshot`
* `model_metadata`
* `data_sources`
* lifecycle/status fields

The Application Layer validates the candidate output and constructs the authoritative `MarketAnalysis`.

### 7.2 Agent Output vs Authoritative Contract

| Concern | Agent (LLM) | Application Layer (Backend) |
|---------|-------------|----------------------------|
| Interpretive fields (`trend_context`, `volatility_context`, `key_levels`, `market_observations`, `uncertainties`) | Generates candidate content | Validates schema, enums, lengths, qualitative safety; accepts or rejects |
| `analysis_id` | Must not generate | Assigns UUID v4 |
| `timestamp_utc` | Must not generate | Assigns UTC timestamp at completion |
| `schema_version` | Must not generate | Assigns current version (e.g., `1.0.0`) |
| `market_snapshot` | Must not generate | Attaches validated snapshot |
| `model_metadata` | Must not generate | Records provider, model, prompt_version, generated_at_utc |
| `data_sources` | Must not generate | Constructs from `MarketSnapshot.data_source` |
| `status` / lifecycle | Must not control | Controls via `AnalysisRun` |

The application layer MUST validate the agent output before persistence. An invalid LLM result produces `analysis.failed` with `ANALYSIS_VALIDATION_ERROR` and is never persisted as a successful `MarketAnalysis`.

---

## 8. Analytical Scope

The agent MAY interpret the following from the supplied snapshot:

* **Market context**: Current bid/ask/mid, recent price action, bar structure
* **Trend structure**: Direction (`up | down | sideways | unclear`), strength (`weak | moderate | strong | unclear`), analytical description
* **Volatility context**: Regime (`low | moderate | high | unclear`), analytical description
* **Relevant price levels**: Support/resistance observations with price and description
* **Market observations**: Concise qualitative observations grounded in the snapshot
* **Uncertainties**: Explicit limitations, ambiguous conditions, data gaps
* **Provenance awareness**: The agent receives `MarketSnapshot.data_source` as input context; it may be aware of the data source mode/provenance; it does not generate, modify, or own provenance fields; the Application Layer remains responsible for `MarketAnalysis.data_sources`.

`unclear` is a VALID analytical result when evidence is insufficient. The agent MUST NOT transform ambiguity into a fabricated directional call.

---

## 9. Grounding and Evidence Rules

The agent MUST ground all assertions exclusively in the supplied `MarketSnapshot` and its `DataSource`.

The agent MUST NOT:

* Invent prices, bars, volume, or OHLC values
* Invent market events, news, or external catalysts
* Attribute data not present in the input (e.g., "fed policy caused this move" without supporting data in snapshot)
* Present external knowledge as if derived from the snapshot
* Hallucinate data source provenance or timestamps

When evidence is insufficient for a confident interpretation:

* Use `unclear` for `TrendContext.direction`, `TrendContext.strength`, `VolatilityContext.regime`
* Populate `uncertainties` with explicit descriptions of the limitation
* Leave `key_levels` empty rather than inventing levels

---

## 10. Qualitative Analysis Methodology

The agent organizes its interpretation conceptually around these steps (not a trading strategy):

1. **Current market context**: Assess bid/ask/mid, recent bars, snapshot timestamp
2. **Recent structural behavior**: Observe bar sequence, range, momentum, volume patterns
3. **Trend context**: Determine direction, strength, describe reasoning
4. **Volatility context**: Assess regime, describe reasoning
5. **Relevant price areas**: Identify support/resistance observations from bars
6. **Supporting observations**: Concise qualitative statements grounded in data
7. **Uncertainties**: Explicit limitations, data gaps, ambiguous signals

These seven steps are **conceptual guidance only**. The methodology is:

* **Not a deterministic trading algorithm**
* **Not a required implementation sequence**
* **Not a requirement to expose or persist private reasoning traces**
* **Not a chain-of-thought requirement**

No arbitrary mathematical rules, multipliers, thresholds, or trading heuristics are introduced. The objective is structured reasoning, not signal generation.

---

## 11. LLM Interaction

The agent interacts with the LLM through the `LLMProvider` abstraction:

```text
Agent
   ↓
LLMProvider (FakeLLMProvider | OpenRouterProvider)
   ↓
Structured candidate output
```

The LLM MUST NOT:

* Write directly to PostgreSQL
* Modify system state
* Publish WebSocket events
* Invent provenance
* Decide analysis success/failure
* Execute external actions

The agent implementation MUST work with both `FakeLLMProvider` (deterministic test output) and `OpenRouterProvider` (production) without code changes.

---

## 12. Prompt Principles

The Market Intelligence Agent prompt MUST specify:

* **Input context**: Exact structure of `MarketSnapshot` and `DataSource` received
* **Task**: Produce qualitative interpretation per the analytical scope (§8)
* **Output contract**: Exact candidate output shape defined in §7.1, containing only the interpretive fields required to construct `MarketAnalysis`
* **Out of scope**: Trading instructions, BUY/SELL, orders, risk, execution, broker actions
* **Grounding requirement**: All assertions must trace to supplied snapshot data
* **Uncertainty declaration**: Use `unclear` and `uncertainties` when evidence is insufficient
* **Forbidden output**: No trading instructions, entry/exit levels, position sizing, broker/execution instructions

This section defines requirements for the future production prompt. The prompt itself is not included in this specification.

---

## 13. Forbidden Output Behavior

The following in agent output MUST cause validation failure (`ANALYSIS_VALIDATION_ERROR`):

* BUY/SELL instructions (explicit or implicit)
* Entry/exit price instructions
* Stop-loss / take-profit instructions
* Position sizing recommendations
* Broker or order instructions
* Execution instructions
* Fabricated market values (prices, bars, volume not in snapshot)
* Unsupported external claims (news, events, macro catalysts not in input)
* Trading signal language ("go long", "short the market", "enter at", "target")

The validation approach is contract-based: the application layer validates the output structure, enums, field constraints, and qualitative safety (descriptions must not contain trading instructions). A brittle string blacklist is not the primary mechanism; the contract schema and qualitative validation are.

---

## 14. Uncertainty Behavior

When the agent encounters insufficient or ambiguous evidence:

| Condition | Agent Behavior |
|-----------|----------------|
| Insufficient sample | `unclear` for trend/volatility; populate `uncertainties` |
| Ambiguous structure | `unclear` for trend direction/strength; describe ambiguity in `uncertainties` |
| Volatility context unclear | `VolatilityContext.regime = unclear`; describe in `uncertainties` |
| Key levels not well-defined | Empty `key_levels`; note in `uncertainties` if relevant |
| Evidence does not support conclusion | `unclear` + explicit `uncertainties` entry |

The agent MUST NOT convert legitimate analytical uncertainty into a system error. `unclear` is a valid enum value, not a failure.

---

## 15. Failure Behavior

### Analytical Uncertainty (Valid Analysis)
* `TrendContext.direction = unclear`
* `VolatilityContext.regime = unclear`
* `uncertainties` populated
* Result: `status = completed` with valid `MarketAnalysis`

### System Failures (Invalid Analysis)
| Failure | Error Code | Handling |
|---------|------------|----------|
| LLM unavailable / timeout | `LLM_ERROR` | `analysis.failed`, no `MarketAnalysis` |
| Malformed LLM output (schema violation) | `ANALYSIS_VALIDATION_ERROR` | `analysis.failed`, no `MarketAnalysis` |
| Forbidden content in LLM output | `ANALYSIS_VALIDATION_ERROR` | `analysis.failed`, no `MarketAnalysis` |
| Market data provider unavailable | `PROVIDER_ERROR` / `CONFIGURATION_ERROR` | Fails before agent invocation |
| Provider returns invalid data | `PROVIDER_ERROR` | Fails before agent invocation |
| Persistence failure | `PERSISTENCE_ERROR` | Handled by the Application Layer per architecture/data contracts |

Error codes per `DATA_CONTRACTS.md` §13.

The agent does not:
* persist failure state;
* retry persistence;
* control lifecycle recovery;
* decide how persistence outages are handled.

---

## 16. Provenance Behavior

The agent MUST maintain awareness of the data origin but MUST NOT invent or modify provenance.

| Provenance Element | Owner |
|--------------------|-------|
| `MarketSnapshot.data_source` | Backend (provider layer) |
| `MarketAnalysis.data_sources` | Application layer (constructed from snapshot) |
| `ModelMetadata` | Application layer (records LLM provider, model, prompt, timestamp) |

The agent receives `MarketSnapshot.data_source` as part of the input. The application layer ensures `MarketAnalysis.data_sources` includes at least the snapshot's `DataSource` per `DATA_CONTRACTS.md` §7.

---

## 17. Determinism and Testing

The agent MUST be testable without a live LLM.

**Test baseline**: `FakeLLMProvider` + deterministic fixture `MarketSnapshot`

**Required test coverage**:
* Valid output → produces candidate analytical/interpretive content passing application-layer validation
* Malformed output (missing fields, wrong types) → caught by validation
* Forbidden output (trading instructions) → caught by qualitative validation → `ANALYSIS_VALIDATION_ERROR`
* Uncertainty handling → `unclear` enums + `uncertainties` populated
* Provider failure (upstream) → `PROVIDER_ERROR` before agent
* LLM failure (`FakeLLMProvider` simulating error) → `LLM_ERROR`
* Reproducibility: same fixture + same request + same deterministic `FakeLLMProvider` configuration must produce the same candidate output structure. Reproducibility is guaranteed only for the deterministic test baseline; external `OpenRouterProvider` calls are not required to be reproducible.

Automated tests MUST NOT depend on real OpenRouter calls.

---

## 18. Observability and Execution Boundaries

The agent MAY log (structured, correlated by `analysis_id`):

* Invocation start/end
* Input snapshot summary (symbol, timeframe, data_source.mode)
* LLM provider used

The agent MUST NEVER log:

* API keys, credentials, authentication headers
* Private reasoning traces / full prompts
* Unnecessary secrets

The Application/execution layer MAY log:

* Output validation result (pass/fail with error code)
* Validation error code
* Lifecycle transition if appropriate

No new observability platform is introduced in MVP-0.

---

## 19. Agent Lifecycle

The agent participates in the execution flow but does not control it:

```text
pending
   ↓
running
   ↓
Application invokes agent with validated MarketSnapshot
   ↓
Agent → LLMProvider → candidate structured output
   ↓
Application validates candidate output
   ↓
Validation passes → completed (MarketAnalysis persisted)
Validation fails  → failed (ANALYSIS_VALIDATION_ERROR)
```

The `Application` layer (use case `CreateMarketAnalysis`) controls the lifecycle. The agent is side-effect-free with respect to application state, persistence and lifecycle control. It transforms validated input through the configured `LLMProvider` into candidate structured output.

---

## 20. Acceptance Criteria

`AGENT_SPEC.md` is complete when:

* [ ] Agent identity is explicit (name, identifier, department, capability)
* [ ] Responsibilities are explicit and limited to qualitative interpretation
* [ ] Non-responsibilities explicitly exclude all trading/execution/risk concerns
* [ ] Input contract is compatible with `DATA_CONTRACTS.md` (`MarketSnapshot`, `DataSource`, `AnalysisRequest`)
* [ ] Output contract defines the exact candidate output shape and its mapping to `MarketAnalysis` from `DATA_CONTRACTS.md` §9
* [ ] Grounding rules require traceability to supplied snapshot
* [ ] Uncertainty behavior defines `unclear` usage and `uncertainties` field
* [ ] Forbidden output behavior maps to `ANALYSIS_VALIDATION_ERROR`
* [ ] Failure behavior distinguishes analytical uncertainty from system failures using `DATA_CONTRACTS.md` error codes
* [ ] LLM boundaries defined via `LLMProvider` abstraction (fake + production)
* [ ] Deterministic testing specified with `FakeLLMProvider` and fixture data
* [ ] No trading execution behavior introduced (no BUY/SELL, orders, risk, positions, broker, strategy, multi-agent)

---

## Appendix: Document Hierarchy Compliance

This document respects the source-of-truth hierarchy:

```text
MVP_SCOPE.md
    ↓
ARCHITECTURE.md
    ↓
DATA_CONTRACTS.md
    ↓
AGENT_SPEC.md
```

All contracts, enums, error codes, and data structures referenced herein are defined in the upstream documents. This specification adds no new fields, types, or contracts.