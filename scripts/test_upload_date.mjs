import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

// A leitura pode terminar depois de o usuário editar a referência.
const elements = new Map();
const element = (id) => {
  if (!elements.has(id)) {
    elements.set(id, {
      value: '',
      files: [],
      handlers: {},
      classList: { add() {}, remove() {} },
      addEventListener(name, handler) {
        this.handlers[name] = handler;
      },
      append() {},
      replaceChildren() {},
    });
  }
  return elements.get(id);
};
const context = vm.createContext({
  document: { getElementById: element, createElement: () => ({}) },
  matchMedia: () => ({ matches: false }),
  Date,
  Intl,
});
vm.runInContext(
  readFileSync(new URL('../webapp/static/new-analysis.js', import.meta.url), 'utf8'),
  context,
);
let finishRead;
element('csv-file').files = [
  {
    name: 'base.csv',
    size: 100,
    text: () =>
      new Promise((resolve) => {
        finishRead = resolve;
      }),
  },
];
const pending = vm.runInContext('onFile()', context);
element('reference-date').value = '2026-09-22';
element('reference-date').handlers.input();
finishRead('2026-09-18');
await pending;
assert.equal(element('reference-date').value, '2026-09-22');
assert.equal(element('date-suggestion').textContent, '');
console.log('Referência editada preservada durante leitura assíncrona do CSV.');
