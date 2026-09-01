# XenArb NFL live-data gate

## Current state

Live mode is disabled. The current XenArb process consumes Monster.bet arbitrage events and does not expose the traceable schedule, game-state, per-sportsbook market history, injury or public HTTP/SSE interfaces required by Monsterbet.ai. That dataset must not power the NFL odds board.

## Recommended provider

SportsDataIO commercial NFL feeds are the cleanest single-provider fit because their official NFL workflow covers schedules and status, injuries, pre-game and in-play game lines, line movement, consensus lines, and player/game/team props. Their Discovery Lab Odds plan is $99/month or $599/year, but it is next-day delayed and not licensed for commercial redistribution, so it cannot satisfy this production use case. Real-time commercial pricing and redistribution rights require a written SportsDataIO sales quote; no public fixed price exists.

Rémi must obtain:

- SportsDataIO commercial NFL Odds access;
- NFL scores/schedules and game-status access;
- NFL injuries/depth-chart access if licensed for display;
- NFL Props access if player props are enabled;
- commercial web-display/redistribution rights for Monsterbet.ai;
- production API key supplied as `SPORTSDATAIO_API_KEY` only on XenHive;
- confirmed request limits, permitted cache duration, required attribution and SLA;
- written price quote and contract term.

Authentication uses the server-side header `Ocp-Apim-Subscription-Key: <key>`. The key must never reach GitHub Pages or browser JavaScript.

## XenArb ingestion

1. Add a separate `nfl-provider` module to `/home/xenhive/xenarb`; do not reuse prediction-market or arbitrage records.
2. Poll provider endpoints at the licensed interval and honor cache headers, quota headers and `429 Retry-After`.
3. Normalize schedule/status, teams, kickoff, sportsbook, event ID, market ID, selection, line/value, American price, provider update time and XenArb ingestion time.
4. Persist every changed outcome as an immutable historical snapshot in PostgreSQL (recommended), keyed by provider, event, market, sportsbook, selection and provider timestamp.
5. Calculate opening/current movement, size/direction, best available price, implied probability, consensus, sportsbook disagreement, unusual movement and last-change time inside XenArb.
6. Expose read-only `GET /v1/nfl/board` and optional `GET /v1/nfl/stream` SSE endpoints matching `xenarb-nfl-api-contract.json`.
7. Allow CORS only from `https://monsterbet.ai`; expose no credentials or upstream URLs.
8. Put the public API behind HTTPS, rate limiting, health checks and structured logs.
9. Set `enabled`, `apiBase`, transport and provider-compliant intervals in `xenarb-config.js` only after Hawk completes the gate below.

## Required source fields

SportsDataIO mappings must include `ScoreID`/`BettingEventID`, `GameStartTime`, `GameStatus`, home/away IDs and names, `BettingMarketID`, market/bet/period types, `BettingOutcomeID`, `SportsBook`, `BettingOutcomeType`, `Value`, `PayoutAmerican`, `PayoutDecimal`, `IsAvailable`, `IsInPlay`, `SportsbookMarketID`, `SportsbookOutcomeID`, `Created`, `Updated`, player/team IDs when applicable, consensus outcomes and injury/practice status timestamps.

## Production evidence gate

Hawk must capture evidence that:

1. a real provider update entered XenArb;
2. `GET /v1/nfl/board` returned that updated value with trace fields;
3. the open Monsterbet.ai page changed without deployment or refresh;
4. the displayed timestamp exactly matched the provider timestamp;
5. a forced stale snapshot changed the UI to `Delayed` while preserving the original timestamp;
6. searches of the production HTML/JS bundle found no hardcoded NFL lines, prices, teams, events or statistics.

Until all six pass, `xenarb-config.js` must remain `enabled: false` and the public UI must say `Live NFL data temporarily unavailable`.
