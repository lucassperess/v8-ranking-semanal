import { readFileSync, readdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import postcss from 'postcss';

const root = path.resolve(import.meta.dirname, '..');
const folder = path.join(root, 'webapp/static');
for (const name of readdirSync(folder)) {
  const file = path.join(folder, name);
  if (name.endsWith('.js')) {
    const result = spawnSync(process.execPath, ['--check', file], { stdio: 'inherit' });
    if (result.status !== 0) process.exit(1);
  }
  if (name.endsWith('.css')) {
    const css = postcss.parse(readFileSync(file, 'utf8'), { from: file });
    const declarations = new Set();
    css.walkDecls((declaration) => {
      const parents = [];
      for (let parent = declaration.parent; parent.type !== 'root'; parent = parent.parent) {
        parents.unshift(
          parent.type === 'rule' ? parent.selector : `@${parent.name} ${parent.params}`,
        );
      }
      const key = [...parents, declaration.prop, Boolean(declaration.important)].join('|');
      if (declarations.has(key)) {
        throw new Error(`${name}:${declaration.source.start.line}: declaração repetida: ${key}`);
      }
      declarations.add(key);
    });
  }
}
console.log('JavaScript válido; CSS sem declarações sobrescritas no mesmo seletor e contexto.');
await import('./test_upload_date.mjs');
