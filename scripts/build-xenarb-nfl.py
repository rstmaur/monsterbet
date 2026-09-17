#!/usr/bin/env python3
"""Resolve Monster.bet NFL signals and publish the public intelligence file.

Runs server-side ONLY, on a schedule. Reads MONSTER_API_KEY from
/home/xenhive/xenarb/.env and never writes it to the output.

Pipeline
--------
1.  Pull the arbitrage snapshot (the provider's only data route).
2.  Keep `pipeline == 'sportsbook'` AND `sport == 'nfl'` rows. Filtering on
    `sport=` server-side is broken (it returns 0 in the same second the
    unfiltered call returns NFL rows), so filter client-side and always pass
    an explicit high `limit` - NFL rows sit past the default page of 100.
3.  For every row, try to RESOLVE the fields the public strip needs but the
    arbitrage record does not carry, by calling the resolver chain below with
    the row's `game_id`.
4.  Publish a signal ONLY when every required field resolved. Nothing is
    defaulted, rounded, inferred or carried over from a previous run.

A signal needs all of: home + away, sportsbook, first-seen price, current
price, and a source timestamp. Zero publishable signals is a valid result -
the page then renders no section at all.

Exit status is 0 whenever the run completed, including a zero-signal run;
a non-zero status means the run itself failed and the previous file stands.
"""
import json, os, sys, urllib.request, urllib.error, datetime, argparse

ENVF = '/home/xenhive/xenarb/.env'
BASE = 'https://api-v2.monster.bet'
SNAP = BASE + '/v1/arbitrage/snapshot?sport=all&limit=500'

# Resolver chain: every published path that could turn an opaque `game_id`
# into a matchup. Probed in order; the first 200 with a usable body wins.
RESOLVERS = [
    '/v1/games/{gid}', '/v1/game/{gid}', '/v1/events/{gid}', '/v1/event/{gid}',
    '/v1/matches/{gid}', '/v1/fixtures/{gid}',
    '/v1/games?ids={gid}', '/v1/games?game_id={gid}',
    '/v1/arbitrage/game/{gid}', '/v1/arbitrage/{gid}',
    '/v1/odds?game_id={gid}', '/v1/lines?game_id={gid}',
    '/v1/markets?game_id={gid}', '/v1/quotes?game_id={gid}',
    '/v1/history?game_id={gid}', '/v1/arbitrage/history?game_id={gid}',
]
REQUIRED = ('away', 'home', 'kickoff', 'sportsbook', 'firstSeenPrice',
            'currentPrice', 'observedAt')


def api_key():
    for line in open(ENVF, encoding='utf-8', errors='replace'):
        if line.startswith('MONSTER_API_KEY='):
            return line.split('=', 1)[1].strip().strip('"').strip("'")
    print('MONSTER_API_KEY missing from ' + ENVF, file=sys.stderr)
    sys.exit(2)


