const cutoff = Date.now() - 24 * 60 * 60 * 1000;
const preferred = /reuters|associated press|\bap\b|bbc|orf|deutsche welle|\bdw\b|andina|\brpp\b|bloomberg|financial times|\bft\b|gestión|gestion|apa|der standard|afp|washington post|nytimes|el país|el comercio|npr/i;
const blocked = /britannica|wikipedia|wiki\b|encyclopedia/i;
const teaserRe = /\b(conoce|revisa|ent[eé]rate|en vivo|últim[oa]s? noticias)\b/i;
const excludedTopic = /\b(f[uú]tbol|football|soccer|nba|nfl|mlb|nhl|bundesliga|champions league|gol\b|partido|deportes?|sports?|olympics?|ol[ií]mpic|tenis|tennis|f1\b|formula 1|boxeo|boxing|atletismo|transfermarket|cine\b|pel[ií]cula|movie|hollywood|streaming|netflix|hollywoodjuego|video ?game|esport|celebridad|celebrity|influencer|reality|gossip|moda\b|fashion|belleza|beauty|turismo|tourism|hotel|viaje|travel|receta|recipe|restaurante|gastronom|oferta|descuento|deal\b|shopping|hor[oó]scopo|astrolog| Concierto|concert|album|festival de m[uú]sica|meme\b|viral\b)\b/i;
const impactException = /\b(guerra|war|sanci[oó]n|diplomacia|geopol[ií]tica|regulaci[oó]n|inflaci[oó]n|banco central|climate|clima|salud p[uú]blica|public health|pandemia|ciberataque|cyber|elecciones|election|congreso|parliament|energ[ií]a|opec|nato|onu|imf|fmi)\b/i;
const priorityCats = ['Perú', 'Estados Unidos', 'Europa y Austria'];
const perPriority = 12;
const perSourceCap = 12;
const maxTotal = 120;
const monthMap = {
  january: 0, febrero: 1, february: 1, marzo: 2, march: 2, abril: 3, april: 3,
  mayo: 4, may: 4, junio: 5, june: 5, julio: 6, july: 6, agosto: 7, august: 7,
  septiembre: 8, september: 8, octubre: 9, october: 9, noviembre: 10, november: 10,
  diciembre: 11, december: 11, enero: 0,
};
const now = new Date();
const currentMonth = now.getUTCMonth();
const currentYear = now.getUTCFullYear();
const seen = new Set();
const headlines = [];
function isGte(a, b) { return Math.min(a, b) === b; }
function isGt(a, b) { return Math.min(a, b) === b && a !== b; }

function sourceName(value) {
  if (!value) return 'Google News';
  if (typeof value === 'string') return value.trim() || 'Google News';
  return String(value.name || value._ || value.title || 'Google News').trim() || 'Google News';
}

function parseWhen(row) {
  const raw = row.iso_date || row.date || row.published;
  if (raw == null || raw === '') return null;
  if (typeof raw === 'number') {
    const ms = isGte(raw, 1e12) ? raw : raw * 1000;
    const d = new Date(ms);
    return Number.isNaN(d.getTime()) ? null : d;
  }
  const text = String(raw).trim();
  const direct = new Date(text);
  if (!Number.isNaN(direct.getTime())) return direct;
  const m = text.match(/(\d+)\s+(minute|minutes|hour|hours|day|days|minuto|minutos|hora|horas|día|dias|días)/i);
  if (m) {
    const n = Number(m[1]);
    const unit = m[2].toLowerCase();
    const ago = new Date();
    if (/minute|minuto/.test(unit)) ago.setMinutes(ago.getMinutes() - n);
    else if (/hour|hora/.test(unit)) ago.setHours(ago.getHours() - n);
    else ago.setDate(ago.getDate() - n);
    return ago;
  }
  return null;
}

