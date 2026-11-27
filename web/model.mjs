export const windows = {
  '1y': 'Past year',
  '1w': 'Past week',
  '1m': 'Past month',
  '3m': 'Past 3 months',
  '2y': 'Past 2 years',
  '3y': 'Past 3 years',
  '5y': 'Past 5 years',
  all: 'All recorded sales',
  all_retail: 'All-time retail',
  all_wholesale: 'All-time wholesale',
};
export const number = (value) => new Intl.NumberFormat('en-US').format(value);
export const dollars = (value) =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(value);
export function normalize(value) {
  return (
    '.' +
    String(value || '')
      .trim()
      .toLowerCase()
      .replace(/^\.+/, '')
  );
}
export function selection(query, records, defaults) {
  const params = new URLSearchParams(query);
  const byName = new Map(records.map((r) => [r.extension, r]));
  const period = Object.hasOwn(windows, params.get('period'))
    ? params.get('period')
    : defaults.period;
  const values = ['tld', 'compare', 'also'].map((k, i) =>
    normalize(params.has(k) ? params.get(k) : defaults.defaults[i]),
  );
  const selected = [...new Set(values)]
    .map((v) => byName.get(v))
    .filter(Boolean);
  return { period, values, selected };
}
