# NFL odds provider — definitive purchase decision

> **Canonical source: `Xentraffic/xenarb`.** This memo and the board contract
> `xenarb-nfl-api-contract.json` are maintained in
> <https://github.com/Xentraffic/xenarb> (`docs/nfl/`). The copies in this
> repository are synchronised from there and must not be edited in place.
> The poll cadence of record is `src/nfl/config.js` in that repository.

Rev 3, 2026-09-03. Supersedes Rev 2 and the earlier SportsGameOdds recommendation.
The licence blocker is **cleared** — the provider confirmed our use case in writing on
2026-09-02. Nothing has been purchased. No account has been created.

## The contradiction, and why it happened

Two earlier reports disagreed:

- The first recommended **SportsGameOdds Rookie, $99/month**, on the grounds that
  The Odds API's terms were *silent* on public display and SportsGameOdds' were explicit.
- The second recommended **The Odds API, $119/month**, on the grounds that its terms
  *expressly permit* commercial display.

Both reads were of the same page. The first was not wrong when it was made.
**The Odds API's Terms and Conditions carry `Last updated: 31 August 2026`** — they were
revised the day before the second read. The current version adds an explicit permitted-uses
list that did not previously exist.

The $40/month that the SportsGameOdds recommendation was buying — an express written
display right — is now available from The Odds API at a lower price for the quota we
actually need. That is what changed, and it is the whole basis for switching.

Everything below is quoted from the live pages, fetched raw rather than summarised.

---

## Decision: The Odds API — 5M plan, $119/month

| | |
|---|---|
| Provider | The Odds API (The Odds API Pty Ltd, ACN 627461947, New South Wales, Australia) |
| Plan name | **5M** |
| Live checkout price | **$119 per month, USD** |
| Quota | **5,000,000 credits per month** |
| Purchase URL | <https://the-odds-api.com/#get-access> → START, which resolves to <https://dash.the-odds-api.com/> |
| Screenshot | `evidence/provider-plans.png` — all five live tiers |
| Activation | Self-serve. "Subscribe to receive your API key via email." No sales call, no contract, no minimum term. |

Full live pricing table, captured 2026-09-01:

| Plan | Price | Credits / month | Historical Odds |
|---|---|---|---|
| Starter | FREE | 500 | ✗ (struck through) |
| 20K | $30 /mo USD | 20,000 | ✓ |
| 100K | $59 /mo USD | 100,000 | ✓ |
| **5M** | **$119 /mo USD** | **5,000,000** | ✓ |
| 15M | $249 /mo USD | 15,000,000 | ✓ |

All paid tiers advertise "All sports", "All bookmakers", "All betting markets".

---

## Evidence

### 1. Exact contractual language permitting commercial display

From <https://the-odds-api.com/terms-and-conditions.html>, section **Restrictions**,
verbatim:

> Do not resell, repackage, or redistribute our data as a standalone data product. This
> includes, but is not limited to, offering our data through your own API, data feed,
> downloadable files, or any other format intended to serve as a source of raw data for
> others.
>
> We support and encourage the use of our data in websites, mobile apps, dashboards,
> analytical tools, and other user-facing applications, including commercial use, provided
> our data is not the primary product being sold or redistributed.
>
> Permitted uses include, but are not limited to:
>
> - Storing our data and retaining it indefinitely
> - **Displaying our data in a UI, website, or mobile app, including for commercial use**
> - Using our data in research papers and analytical dashboards
> - Calculating and displaying values you derive from our data
> - Using our data to train statistical and machine learning models
>
> We mainly prohibit reselling the data as a raw data feed, i.e. a competing product. In
> other words, don't resell our data as your own API or data source.
>
> Attribution to The Odds API is not required, but is always appreciated.

Three clauses matter to us and all three are favourable: commercial display is named
explicitly; indefinite storage is named explicitly, which is what makes our line-movement
history lawful; and derived values — our movement, best-line and disagreement columns — are
named explicitly.

One further clause we already satisfy, from **Responsible Gambling**:

> If the Service is used to promote bookmakers or gambling services, users are encouraged to
> display appropriate responsible gambling messaging (e.g., "Gamble Responsibly. 18+") on
> their customer-facing platforms.

