# XenArb NFL live-data gate

## Current state

Live mode is disabled. The current XenArb process consumes Monster.bet arbitrage events and does not expose the traceable schedule, game-state, per-sportsbook market history, injury or public HTTP/SSE interfaces required by Monsterbet.ai. That dataset must not power the NFL odds board.

## Recommended provider

Decision memo with costs, activation times, fields and redistribution rights:
**`NFL-ODDS-PROVIDER-DECISION.md`**. Summary of the recommendation:

**The Odds API (the-odds-api.com), 5M-credit plan, $119/month.** Self-serve, key issued
immediately, covers DraftKings / FanDuel / BetMGM on `americanfootball_nfl` for `h2h`,
`spreads` and `totals`, expressly permits commercial display of the data in a website, and
expressly permits retaining it indefinitely (which is what makes our line-movement history
legal). Attribution is not required.

SportsDataIO remains the better long-term fit — official NFL workflow, consensus lines,
injuries and props under one written licence — but its real-time commercial feed is
quote-only with a contract, which cannot be activated before NFL Week 1. Its published
Discovery Lab Odds plan ($99/month, $599/year) is next-day delayed and not licensed for
commercial redistribution, so it cannot power this board. Open that conversation for 2027.

Rémi must approve, before any ingestion work starts:

- the $119/month subscription and the card it bills to;
- an email to The Odds API confirming that serving our own first-party `/v1/nfl/board`
  endpoint (CORS-locked to `https://monsterbet.ai`, undocumented, no third-party keys) is
  in scope and not "offering data through your own API" — see the decision memo;
- whether player props are in launch scope, since they use a different endpoint and change
  the credit maths.

The production API key is supplied as `THE_ODDS_API_KEY` on XenHive only. Authentication is
the `apiKey` query parameter, added server-side. The key must never reach GitHub Pages or
browser JavaScript.

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

From The Odds API `/v4/sports/americanfootball_nfl/odds`: `id`, `commence_time`,
`home_team`, `away_team`; per bookmaker `key`, `title`, `last_update`; per market `key`,
`last_update`; per outcome `name`, `price`, `point`.

These map onto `xenarb-nfl-api-contract.json` as: `id` → `eventId`, `commence_time` →
`kickoff`, bookmaker `title` → `sportsbook`, market `key` → `marketId`, outcome `name` →
`selection`, `point` → `value`, `price` → `price`. The provider supplies one `last_update`
per bookmaker/market rather than per outcome; carry that value into `providerTimestamp` for
every outcome in that market, and stamp `xenarbIngestedAt` at write time.

Opening lines are not in the live response. Backfill true openers once per event from
`/v4/historical/sports/americanfootball_nfl/odds` (5-minute snapshots, `10 × markets ×
regions` credits per call), then track movement from XenArb's own stored history. If the
historical backfill is skipped, the board column must read `First seen`, not `Open`.

Game status is not supplied by the odds endpoint. Source `status` from the provider's
scores endpoint, or hold every event at `upcoming` until a status feed is wired in — never
infer it from kickoff time alone.

## Production evidence gate

Hawk must capture evidence that:

1. a real provider update entered XenArb;
2. `GET /v1/nfl/board` returned that updated value with trace fields;
3. the open Monsterbet.ai page changed without deployment or refresh;
4. the displayed timestamp exactly matched the provider timestamp;
5. a forced stale snapshot changed the UI to `Delayed` while preserving the original timestamp;
6. searches of the production HTML/JS bundle found no hardcoded NFL lines, prices, teams, events or statistics.

Until all six pass, `xenarb-config.js` must remain `enabled: false` and the public UI must say `Live NFL data temporarily unavailable`.
