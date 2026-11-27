import { windows, number, dollars, normalize, selection } from './model.mjs';
const $ = (id) => document.getElementById(id);
const names = ['tld', 'compare-input', 'also'];
const params = ['tld', 'compare', 'also'];
const cell = (tag, value) => {
  const e = document.createElement(tag);
  e.textContent = value;
  return e;
};
async function start() {
  const response = await fetch('./data/market.json');
  if (!response.ok) throw Error('The comparison could not load.');
  const edition = await response.json();
  const byName = new Map(edition.records.map((r) => [r.extension, r]));
  const list = document.createDocumentFragment();
  for (const r of edition.records)
    list.append(new Option(r.extension, r.extension));
  $('extensions').replaceChildren(list);
  $('period').replaceChildren(
    ...Object.entries(windows).map(([id, label]) => new Option(label, id)),
  );
  function render(q) {
    const state = selection(q, edition.records, edition.presets);
    names.forEach((id, i) => {
      $(id).value = state.values[i] === '.' ? '' : state.values[i];
    });
    $('period').value = state.period;
    const unknown = state.values.filter((v) => v !== '.' && !byName.has(v));
    $('feedback').textContent = unknown.length
      ? 'No published extension profile for ' +
        [...new Set(unknown)].join(', ') +
        '. Choose a listed extension.'
      : '';
    $('table-context').textContent =
      windows[state.period] + ' · reported aftermarket transactions';
    const highest = Math.max(
      0,
      ...state.selected.map((r) => r.periods[state.period].sale_count),
    );
    const rows = state.selected.map((r) => {
      const stats = r.periods[state.period],
        tr = document.createElement('tr');
      const label = cell('th', '');
      label.scope = 'row';
      const link = cell('a', r.extension);
      link.href = './records/' + r.slug + '/';
      label.append(link);
      const sample = cell('td', '');
      const mark = cell('span', number(stats.sale_count));
      mark.className = 'count-value';
      mark.style.setProperty(
        '--share',
        (highest ? (100 * stats.sale_count) / highest : 0) + '%',
      );
      sample.append(mark);
      tr.append(
        label,
        sample,
        cell('td', dollars(stats.price_sum)),
        cell('td', stats.sale_count ? dollars(stats.price_avg) : '—'),
        cell('td', stats.sale_count ? dollars(stats.price_max) : '—'),
      );
      return tr;
    });
    $('results').replaceChildren(...rows);
  }
  $('controls').addEventListener('submit', (e) => {
    e.preventDefault();
    const q = new URLSearchParams();
    names.forEach((id, i) => q.set(params[i], normalize($(id).value).slice(1)));
    q.set('period', $('period').value);
    history.pushState(null, '', location.pathname + '?' + q);
    render(q);
  });
  window.addEventListener('popstate', () => render(location.search));
  render(location.search);
  $('controls').hidden = false;
}
start().catch(() => {
  $('feedback').textContent =
    'The interactive comparison could not load. Open an extension profile below to read all the published figures.';
});