def get(url, key, timeout=30):
    """Return (status, body-bytes). Never raises on an HTTP error status."""
    rq = urllib.request.Request(url, headers={
        'Authorization': 'Bearer ' + key, 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(rq, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def resolve_game(gid, key, probe_log):
    """Try to turn `game_id` into the fields the arbitrage record lacks.

    Returns a dict of whatever resolved. An empty dict means the provider
    exposes no route that answers for this id - which is the current state,
    and the reason the public strip stays hidden.
    """
    found = {}
    for tpl in RESOLVERS:
        path = tpl.format(gid=gid)
        status, body = get(BASE + path, key)
        probe_log.append({'path': path, 'status': status, 'bytes': len(body)})
        if status != 200 or not body:
            continue
        try:
            doc = json.loads(body)
        except ValueError:
            continue
        # A route that ignores the id and echoes the whole snapshot back is
        # not a resolver. Reject anything that does not narrow to this game.
        if isinstance(doc, dict) and 'items' in doc:
            ids = {str(i.get('game_id')) for i in (doc.get('items') or [])}
            if ids != {str(gid)}:
                probe_log[-1]['note'] = 'ignored game_id; returned full set'
                continue
        for src, dst in (('home_team', 'home'), ('away_team', 'away'),
                         ('home', 'home'), ('away', 'away'),
                         ('commence_time', 'kickoff'), ('kickoff', 'kickoff'),
                         ('start_time', 'kickoff')):
            if isinstance(doc, dict) and doc.get(src) and dst not in found:
                found[dst] = doc[src]
        if found:
            found['resolvedBy'] = path
            break
    return found


def build_signal(row, key, probe_log):
    """Join an arbitrage row with its resolved game. None if incomplete."""
    gid = row.get('game_id')
    if gid is None:
        return None, ['game_id']
    resolved = resolve_game(gid, key, probe_log)

    legs = row.get('legs') or []
    book = None
    for leg in legs:
        if leg.get('best_book') and leg['best_book'] != 'polymarket_us':
            book = leg['best_book']
            break

    candidate = {
        'eventId': str(gid),
        'away': resolved.get('away'),
        'home': resolved.get('home'),
        'kickoff': resolved.get('kickoff'),
        'market': row.get('market_key'),
        'outcome': legs[0].get('outcome') if legs else None,
        'sportsbook': book,
        # The arbitrage record carries a no-vig FAIR decimal, not a price the
        # book actually posted, and carries no earlier observation at all.
        # Neither may be presented as a quoted price, so both stay None until
        # a route exposes them.
        'currentPrice': None,
        'firstSeenPrice': None,
        'observedAt': None,
    }
    missing = [f for f in REQUIRED if not candidate.get(f)]
    return (None, missing) if missing else (candidate, [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out', nargs='?', default='nfl-intel.json')
    ap.add_argument('--probe-out', default=None,
                    help='write the raw resolver probe log here')
    args = ap.parse_args()

    key = api_key()
    status, body = get(SNAP, key, timeout=45)
    if status != 200:
        print('snapshot HTTP %s' % status, file=sys.stderr)
        sys.exit(3)
    snap = json.loads(body)

    items = snap.get('items') or []
    cands = [i for i in items
             if i.get('pipeline') == 'sportsbook'
             and str(i.get('sport', '')).lower() in ('nfl', 'americanfootball_nfl')]

    probe_log, signals, missing_union = [], [], set()
    for row in cands:
        sig, missing = build_signal(row, key, probe_log)
        if sig:
            signals.append(sig)
        else:
            missing_union.update(missing)

    now = (datetime.datetime.now(datetime.timezone.utc)
           .replace(microsecond=0).isoformat().replace('+00:00', 'Z'))
    doc = {
        'schemaVersion': '2.0',
        'source': 'Verified Monster.bet intelligence',
        'sourceTimestamp': snap.get('ts'),
        'generatedAt': now,
        'itemsScanned': len(items),
        'nflSportsbookCandidates': len(cands),
        'signals': signals[:3],
        'unresolvedFields': sorted(missing_union),
    }
    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    json.dump(doc, open(args.out, 'w', encoding='utf-8'), indent=1)
    open(args.out, 'a').write('\n')

    if args.probe_out:
        json.dump({'generatedAt': now, 'gameIds': [c.get('game_id') for c in cands],
                   'probes': probe_log},
                  open(args.probe_out, 'w', encoding='utf-8'), indent=1)

    print('snapshot ts          : %s' % snap.get('ts'))
    print('items scanned        : %d' % len(items))
    print('NFL sportsbook rows  : %d  (game_ids: %s)'
          % (len(cands), ', '.join(str(c.get('game_id')) for c in cands)))
    print('resolver calls made  : %d' % len(probe_log))
    print('signals published    : %d' % len(doc['signals']))
    print('unresolved fields    : %s' % (', '.join(doc['unresolvedFields']) or '-'))
    print('wrote                : %s' % args.out)


if __name__ == '__main__':
    main()
