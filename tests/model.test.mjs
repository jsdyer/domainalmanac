import test from 'node:test';
import assert from 'node:assert/strict';
import { normalize, selection } from '../web/model.mjs';
const data = ['.ca', '.games', '.lol', '.art'].map((extension) => ({
  extension,
}));
const defaults = { defaults: ['.ca', '.games', '.lol'], period: '1y' };
test('defaults and shared comparisons accept every captured extension', () => {
  assert.deepEqual(
    selection('', data, defaults).selected.map((r) => r.extension),
    defaults.defaults,
  );
  const custom = selection(
    '?tld=ART&compare=ca&also=&period=all_retail',
    data,
    defaults,
  );
  assert.deepEqual(
    custom.selected.map((r) => r.extension),
    ['.art', '.ca'],
  );
  assert.equal(custom.period, 'all_retail');
});
test('unknown extensions are not zero sales, duplicates are removed, windows validated', () => {
  const s = selection(
    'tld=ca&compare=.CA&also=unreported&period=anything',
    data,
    defaults,
  );
  assert.equal(s.period, '1y');
  assert.deepEqual(
    s.selected.map((r) => r.extension),
    ['.ca'],
  );
  assert.equal(s.values[2], '.unreported');
  assert.equal(normalize(' .GAMES '), '.games');
});
