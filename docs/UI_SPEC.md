# Agencia Automatizada MVP — UI/UX Specification

**Status:** Proposed for MVP-0
**Product:** Agencia Automatizada
**Department:** Trading
**Initial capability:** XAU/USD Market Analysis
**Primary user:** Project owner
**Repository:** `Agencia-automatizada-MVP`

---

## 1. Purpose

This document defines the user experience, visual responsibilities, interaction behavior, frontend state presentation and information architecture of the MVP-0 frontend.

It translates the approved product scope (`MVP_SCOPE.md`), architecture (`ARCHITECTURE.md`), data contracts (`DATA_CONTRACTS.md`) and agent specification (`AGENT_SPEC.md`) into a definition of WHAT the interface must do and HOW the user should experience it.

This document is **subordinate** to the upstream documents. It must not contradict them, must not redefine their contracts, and must not invent backend behavior that they do not specify. Where something is not specified upstream, this document defines only the minimum UI behavior necessary, and never in a way that creates a new backend contract, endpoint, schema or domain model.

This document is **not** a frontend implementation guide. It does not contain React or Phaser source code, CSS implementation, arbitrary package choices, or backend/database implementation. It defines responsibilities, states, content and behavior. Implementation details belong to the later development specifications and code.

MVP-0 is an **analysis product**, not a trading execution product. Everything in this document is constrained by that boundary: the interface presents qualitative market analysis, its provenance, its uncertainties and its lifecycle — never trading actions.

---

## 2. MVP-0 UX Principles

The following principles govern every UI decision in MVP-0. When a concrete rule elsewhere in this document is ambiguous, these principles decide.

### 2.1 Backend authority

The backend is the single source of truth for analysis state, market data, timestamps, analysis results, provider provenance, model metadata and errors. The frontend renders backend state; it never fabricates, overrides or derives authoritative values. UI animation, timers or local computation can never establish that an analysis succeeded, failed, or produced any value.

### 2.2 Explicit system state

At every moment the user can answer: "What is the system doing right now?" The current lifecycle state (`idle`, `submitting`, `pending`, `running`, `completed`, `failed`) is always visible as text, in conventional UI — never communicated through the Pixel Art scene alone.

### 2.3 No fabricated success

The UI prefers an explicit failure over a convincing fake. It never fabricates:

* agent activity or autonomy;
* market data or prices;
* analysis results or analysis content;
* timestamps;
* successful execution or completion;
* progress that implies more precision than the backend provides.

An animation finishing is never interpreted as an analysis completing. Completion comes only from backend state.

### 2.4 Analytical neutrality

The interface presents qualitative analysis as analysis. Trend direction, strength, volatility regime and key levels are descriptive observations. The UI never converts them into BUY/SELL recommendations, entries, exits, targets, position sizes or any trading instruction, and never uses trade-connotative styling (order-button colors, "execute" language, profit framing) around analytical content.

### 2.5 Provenance visibility

The user can always identify where an analysis came from: fixture or live mode, provider identity, source observation time, retrieval time, and model metadata. The fixture/live distinction is visible everywhere the data is shown and is never collapsed, hidden or silently switched.

### 2.6 Uncertainty visibility

`unclear` is a valid analytical result. Uncertainties are first-class, visible content — not warnings to be suppressed, collapsed away by default, or styled as system errors. An analytical ambiguity must never be rendered as a system failure, and a system failure must never be rendered as an analytical ambiguity.

### 2.7 Separation of environment and information panels

The Pixel Art Trading Desk (Phaser) and the conventional React information UI are two distinct visual registers with distinct responsibilities. The environment provides identity, spatial presence and visual state. The panels provide structured, readable, accessible information. Neither substitutes for the other.

### 2.8 Professional usability

The product should feel like a serious analytical tool: readable typography, stable layout, predictable interactions, plain language, and no gratuitous motion or noise. The Pixel Art identity coexists with professional information design.

### 2.9 Minimal MVP scope

The UI serves exactly one department (Trading), one agent (Market Intelligence Agent) and one capability (XAU/USD analysis). No navigation, content or affordance is added for future departments, future agents or postponed capabilities.
---

## 3. Information Architecture

The MVP-0 interface is organized into the following major areas:

```text
Application Shell
├── Trading Department Header
├── Trading Desk / Phaser Environment
├── Agent Interaction Area
├── Analysis Controls
├── Analysis Status
├── Analysis Result Panel
└── Analysis History
```

| Area | Responsibility |
|------|----------------|
| **Application Shell** | Page structure, department identity, capability identification, global status area. Owns layout and responsive behavior. |
| **Trading Department Header** | Persistent identification of the department ("Trading"), the active capability ("XAU/USD Market Analysis") and the general status area. |
| **Trading Desk / Phaser Environment** | Visual Pixel Art representation of the Trading department: the desk scene and the Market Intelligence Agent as a visible, interactive entity. A visualization layer only. |
| **Agent Interaction Area** | The point of interaction with the agent (selecting the agent in the scene or its accessible equivalent) that opens/focuses the analysis workflow, plus the agent's identity and state as text. |
| **Analysis Controls** | Input collection: instrument (fixed XAU/USD), timeframe, data mode, and the primary "Analyze XAU/USD" action. |
| **Analysis Status** | Explicit, textual presentation of the current lifecycle state of the active analysis, including failure and transport (WebSocket) status. |
| **Analysis Result Panel** | Structured presentation of a `MarketAnalysis`: snapshot, trend, volatility, key levels, observations, uncertainties, provenance, model metadata. |
| **Analysis History** | Backend-backed list of previous analyses (`AnalysisSummary`) with selection and retrieval of full historical analyses. |

