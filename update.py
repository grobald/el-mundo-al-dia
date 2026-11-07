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
    ('Geopolítica', 'Geopolitik', 'site:reuters.com', 'us', 'en'),
    ('Geopolítica', 'Geopolitik', 'site:apnews.com', 'us', 'en'),
    ('Europa y Austria', 'Europa und Österreich', 'Austria Europe politics economy (ORF OR APA OR Reuters OR DW OR "Der Standard")', 'at', 'de'),
    ('Estados Unidos', 'Vereinigte Staaten', 'United States politics (Reuters OR AP OR Bloomberg OR BBC)', 'us', 'en'),
    ('Perú', 'Peru', 'Peru noticias actualidad (Andina OR RPP OR Gestión OR Reuters OR BBC)', 'pe', 'es'),
    ('Perú', 'Peru', 'sismo OR temblor Perú magnitud IGP', 'pe', 'es'),
    ('Economía', 'Wirtschaft', 'world economy financial markets (Bloomberg OR Reuters OR "Financial Times" OR CNBC)', 'us', 'en'),
    ('Economía', 'Wirtschaft', 'site:bloomberg.com', 'us', 'en'),
    ('Economía', 'Wirtschaft', 'site:ft.com', 'us', 'en'),
    ('Inteligencia artificial', 'Künstliche Intelligenz', 'artificial intelligence technology (Reuters OR Bloomberg OR BBC OR Wired)', 'us', 'en'),
    ('Criptomonedas', 'Kryptowährungen', 'bitcoin cryptocurrency regulation (Reuters OR Bloomberg OR CoinDesk)', 'us', 'en'),
]
OUTLET_FEEDS = [
    ('Europa y Austria', 'Europa und Österreich', 'ORF', 'https://rss.orf.at/news.xml'),
    ('Europa y Austria', 'Europa und Österreich', 'ORF', 'https://rss.orf.at/oesterreich.xml'),
    ('Europa y Austria', 'Europa und Österreich', 'Der Standard', 'https://www.derstandard.at/rss'),
    ('Europa y Austria', 'Europa und Österreich', 'DW', 'https://rss.dw.com/rdf/rss-de-eu'),
    ('Europa y Austria', 'Europa und Österreich', 'BBC', 'https://feeds.bbci.co.uk/news/world/europe/rss.xml'),
    ('Estados Unidos', 'Vereinigte Staaten', 'BBC', 'https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml'),
    ('Estados Unidos', 'Vereinigte Staaten', 'NPR', 'https://feeds.npr.org/1001/rss.xml'),
    ('Geopolítica', 'Geopolitik', 'BBC Mundo', 'https://feeds.bbci.co.uk/mundo/rss.xml'),
    ('Geopolítica', 'Geopolitik', 'BBC', 'https://feeds.bbci.co.uk/news/world/rss.xml'),
    ('Geopolítica', 'Geopolitik', 'DW', 'https://rss.dw.com/rdf/rss-sp-inter'),
    ('Perú', 'Peru', 'Andina', 'https://andina.pe/agencia/rss.aspx'),
    ('Perú', 'Peru', 'RPP', 'https://rpp.pe/feed'),
    ('Perú', 'Peru', 'RPP', 'https://rpp.pe/feed/politica'),
    ('Perú', 'Peru', 'RPP', 'https://rpp.pe/feed/actualidad'),
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

EDITOR_PROMPT = (Path(__file__).parent / 'prompt.md').read_text(encoding='utf-8') if (Path(__file__).parent / 'prompt.md').exists() else '''
Select 7-10 verified stories from the last 24 hours on geopolitics, EU/Austria, USA, Peru,
economy/markets, AI/tech, crypto, major climate/energy, and significant social/education policy.
Exclude sports, culture, entertainment, lifestyle, travel, food, shopping, celebrities, viral trivia,
astrology, isolated crime without public relevance, and minor science without impact, unless the
EXCEPTION RULE applies (substantial geopolitical, economic, regulatory, scientific, public-health
or societal consequences). Prefer fewer high-quality stories; do not force equal category counts.
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


MONTH_MAP = {
    'january': 0, 'febrero': 1, 'february': 1, 'marzo': 2, 'march': 2, 'abril': 3, 'april': 3,
    'mayo': 4, 'may': 4, 'junio': 5, 'june': 5, 'julio': 6, 'july': 6, 'agosto': 7, 'august': 7,
    'septiembre': 8, 'september': 8, 'octubre': 9, 'october': 9, 'noviembre': 10, 'november': 10,
    'diciembre': 11, 'december': 11, 'enero': 0,
}


def fact_score(title, source, origin='serpapi'):
    score = min(len(re.findall(r'\d', title)), 8)
    if re.search(r'\bmagnitud\s*\d', title, re.I):
        score += 12
    if re.search(r'\bIGP\b', title):
        score += 8
    if PREFERRED.search(source) or PREFERRED.search(title):
        score += 10
    if origin == 'rss' and PREFERRED.search(source):
        score += 6
    if re.search(r'\b(conoce|revisa|ent[eé]rate|en vivo)\b', title, re.I) and not re.search(r'\d', title):
        score -= 8
    return score


def is_stale_by_text(title, snippet=''):
    now = datetime.now(timezone.utc)
    text = f'{title} {snippet}'.lower()
    year_match = re.search(r'\b(20\d{2})\b', text)
    if year_match and int(year_match.group(1)) < now.year:
        return True
    month_match = re.search(
        r'\b(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|'
        r'january|february|march|april|may|june|july|august|september|october|november|december)\b',
        text,
    )
    if month_match:
        month = MONTH_MAP.get(month_match.group(1))
        if month is not None and month != (now.month - 1):
            if re.search(r'\b\d{1,2}\b', text) or re.search(r'\b(20\d{2})\b', text):
                return True
    return False


BLOCKED = re.compile(r'britannica|wikipedia|wiki\b|encyclopedia', re.I)
EXCLUDED_TOPIC = re.compile(
    r'\b(f[uú]tbol|football|soccer|nba|nfl|mlb|nhl|bundesliga|champions league|gol\b|partido|'
    r'deportes?|sports?|olympics?|ol[ií]mpic|tenis|tennis|f1\b|formula 1|boxeo|boxing|'
    r'cine\b|pel[ií]cula|movie|hollywood|streaming|netflix|video ?game|esport|celebridad|celebrity|'
    r'influencer|reality|gossip|moda\b|fashion|belleza|beauty|turismo|tourism|hotel|viaje|travel|'
    r'receta|recipe|restaurante|gastronom|oferta|descuento|deal\b|shopping|hor[oó]scopo|astrolog|'
    r'concierto|concert|album|meme\b|viral\b)\b',
    re.I,
)
IMPACT_EXCEPTION = re.compile(
    r'\b(guerra|war|sanci[oó]n|diplomacia|geopol[ií]tica|regulaci[oó]n|inflaci[oó]n|'
    r'banco central|climate|clima|salud p[uú]blica|public health|pandemia|ciberataque|cyber|'
    r'elecciones|election|congreso|parliament|energ[ií]a|opec|nato|onu|imf|fmi)\b',
    re.I,
)


def append_item(out, seen, cutoff, *, category, category_de, title, link, source, when, snippet, origin):
    if not title or not link or not when or when < cutoff or link in seen:
        return
    if is_stale_by_text(title, snippet):
        return
    if BLOCKED.search(source) or BLOCKED.search(title) or BLOCKED.search(link):
        return
    topic_text = f'{title} {snippet}'
    if EXCLUDED_TOPIC.search(topic_text) and not IMPACT_EXCEPTION.search(topic_text):
        return
    seen.add(link)
    item = {
        'category': category,
        'category_de': category_de,
        'title': title,
        'url': link,
        'source': source,
        'published': when.isoformat(),
        'origin': origin,
        'fact_score': fact_score(title, source, origin),
    }
    if snippet and snippet != title:
        item['snippet'] = snippet
    out.append(item)


def collect_rss(out, seen, cutoff):
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime
    for cat, cat_de, source_name_default, feed_url in OUTLET_FEEDS:
        try:
            root = ET.fromstring(fetch(feed_url))
        except Exception as exc:
            print('RSS failed', source_name_default, exc)
            continue
        items = root.findall('.//item') or root.findall('.//{http://purl.org/rss/1.0/}item')
        for item in items[:20]:
            title = (item.findtext('title') or item.findtext('{http://purl.org/rss/1.0/}title') or '').strip()
            link = (item.findtext('link') or item.findtext('{http://purl.org/rss/1.0/}link') or '').strip()
            pub = item.findtext('pubDate') or item.findtext('{http://purl.org/dc/elements/1.1/}date') or ''
            when = None
            if pub:
                try:
                    when = parsedate_to_datetime(pub).astimezone(timezone.utc) if ',' in pub else datetime.fromisoformat(pub.replace('Z', '+00:00'))
                except Exception:
                    when = parse_when({'date': pub})
            raw = item.findtext('description') or item.findtext('{http://purl.org/rss/1.0/}description') or ''
            snippet = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', raw)).strip()[:320]
            append_item(
                out, seen, cutoff,
                category=cat, category_de=cat_de, title=title, link=link,
                source=source_name_default, when=when, snippet=snippet, origin='rss',
            )


def collect():
    key = os.environ.get('SERPAPI_API_KEY', '').strip()
    if not key:
        raise RuntimeError('SERPAPI_API_KEY no configurada.')
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
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
            source = source_name(row.get('source'))
            snippet = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', str(row.get('snippet') or ''))).strip()[:320]
            append_item(
                out, seen, cutoff,
                category=cat, category_de=cat_de, title=title, link=link,
                source=source, when=when, snippet=snippet, origin='serpapi',
            )
    collect_rss(out, seen, cutoff)
    out.sort(key=lambda x: (-x['fact_score'], x['published']))

    def norm_cat(category):
        c = (category or '').lower()
        if re.search(r'per[uú]', c):
            return 'Perú'
        if re.search(r'estados unidos|ee\.?\s?uu|usa|united states', c):
            return 'Estados Unidos'
        if re.search(r'europa|austria|österreich', c):
            return 'Europa y Austria'
        return category or 'Mundo'

    priority = ['Perú', 'Estados Unidos', 'Europa y Austria']
    per_priority, per_source_cap, max_total = 10, 12, 150
    selected_raw, used_urls, per_source, per_cat = [], set(), {}, {}

    def try_add(item, cat_limit=None):
        if item['url'] in used_urls or len(selected_raw) >= max_total:
            return False
        src = (item.get('source') or 'unknown').lower()
        if per_source.get(src, 0) >= per_source_cap:
            return False
        cat = norm_cat(item.get('category'))
        if cat_limit is not None and per_cat.get(cat, 0) >= cat_limit:
            return False
        used_urls.add(item['url'])
        per_source[src] = per_source.get(src, 0) + 1
        per_cat[cat] = per_cat.get(cat, 0) + 1
        item = dict(item)
        item['category'] = cat
        selected_raw.append(item)
        return True

    for cat in priority:
        for item in out:
            if norm_cat(item.get('category')) == cat:
                try_add(item, per_priority)
    for item in out:
        try_add(item)

    selected = []
    for i, item in enumerate(selected_raw):
        row = {
            'id': f'h{i + 1}',
            'category': item['category'],
            'category_de': item['category_de'],
            'title': item['title'],
            'source': item['source'],
            'published': item['published'],
            'url': item['url'],
            'origin': item.get('origin', 'serpapi'),
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
    for symbol, ticker in (
        ('S&P 500', '%5EGSPC'),
        ('Nasdaq', '%5EIXIC'),
        ('Gold', 'GC=F'),
        ('Brent', 'BZ=F'),
    ):
        try:
            data = fetch_json(
                f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d'
            )
            meta = (((data or {}).get('chart') or {}).get('result') or [{}])[0].get('meta') or {}
            price = meta.get('regularMarketPrice')
            if price is None:
                continue
            as_of = now.isoformat()
            if meta.get('regularMarketTime'):
                as_of = datetime.fromtimestamp(meta['regularMarketTime'], tz=timezone.utc).isoformat()
            items.append({'symbol': symbol, 'price': price, 'as_of': as_of, 'source': 'Yahoo Finance'})
        except Exception as exc:
            print('Yahoo failed', symbol, exc)
    return {
        'note': 'Solo precios verificados del research pack. Si falta un activo, omitirlo.',
        'source': 'CoinGecko + Frankfurter + Yahoo Finance',
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
            'La investigación usa Google News vía SerpAPI más RSS directos (ORF, BBC, DW, Andina, RPP) '
            'y precios de CoinGecko/Frankfurter/Yahoo Finance. No se leen artículos completos. '
            'Solo eventos de las últimas 24 horas.'
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
