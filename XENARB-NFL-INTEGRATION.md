# XenArb NFL live-data gate

## Current state

Live mode is disabled. `xenarb-config.js` is `enabled: false` and the board renders its
empty state.

The ingestion subsystem is **built and tested**, waiting only on an approved API key. It
lives at `/home/xenhive/xenarb/src/nfl/` and is deliberately independent of the existing
Monster.bet arbitrage pipeline — it shares the logger only, and writes to its own
`data/nfl/` store. It makes **zero outbound requests** unless `NFL_ENABLED=true` *and*
`THE_ODDS_API_KEY` is set; with either missing it logs exactly what is absent and exits 0.

| File | Role |
|---|---|
| `src/nfl/config.js` | Feature flag, provider settings, poll cadence, origin lock |
| `src/nfl/provider.js` | The Odds API client; quota headers, 429 `Retry-After`, key redaction |
| `src/nfl/normalize.js` | Provider payload → contract quote objects |
| `src/nfl/history.js` | Append-only `quotes.jsonl` + first-seen store |
| `src/nfl/board.js` | Movement, best line, disagreement → contract snapshot |
| `src/nfl/server.js` | `GET /v1/nfl/board`, `GET /v1/nfl/health`, origin-locked |
| `src/nfl/index.js` | Entry point + poller |
| `scripts/nfl-selftest.js` | 30 offline assertions; needs no key, makes no network call |

Run `npm run nfl:selftest` to re-verify the pipeline without a subscription.

## Provider

**The Odds API, 5M plan, $119/month.** Costs, exact contractual language, bookmaker and
market evidence, the weekly quota calculation and the outstanding licence question are all
in **`NFL-ODDS-PROVIDER-DECISION.md`**. Summary:

- Terms (last updated 31 August 2026) expressly permit displaying the data in a commercial
  website, retaining it indefinitely, and displaying values derived from it.
- They expressly prohibit reselling it as a standalone data product "through your own API,
  data feed, downloadable files, or any other format intended to serve as a source of raw
  data for others".
- **Open question, blocking purchase:** whether our first-party `GET /v1/nfl/board`
  endpoint falls on the permitted side of that line. Email sent 2026-09-01 to
  `team@the-odds-api.com`; awaiting written reply. Do not subscribe until it arrives.

The production key is `THE_ODDS_API_KEY` in `/home/xenhive/xenarb/.env` on XenHive only.
Auth is the `apiKey` query parameter, added server-side. It must never reach GitHub Pages
or browser JavaScript; `provider.js` redacts it from every log line.

## Board conventions

Fixed here so the rendered numbers are auditable:

- The board renders one side per market: **spreads** → the home team's handicap,
  **h2h** → the home team's moneyline, **totals** → the Over.
- Market-level `current` is the modal line across the three books (median American price
  for moneyline). `opening` is the same statistic at first observation.
- **Best line** — spreads: the largest handicap for the home side, ties broken on price;
  totals: the lowest Over number, ties broken on price; moneyline: the highest American
  price.
- `unusualMovement` is set when the spread has moved two points or more from first seen.
- Game status is **not** supplied by the odds endpoint. Events read `upcoming` before
  kickoff and `live` after it; the board never claims `final` until a scores feed is wired in.

## Opening lines

`openingSource` is carried at snapshot and market level and takes one of two values:

- `first_seen` — XenArb's own earliest observation. **This is the default and the current
  state.** The page labels its column **"First seen"**.
- `provider_historical` — a genuine book opener from the provider's historical endpoint,
  applied through `history.applyHistoricalOpeners()`, which refuses any other source value.
  Only then does the page relabel the column "Opening".

Historical access costs `10 × markets × regions` = 30 credits per lookup, with 5-minute
snapshots back to 2020. It is **out of launch scope**: the column stays "First seen" until
a backfill has been run *and* verified.

## XenArb ingestion

1. Separate `nfl-provider` subsystem under `/home/xenhive/xenarb/src/nfl/`; no reuse of
   prediction-market or arbitrage records. **Done.**
2. Poll at the licensed interval, honour quota headers and `429 Retry-After`. **Done** —
   60s, tightening to 30s while a game is live or within 60 minutes of kickoff.
3. Normalize schedule, teams, kickoff, sportsbook, event ID, market ID, selection, line,
   American price, provider update time and XenArb ingestion time. **Done.**
4. Persist every changed outcome as an immutable snapshot. **Done** — `data/nfl/quotes.jsonl`,
   append-only, unchanged quotes are not re-appended.
5. Calculate movement, size, direction, best price, implied probability, consensus,
   disagreement and last-change time inside XenArb. **Done.**
6. Expose read-only `GET /v1/nfl/board`. **Done.** SSE remains optional and unbuilt.
7. Allow CORS only from `https://monsterbet.ai`; expose no credentials or upstream URLs.
   **Done** — a foreign `Origin` gets 403, `Allow-Origin` is never a wildcard or reflected,
   and the server binds to `127.0.0.1` by default.
8. Put the public API behind HTTPS, rate limiting, health checks and structured logs.
   **Partly** — `/v1/nfl/health` and structured logs are in; TLS termination and rate
   limiting are reverse-proxy work, still to do at activation.
9. Set `enabled`, `apiBase` and intervals in `xenarb-config.js` only after the gate below.

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
