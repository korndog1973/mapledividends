import assert from 'node:assert/strict';
import test from 'node:test';
import { project } from '../site/static/compare.mjs';

const scenario = {
  investment: 1000, years: 2, price: 100, dividend: 2, payments: 4,
  dividendGrowth: 0, priceGrowth: 0, reinvest: false,
};

test('cash dividends add to ending value once', () => {
  const [first, second] = project(scenario);
  assert.equal(first.income, 80);
  assert.equal(second.cumulative, 160);
  assert.equal(second.stockValue, 1000);
  assert.equal(second.total, 1160);
});

test('dividend and share-price growth apply independently', () => {
  const [first, second] = project({ ...scenario, dividendGrowth: 0.25, priceGrowth: 0.1 });
  assert.equal(first.income, 80);
  assert.equal(second.income, 100);
  assert.ok(Math.abs(second.stockValue - 1210) < 1e-10);
  assert.ok(Math.abs(second.total - 1390) < 1e-10);
});

test('reinvests at each payment and counts the new shares in later payouts', () => {
  const [first] = project({ ...scenario, reinvest: true });
  const expectedValue = 1000 * 1.02 ** 4;
  assert.equal(first.cash, 0);
  assert.ok(Math.abs(first.total - expectedValue) < 1e-10);
  assert.ok(Math.abs(first.cumulative - (expectedValue - 1000)) < 1e-10);
});

test('a full dividend cut stops payouts from year two', () => {
  const [first, second] = project({ ...scenario, dividendGrowth: -1 });
  assert.equal(first.income, 80);
  assert.equal(second.income, 0);
  assert.equal(second.total, first.total);
});
