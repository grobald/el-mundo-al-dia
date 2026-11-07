const pack = $('Filter recent headlines').first().json;
const now = $now.setZone('Europe/Vienna');
const windowEnd = now;
const windowStart = now.minus({ hours: 24 });
const markets = {
  note: 'Solo precios verificados del research pack. Si falta un activo, omitirlo.',
  source: 'CoinGecko + Frankfurter + Yahoo Finance',
  fetched_at: now.toISO(),
  items: [],
};

try {
  const cg = $('Fetch markets').first().json || {};
  if (cg.bitcoin && cg.bitcoin.usd != null) {
    markets.items.push({
      symbol: 'BTC',
      price_usd: cg.bitcoin.usd,
      as_of: cg.bitcoin.last_updated_at
        ? new Date(cg.bitcoin.last_updated_at * 1000).toISOString()
        : markets.fetched_at,
      source: 'CoinGecko',
    });
  }
  if (cg.ethereum && cg.ethereum.usd != null) {
    markets.items.push({
      symbol: 'ETH',
      price_usd: cg.ethereum.usd,
      as_of: cg.ethereum.last_updated_at
        ? new Date(cg.ethereum.last_updated_at * 1000).toISOString()
        : markets.fetched_at,
      source: 'CoinGecko',
    });
  }
} catch (e) {}

try {
  const fx = $('Fetch FX').first().json || {};
  if (fx.rates && fx.rates.USD != null) {
    markets.items.push({
      symbol: 'EUR/USD',
      price: fx.rates.USD,
      as_of: fx.date ? fx.date + 'T00:00:00Z' : markets.fetched_at,
      source: 'Frankfurter.app',
    });
  }
} catch (e) {}

function pushYahoo(symbol, nodeName) {
  try {
    const data = $(nodeName).first().json || {};
    const meta = (((data.chart || {}).result || [])[0] || {}).meta || {};
    if (meta.regularMarketPrice == null) return;
    markets.items.push({
      symbol: symbol,
      price: meta.regularMarketPrice,
      as_of: meta.regularMarketTime
        ? new Date(meta.regularMarketTime * 1000).toISOString()
        : markets.fetched_at,
      source: 'Yahoo Finance',
    });
  } catch (e) {}
}

pushYahoo('S&P 500', 'Fetch SPX');
pushYahoo('Nasdaq', 'Fetch Nasdaq');
pushYahoo('Gold', 'Fetch Gold');
pushYahoo('Brent', 'Fetch Brent');

return [{
  json: {
    edition_date: now.toFormat('yyyy-MM-dd'),
    reporting_window: {
      start: windowStart.toISO(),
      end: windowEnd.toISO(),
      label: windowStart.toFormat('dd/MM/yyyy HH:mm') + ' - ' + windowEnd.toFormat('dd/MM/yyyy HH:mm') + ' (Austria)',
    },
    headlines: pack.headlines || [],
    count: pack.count || 0,
    markets: markets,
    research_limitation: 'La investigacion usa Google News via SerpAPI mas RSS directos (ORF, BBC, DW, Andina, RPP) y precios de CoinGecko/Frankfurter/Yahoo Finance. No se leen articulos completos. Solo eventos de las ultimas 24 horas.',
  },
}];
