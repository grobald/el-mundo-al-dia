"""Daily SerpAPI Google News research + AI editorial briefing. Python 3.11+."""
import os, json, re, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / 'data'
DATA.mkdir(exist_ok=True)

TOPICS = [
    ('Geopolítica', 'Geopolitik', 'geopolitics world diplomacy conflict (Reuters OR AP OR BBC OR DW OR AFP)', 'us', 'en'),
    ('Geopolítica', 'Geopolitik', 'geopolítica diplomacia conflicto (Reuters OR BBC OR DW OR AFP)', 'us', 'es'),
    ('Europa y Austria', 'Europa und Österreich', 'Austria Europe politics economy (ORF OR APA OR Reuters OR DW OR "Der Standard")', 'at', 'de'),
    ('Estados Unidos', 'Vereinigte Staaten', 'United States politics (Reuters OR AP OR Bloomberg OR BBC)', 'us', 'en'),
    ('Perú', 'Peru', 'Peru noticias actualidad (Andina OR RPP OR Gestión OR Reuters OR BBC)', 'pe', 'es'),
    ('Perú', 'Peru', 'sismo OR temblor Perú magnitud IGP', 'pe', 'es'),
    ('Economía', 'Wirtschaft', 'world economy financial markets (Bloomberg OR Reuters OR "Financial Times" OR CNBC)', 'us', 'en'),
    ('Inteligencia artificial', 'Künstliche Intelligenz', 'artificial intelligence technology (Reuters OR Bloomberg OR BBC OR Wired)', 'us', 'en'),
    ('Criptomonedas', 'Kryptowährungen', 'bitcoin cryptocurrency regulation (Reuters OR Bloomberg OR CoinDesk)', 'us', 'en'),
]
REGIONS = {'Perú': 'peru', 'Estados Unidos': 'us', 'Europa y Austria': 'at-eu'}
CAT_DE = {
    'Geopolítica': 'Geopolitik', 'Europa y Austria': 'Europa und Österreich',
    'Estados Unidos': 'Vereinigte Staaten', 'Perú': 'Peru', 'Economía': 'Wirtschaft',
    'Inteligencia artificial': 'Künstliche Intelligenz', 'Criptomonedas': 'Kryptowährungen', 'Mundo': 'Welt',
}
PREFERRED = re.compile(
    r'reuters|associated press|\bap\b|bbc|orf|deutsche welle|\bdw\b|andina|\brpp\b|'
    r'bloomberg|financial times|\bft\b|gestión|gestion|apa|der standard|afp',
    re.I,
)
AGENTS = {'User-Agent': 'ElMundoAlDia/1.0 (personal news reader)'}

EDITOR_PROMPT = '''You are the senior news editor and researcher for "El Mundo al Día",
a daily Spanish-language international news briefing for families (Peruvian Spanish + Austrian German).

You receive a RESEARCH PACK with SerpAPI Google News headlines (id, category, title, source, published, url, optional snippet),
a market snapshot with verified prices, the 24-hour reporting window, and an explicit research limitation.
You do NOT receive full article texts. Never invent facts beyond the pack.

TASK
Research and summarize the 7–10 most important news stories from the last 24 hours (fewer if necessary).

PRIORITIES
1. Global geopolitics, conflicts, and diplomacy
2. Europe and Austria
3. United States
4. Peru
5. Economy, financial markets, and energy
6. Artificial intelligence and technology
7. Cryptocurrencies and blockchain

RESEARCH & VERIFICATION
- Prefer Reuters, AP, BBC, ORF, DW, Andina, RPP, Bloomberg, Financial Times and similar outlets when present.
- Verify major claims using at least two independent headlines/snippets whenever possible; otherwise label as single-source.
- Check event dates, publication dates, and article URLs from the pack only.
- Distinguish confirmed facts, attributed claims, and rumors.
- Never invent events, quotes, figures, prices, or sources.
- Exclude outdated, duplicated, or insufficiently verified news.
- Include Peru and Austria when relevant verified news exists.

EDITORIAL REQUIREMENTS
- Highlight the three most significant stories with is_top=true and put them first.
- Write clear, neutral, accessible Spanish (Peruvian-friendly) and Austrian German (*_de) with NO added facts.
- ALWAYS rewrite title into Spanish. Never leave English/German source headlines as the published title.
- Prefer at least one Peru story when the pack contains verified Peru headlines.
- summary: 80–120 words.
- For each story return the exact headline id and that headline's url exactly. Optional sources: 1–3 pack urls only.
- Markets: only from the research pack; omit missing assets. Do not invent S&P/Nasdaq/gold/Brent if absent.

OUTPUT
Return JSON only:
{"edition_date":"YYYY-MM-DD","reporting_window":"...","headline":"...","intro":"...","headline_de":"...","intro_de":"...","stories":[{"id":"h1","is_top":true,"category":"...","country_region":"...","event_date":"YYYY-MM-DD","title":"...","summary":"...","confirmed_facts":"...","unverified_claims":"...","impact":"...","verification":"...","title_de":"...","summary_de":"...","impact_de":"...","verification_de":"...","source":"...","url":"...","sources":[{"id":"h1","url":"...","source":"...","published":"..."}]}],"peru_update":"...","austria_update":"...","peru_update_de":"...","austria_update_de":"...","markets":{"items":[{"symbol":"BTC","price":0,"as_of":"...","source":"..."}],"note":"..."},"conclusion":"...","conclusion_de":"..."}

IMPORTANT
Accuracy and verifiable sources beat story count. Never present speculation as fact.
verification must include: Información basada en investigación de titulares/snippets vía SerpAPI; consultar las fuentes originales.
verification_de must include: Information beruht auf SerpAPI-Titeln/Snippets; Originalquellen prüfen.
'''


