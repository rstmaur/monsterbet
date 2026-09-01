# NFL odds provider — decision required from Rémi

Prepared 2026-09-01. Read-only research; nothing purchased, no account created, no key requested.

The board in this PR stays empty until one of these providers is contracted. NFL Week 1
opens 2026-09-10, so "this week" means a provider that can be live inside ~7 days.

## Recommendation: The Odds API — $119/month, live in under an hour

| | |
|---|---|
| Provider | The Odds API (the-odds-api.com) |
| Plan | 5M credits/month — **$119/month** |
| Activation | Self-serve. Email → API key issued immediately. No sales call, no contract. |
| NFL coverage | `americanfootball_nfl`, region `us` — DraftKings, FanDuel, BetMGM all present |
| Markets | `h2h` (moneyline), `spreads`, `totals`. Player props via the per-event endpoint. |
| Redistribution | Display in a commercial website/app **expressly permitted**. Resale of the data as a standalone data product **prohibited**. |
| Storage | Retaining the data indefinitely is expressly permitted — this is what makes our line-movement history legal. |
| Attribution | Not required. |

### Why this one

It is the only provider found that is simultaneously (a) self-serve with an instant key,
(b) priced in the low hundreds rather than the low thousands, and (c) explicit in writing
that commercial display in a website is an allowed use. Every other candidate fails at
least one of those three, and the two that fail on activation time cannot be live for Week 1.

### Cost sizing

Current-odds cost formula: `credits = markets × regions`. Our board is 3 markets × 1 region
(`us`) = **3 credits per refresh**.

| Refresh | Requests/month | Credits/month | Cheapest plan that fits |
|---|---|---|---|
| 30s, 24/7 | 86,400 | 259,200 | 5M — **$119** |
| 60s, 24/7 | 43,200 | 129,600 | 5M — $119 |
| 60s, game windows only | ~12,000 | ~36,000 | 100K — $59 |

The $59/100K plan technically fits a windowed poller, but it leaves no headroom for
retries, backfill or a second sport. **Take the $119 plan**; at 30s polling it runs at ~5%
of quota.

### Opening lines

The live endpoint returns current prices only. Two routes to the "Open" column:

1. **True book openers** — the historical endpoint (`/v4/historical/...`, snapshots every
   5 minutes back to 2020) costs `10 × markets × regions` = 30 credits per lookup. One
   lookup per event per week for ~16 games is ~500 credits. Negligible.
2. **First-sighting opener** — XenArb records its own first observation of each event and
   labels the column accordingly.

Use (1) to backfill Week 1, then (2) going forward. If we ship (2) only, the column must be
labelled "First seen", not "Open".

### Fields we consume

`id`, `commence_time`, `home_team`, `away_team`, then per bookmaker `key`, `title`,
`last_update`, and per market `key`, `last_update`, `outcomes[].name`, `outcomes[].price`,
`outcomes[].point`. That maps 1:1 onto the `quote` object in `xenarb-nfl-api-contract.json`
except that the provider gives one `last_update` per bookmaker/market rather than per
outcome — XenArb should carry that value into `providerTimestamp` for every outcome in
that market.

### ⚠️ One licence question Rémi must settle in writing before launch

The XenArb design in `XENARB-NFL-INTEGRATION.md` publishes `GET /v1/nfl/board` as an
HTTPS JSON endpoint. Read literally, "offering data through your own API or data feed"
is the prohibited behaviour, even though our intent is only to feed our own page.

Mitigations already specified in the integration doc: CORS restricted to
`https://monsterbet.ai`, the endpoint undocumented publicly, no third-party keys.
That is very likely fine — it is our own front end, not a data product — but it is worth
one email to their support asking for confirmation that serving our own first-party page
from our own JSON endpoint is in scope. Their terms invite exactly this question. **Do not
launch paid traffic against the board until that reply is in hand.**

## Alternatives considered

| Provider | Cost | Activation | Verdict |
|---|---|---|---|
| **OddsBlaze** | $29–$999/mo; the $29 tier carries ~2-minute delay, sub-second needs $249+ | self-serve, same day | Viable fallback. Terms of service on redistribution are **not published** — would need to be confirmed before use, which costs us the time advantage. |
| **SportsDataIO** | No public price for the commercial real-time feed. Their listed "Discovery Lab Odds" plan ($99/mo, $599/yr) is **next-day delayed and not licensed for commercial redistribution**, so it cannot serve this page. | Sales quote + contract — days to weeks | Best long-term fit (official NFL workflow, consensus lines, injuries, props) but cannot be live for Week 1. Worth opening the conversation now for the 2027 season. |
| **OddsJam** | Reported ~$4,995/mo, quote-gated | sales call | Out of budget by ~40×. |
| **OpticOdds** | Reported ~$5,000/mo per sport, quote-gated | sales call | Out of budget. |
| **Sportradar / LSports** | Enterprise, quote only | weeks, incl. compliance review | Not achievable this week. |

The OddsJam and OpticOdds figures come from third-party comparison articles, not from the
vendors — treat them as indicative only. Neither publishes pricing.

## What Rémi needs to decide

1. **Approve $119/month for The Odds API 5M plan** (and name the card — the AmEx that
   killed the Google Ads / GCP / Workspace billing must not be used here).
2. **Approve the licence email** asking The Odds API to confirm the first-party
   `/v1/nfl/board` endpoint is in scope.
3. Confirm whether player props are in scope for launch or deferred — props use a
   different endpoint and change the credit maths.

Once 1 and 2 are answered, XenArb ingestion is roughly a day of work, and the six-part
evidence gate in `XENARB-NFL-INTEGRATION.md` governs when `xenarb-config.js` flips to
`enabled: true`.
