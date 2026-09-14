#!/usr/bin/env python3
"""Build xenarb-nfl.json for the public pre-lander.

Runs server-side ONLY. Reads MONSTER_API_KEY from /home/xenhive/xenarb/.env and
never writes it to the output. Emits a matchup only when the live feed carries
every field needed to state it truthfully; anything short of that is dropped,
so the page has nothing to invent. Zero matchups is a valid, expected result -
the module then hides itself.
"""
import json, os, sys, urllib.request, datetime

ENVF = '/home/xenhive/xenarb/.env'
API = 'https://api-v2.monster.bet/v1/arbitrage/snapshot?sport=all&limit=200'
OUT = sys.argv[1] if len(sys.argv) > 1 else 'site/xenarb-nfl.json'

key = None
for line in open(ENVF, encoding='utf-8', errors='replace'):
    if line.startswith('MONSTER_API_KEY='):
        key = line.split('=', 1)[1].strip().strip('"').strip("'"); break
if not key:
    print('MONSTER_API_KEY missing', file=sys.stderr); sys.exit(2)

req = urllib.request.Request(API, headers={
    'Authorization': 'Bearer ' + key, 'Accept': 'application/json'})
with urllib.request.urlopen(req, timeout=45) as r:
    snap = json.load(r)

items = snap.get('items') or []
src_ts = snap.get('ts')

NFL_HINT = ('nfl', 'pro football')

def is_nfl_sportsbook_matchup(it):
    """A record qualifies only if it is a sportsbook-pipeline NFL *game*.

    The prediction pipeline carries Polymarket/Kalshi season futures ("will X
    win the MVP"), not matchups: no two teams meeting, no kickoff, no line.
    Those can never satisfy the module contract, so they are excluded by
    pipeline before anything else is considered.
    """
    if it.get('pipeline') != 'sportsbook':
        return False
    if str(it.get('sport', '')).lower() not in ('nfl', 'americanfootball_nfl'):
        return False
    return True

REQUIRED = ('teams', 'kickoff')

def to_matchup(it):
    """Map a qualifying record, or return None if any required field is absent.

    Never synthesises, defaults or rounds a value into existence.
    """
    teams = it.get('teams') or {}
    away, home = teams.get('away'), teams.get('home')
    kickoff = it.get('kickoff') or it.get('commence_time')
    if not (away and home and kickoff):
        return None

    signals = []
    mv = it.get('line_movement') or {}
    if mv.get('open') is not None and mv.get('current') is not None:
        signals.append({'kind': 'line_movement', 'open': mv['open'],
                        'current': mv['current'], 'market': mv.get('market'),
                        'observedAt': mv.get('observed_at')})
    ctx = it.get('injury_context') or it.get('context')
    if ctx:
        signals.append({'kind': 'context', 'text': str(ctx)})
    books = it.get('books') or []
    if len(books) >= 2:
        signals.append({'kind': 'disagreement',
                        'books': [{'book': b.get('sportsbook'),
                                   'price': b.get('price'),
                                   'value': b.get('value')} for b in books]})
    if not signals:
        return None          # nothing verified to show -> do not show the row

    return {'eventId': it.get('game_id') or it.get('matched_pair_id'),
            'away': away, 'home': home, 'kickoff': kickoff,
            'signals': signals,
            'provider': it.get('best_book') or it.get('provider'),
            'observedAt': (it.get('orderbook') or {}).get('snapshot_age_anchor')}

cands = [i for i in items if is_nfl_sportsbook_matchup(i)]
matchups = [m for m in (to_matchup(i) for i in cands) if m][:5]

doc = {
    'schemaVersion': '1.0',
    'source': 'Monster.bet arbitrage API v1 (XenArb)',
    'sourceTimestamp': src_ts,
    'generatedAt': datetime.datetime.now(datetime.timezone.utc)
                   .replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
    'itemsScanned': len(items),
    'nflSportsbookCandidates': len(cands),
    'matchups': matchups,
}
os.makedirs(os.path.dirname(OUT) or '.', exist_ok=True)
json.dump(doc, open(OUT, 'w', encoding='utf-8'), indent=1)

pipe = {}
for i in items:
    pipe[i.get('pipeline')] = pipe.get(i.get('pipeline'), 0) + 1
sport = {}
for i in items:
    if i.get('pipeline') == 'sportsbook':
        sport[str(i.get('sport'))] = sport.get(str(i.get('sport')), 0) + 1

print(f'snapshot ts          : {src_ts}')
print(f'items scanned        : {len(items)}')
print(f'pipeline breakdown   : {pipe}')
print(f'sportsbook by sport  : {sport}')
print(f'NFL sportsbook cands : {len(cands)}')
print(f'matchups published   : {len(matchups)}')
print(f'wrote                : {OUT}')