function isStaleByText(title, snippet) {
  const text = (title + ' ' + (snippet || '')).toLowerCase();
  const yearMatch = text.match(/\b(20\d{2})\b/);
  if (yearMatch && isGt(currentYear, Number(yearMatch[1]))) return true;
  const monthMatch = text.match(/\b(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|january|february|march|april|may|june|july|august|september|october|november|december)\b/);
  if (monthMatch) {
    const month = monthMap[monthMatch[1]];
    if (month != null && month !== currentMonth) {
      if (/\b\d{1,2}\b/.test(text) || /\b(20\d{2})\b/.test(text)) return true;
    }
  }
  return false;
}

function factScore(title, source, origin) {
  let score = 0;
  const digits = (title.match(/\d/g) || []).length;
  score += Math.min(digits, 8);
  if (/\bmagnitud\s*\d/i.test(title)) score += 12;
  if (/\bIGP\b/i.test(title)) score += 8;
  if (/\d+[.,]?\d*\s*%|\$\s*\d|\d+[.,]\d+/.test(title)) score += 4;
  if (preferred.test(source) || preferred.test(title)) score += 10;
  if (origin === 'rss' && preferred.test(source)) score += 6;
  if (teaserRe.test(title) && !/\d/.test(title)) score -= 8;
  return score;
}

function normCat(category) {
  const c = String(category || '').toLowerCase();
  if (/per[uú]/.test(c)) return 'Perú';
  if (/estados unidos|ee\.?\s?uu|usa|united states/.test(c)) return 'Estados Unidos';
  if (/europa|austria|österreich/.test(c)) return 'Europa y Austria';
  return category || 'Mundo';
}

for (const item of $input.all()) {
  const row = item.json || {};
  if (row.empty) continue;
  const title = String(row.title || '').trim();
  const link = String(row.url || row.link || '').trim();
  const when = parseWhen(row);
  const snippet = String(row.snippet || '').trim().slice(0, 320);
  if (!title || !link || !when || !isGte(when.getTime(), cutoff) || seen.has(link)) continue;
  if (isStaleByText(title, snippet)) continue;
  const source = sourceName(row.source);
  if (blocked.test(source) || blocked.test(title) || blocked.test(link)) continue;
  const topicText = title + ' ' + snippet;
  if (excludedTopic.test(topicText) && !impactException.test(topicText)) continue;
  seen.add(link);
  headlines.push({
    category: normCat(row.category_es || 'Mundo'),
    category_de: row.category_de || '',
    title: title,
    url: link,
    source: source,
    published: when.toISOString(),
    origin: row.origin || 'unknown',
    fact_score: factScore(title, source, row.origin),
    snippet: snippet && snippet !== title ? snippet : undefined,
  });
}

headlines.sort(function(a, b) {
  return (b.fact_score - a.fact_score) || String(b.published).localeCompare(String(a.published));
});

const selectedRaw = [];
const usedUrls = new Set();
const perSource = {};
const perCat = {};

function tryAdd(item, catLimit) {
  if (usedUrls.has(item.url)) return false;
  if (Math.min(selectedRaw.length, maxTotal) === maxTotal) return false;
  const src = String(item.source || 'unknown').toLowerCase();
  const srcN = perSource[src] || 0;
  if (Math.min(srcN, perSourceCap) === perSourceCap) return false;
  const cat = normCat(item.category);
  const catN = perCat[cat] || 0;
  if (catLimit != null && Math.min(catN, catLimit) === catLimit) return false;
  usedUrls.add(item.url);
  perSource[src] = srcN + 1;
  perCat[cat] = catN + 1;
  selectedRaw.push(item);
  return true;
}

for (const cat of priorityCats) {
  for (const item of headlines) {
    if (normCat(item.category) !== cat) continue;
    tryAdd(item, perPriority);
  }
}

for (const item of headlines) {
  tryAdd(item, null);
}

const selected = selectedRaw.map(function(item, index) {
  const row = {
    id: 'h' + (index + 1),
    category: item.category,
    category_de: item.category_de,
    title: item.title,
    source: item.source,
    published: item.published,
    url: item.url,
    origin: item.origin,
  };
  if (item.snippet) row.snippet = item.snippet;
  return row;
});
return [{ json: { headlines: selected, count: selected.length, collected: headlines.length, per_category: perCat } }];
