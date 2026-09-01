# NFL odds provider — definitive purchase decision

Rev 2, 2026-09-01. Supersedes Rev 1 and the earlier SportsGameOdds recommendation.
Nothing has been purchased. No account has been created.

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

The shipped poller defaults to 60 seconds, tightening to 30 seconds while a game is live or
within 60 minutes of kickoff:

| Window | Hours / week | Interval | Requests / week |
|---|---|---|---|
| Live + 60 min pre-kickoff (Thu / Sun / Mon) | ~19 | 30s | 2,280 |
| Remainder | ~149 | 60s | 8,940 |
| **Total** | 168 | | **11,220** |

- **33,660 credits per week** (11,220 × 3)
- **≈ 145,900 credits per month** (33,660 × 52 ÷ 12)

That exceeds the 100K plan, which is why the 5M plan is the purchase. Utilisation on 5M is
**2.9%**, leaving room for retries, a second sport, and any runaway-poller incident.

For completeness: the $59 100K plan fits only at a flat 2-minute interval
(5,040 requests/week → 15,120 credits/week → ~65,700/month, 66% utilisation). A two-minute-old
line is a poor foundation for a product whose selling point is line movement, and the
saving is $60/month.

**Not published:** the provider documents a 1-minute update interval for *additional*
markets but publishes no refresh SLA for featured markets. Every quote carries the
provider's own `last_update`, which the board surfaces verbatim. Confirming the featured-market
cadence is one of the questions in the email below.

### 4. Written confirmation covering the private CORS-restricted endpoint

**PENDING — this is the one remaining blocker.**

Our static front end cannot hold an API key, so XenArb exposes `GET /v1/nfl/board`. The
Restrictions clause names "offering our data through your own API" as prohibited. Our
endpoint is the transport layer of our own site, not a product offered to others, but that
is our reading and not theirs.

Email sent 2026-09-01 to `team@the-odds-api.com`, the address published in their terms,
which also state "If you are unsure whether your use case is permitted, please contact us."
Gmail message id `1a05e2a741c8e5df`. It sets out the exact intended use, the endpoint's
CORS lock, the absence of third-party credentials, and asks for confirmation or for the
arrangement they would accept instead. It also asks the two open technical questions
(featured-market refresh interval; rate limits beyond the credit quota).

**Do not purchase until that reply is in hand.**

---

## Alternatives, for the record

| Provider | Cost | Activation | Why not |
|---|---|---|---|
| SportsGameOdds — Rookie | $99 /mo | Self-serve | Was the right call while The Odds API's terms were silent. Now costs less for an equivalent express display right elsewhere, and the same "no data dumps, feeds or white-label" restriction applies to our endpoint, so it does not remove the pending question either. |
| OddsBlaze | $29–$999 /mo | Self-serve | $29 tier runs ~2 minutes behind; sub-second needs $249+. Redistribution terms not published. |
| SportsDataIO | Quote only | Days to weeks | Best long-term feed. Cannot activate before Week 1. Its public $99/mo Discovery Lab plan is next-day delayed and not licensed for commercial redistribution. |
| OddsJam | ~$4,995 /mo | Sales call | ~40× budget. Third-party price report; they publish none. |
| OpticOdds | ~$5,000 /mo per sport | Sales call | Same. |
| Sportradar / LSports | Quote only | Weeks + compliance | Not achievable this week at any price. |

---

## Same-day activation sequence

The integration is already built and tested behind a disabled flag
(`/home/xenhive/xenarb/src/nfl/`, 30/30 offline self-test passing). Once the reply arrives:

1. Reply confirms the endpoint → subscribe to the 5M plan at
   <https://dash.the-odds-api.com/>; key arrives by email. *(~5 min)*
2. Put the key in `/home/xenhive/xenarb/.env` as `THE_ODDS_API_KEY`, set
   `NFL_ENABLED=true`. *(~2 min)*
3. `pm2 start ecosystem.config.cjs --only xenarb-nfl-board`. *(~1 min)*
4. Run the six-part production evidence gate in `XENARB-NFL-INTEGRATION.md`. *(~30 min)*
5. Only if all six pass: set `enabled: true` and `apiBase` in `xenarb-config.js`, merge
   PR #5. *(~5 min)*

If the reply instead says the endpoint is out of scope, step 1 becomes server-side rendering
or signed requests to that endpoint; nothing else in the pipeline changes, and the flag stays off.

**Until a licensed historical backfill has been run and verified, the board's column reads
"First seen", never "Opening".** It is driven by `openingSource` in the board contract, so it
relabels itself only when XenArb reports `provider_historical`.