The page footer already carries "18+; know your local laws and play responsibly."

### 2. FanDuel, DraftKings and BetMGM — NFL spread, moneyline, total

From <https://the-odds-api.com/sports-odds-data/bookmaker-apis.html>, US region:

| Region key | Bookmaker key | Bookmaker | Tier restriction |
|---|---|---|---|
| `us` | `fanduel` | FanDuel | none |
| `us` | `draftkings` | DraftKings | none |
| `us` | `betmgm` | BetMGM | none |

None of the three carries the "Only available on paid subscriptions" note that Caesars,
Fanatics and ReBet carry, so all three are present on every tier.

From <https://the-odds-api.com/sports-odds-data/betting-markets.html>, Featured Betting
Markets:

| Market key | Market names |
|---|---|
| `h2h` | Head to head, Moneyline |
| `spreads` | Points spread, Handicap |
| `totals` | Total points/goals, Over/Under |

> spreads and totals markets are mainly available for US sports and bookmakers at this time.

NFL is a US sport and the sport key is `americanfootball_nfl`, which appears in the
provider's own homepage response sample alongside a `fanduel` bookmaker block.

### 3. Refresh frequency and quota calculation

Cost formula, from the v4 documentation: `credits = [markets] × [regions]`.
Our board is 3 markets × 1 region = **3 credits per request**.

The shipped poller runs at a **flat 60 seconds, round the clock**. It is not tightened
inside the game window: the provider confirmed in writing on 2026-09-02 that featured
markets refresh every **40-60 seconds**, so a 30-second poll returns the same numbers at
twice the credit cost. Rev 2 of this memo assumed a 30s live-window cadence; that
assumption is withdrawn.

| Window | Hours / week | Interval | Requests / week |
|---|---|---|---|
| All hours, including live and pre-kickoff | 168 | 60s | 10,080 |
| **Total** | 168 | | **10,080** |

- **30,240 credits per week** (10,080 × 3)
- **≈ 131,000 credits per month** (30,240 × 52 ÷ 12; ≈ 129,600 on a flat 30-day month,
  the figure carried in `src/nfl/config.js` in `Xentraffic/xenarb`)

That still exceeds the 100K plan, so the 5M plan remains the purchase. Utilisation on 5M
falls from 2.9% to **2.6%**, leaving room for retries, a second sport, and any
runaway-poller incident.

The provider's separate **30 requests/second** rate limit is confirmed. At one request per
60 seconds we run at 0.017 req/s — roughly 1,800× under the ceiling — so no poller-side
throttling is required.

For completeness: the $59 100K plan fits only at a flat 2-minute interval
(5,040 requests/week → 15,120 credits/week → ~65,700/month, 66% utilisation). A two-minute-old
line is a poor foundation for a product whose selling point is line movement, and the
saving is $60/month.

**Previously not published, now confirmed in writing:** the provider's public docs give a
1-minute update interval for *additional* markets and no refresh SLA for featured markets.
The 2026-09-02 reply supplies it — featured markets refresh every **40-60 seconds**. Every
quote still carries the provider's own `last_update`, which the board surfaces verbatim.

### 4. Written confirmation covering the private CORS-restricted endpoint

**CLEARED — written approval received 2026-09-02.**

Our static front end cannot hold an API key, so XenArb exposes `GET /v1/nfl/board`. The
Restrictions clause names "offering our data through your own API" as prohibited. Rev 2
flagged this as the one remaining blocker and instructed that nothing be purchased until
the provider answered. They have answered, and the answer is favourable.

The question was put on 2026-09-01 to `team@the-odds-api.com`, the address published in
their terms, which also state "If you are unsure whether your use case is permitted, please
contact us." It set out the exact intended use, the endpoint's CORS lock to
`https://monsterbet.ai`, and the absence of any third-party credentials.

**Reply received 2026-09-02 02:28 UTC** from Raphy, The Odds API team
(`team@the-odds-api.com`). Gmail thread `1a05e2a741c8e5df`, message `1a05ff2d0c864850`.
Verbatim:

