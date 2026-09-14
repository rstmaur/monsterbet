# XenArb NFL enrichment — resolver trace and blocker

**Status: BLOCKED at the provider.** The public "Verified NFL intelligence"
strip is built, wired and scheduled, and it renders nothing, because the
Monster.bet API exposes no route that resolves a `game_id` into a matchup.

Traced live on **2026-09-14**. No API was purchased and no value was invented.

## What the strip needs, and what the provider has

| Field required by the strip | Resolves? | Where it would come from |
|---|---|---|
| Home / away teams | **NO** | absent from every record; no resolver route |
| Kickoff time | **NO** | absent from every record |
| Market | yes | `market_key` (`moneyline`, `spread`, `total`, ~30 prop keys) |
| Outcome | yes | `legs[].outcome` (`home`/`away`/`over`/`under`) |
| Sportsbook | yes | `legs[].best_book` |
| Current price | **NO** | only `fair_decimal` — a no-vig *fair* value, not a posted price |
| Prior / first-seen price | **NO** | no history route; snapshot carries one instant only |
| Source timestamp | partial | snapshot-level `ts` only; no per-quote timestamp |

Five of the eight required fields do not exist, so a row can never be stated
truthfully. `build-xenarb-nfl.py` therefore publishes zero signals and the
section stays `display:none`.

## The whole API surface

```
GET  https://api-v2.monster.bet/v1/arbitrage/snapshot
WSS  wss://api-v2.monster.bet/v1/stream
```

The WebSocket `hello` frame is authoritative and advertises exactly:

```json
{"channels":["arbitrage.new","arbitrage.update","arbitrage.closed"],
 "default_event":"arb.opened arb.updated arb.closed","key_id":1,"type":"hello"}
```

There is no odds channel, no game channel and no event channel. (The server
echoes back *any* channel name you subscribe to with a `subscribed` frame, so
only the `hello` frame proves what exists.)

## Resolver probe — every path tried with `game_id=4067`

Control first, to prove the key and transport are healthy:

```
 200    8884B  /v1/arbitrage/snapshot?sport=all&limit=5      ← control, OK
```

Every `game_id`-resolving candidate, authenticated, same session:

```
 404       0B  /v1/games/4067            404       0B  /v1/game/4067
 404       0B  /v1/events/4067           404       0B  /v1/event/4067
 404       0B  /v1/matches/4067          404       0B  /v1/fixtures/4067
 404       0B  /v1/games?ids=4067        404       0B  /v1/games?game_id=4067
 404       0B  /v1/games                 404       0B  /v1/arbitrage/game/4067
 404       0B  /v1/arbitrage/4067        404       0B  /v1/odds?game_id=4067
 404       0B  /v1/lines?game_id=4067    404       0B  /v1/markets?game_id=4067
 404       0B  /v1/quotes?game_id=4067   404       0B  /v1/history?game_id=4067
 404       0B  /v1/arbitrage/history?game_id=4067
 404       0B  /v1/books?game_id=4067    404       0B  /v1/sportsbook/4067
 404       0B  /v1   /v1/   /   /openapi.json   /docs   /v1/schema
```

**404 with zero bytes is genuine absence, not an entitlement gate** — an
unauthenticated call to the snapshot returns `401` *with a message body*, so a
gated route would answer, not vanish.

Three routes returned `200` and still resolve nothing:

```
 200  133234B  /v1/arbitrage/snapshot?game_id=4067      ← param IGNORED: this is
                                                          the full unfiltered set
 200    8884B  /v1/arbitrage/snapshot?…&expand=game     ← byte-identical to control
 200    8884B  /v1/arbitrage/snapshot?…&include=teams   ← byte-identical to control
```

The builder rejects these on purpose: a route that returns every game is not a
resolver for one game.

## No internal join is possible either

In a 243-item snapshot:

* `game_id` appears on **11 of 243** rows — every one of them
  `pipeline == "sportsbook"`.
* **Zero** `prediction`-pipeline rows carry a `game_id`, so there is no join key.
* `titles` — the only team-name-shaped field anywhere — appears **only** on the
  232 prediction rows, which are political and futures markets
  ("Will the 2026 Midterm Elections happen as scheduled?"), not NFL matchups.

So the team names cannot be recovered by joining the payload to itself.

## A real NFL source record, verbatim

```json
{"confidence_caveats":[],"event":"arb.opened","game_id":"4067","leg_count":2,
 "legs":[{"best_book":"fanduel","fair_decimal":2.6,"implied":0.3846,"outcome":"away"},
         {"best_book":"polymarket_us","fair_decimal":1.6536,"implied":0.6047,"outcome":"home"}],
 "line_value":null,"market_key":"moneyline","pipeline":"sportsbook",
 "player_id":null,"pricing":{"edge_pct":1.0642,"implied_sum":0.9894},"sport":"nfl"}
```

`line_value` is `null` even on a spread-capable market.

## Two traps that make probing lie to you

1. **The default `limit` is 100 and NFL rows sit past it.** `?sport=all` alone
   returned 105 items / 0 NFL; `&limit=200` returned 207 items with 4 NFL rows.
   Always pass an explicit high limit before concluding absence.
2. **The server-side `sport=` filter is broken.** `sport=nfl` returns 0 items in
   the same second `sport=all` returns NFL rows. Filter client-side.

## How the refresh works

`scripts/build-xenarb-nfl.py` runs server-side on a schedule, never in the
browser — the `mk_live_` key stays on the box and never reaches a static page.

```
*/15 * * * * cd /srv/monsterbet && python3 scripts/build-xenarb-nfl.py nfl-intel.json \
             && ./publish-nfl-intel.sh    # commits nfl-intel.json only
```

**The schedule is deliberately NOT armed in this PR.** Arming it would republish
an empty file every 15 minutes and redeploy the site each time for no visible
change. Arm it in the same change that clears the blocker.

Timestamp movement is real and was verified across two consecutive runs:

```
sourceTimestamp   A=2026-09-14T04:26:24.631773927+00:00
                  B=2026-09-14T04:27:36.302473515+00:00   changed
generatedAt       A=2026-09-14T04:26:30Z  B=2026-09-14T04:27:41Z   changed
itemsScanned      A=240                   B=237                    changed
```

## What would unblock it

One of, in order of preference:

1. Monster.bet exposes a game/event resolver (`GET /v1/games/{id}` returning
   teams + kickoff) **and** either a per-book quote table or a history route for
   the first-seen price. This is a provider request, not work on our side.
2. A licensed odds feed supplies teams, kickoff, per-book prices and openers.
   Deliberately **not** pursued here — no API was to be purchased.

Until then the correct behaviour is exactly what ships: the section renders
nothing at all, with no empty state and no "coming soon".