def fetch(url):
    req = urllib.request.Request(url, headers=AGENTS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def fetch_json(url):
    return json.loads(fetch(url).decode('utf-8'))


def source_name(value):
    if not value:
        return 'Google News'
    if isinstance(value, str):
        return value.strip() or 'Google News'
    return str(value.get('name') or value.get('title') or 'Google News').strip() or 'Google News'


def parse_when(row):
    raw = row.get('iso_date') or row.get('date') or row.get('published')
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        ms = raw * 1000 if raw < 1e12 else raw
        dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
        return dt
    text = str(raw).strip()
    try:
        return datetime.fromisoformat(text.replace('Z', '+00:00')).astimezone(timezone.utc)
    except Exception:
        pass
    m = re.search(r'(\d+)\s+(minute|minutes|hour|hours|day|days|minuto|minutos|hora|horas|día|dias|días)', text, re.I)
    if not m:
        return None
    n = int(m.group(1))
    unit = m.group(2).lower()
    now = datetime.now(timezone.utc)
    if 'minute' in unit or 'minuto' in unit:
        return now - timedelta(minutes=n)
    if 'hour' in unit or 'hora' in unit:
        return now - timedelta(hours=n)
    return now - timedelta(days=n)


def fact_score(title, source):
    score = min(len(re.findall(r'\d', title)), 8)
    if re.search(r'\bmagnitud\s*\d', title, re.I):
        score += 12
    if re.search(r'\bIGP\b', title):
        score += 8
    if PREFERRED.search(source) or PREFERRED.search(title):
        score += 10
    if re.search(r'\b(conoce|revisa|ent[eé]rate|en vivo)\b', title, re.I) and not re.search(r'\d', title):
        score -= 8
    return score


def collect():
    key = os.environ.get('SERPAPI_API_KEY', '').strip()
    if not key:
        raise RuntimeError('SERPAPI_API_KEY no configurada.')
    cutoff = datetime.now(timezone.utc) - timedelta(hours=30)
    out = []
    seen = set()
    for cat, cat_de, query, gl, hl in TOPICS:
        params = urllib.parse.urlencode({
            'engine': 'google_news',
            'q': query + ' when:1d',
            'gl': gl,
            'hl': hl,
            'api_key': key,
            'json_restrictor': 'news_results[0:12].{title,link,source,date,snippet,iso_date}',
        })
        try:
            data = fetch_json('https://serpapi.com/search.json?' + params)
        except Exception as exc:
            print('SerpAPI failed', cat, exc)
            continue
        for row in (data.get('news_results') or [])[:12]:
            title = str(row.get('title') or '').strip()
            link = str(row.get('link') or row.get('url') or '').strip()
            when = parse_when(row)
            if not title or not link or not when or when < cutoff or link in seen:
                continue
            seen.add(link)
            source = source_name(row.get('source'))
            snippet = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', str(row.get('snippet') or ''))).strip()[:320]
            item = {
                'category': cat,
                'category_de': cat_de,
                'title': title,
                'url': link,
                'source': source,
                'published': when.isoformat(),
                'fact_score': fact_score(title, source),
            }
            if snippet and snippet != title:
                item['snippet'] = snippet
            out.append(item)
    out.sort(key=lambda x: (-x['fact_score'], x['published']), reverse=False)
    out.sort(key=lambda x: (-x['fact_score'], x['published']))
    selected = []
    for i, item in enumerate(out[:80]):
        row = {
            'id': f'h{i + 1}',
            'category': item['category'],
            'category_de': item['category_de'],
            'title': item['title'],
            'source': item['source'],
            'published': item['published'],
            'url': item['url'],
        }
        if item.get('snippet'):
            row['snippet'] = item['snippet']
        selected.append(row)
    return selected


def markets_pack(now):
    items = []
    try:
        cg = fetch_json(
            'https://api.coingecko.com/api/v3/simple/price?'
            'ids=bitcoin,ethereum&vs_currencies=usd&include_last_updated_at=true'
        )
        for symbol, key in (('BTC', 'bitcoin'), ('ETH', 'ethereum')):
            row = cg.get(key) or {}
            if row.get('usd') is None:
                continue
            as_of = now.isoformat()
            if row.get('last_updated_at'):
                as_of = datetime.fromtimestamp(row['last_updated_at'], tz=timezone.utc).isoformat()
            items.append({'symbol': symbol, 'price_usd': row['usd'], 'as_of': as_of, 'source': 'CoinGecko'})
    except Exception as exc:
        print('CoinGecko failed', exc)
    try:
        fx = fetch_json('https://api.frankfurter.app/latest?from=EUR&to=USD')
        if fx.get('rates', {}).get('USD') is not None:
            items.append({
                'symbol': 'EUR/USD',
                'price': fx['rates']['USD'],
                'as_of': (fx.get('date') or now.date().isoformat()) + 'T00:00:00Z',
                'source': 'Frankfurter.app',
            })
    except Exception as exc:
        print('Frankfurter failed', exc)
    return {
        'note': 'Solo precios verificados del research pack. Si falta un activo, omitirlo.',
        'source': 'CoinGecko + Frankfurter',
        'fetched_at': now.isoformat(),
        'items': items,
    }


def summarize(pack):
    key = os.environ.get('OPENAI_API_KEY', '').strip()
    if not key:
        raise RuntimeError('OPENAI_API_KEY no configurada.')
    from openai import OpenAI
    client = OpenAI(api_key=key)
    response = client.chat.completions.create(
        model=os.environ.get('OPENAI_MODEL', 'gpt-4.1-mini'),
        temperature=0.1,
        response_format={'type': 'json_object'},
        messages=[
            {'role': 'system', 'content': EDITOR_PROMPT},
            {'role': 'user', 'content': json.dumps(pack, ensure_ascii=False)},
        ],
    )
    return json.loads(response.choices[0].message.content)


def region_of(category, country_region=''):
    c = (category or '').lower()
    r = (country_region or '').lower()
    if re.search(r'per[uú]', c) or re.search(r'per[uú]', r):
        return 'peru'
    if re.search(r'estados unidos|ee\.?\s?uu|usa|united states', c) or re.search(r'usa|united states|ee\.?\s?uu', r):
        return 'us'
    if re.search(r'austria|österreich|europa|europe|uni[oó]n europea', c) or re.search(r'austria|österreich|europe|\beu\b', r):
        return 'at-eu'
    return 'world'


def main():
    headlines = collect()
    print('Collected', len(headlines), 'headlines')
    if len(headlines) < 10:
        raise RuntimeError('Insuficientes titulares recientes; se conserva la edición anterior.')
    now = datetime.now(ZoneInfo('Europe/Vienna'))
    window_start = now - timedelta(hours=24)
    markets = markets_pack(now.astimezone(timezone.utc))
    pack = {
        'edition_date': now.date().isoformat(),
        'reporting_window': {
            'start': window_start.isoformat(),
            'end': now.isoformat(),
            'label': f"{window_start.strftime('%d/%m/%Y %H:%M')} – {now.strftime('%d/%m/%Y %H:%M')} (Austria)",
        },
        'headlines': headlines,
        'markets': markets,
        'research_limitation': (
            'La investigación usa Google News vía SerpAPI (titulares, snippets, fechas y enlaces) '
            'más precios de CoinGecko/Frankfurter. No se leen artículos completos.'
        ),
    }
    edition = summarize(pack)
    by_id = {x['id']: x for x in headlines}
    by_url = {x['url']: x for x in headlines}
    cleaned = []
    used = set()
    top_count = 0
    allowed_symbols = {str(x.get('symbol', '')).upper() for x in markets.get('items', [])}
    for story in edition.get('stories', []):
        original = by_id.get(str(story.get('id', '')).strip()) or by_url.get(str(story.get('url', '')).strip())
        if not original or original['url'] in used:
            continue
        used.add(original['url'])
        is_top = bool(story.get('is_top')) or top_count < 3
        if is_top:
            top_count += 1
        extras = []
        for src in story.get('sources') or []:
            ref = by_id.get(str(src.get('id', '')).strip()) or by_url.get(str(src.get('url', '')).strip())
            if not ref or ref['url'] == original['url']:
                continue
            if any(x['url'] == ref['url'] for x in extras):
                continue
            extras.append({'source': ref['source'], 'url': ref['url'], 'published': ref['published']})
            if len(extras) >= 2:
                break
        cleaned.append({
            'category': original['category'],
            'category_de': original.get('category_de') or CAT_DE.get(original['category'], original['category']),
            'region': region_of(original['category'], story.get('country_region', '')),
            'country_region': str(story.get('country_region') or ''),
            'event_date': str(story.get('event_date') or '')[:10],
            'is_top': is_top,
            'title': str(story.get('title') or original['title']),
            'title_de': str(story.get('title_de') or ''),
            'summary': str(story.get('summary') or ''),
            'summary_de': str(story.get('summary_de') or ''),
            'confirmed_facts': str(story.get('confirmed_facts') or ''),
            'unverified_claims': str(story.get('unverified_claims') or ''),
            'impact': str(story.get('impact') or ''),
            'impact_de': str(story.get('impact_de') or ''),
            'verification': 'Información basada en investigación de titulares/snippets vía SerpAPI; consultar las fuentes originales. ' + str(story.get('verification') or ''),
            'verification_de': 'Information beruht auf SerpAPI-Titeln/Snippets; Originalquellen prüfen. ' + str(story.get('verification_de') or ''),
            'source': original['source'],
            'url': original['url'],
            'published': original['published'],
            'sources': [{'source': original['source'], 'url': original['url'], 'published': original['published']}, *extras],
        })
    if len(cleaned) < 5:
        raise RuntimeError('Selección insuficiente; se conserva la edición anterior.')
    day = now.date().isoformat()
    market_items = []
    for item in (edition.get('markets') or {}).get('items') or markets.get('items') or []:
        symbol = str(item.get('symbol') or '').upper()
        price = item.get('price', item.get('price_usd'))
        if symbol in allowed_symbols and price is not None:
            market_items.append({
                'symbol': symbol,
                'price': price,
                'as_of': str(item.get('as_of') or ''),
                'source': str(item.get('source') or ''),
            })
    payload = {
        'date': day,
        'date_label': now.strftime('%d/%m/%Y · %H:%M (Austria)'),
        'reporting_window': pack['reporting_window']['label'],
        'demo': False,
        'headline': str(edition.get('headline') or 'Las noticias del día'),
        'headline_de': str(edition.get('headline_de') or ''),
        'intro': str(edition.get('intro') or ''),
        'intro_de': str(edition.get('intro_de') or ''),
        'peru_update': str(edition.get('peru_update') or ''),
        'austria_update': str(edition.get('austria_update') or ''),
        'peru_update_de': str(edition.get('peru_update_de') or ''),
        'austria_update_de': str(edition.get('austria_update_de') or ''),
        'markets': {'note': str((edition.get('markets') or {}).get('note') or markets.get('note') or ''), 'items': market_items},
        'conclusion': str(edition.get('conclusion') or ''),
        'conclusion_de': str(edition.get('conclusion_de') or ''),
        'stories': cleaned[:10],
    }
    (DATA / (day + '.json')).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    manifest = DATA / 'manifest.json'
    old = json.loads(manifest.read_text()) if manifest.exists() else {'editions': []}
    editions = [{'date': day, 'file': day + '.json'}] + [x for x in old['editions'] if x['date'] != day]
    manifest.write_text(json.dumps({'editions': editions[:90]}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Published edition', day)


if __name__ == '__main__':
    main()