> Your use case sounds well within our Terms of Use. An internal API delivering odds to
> your application is permitted.
>
> The restriction would apply if you offered third parties access to an API or data feed
> that effectively resells our odds data as a standalone service. Using the data within
> your own application or user interface, including as part of a paid product, is permitted
> and doesn't sound like an issue in your case.
>
> Answers to your other questions:
>
> 1. Featured markets update at intervals between 40 and 60 seconds, depending on proximity
>    to live games.
>
> 2. There's a rate limit of 30 requests per second, explained on this page
>    [https://the-odds-api.com/guide/rate-limit.html]

That resolves all three open items in one reply:

| Item | Rev 2 status | Now |
|---|---|---|
| First-party `GET /v1/nfl/board` endpoint | Open, blocking purchase | **Permitted in writing** |
| Featured-market refresh interval | Not published | **40-60 seconds** |
| Rate limit beyond the credit quota | Unknown | **30 requests / second** |

The conditions attached to the approval are ones we already meet and must keep meeting:
no third party is issued credentials to `/v1/nfl/board`, the endpoint stays CORS-locked to
our own origin, and the odds are never offered as a standalone data product. If that ever
changes, the approval no longer covers us and the question must be put again.

The 40-60 second figure is also the direct reason the poller is a flat 60s: see section 3.

**Purchase is unblocked.** It has not been made — see the activation sequence below.

---

## Alternatives, for the record

| Provider | Cost | Activation | Why not |
|---|---|---|---|
| SportsGameOdds — Rookie | $99 /mo | Self-serve | Was the right call while The Odds API's terms were silent. Costs $20/mo more for an equivalent express display right, and its own "no data dumps, feeds or white-label" restriction would have had to be cleared separately — whereas The Odds API has now cleared ours in writing. |
| OddsBlaze | $29–$999 /mo | Self-serve | $29 tier runs ~2 minutes behind; sub-second needs $249+. Redistribution terms not published. |
| SportsDataIO | Quote only | Days to weeks | Superseded. An earlier revision of the Monsterbet PR recommended commercial SportsDataIO access; that recommendation is withdrawn. Cannot activate before Week 1, and its public $99/mo Discovery Lab plan is next-day delayed and not licensed for commercial redistribution. |
| OddsJam | ~$4,995 /mo | Sales call | ~40× budget. Third-party price report; they publish none. |
| OpticOdds | ~$5,000 /mo per sport | Sales call | Same. |
| Sportradar / LSports | Quote only | Weeks + compliance | Not achievable this week at any price. |

---

## Same-day activation sequence

The integration is already built and tested behind a disabled flag
(`Xentraffic/xenarb`, `src/nfl/`, 30/30 offline self-test passing) and the licence blocker
is cleared. Every step below is still outstanding — nothing has been purchased or started.

1. **Subscribe to the 5M plan, $119/month**, at <https://the-odds-api.com/#get-access>
   (START resolves to <https://dash.the-odds-api.com/>). The key arrives by email.
   *(~5 min, requires a payment decision by Rémi)*
2. Install the key on XenHive **without writing it into the repository or into shell
   history**:
   `printf 'THE_ODDS_API_KEY=%s\nNFL_ENABLED=true\n' '<PASTE_KEY_HERE>' >> /home/xenhive/xenarb/.env`
   `.env` is git-ignored; `provider.js` redacts the key from every log line. *(~2 min)*
3. `pm2 start ecosystem.config.cjs --only xenarb-nfl-board`. *(~1 min)*
4. Run the six-part production evidence gate in `XENARB-NFL-INTEGRATION.md`. *(~30 min)*
5. Only if all six pass: set `enabled: true` and `apiBase` in `xenarb-config.js`, merge
   PR #5, deploy. *(~5 min)*

The fallback path in Rev 2 — server-side rendering or signed requests, in case the endpoint
was ruled out of scope — is no longer needed. The endpoint was approved as built.

**Until a licensed historical backfill has been run and verified, the board's column reads
"First seen", never "Opening".** It is driven by `openingSource` in the board contract, so it
relabels itself only when XenArb reports `provider_historical`.
