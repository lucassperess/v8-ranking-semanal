(() => {
  let context = null;
  let message = '';
  let renderedSelection = '';
  let activeView = 'graph';
  function showView(view, focus = false) {
    activeView = view;
    for (const name of ['graph', 'context']) {
      const button = document.getElementById(`asset-${name}-tab`);
      const selected = name === view;
      button.classList.toggle('active', selected);
      button.setAttribute('aria-selected', String(selected));
      button.tabIndex = selected ? 0 : -1;
      if (selected && focus) button.focus();
    }
    document.getElementById('asset-chart-view').hidden = view !== 'graph';
    document.getElementById('company-context').hidden = view !== 'context';
  }
  document.addEventListener('DOMContentLoaded', () => {
    for (const name of ['graph', 'context']) {
      const button = document.getElementById(`asset-${name}-tab`);
      button.addEventListener('click', () => {
        showView(name);
        window.dispatchEvent(new Event('asset-view-change'));
      });
      button.addEventListener('keydown', (event) => {
        if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
        event.preventDefault();
        showView(
          event.key === 'Home'
            ? 'graph'
            : event.key === 'End'
              ? 'context'
              : activeView === 'graph'
                ? 'context'
                : 'graph',
          true,
        );
        window.dispatchEvent(new Event('asset-view-change'));
      });
    }
    showView('graph');
  });
  const el = (tag, value, cls) => {
    const element = document.createElement(tag);
    if (value) element.textContent = value;
    if (cls) element.className = cls;
    return element;
  };
  const date = (value) => value?.split('-').reverse().join('/') || '';
  const number = new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  function link(label, url) {
    const anchor = el('a', `${label} ↗`);
    try {
      const parsed = new URL(url);
      if (!['http:', 'https:'].includes(parsed.protocol)) return el('span', label);
      anchor.href = parsed.href;
    } catch {
      return el('span', label);
    }
    anchor.target = '_blank';
    anchor.rel = 'noopener noreferrer';
    return anchor;
  }
  function sources(parent, ids) {
    const list = el('div', '', 'context-sources');
    for (const id of ids || []) {
      const source = context.company.sources.find((item) => item.id === id);
      if (source) list.append(link(source.title, source.url));
    }
    if (list.childElementCount) parent.append(list);
  }
  function details(title, text, ids) {
    const item = el('details');
    item.append(el('summary', title), el('p', text));
    sources(item, ids);
    return item;
  }
  function render(ticker, selectedWindow) {
    const selectionKey = `${ticker}:${selectedWindow}:${context ? 'available' : message}`;
    if (selectionKey === renderedSelection) return;
    renderedSelection = selectionKey;
    const companyPanel = document.getElementById('company-context');
    const marketPanel = document.getElementById('market-context');
    const marketNewsOpen = marketPanel.querySelector('.market-news')?.open || false;
    companyPanel.replaceChildren();
    companyPanel.scrollTop = 0;
    marketPanel.replaceChildren();
    showView(activeView);
    if (!context) {
      companyPanel.append(el('p', message || 'Carregando o contexto revisado…'));
      marketPanel.hidden = true;
      return;
    }
    const asset = context.company.assets.find((item) => item.ticker === ticker);
    const issuer = context.company.issuers.find((item) => item.cvm_code === asset?.cvm_code);
    if (!issuer) {
      companyPanel.append(el('p', 'Não há contexto revisado para este ativo.'));
      return;
    }
    companyPanel.append(el('h3', `Contexto de ${ticker}`), el('p', issuer.name, 'context-muted'));
    const price = selectedWindow === 'alternative' ? asset.alternative : asset.main;
    companyPanel.append(el('p', price.text));
    companyPanel.append(el('p', issuer.interpretation.text));
    const references = el('details');
    references.append(el('summary', 'Fontes desta leitura'));
    sources(references, issuer.interpretation.source_ids);
    if (issuer.interpretation.source_ids.length) companyPanel.append(references);
    if (issuer.financial_context)
      companyPanel.append(
        details(
          'Resultados anteriores à semana',
          issuer.financial_context.text,
          issuer.financial_context.source_ids,
        ),
      );
    const news = el('details');
    news.append(el('summary', `Acontecimentos e antecedentes (${issuer.events.length})`));
    if (
      issuer.events.some((event) =>
        event.source_ids.some((id) =>
          context.company.sources.find((source) => source.id === id)?.date_basis.startsWith('cvm_'),
        ),
      )
    ) {
      news.append(
        el(
          'p',
          'Nos documentos oficiais, a data de entrega à CVM indica quando o documento foi registrado. O acontecimento e a primeira divulgação pública podem ter ocorrido antes.',
          'context-muted',
        ),
      );
    }
    for (const event of issuer.events) {
      const item = el('article', '', 'context-event');
      const evidence = (event.source_ids || []).map((id) =>
        context.company.sources.find((source) => source.id === id),
      );
      const deliveryDates = [
        ...new Set(
          evidence
            .filter((source) => source?.date_basis.startsWith('cvm_'))
            .map((source) => source.publication_date),
        ),
      ].sort();
      const dateText =
        evidence.length && evidence.every((source) => source?.date_basis.startsWith('cvm_'))
          ? `Entrega à CVM em ${deliveryDates.map(date).join(' e ')}`
          : `Publicado em ${date(event.publication_date)}`;
      item.append(
        el('h4', event.title),
        el(
          'p',
          `${dateText}${event.event_date && event.event_date !== event.publication_date ? ` · acontecimento em ${date(event.event_date)}` : ''}`,
          'context-muted',
        ),
      );
      if (event.after_price_end)
        item.append(
          el(
            'strong',
            'Depois do fechamento de 18/09: não explica o retorno encerrado nessa data.',
          ),
        );
      item.append(el('p', event.text));
      sources(item, event.source_ids);
      news.append(item);
    }
    if (issuer.events.length) companyPanel.append(news);
    companyPanel.append(details('Como a janela muda esta leitura', asset.window_explanation));
    companyPanel.append(
      details('O que ainda não conseguimos confirmar', issuer.unresolved_question),
    );
    companyPanel.append(el('p', context.company.disclosure, 'context-muted'));
    marketPanel.hidden = false;
    marketPanel.append(
      el('h2', 'Contexto geral da semana'),
      el(
        'p',
        '14 a 20/09/2026 · referências de mercado e acontecimentos do período. Não comprovam a causa do retorno de cada ação.',
        'context-muted',
      ),
    );
    const grid = el('div', '', 'market-indicators');
    for (const indicator of context.market.indicators) {
      const values = indicator[selectedWindow];
      const card = el('article', '', 'market-card');
      const value = Number(values.change_pct);
      card.append(
        el('h3', indicator.label),
        el(
          'strong',
          `${value > 0 ? '+' : ''}${number.format(value)}%`,
          value < 0 ? 'negative' : 'positive',
        ),
      );
      card.append(
        el(
          'p',
          `${date(values.start_date)} → ${date(values.end_date)} · ${selectedWindow === 'primary' ? 'Semana completa' : 'Dentro da semana'}`,
        ),
      );
      card.append(
        el(
          'p',
          `${number.format(Number(values.start_value))} → ${number.format(Number(values.end_value))} ${indicator.unit}`,
        ),
      );
      card.append(
        el('p', indicator.definition, 'context-muted'),
        link(indicator.source_label, indicator.source_url),
      );
      grid.append(card);
    }
    marketPanel.append(grid);
    const newsGroup = el('details', '', 'market-news');
    newsGroup.open = marketNewsOpen;
    newsGroup.append(el('summary', 'Acontecimentos da semana · juros, economia e política'));
    const events = el('div', '', 'market-events');
    for (const event of context.market.events) {
      const card = el('article', '', 'market-card');
      card.append(
        el('p', event.date_label, 'context-muted'),
        el('h3', event.title),
        el('p', event.text),
        link(event.source_label, event.source_url),
      );
      events.append(card);
    }
    newsGroup.append(events);
    marketPanel.append(newsGroup, el('p', context.market.method, 'context-muted'));
  }
  async function load(kind, selection) {
    context = null;
    renderedSelection = '';
    message =
      kind === 'featured'
        ? 'Carregando o contexto revisado…'
        : 'O contexto de notícias foi preparado para o case de referência. Este novo envio não recebe automaticamente os textos do case.';
    render(selection().ticker, selection().window);
    if (kind !== 'featured') return;
    try {
      const response = await fetch('/api/featured/context');
      if (!response.ok) throw new Error('Context request failed');
      const payload = await response.json();
      if (payload.status === 'available') context = payload;
      else message = payload.message;
    } catch {
      message =
        'Não foi possível carregar o contexto. O ranking e os gráficos continuam disponíveis.';
    }
    render(selection().ticker, selection().window);
  }
  window.rankingContext = { load, render };
})();