The Trading Desk environment is the *identity* layer; the panels are the *information* layer. All authoritative information (status, results, provenance, errors, history) lives in the conventional UI.

---

## 4. Application Shell

### 4.1 Page structure

The shell is a single page for MVP-0:

* a persistent **header**;
* the **Trading Desk environment** (Phaser canvas) as the visual anchor;
* an **operations column/section** containing the agent interaction entry point, analysis controls, analysis status, result panel and history.

The exact spatial arrangement (e.g., environment left / panels right) is an implementation decision, but the two registers — environment and information — must remain visually and semantically separated.

### 4.2 Navigation

MVP-0 has no multi-page or multi-department navigation. There is exactly one department and one capability. The shell must not render navigation placeholders, disabled menu entries or "coming soon" items for future departments or agents.

### 4.3 Department and capability identification

The header permanently identifies:

* the department: **Trading**;
* the current capability: **XAU/USD Market Analysis**;
* the product identity: **Agencia Automatizada**.

This gives the user a stable answer to "where am I and what can I do here".

### 4.4 General status area

The header (or an adjacent persistent strip) contains a general status area that may present:

* the current active-analysis lifecycle label (see §8);
* the real-time channel transport status (connected / disconnected), presented explicitly as a notification-channel status — never as analysis state;
* the data-mode context of the currently displayed analysis (`fixture` / `live`), consistent with §12.

All status entries are textual (with optional icons). The status area never fabricates backend health: "connected" describes the WebSocket transport only, and absence of a live analysis must be shown as such, not as a generic "all systems operational" claim.

### 4.5 Responsive behavior

The shell adapts at defined breakpoints (see §17) without changing the information architecture: the same areas persist, reordered and resized. No content or function is desktop-exclusive.
---

## 5. Trading Desk / Pixel Art Environment

The Trading Desk is the visual representation of the Trading department: a Pixel Art environment rendered with Phaser, embedded in the React application.

### 5.1 Phaser responsibilities

* Render the Trading Desk environment (the "office" of the Trading department).
* Render the Market Intelligence Agent as a visible sprite/entity within the scene.
* Animate the agent and scene according to backend state supplied by the application.
* Provide an interaction point on the agent (select/tap) that opens or focuses the analysis workflow.
* Provide visual feedback for lifecycle transitions (see §8), derived from application state.

### 5.2 Agent visual representation

The Market Intelligence Agent appears as a distinct, identifiable entity at a fixed, discoverable position in the scene. Its identity is always reinforced outside the scene: the agent's name and current state are also shown as text in the Agent Interaction Area (§6). The Pixel Art representation must never be the only place the agent's identity or state is communicated.

### 5.3 Interaction point

