const FEEDS = [
  { rss_url: 'https://rss.orf.at/news.xml', category_es: 'Europa y Austria', category_de: 'Europa und Österreich', source_name: 'ORF' },
  { rss_url: 'https://rss.orf.at/oesterreich.xml', category_es: 'Europa y Austria', category_de: 'Europa und Österreich', source_name: 'ORF' },
  { rss_url: 'https://www.derstandard.at/rss', category_es: 'Europa y Austria', category_de: 'Europa und Österreich', source_name: 'Der Standard' },
  { rss_url: 'https://rss.dw.com/rdf/rss-de-eu', category_es: 'Europa y Austria', category_de: 'Europa und Österreich', source_name: 'DW' },
  { rss_url: 'https://feeds.bbci.co.uk/news/world/europe/rss.xml', category_es: 'Europa y Austria', category_de: 'Europa und Österreich', source_name: 'BBC' },
  { rss_url: 'https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml', category_es: 'Estados Unidos', category_de: 'Vereinigte Staaten', source_name: 'BBC' },
  { rss_url: 'https://feeds.npr.org/1001/rss.xml', category_es: 'Estados Unidos', category_de: 'Vereinigte Staaten', source_name: 'NPR' },
  { rss_url: 'https://feeds.bbci.co.uk/mundo/rss.xml', category_es: 'Geopolítica', category_de: 'Geopolitik', source_name: 'BBC Mundo' },
  { rss_url: 'https://feeds.bbci.co.uk/news/world/rss.xml', category_es: 'Geopolítica', category_de: 'Geopolitik', source_name: 'BBC' },
  { rss_url: 'https://rss.dw.com/rdf/rss-sp-inter', category_es: 'Geopolítica', category_de: 'Geopolitik', source_name: 'DW' },
  { rss_url: 'https://andina.pe/agencia/rss.aspx', category_es: 'Perú', category_de: 'Peru', source_name: 'Andina' },
  { rss_url: 'https://rpp.pe/feed', category_es: 'Perú', category_de: 'Peru', source_name: 'RPP' },
  { rss_url: 'https://rpp.pe/feed/politica', category_es: 'Perú', category_de: 'Peru', source_name: 'RPP' },
  { rss_url: 'https://rpp.pe/feed/actualidad', category_es: 'Perú', category_de: 'Peru', source_name: 'RPP' },
];
const out = [];
function clean(value) {
  const open = String.fromCharCode(60);
  const close = String.fromCharCode(62);
  let text = String(value || '');
  while (text.includes(open)) {
    const start = text.indexOf(open);
    const end = text.indexOf(close, start);
    if (end === -1) break;
    text = text.slice(0, start) + ' ' + text.slice(end + 1);
  }
  return text.split(/\s+/).filter(Boolean).join(' ').trim().slice(0, 320);
}
function feedFromUrl(url) {
  const text = String(url || '').toLowerCase();
  if (text.includes('orf.at')) return FEEDS[0];
  if (text.includes('derstandard')) return FEEDS[2];
  if (text.includes('npr.org')) return FEEDS[6];
  if (text.includes('bbc') && (text.includes('us_and_canada') || text.includes('/us/'))) return FEEDS[5];
  if (text.includes('bbc') && text.includes('europe')) return FEEDS[4];
  if (text.includes('bbc') && text.includes('mundo')) return FEEDS[7];
  if (text.includes('bbc')) return FEEDS[8];
  if (text.includes('dw.com') || text.includes('/dw/')) return FEEDS[3];
  if (text.includes('andina')) return FEEDS[10];
  if (text.includes('rpp')) return FEEDS[11];
  return null;
}
for (const item of $input.all()) {
  const data = item.json || {};
  const pair = item.pairedItem;
  const index = typeof pair?.item === 'number' ? pair.item : (Array.isArray(pair) ? pair[0]?.item : 0) || 0;
  const feed = FEEDS[index] || feedFromUrl(data.link || data.url) || {
    category_es: 'Mundo',
    category_de: '',
    source_name: 'RSS',
  };
  const title = String(data.title || '').trim();
  const link = String(data.link || data.url || '').trim();
  if (!title || !link) continue;
  const sourceValue = data.source;
  const source = typeof sourceValue === 'string'
    ? sourceValue
    : (sourceValue && (sourceValue._ || sourceValue.name)) || data.creator || feed.source_name || 'RSS';
  const snippet = clean(data.contentSnippet || data.content || data.description || '');
  out.push({
    json: {
      origin: 'rss',
      category_es: feed.category_es || 'Mundo',
      category_de: feed.category_de || '',
      title: title,
      url: link,
      source: String(source).trim() || feed.source_name || 'RSS',
      date: data.pubDate || data.isoDate || data.date || data['dc:date'],
      iso_date: data.isoDate || data.pubDate || data.date || data['dc:date'],
      snippet: snippet,
    },
  });
}
return out.length ? out : [{ json: { origin: 'rss', empty: true } }];
