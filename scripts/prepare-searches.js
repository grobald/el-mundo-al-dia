const localeByCat = {
  'Geopolítica': { gl: 'us', hl: 'en' },
  'Europa y Austria': { gl: 'at', hl: 'de' },
  'Estados Unidos': { gl: 'us', hl: 'en' },
  'Perú': { gl: 'pe', hl: 'es' },
  'Economía': { gl: 'us', hl: 'en' },
  'Inteligencia artificial': { gl: 'us', hl: 'en' },
  'Criptomonedas': { gl: 'us', hl: 'en' },
  'Mundo': { gl: 'us', hl: 'en' },
};
const boostByCat = {
  'Geopolítica': ' (Reuters OR AP OR BBC OR DW OR AFP)',
  'Europa y Austria': ' (ORF OR APA OR Reuters OR DW OR "Der Standard")',
  'Estados Unidos': ' (Reuters OR AP OR Bloomberg OR BBC OR NPR)',
  'Perú': ' (Andina OR RPP OR Gestión OR Reuters OR BBC OR "El Comercio")',
  'Economía': ' (Bloomberg OR Reuters OR "Financial Times" OR CNBC)',
  'Inteligencia artificial': ' (Reuters OR Bloomberg OR BBC OR Wired OR TechCrunch)',
  'Criptomonedas': ' (Reuters OR Bloomberg OR CoinDesk OR "Financial Times")',
};
const seen = new Set();
const out = [];
for (const item of $input.all()) {
  const row = item.json || {};
  if (row.enabled === false) continue;
  const category = String(row.category_es || 'Mundo').trim();
  const baseQuery = String(row.query || '').trim();
  if (!baseQuery) continue;
  const key = category + '|' + baseQuery.toLowerCase();
  if (seen.has(key)) continue;
  seen.add(key);
  const locale = localeByCat[category] || { gl: row.gl || 'us', hl: row.hl || 'en' };
  const boost = boostByCat[category] || '';
  out.push({
    json: {
      category_es: category,
      category_de: String(row.category_de || ''),
      query: baseQuery + boost + ' when:1d',
      gl: String(row.gl || locale.gl),
      hl: String(row.hl || locale.hl),
    },
  });
}
const extras = [
  { category_es: 'Perú', category_de: 'Peru', query: 'Perú política economía noticias when:1d (Andina OR RPP OR Gestión OR "El Comercio")', gl: 'pe', hl: 'es' },
  { category_es: 'Perú', category_de: 'Peru', query: 'sismo OR temblor OR IGP Perú when:1d', gl: 'pe', hl: 'es' },
  { category_es: 'Perú', category_de: 'Peru', query: 'site:rpp.pe when:1d', gl: 'pe', hl: 'es' },
  { category_es: 'Perú', category_de: 'Peru', query: 'site:andina.pe when:1d', gl: 'pe', hl: 'es' },
  { category_es: 'Estados Unidos', category_de: 'Vereinigte Staaten', query: 'United States politics Congress White House when:1d (Reuters OR AP OR Bloomberg)', gl: 'us', hl: 'en' },
  { category_es: 'Estados Unidos', category_de: 'Vereinigte Staaten', query: 'US economy Federal Reserve markets when:1d (Reuters OR Bloomberg OR AP)', gl: 'us', hl: 'en' },
  { category_es: 'Estados Unidos', category_de: 'Vereinigte Staaten', query: 'site:apnews.com United States when:1d', gl: 'us', hl: 'en' },
  { category_es: 'Estados Unidos', category_de: 'Vereinigte Staaten', query: 'site:reuters.com United States when:1d', gl: 'us', hl: 'en' },
  { category_es: 'Europa y Austria', category_de: 'Europa und Österreich', query: 'Austria Politik Wirtschaft ORF APA when:1d', gl: 'at', hl: 'de' },
  { category_es: 'Europa y Austria', category_de: 'Europa und Österreich', query: 'EU Europa Kommission Rat when:1d (Reuters OR DW OR APA)', gl: 'at', hl: 'de' },
  { category_es: 'Europa y Austria', category_de: 'Europa und Österreich', query: 'site:orf.at when:1d', gl: 'at', hl: 'de' },
  { category_es: 'Europa y Austria', category_de: 'Europa und Österreich', query: 'site:derstandard.at when:1d', gl: 'at', hl: 'de' },
  { category_es: 'Geopolítica', category_de: 'Geopolitik', query: 'site:reuters.com when:1d', gl: 'us', hl: 'en' },
  { category_es: 'Geopolítica', category_de: 'Geopolitik', query: 'site:apnews.com when:1d', gl: 'us', hl: 'en' },
  { category_es: 'Economía', category_de: 'Wirtschaft', query: 'site:bloomberg.com when:1d', gl: 'us', hl: 'en' },
  { category_es: 'Economía', category_de: 'Wirtschaft', query: 'site:ft.com when:1d', gl: 'us', hl: 'en' },
];
for (const extra of extras) {
  const key = extra.category_es + '|' + extra.query.toLowerCase();
  if (seen.has(key)) continue;
  seen.add(key);
  out.push({ json: extra });
}
return out;