Selecting the agent in the scene (mouse, touch or keyboard via the scene's accessible equivalent — a conventional button that performs the same action) opens or focuses the analysis workflow: it brings the analysis controls into view/focus. If a previously retrieved result or history selection exists, interaction also brings the result panel into view. Selecting the agent must never itself start an analysis; the analysis starts only through the explicit primary action (§7).

### 5.4 Visual state representation

The scene visualizes the states the application received from the backend:

| Backend/application state | Scene presentation |
|---|---|
| `idle` (frontend-only, no active request) | Agent in a neutral idle pose/loop; no activity implied. |
| `submitting` (frontend-only, request in flight, no backend confirmation yet) | Neutral "waiting" presentation. The scene must NOT show the agent working, because execution has not been confirmed. |
| `pending` (backend) | "Accepted / waiting to run" presentation, still without work-in-progress motion. |
| `running` (backend, via `analysis.started` or GET) | Agent working animation. |
| `completed` (backend, confirmed) | Success cue (e.g., brief completion animation), then return to idle. |
| `failed` (backend, confirmed) | Neutral error cue (e.g., alert icon / muted visual), never a crash masquerading as idle success. |

On WebSocket disconnect the scene holds the last backend-confirmed state unchanged. It must not improvise.

### 5.5 Environment boundaries

The scene is a visualization layer, not a simulation. It may animate:

* ambient, decorative loops that carry no information (lighting, subtle scenery motion);
* the agent's state animations strictly bound to backend state as in §5.4;
* interaction feedback (hover/selection highlight on the agent).

The scene must NOT invent:

* random or autonomous agent activity (wandering, "thinking", self-initiated work) when no backend execution is running;
* fake market activity — no ticker tapes, price tickers, moving charts, news feeds or any number that looks like market data;
* fake analysis generation (fake typing of results, fake progress percentages, fake "model output");
* fake status progression — no timers or animation completion that imply the analysis advanced;
* any state the application did not receive from the backend.

There is no scenario in which the scene being "wrong about the world" is acceptable: if the scene cannot represent a state truthfully, it represents nothing rather than inventing.

---

## 6. Market Intelligence Agent Presentation

### 6.1 Identity

The single MVP-0 agent is presented with its upstream identity (`AGENT_SPEC.md` §2):

* **Name:** Market Intelligence Agent
* **Identifier:** `trading_market_intelligence_agent` (may be shown as secondary/technical detail)
* **Department:** Trading
* **Capability:** Structured qualitative market analysis of XAU/USD

The agent's presentation must make its nature unmistakable: it *analyzes* markets. It is never presented as a trader, executor, signal provider, advisor or profitability engine. Descriptive copy may say, for example, that the agent "produces a structured qualitative analysis of XAU/USD market conditions" — and must not promise trades, signals, profits or decisions.

### 6.2 Available interaction

Exactly one interaction is offered for MVP-0: requesting a qualitative XAU/USD market analysis through the analysis workflow (§7). The agent is always available for interaction (there is no user-togglable on/off duty cycle in MVP-0).

### 6.3 Active/inactive state

The agent's visible state reflects the lifecycle of the active analysis (per §5.4): neutral when idle or awaiting backend confirmation, working when the backend reports `running`, success/failure cues on confirmed terminal states. The UI must not display invented intermediate agent moods, activities or "agent is thinking on its own" states.

### 6.4 Relationship between agent interaction and the analysis workflow

Selecting the agent (in-scene or via its accessible equivalent) opens/focuses the analysis workflow: the controls, status and result areas. This creates a single, discoverable path:

```text
See the agent  →  select it  →  analysis controls  →  "Analyze XAU/USD"
```

The workflow that opens is the same regardless of entry point; the scene is never a separate logic path.
---

## 7. Analysis Controls

The controls collect exactly the fields of `AnalysisRequest` (`DATA_CONTRACTS.md` §5): `symbol`, `timeframe`, `data_mode`. No additional request parameters are offered.

### 7.1 Symbol

The instrument is fixed for MVP-0: **XAU/USD** (canonical value `XAUUSD`).

* Presented as a fixed, labeled value — not a free-text input and not a searchable symbol picker.
* The UI displays the human-readable form "XAU/USD"; the value submitted is `XAUUSD`.
* No other symbols are offered or accepted.

### 7.2 Timeframe

A single-select control listing exactly the contract enum (`DATA_CONTRACTS.md` §4.2):

```text
1m · 5m · 15m · 1h · 4h · 1d
```

* The UI lists exactly the contract enum: `1m`, `5m`, `15m`, `1h`, `4h`, `1d`. No invented timeframes, presets, aliases or subsets.
* Provider capability (which timeframes a given provider/data mode actually supports) is validated by the backend, not by the UI.
* If a selected timeframe is unsupported, the backend's error is surfaced explicitly (§15). The UI never silently substitutes another timeframe.

### 7.3 Data mode

An explicit, always-visible two-option control:

```text
fixture  — deterministic test data
live     — real market-data provider
```

Rules:

* The options are labeled with the contract values; "fixture" is always identifiable as test data, never as "demo", "sample" or "simulated live".
* The selected mode is submitted verbatim. The UI must never silently switch `live` → `fixture` (or vice versa), and must never disable the `live` option "temporarily" while quietly running fixture analyses.
* Availability is a backend concern: there is no capability-discovery endpoint in MVP-0, so the UI does not pre-validate availability client-side. If `live` is requested and unavailable or unconfigured, the backend returns an explicit `PROVIDER_ERROR`/`CONFIGURATION_ERROR`, and the UI represents that as an unavailable/error state (§15) — never as a fixture analysis.
* The default selection is `fixture`, matching MVP-0's initially supported mode. The default is visible and changeable, not a hidden substitution.

### 7.4 Primary action

One primary action, labeled:

```text
Analyze XAU/USD
```

* It requests a qualitative market analysis. Supporting copy near the button may clarify: "Requests a structured qualitative market analysis."
* The label and its treatment must never be confusable with a trade instruction: no "Execute", "Trade", "Buy", "Sell", "Open position" wording, icons or styling.
* While a request is in flight, the button is disabled to prevent duplicate submissions, and the in-flight state is shown in the status area (§8).
* Keyboard activation (Enter/Space on a semantic button) must work.

### 7.5 Input persistence (optional)

The UI may remember the user's last timeframe/data-mode selection as a local convenience. Such preferences are presentation-only; they never reconstruct previous analyses or pretend to be history (§14).

---

## 8. Analysis Lifecycle UX

### 8.1 States

The UI distinguishes backend lifecycle states from frontend-only presentation states:

| State | Origin | Meaning |
|---|---|---|
| `idle` | frontend-only | No active request and nothing being viewed as active. |
| `submitting` | frontend-only | Request sent, authoritative response not yet received. |
| `pending` | backend | AnalysisRun created; execution not yet started. |
| `running` | backend | Execution in progress. |
| `completed` | backend | Analysis persisted successfully. |
| `failed` | backend | Execution failed; error persisted. |

`idle` and `submitting` are presentation states. They are never shown as if they were backend states, never sent to the API, and never persisted. Backend states are displayed with their contract values (`pending`, `running`, `completed`, `failed`) so the UI always speaks the backend's language.

Because MVP-0 execution is synchronous, the authoritative answer to a request is the final HTTP response of `POST /api/v1/market-analyses` (which returns only after completion or failure). `pending`/`running` are observable in the meantime only through WebSocket notifications (§9) or a GET reconciliation; if neither is available, the UI remains in `submitting` and says exactly that.

### 8.2 What the user sees, per phase

* **Request submission (frontend `submitting`):** Controls are disabled (including the primary action) to prevent duplicates. Status area shows a text label such as "Request submitted — waiting for backend confirmation" with an indeterminate indicator. The agent visual stays neutral (§5.4). No progress percentage, no countdown, no fabricated intermediate content.
* **`pending` (backend):** Status label "Analysis accepted — pending" when known (via notification or GET). Indeterminate indicator. Controls remain disabled.
* **`running` (backend):** Status label "Analysis running". Indeterminate indicator. Agent working animation. Controls remain disabled. Progress bars with percentages are not shown — the backend does not provide progress granularity, and the UI must not invent it.
* **`completed` (backend):** The POST response (or GET reconciliation) confirms completion and provides the `analysis_id`; the UI then retrieves the authoritative result via `GET /api/v1/market-analyses/{analysis_id}` and renders the result panel (§10). Status label "Analysis completed". Result content is rendered only from the retrieved `MarketAnalysis` — never from an event payload, cache guess or animation.
* **`failed` (backend):** Status label "Analysis failed" with the safe error information from the authoritative failure state (§15). The failure is explicit and prominent; controls become enabled again so the user can retry. A failed analysis is never rendered as, or near, a successful result.
* **Unknown outcome (network failure during submission):** If the HTTP response is lost before the client receives an `analysis_id` (timeout/disconnect), the UI must not guess and cannot assume it knows which run to look up. It shows an explicit "outcome unknown" state and may refresh the history list (§14) so the user can identify the corresponding persisted run. Once the correct `analysis_id` is known, the UI retrieves the authoritative state via GET. The UI never converts an unknown outcome into success or failure on its own.

The UI must never assume `animation finished = analysis completed`. Completion and failure come only from backend state.
---

## 9. WebSocket UX Behavior

The UI maintains the WebSocket connection (`/api/v1/ws`) while the Trading Desk is open and uses `analysis.started`, `analysis.completed` and `analysis.failed` **only as notifications**. They never establish authoritative state by themselves.

### 9.1 Event handling

Each event arrives in the `WebSocketEvent` envelope, which carries `event_id`, `event_type`, `occurred_at`, `analysis_id` and `payload` (`DATA_CONTRACTS.md` §12). The `payload` contains only lifecycle notification content — the `status`, and for `analysis.failed` a safe, non-authoritative error summary — never analysis content. The UI applies an event only when the envelope's `analysis_id` refers to the currently active analysis view; events for other analyses must not mutate the active view (they may mark the history list as stale for refresh, since the list endpoint is a contract).

| Event | Visual update |
|---|---|
| `analysis.started` | Status area → "Analysis running" (backend `running`). Agent visual → working. |
| `analysis.completed` | Status area → "Analysis completed (backend notification)". The UI immediately retrieves the authoritative result via `GET /api/v1/market-analyses/{analysis_id}` and renders the result panel from that response only. The event payload (`{"status": "completed"}`) contains no analysis content and is never rendered as one. |
| `analysis.failed` | Status area → "Analysis failed". The payload may contain a safe, non-authoritative error summary for immediate feedback; the UI then retrieves the authoritative failure state via `GET /api/v1/market-analyses/{analysis_id}` and displays that. |

If a notification conflicts with the authoritative HTTP state (POST response or GET), the HTTP state wins and the UI reconciles to it.

### 9.2 Disconnect behavior

On WebSocket disconnect:

* the general status area shows the transport as disconnected (text label, e.g., "Real-time updates disconnected");
* the last backend-confirmed state remains displayed, unchanged;
* the scene holds its last confirmed visual state (§5.4);
* the UI does not fabricate progress, completion or failure during the outage.

A disconnect never invalidates a synchronous POST in flight: its HTTP response is unaffected and remains the authoritative outcome.

### 9.3 Reconciliation through GET

HTTP GET is the authoritative reconciliation path. The UI re-fetches via GET when:

* `analysis.completed` or `analysis.failed` is received (to load the authoritative result/error);
* the WebSocket reconnects (re-fetch the active analysis, if one is active, to replace any stale presentation state);
* the outcome of a submission is unknown (§8.2 — via history discovery, then GET by `analysis_id`);
* the user reopens or selects a historical analysis (§14).

### 9.4 Recovery after reconnect

After reconnecting, the UI:

1. restores the transport status label to connected;
2. re-fetches the active analysis via `GET /api/v1/market-analyses/{analysis_id}` (if one is active) and reconciles the status/result presentation to the persisted state;
3. may refresh the history list so it reflects anything that happened during the outage.

Reconnection attempts are automatic while the desk is open; specific retry timings are an implementation decision.

---

## 10. Analysis Result Panel

The result panel presents a successful `MarketAnalysis` exactly as defined by `DATA_CONTRACTS.md` §9. It renders the contract fields; it invents no new fields and hides no important provenance.

### 10.1 Required presentation areas

* **Instrument and parameters:** `symbol` shown as "XAU/USD" (canonical `XAUUSD`), `timeframe`, plus the `analysis_id` and `schema_version` as secondary identification.
* **Final analysis timestamp:** `MarketAnalysis.timestamp_utc`, explicitly labeled as the analysis finalization time (UTC) — the moment the backend finalized the validated result. This is a different concept from the snapshot's market observation time (§11).
* **Market snapshot:** per §11.
* **Trend context:** per §10.2.
* **Volatility context:** per §10.3.
* **Key levels:** per §10.4.
* **Market observations:** per §10.5.
* **Uncertainties:** per §10.6.
* **Data sources:** per §12.
* **Model metadata:** per §13.

### 10.2 Trend presentation

`TrendContext` is presented as three elements: `direction`, `strength`, `description`.

* Direction values — `up`, `down`, `sideways`, `unclear` — and strength values — `weak`, `moderate`, `strong`, `unclear` — are shown verbatim as analytical descriptions, with their plain-language reading where helpful (e.g., "up").
* The UI must not convert them into BUY/SELL recommendations, bias labels ("bullish — consider buying") or action prompts.
* Color coding, if any, is secondary; the textual value is always present (§18). Avoid trade-connotative styling (e.g., profit-green "up" call-to-action treatment).
* `unclear` is rendered as a neutral-informational state (§2.6), not as an error or a degraded result.

### 10.3 Volatility presentation

`VolatilityContext` shows `regime` (`low`, `moderate`, `high`, `unclear`) verbatim plus its `description`. No unsupported deterministic trading interpretations are added (no "expect a breakout", "good conditions for scalping", etc.).

### 10.4 Key levels

Each `KeyLevel` is presented with its `type` (`support` | `resistance`), `price` (as returned) and `description`, in a clear list or table.

* The section makes visually and textually clear that these are analytical observations: e.g., a persistent caption such as "Analytical observations from the analyzed data — not guaranteed levels and not entry/exit instructions."
* `support` and `resistance` receive neutral, symmetric visual treatment: neither type is color-coded or styled to imply an action (no green/red buy/sell connotation), and the type is always shown textually.
* Levels are never styled as actionable targets, and no "distance to level" trading framing is fabricated.

### 10.5 Market observations

`market_observations` is presented as a concise list of qualitative statements, in the order returned. The UI does not embellish, merge, or reinterpret them into advice.

### 10.6 Uncertainties

`uncertainties` is a visible, first-class section — rendered at the same level of prominence as observations, not collapsed away by default, not de-emphasized into a footnote.

* Each uncertainty is listed verbatim.
* If the array is empty (valid per contract), the panel states "No material uncertainties recorded." — the section itself is still present.
* `unclear` values in trend/volatility are valid analysis and must NOT be rendered as errors (§15 draws this boundary explicitly).
---

## 11. Market Data and Snapshot Presentation

The `MarketSnapshot` embedded in the analysis may be presented with the information it actually contains:

* **bid / ask / mid** — the validated prices as returned (decimal strings rendered without altering their value);
* **relevant bar information** — the snapshot's bars may be rendered as raw data: a compact table (timestamp, open, high, low, close, volume) and/or a simple visual representation of the raw values;
* **market observation timestamp** — `MarketSnapshot.as_of_utc`, explicitly labeled as the time the market data represents (the observation time);
* **data source** — the snapshot's `DataSource` (§12).

Presentation rules:

* The snapshot is *input data used for the analysis*, presented as such. Raw bar rendering is data display, not analysis: the UI adds no computed indicators, derived metrics or technical-analysis overlays of its own in MVP-0.
* Volume may be zero; the UI renders it as returned and does not treat zero volume as a display error.
* Prices are displayed with their decimal precision as returned; display formatting must not change the value.

### 11.1 Timestamp distinctions

The UI must keep these concepts visually and verbally distinct; they are never merged into a single "time" field:

| Field | Meaning | Label style |
|---|---|---|
| `MarketSnapshot.as_of_utc` | The market-data observation time | "Market data as of (UTC)" |
| `MarketAnalysis.timestamp_utc` | When the backend finalized the successful analysis | "Analysis finalized (UTC)" |
| `DataSource.source_as_of_utc` | The source data timestamp | "Source data as of (UTC)" |
| `DataSource.retrieved_at_utc` | When the provider returned the data | "Data retrieved (UTC)" |
| `ModelMetadata.generated_at_utc` | When the model generated the interpretation | "Interpretation generated (UTC)" |

All timestamps are displayed as UTC (with a visible "UTC" designation). If a local-time rendering is added for readability, it is secondary and clearly labeled; the UTC value remains the authoritative displayed value.

---

## 12. Provenance Presentation

Provenance is always visible for a displayed analysis. The user must be able to identify, without leaving the panel:

### 12.1 Fixture/live distinction

* The data source `mode` — `fixture` or `live` — is shown wherever an analysis or snapshot is displayed (result panel, history entries, and the general status area for the active analysis).
* `fixture` is unmistakably marked as test data (e.g., a badge reading "Fixture (test data)"). It is never styled to look like live market data, and never labeled with softer synonyms that obscure its nature.
* The interface must never present fixture data as live. Any view that cannot determine the mode shows that it is undetermined rather than guessing.

### 12.2 Provider provenance

For each `DataSource`:

* `mode`, `provider_name`, `provider_version`;
* `source_as_of_utc` (source observation time) and `retrieved_at_utc` (retrieval time), kept distinct per §11.1.

The UI shows exactly what the backend provides; it does not infer provider capabilities, locations or quality from names.

### 12.3 Data-mode labeling of analyses

When a displayed analysis was requested as `live`, the UI presents it as live only if the analysis's effective provenance (`data_sources[].mode`) is `live`. In MVP-0 the backend never silently substitutes fixture data for a live request — it fails explicitly (§7.3, §15) — so a successfully completed live-mode analysis carries live provenance. If requested and effective modes ever disagreed, the UI would display the effective provenance from the analysis itself and surface the discrepancy rather than resolve it silently.

---

## 13. Model Metadata Presentation

The result panel presents `ModelMetadata`:

* `provider` (e.g., `openrouter`);
* `model` (the configured runtime model identifier);
* `prompt_version` (e.g., `market-intelligence-v1`);
* `generated_at_utc` (labeled per §11.1).

Rules:

* Metadata is presented as factual provenance of the interpretation, typically in a "Model" / "Metadata" section of the result panel.
* The UI never exposes private reasoning traces, hidden chain-of-thought, full prompts, or internal diagnostics.
* The UI never exposes API keys, credentials or any secret material. (The backend never sends them — `ARCHITECTURE.md` §28 — and the UI does not attempt to display anything of the kind.)
* The presentation is neutral: the model is the instrument that produced the interpretation, not an authority, oracle or trader.
---

## 14. Analysis History

MVP-0 includes minimal, backend-backed history. The history view uses only the fields supplied by `AnalysisSummary` (`DATA_CONTRACTS.md` §14.8):

* `analysis_id`
* `symbol`
* `timeframe`
* `status`
* `timestamp_utc`
* `data_source_mode`

### 14.1 List presentation

* Each entry shows the six fields above. `symbol` may be displayed as "XAU/USD"; `status` is shown verbatim (`pending`, `running`, `completed`, `failed`); `data_source_mode` is shown as `fixture`/`live` with the same fixture-is-test-data marking as §12.
* `timestamp_utc` in a summary equals the run's creation time (`AnalysisRun.created_at_utc`). It is labeled as the request/creation time (e.g., "Requested (UTC)") and is distinct from the analysis finalization time shown in the result panel (§11.1).
* The list is presented in the order returned by the backend. The expected MVP-0 ordering is by `timestamp_utc`, most recent first; the UI does not re-sort with local data or fabricate entries.

### 14.2 Data source

Historical analyses come exclusively from backend persistence (`GET /api/v1/market-analyses`). The frontend never reconstructs history from local memory, session state or localStorage. A page reload must not lose history, and a history entry must remain retrievable after reload.

### 14.3 Pagination

The list endpoint uses server-side pagination with `limit` / `offset` / `has_more`. The UI:

* requests an initial page with a frontend-chosen `limit`;
* offers a "load more" action that increments `offset` while `has_more` is true;
* introduces no pagination behavior that contradicts the contract (no client-side "fetch everything", no invented cursors, no filtering the API does not provide).

### 14.4 Selecting a historical analysis

Selecting an entry triggers `GET /api/v1/market-analyses/{analysis_id}` and renders the retrieved analysis in the result panel, clearly marked as a historical/retrieved analysis. Completed entries render the full result panel (§10); `failed` entries render the persisted failure state (§15); `pending`/`running` entries render their lifecycle state as persisted.

### 14.5 Loading and error states

* While a page of history is being fetched, the history area shows an indeterminate loading state (no invented rows).
* If the history request fails, the history area shows an explicit error state with a retry action (§15). Existing already-loaded entries remain visible and are not silently discarded or replaced with fake data.

### 14.6 Empty history state

When no analyses exist, the history area shows an explicit empty state (e.g., "No analyses yet — request your first XAU/USD analysis.") rather than a blank region.

### 14.7 Refresh

The UI may refresh the history list after a new analysis reaches a terminal state (§9.1) and after reconnection (§9.4). Refresh always goes through the list endpoint.

---

## 15. Error UX

The UI prefers explicit failure over fake success. All errors are presented from the backend's safe error contract (`DATA_CONTRACTS.md` §13): `code`, safe `message`, optional `details`, plus `meta.request_id` where available for correlation.

### 15.1 Error code presentation

| Code | User-facing meaning | Presentation notes |
|---|---|---|
| `VALIDATION_ERROR` | The request was not valid (e.g., unsupported timeframe). | Shown near the analysis controls; when `details` identifies a field, the specific control is indicated. Controls remain available for correction. |
| `CONFIGURATION_ERROR` | The system is not configured for the requested operation (e.g., live mode not configured). | Explicit configuration-failure message. Never softened into a mode switch or fallback (§7.3). |
| `PROVIDER_ERROR` | Market-data provider failed or is unavailable. | "Market data unavailable" style message; the analysis did not run. |
| `LLM_ERROR` | The analysis engine (LLM) is unavailable or failed. | "Analysis engine unavailable" style message. |
| `ANALYSIS_VALIDATION_ERROR` | The produced analysis did not pass validation. | Presented as an internal validation failure of this run; no analysis result exists for it. |
| `PERSISTENCE_ERROR` | The result could not be persisted successfully. | Presented as an explicit persistence failure. The UI must not claim that the failed state was persisted unless the authoritative backend state can be confirmed through GET. |
| `NOT_FOUND` | The requested analysis does not exist. | Shown when retrieving by `analysis_id` (e.g., stale history entry); history refresh is offered. |
| `UNEXPECTED_ERROR` | Unexpected internal failure. | Safe generic failure message with the error code; no internal detail. |

The lifecycle status area shows the run as `failed` for run-level failures; controls become enabled again for retry.

### 15.2 Failure vs analytical uncertainty

An explicit boundary is maintained:

* **System failure** (this section): the analysis did not complete. Distinct visual treatment (error styling, error icon, text like "Analysis failed").
* **Analytical uncertainty** (§10.2, §10.6): the analysis *completed* and honestly reports ambiguity (`unclear`, `uncertainties`). Neutral-informational styling, never error styling.

The UI must never blur these: an uncertain analysis is not a failure, and a failure is never dressed up as uncertainty.

### 15.3 What must never be shown

* Secrets, credentials, API keys, authentication headers.
* Internal stack traces, internal diagnostic details or raw provider responses.
* Private reasoning traces or full prompts.
* Any fabricated "best effort" analysis offered when the real one failed.

### 15.4 Transport-level failures

Network failures, timeouts and non-contract responses (e.g., gateway errors without the error envelope) are represented explicitly as request failures with a safe generic message. For a submission whose outcome is unknown, §8.2 applies. The UI never treats "no response" as success.
---

## 16. Empty / Initial / Loading States

Every state below is explicit, textual, and free of fabricated content:

| Situation | Required presentation |
|---|---|
| Initial state, no analysis requested yet | Result panel shows an explanatory empty state (e.g., "No analysis yet — select parameters and choose Analyze XAU/USD."). Controls enabled; agent neutral. |
| No history | History area shows its empty state (§14.6). |
| Request in progress (`submitting`) | Indeterminate indicator + text; controls disabled; no fabricated intermediate content (§8.2). |
| Waiting for backend activity (`pending`/`running`) | Indeterminate indicator + the backend state label; no progress percentages, no simulated steps (§8.2). |
| Completed analysis | Full result panel (§10) rendered only from the GET-retrieved `MarketAnalysis`. |
| Failed analysis | Explicit failure state in the status area and result area (§15); no result content. |
| Historical analysis loading | Indeterminate indicator in the result panel while the GET resolves; previous content is not silently swapped until the new one arrives (or a clearly labeled loading state replaces it). |
| Data source unavailable | If `live` was requested and failed per §7.3/§15, an explicit unavailable/error state — never a fixture substitution. If the displayed analysis cannot determine provenance, the UI says so. |

No loading state may fabricate prices, analysis content, or a completion impression (e.g., an animation that ends exactly when a real result "should" arrive).

---

## 17. Responsive Behavior

The primary experience is **desktop-oriented**: the Trading Desk visual environment is a core part of the product and deserves space.

### 17.1 Desktop (primary)

The Trading Desk environment and the information panels are shown side by side (or in a dominant environment region with an adjacent operations column). All areas are visible without scrolling away the controls.

### 17.2 Narrow desktop / smaller browser widths

* The environment region shrinks proportionally; the scene remains visible and functional.
* Panels may narrow; tables (bars, key levels) compress gracefully or move to definition-list rendering.
* The shell must not require horizontal scrolling for core content.

### 17.3 Tablet

* The environment and panels stack vertically (environment above or below the operations area).
* The scene remains interactive (agent selection) and keeps its visual state behavior.
* All functionality is preserved; nothing is dropped at this width.

### 17.4 General rules

* The Pixel Art environment scales as a proportional canvas; it is not cropped into unusability and does not push information panels below the fold on desktop.
* There is no separate mobile product design in MVP-0; the same single page adapts. If very narrow viewports make the environment impractically small, it may be presented in a compact strip — it is not removed and its state must still be available textually in the conventional UI.
* Breakpoint values are an implementation decision; the behavioral requirements above are the contract.

---

## 18. Accessibility and Usability

Minimum expectations for MVP-0:

* **Readable text:** sufficient size and contrast for all informational content; pixel-art aesthetic never degrades text readability.
* **Contrast:** text, status badges and controls meet usable contrast against their backgrounds, in both the environment chrome and the panels.
* **Keyboard accessibility:** all interactive elements — timeframe select, data-mode control, primary action, agent interaction equivalent, history entries, "load more", retry actions — are reachable and operable by keyboard, in a sensible order.
* **Semantic controls:** real buttons for actions, real selection controls for timeframe/data mode, real links/buttons for history entries (not pixel-only hotspots).
* **Visible focus:** a clearly visible focus indicator on every interactive element, including inside/over the environment's accessible equivalents.
* **Non-color-only status:** every state (`running`, `completed`, `failed`, `unclear`, fixture/live) is communicated by text plus icon/shape; color is only a secondary cue.
* **Status communication:** lifecycle changes are announced to assistive technology (e.g., via a polite live region on the status area) so non-visual users observe the same lifecycle the scene shows.
* **Error communication:** errors are text, associated with the relevant control or area, and mention the safe backend message and error code; they never rely on color or the scene alone.
* **Loading communication:** loading states are text + indeterminate indicator; never conveyed by animation alone.
* **Pixel Art redundancy:** the Pixel Art scene never carries information exclusively. Every important backend state (agent working, completed, failed, disconnected) is also represented textually in the conventional UI (§5.2, §4.4).
* **Language:** plain, non-technical wording in labels and empty states; contract values are shown alongside plain-language readings rather than replacing them.
---

## 19. Visual Design Language

MVP-0 combines two visual registers under one coherent identity.

### 19.1 Overall character

* A **professional analytical interface**: calm, precise, information-first. It should feel like a serious tool, not a game dashboard and not a marketing site.
* A **Pixel Art identity** confined to the Trading Desk environment, giving the product a memorable, ownable visual signature.
* **Clear hierarchy:** department/capability identity → primary action → current status → analysis result → provenance/metadata → history.
* **Limited visual noise:** restrained color palette, consistent spacing, minimal decoration outside the environment.
* **Strong readability with high information density:** compact panels that show many contract fields at once without clutter — achieved through grouping (result sections), typographic hierarchy and tabular alignment (e.g., tabular figures for prices/timestamps), not through shrinking text.

### 19.2 Separation of registers

* The environment (Pixel Art, expressive, animated) is visually framed as its own region.
* The operational panels (flat, typographic, precise) never adopt game-like styling, and the environment never renders structured data panels.
* The two registers share only the core palette/brand accents so the product reads as one system.

### 19.3 Status semantics

* Status colors are used consistently across the product (status area, history badges, scene cues): in-progress = informational, completed = positive, failed = alert, `unclear`/uncertainty = neutral-informational.
* Color is always paired with text/icons (§18). `unclear` must be visually distinguishable from `failed`.

### 19.4 Boundaries

* Final CSS/design-token values, typography choices and asset production are implementation concerns.
* The legacy frontend may inspire the visual direction, but this UI obeys the new architecture and state model (§21); legacy visuals that encode fabricated state are not reproduced.

---

## 20. Frontend State Authority

The authority model is:

```text
Backend state      → authoritative
WebSocket          → notification
HTTP GET           → authoritative reconciliation
React state        → presentation/cache
Phaser state       → visual representation
```

### 20.1 Rules

* **Backend state is authoritative** for lifecycle, results, market data, timestamps, provenance and errors. It reaches the frontend through the synchronous HTTP responses and through GET.
* **WebSocket events are notifications only.** They may update presentation promptly (status label, agent working animation) but never establish a terminal state by themselves; completion/failure always leads to a GET of the authoritative record (§9.1).
* **HTTP GET reconciles.** After reconnection, on conflicting signals, for historical selections and for unknown outcomes, the UI re-fetches and conforms its presentation to the persisted state.
* **React state is presentation/cache.** It may hold frontend-only states (`idle`, `submitting`) and cached responses for rendering. It must not contradict or overwrite authoritative values, must not invent any of them, and is refreshed/reconciled via GET whenever truth is in doubt.
* **Phaser state is derived.** The scene receives its state from the application layer (which derives it from backend state) and renders it. Phaser never determines analysis outcomes (§5, and `ARCHITECTURE.md` §9: `analysis.completed → frontend state = completed → Phaser SUCCESS animation`, never the reverse).

### 20.2 Synchronization rules

* Only backend responses update authoritative presentation values; no timer, animation or local computation does.
* Terminal states (`completed`, `failed`) are entered only from backend confirmations (HTTP response or GET); WebSocket notifications for terminal states trigger the GET that confirms them.
* Frontend-only states (`idle`, `submitting`) never appear where backend states are expected (API, persistence — and in the UI they are labeled as request-status, not as analysis results).
* Cached presentation may go stale; when staleness is possible (reconnect, conflict, unknown outcome), the UI reconciles via GET rather than trusting the cache.
* The fixture/live provenance of any displayed value travels with it everywhere and is never lost in caching or re-rendering.

---

## 21. Legacy Repository Reuse

Consistent with `MVP_SCOPE.md` §13, the legacy repository may be mined **selectively** for visual and structural inspiration only.

### 21.1 Potentially reusable

* The Trading office visual concept (the "desk" as department environment).
* Phaser initialization concepts (bootstrap/configuration patterns).
* The `GameContainer` approach (embedding a Phaser game within the React application shell).
* `OfficeScene` design concepts (scene organization, layering, interaction zones).
* `AgentEntity` visual concepts (sprite representation, state-driven animation ideas).
* Visual assets (office/agent sprite art), where quality and licensing allow.

### 21.2 Not reusable as business logic

* simulated agent state / autonomous agent-state loops;
* fabricated market data or mock market-data services;
* fake analysis generation or fake backtesting;
* heuristic Director logic;
* hardcoded trading verdicts, claims or profitability statements;
* fabricated performance metrics;
* legacy state shortcuts (global mutable state, UI-asserted success, persistence bypasses).

### 21.3 Adaptation rule

Any reused concept, code or asset must be reviewed and adapted to the new frontend architecture: state flows from the React application layer (backend-derived), Phaser is a visualization layer only, and no legacy behavior may reintroduce fabrication, execution concepts or authoritative frontend state.
---

## 22. Explicit Non-Goals

The following UI features are intentionally excluded from MVP-0 and must not appear, even as disabled placeholders:

* order entry;
* execution;
* broker interfaces;
* positions;
* portfolio;
* strategy dashboard;
* backtest dashboard;
* risk engine UI;
* multi-agent committee;
* Director UI;
* paper trading controls;
* autonomous controls;
* future departments;
* multi-user administration.

Additionally excluded by upstream scope (see §2, §15): trading signals, BUY/SELL affordances, entry/stop-loss/take-profit instructions, position sizing, profitability claims, and fabricated performance metrics.

---

## 23. UI Acceptance Criteria

The MVP-0 UI is correct when all of the following hold:

* [ ] The Trading Desk is clearly identifiable as the Trading department environment.
* [ ] The Market Intelligence Agent is clearly identifiable (in-scene and as text) and presented as an analytical agent, not a trading executor.
* [ ] XAU/USD analysis is the primary workflow, reachable through the agent interaction and the primary "Analyze XAU/USD" action.
* [ ] Timeframe can be selected according to the contract enum; unsupported selections surface backend validation errors explicitly.
* [ ] The fixture/live distinction is visible everywhere data is displayed; fixture is always marked as test data; the UI never silently switches data mode.
* [ ] The analysis lifecycle (`idle`/`submitting` frontend-only; `pending`/`running`/`completed`/`failed` backend) is represented correctly and textually.
* [ ] The frontend never fabricates authoritative state: no fake agent activity, market data, timestamps, results, progress or completion-from-animation.
* [ ] A successful analysis exposes all required result areas: instrument/timeframe, final analysis timestamp, market snapshot, trend context, volatility context, key levels, market observations, uncertainties, data sources, model metadata.
* [ ] Uncertainties and `unclear` values are visible and rendered as valid analysis, not errors.
* [ ] Provenance (data source mode, provider, timestamps, model metadata) is visible and distinct per §11.1 (snapshot observation time ≠ analysis finalization time).
* [ ] History is backend-backed via `GET /api/v1/market-analyses` using only `AnalysisSummary` fields, with defined empty/loading/error states and contract-compliant pagination.
* [ ] Failures are explicit, use the safe backend error contract, and are distinguishable from analytical uncertainty.
* [ ] WebSocket events (`analysis.started`/`completed`/`failed`) are treated as notifications only.
* [ ] The UI can reconcile state through `GET /api/v1/market-analyses/{analysis_id}` after completion, failure, reconnection and unknown outcomes.
* [ ] No trading execution UI exists (no orders, entries, exits, sizing, broker/portfolio/execution controls).
* [ ] No secrets, credentials, private reasoning or internal stack traces are exposed.
* [ ] No new cross-layer contracts are introduced (no new endpoints, schemas, fields or events beyond the upstream documents).
* [ ] Pixel Art is never the only channel for important information; all backend states are also represented textually.
* [ ] The interface remains within MVP-0 scope: one department, one agent, one capability.

---

## 24. Source-of-Truth Compliance

This document sits at the following position in the document hierarchy:

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
```

`UI_SPEC.md` defines presentation and interaction behavior only. It does not override upstream product, architecture or data contracts; where this document and an upstream document could appear to conflict, the upstream document prevails and this document must be corrected.

All behaviors defined here operate exclusively on contracts already defined upstream (`AnalysisRequest`, `MarketAnalysis`, `MarketSnapshot`, `DataSource`, `ModelMetadata`, `AnalysisRun`, `AnalysisSummary`, `WebSocketEvent`, the error envelope, and their enums) and on the API routes defined in `ARCHITECTURE.md` §§17 and 19, the HTTP API contracts defined in `DATA_CONTRACTS.md` §14, and the WebSocket event contracts defined in `DATA_CONTRACTS.md` §12. No new API route, schema, field, event type or domain concept is introduced by this document.
