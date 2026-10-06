document.addEventListener('DOMContentLoaded', () => {
  const closeTips = () =>
    document
      .querySelectorAll('.info-button[aria-expanded="true"]')
      .forEach((tip) => tip.setAttribute('aria-expanded', 'false'));
  document.querySelectorAll('.info-button').forEach((tip) => {
    tip.setAttribute('aria-expanded', 'false');
    tip.addEventListener('click', () => {
      const open = tip.getAttribute('aria-expanded') === 'true';
      closeTips();
      tip.setAttribute('aria-expanded', String(!open));
    });
  });
  document.addEventListener('click', (event) => {
    if (!event.target.closest('.metric-info,.period-info')) closeTips();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeTips();
  });
  const labelTables = () =>
    document.querySelectorAll('.docs-table table,.audit-table').forEach((table) => {
      const headers = [...table.querySelectorAll('thead th')].map((cell) =>
        cell.textContent.trim(),
      );
      table.querySelectorAll('tbody tr').forEach((row) =>
        [...row.cells].forEach((cell, index) => {
          cell.dataset.label = headers[index] || '';
          if (!cell.querySelector(':scope > .mobile-cell-value')) {
            const value = document.createElement('span');
            value.className = 'mobile-cell-value';
            value.append(...cell.childNodes);
            cell.append(value);
          }
        }),
      );
    });
  labelTables();
  const audit = document.getElementById('method-body');
  if (audit) new MutationObserver(labelTables).observe(audit, { childList: true, subtree: true });
  const button = document.getElementById('fullscreen-button'),
    message = document.getElementById('fullscreen-message');
  if (!button) return;
  const sync = () => {
    const active = Boolean(document.fullscreenElement);
    const label = active ? 'Sair da tela cheia' : 'Entrar em tela cheia';
    button.setAttribute('aria-pressed', String(active));
    button.setAttribute('aria-label', label);
    button.title = label;
  };
  button.addEventListener('click', async () => {
    message.hidden = true;
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else if (document.documentElement.requestFullscreen)
        await document.documentElement.requestFullscreen();
      else throw new Error('unsupported');
    } catch {
      message.textContent = 'Este navegador não permitiu a tela cheia. Use F11 no computador.';
      message.hidden = false;
    }
    sync();
  });
  document.addEventListener('fullscreenchange', sync);
  sync();
});
