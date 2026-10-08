(() => {
  let context = null;
  let message = '';
  let renderedSelection = '';
  let activeView = 'graph';
  let loadGeneration = 0;
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
      companyPanel.append(el('p', message || 'Carregando o contexto desta análise…'));
      marketPanel.hidden = true;
      return;
    }
    const asset = context.company.assets.find((item) => item.ticker === ticker);
    const issuer = context.company.issuers.find((item) => item.cvm_code === asset?.cvm_code);
    if (!issuer) {
      companyPanel.append(el('p', 'Não há contexto disponível para este ativo.'));
      return;
    }
    companyPanel.append(el('h3', `Contexto de ${ticker}`), el('p', issuer.name, 'context-muted'));
    if (issuer.coverage_status === 'financial_antecedent_only')
      companyPanel.append(
        el(
          'p',
          'Base desta leitura: resultados financeiros de um trimestre anterior à semana analisada.',
          'context-muted',
        ),
      );
    if (issuer.coverage_status === 'institutional_context_only')
      companyPanel.append(
        el(
          'p',
          'Documentos institucionais: descrevem regras e atividades da empresa. Seu registro nesta semana não comprova uma mudança no negócio ou a causa da variação do preço.',
          'context-muted',
        ),
      );
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
          'Resultados disponíveis até o fechamento',
          issuer.financial_context.text,
          issuer.financial_context.source_ids,
        ),
      );
    const news = el('details');
    news.append(el('summary', `Documentos e notícias (${issuer.events.length})`));
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
            `Depois do fechamento de ${date(context.company.price_end)}: não explica o retorno encerrado nessa data.`,
          ),
        );
      item.append(el('p', event.text));
      if (event.context_role === 'institutional_document')
        item.append(
          el(
            'p',
            'Documento institucional; não confirma um novo acontecimento empresarial.',
            'context-muted',
          ),
        );
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
    const marketTitle = el('div', '', 'market-title-row');
    const marketInfo = el('span', '', 'asset-info');
    const marketButton = el('button', 'i', 'info-button');
    marketButton.type = 'button';
    marketButton.setAttribute('aria-label', 'Como os indicadores de mercado são calculados');
    marketButton.setAttribute('aria-describedby', 'market-method-help');
    marketButton.setAttribute('aria-expanded', 'false');
    const marketHelp = el(
      'span',
      context.market.method,
      'info-tooltip asset-tooltip market-tooltip',
    );
    marketHelp.id = 'market-method-help';
    marketHelp.setAttribute('role', 'tooltip');
    marketButton.addEventListener('click', () => {
      const open = marketButton.getAttribute('aria-expanded') === 'true';
      document
        .querySelectorAll('.info-button[aria-expanded="true"]')
        .forEach((button) => button.setAttribute('aria-expanded', 'false'));
      marketButton.setAttribute('aria-expanded', String(!open));
    });
    marketInfo.append(marketButton, marketHelp);
    marketTitle.append(el('h2', 'Referências de mercado'), marketInfo);
    const period = context.market.indicators.find((item) => item[selectedWindow])?.[selectedWindow];
    const heading = el('div', '', 'market-heading');
    heading.append(marketTitle);
    if (period)
      heading.append(
        el('span', `${date(period.start_date)} → ${date(period.end_date)}`, 'market-period'),
      );
    marketPanel.append(heading);
    const grid = el('div', '', 'market-quotes');
    const referenceDetails = el('details', '', 'market-reference-details');
    referenceDetails.append(el('summary', 'Dados e fontes de mercado'));
    const tableWrap = el('div', '', 'market-table-wrap');
    tableWrap.tabIndex = 0;
    tableWrap.setAttribute('role', 'region');
    tableWrap.setAttribute(
      'aria-label',
      'Dados e fontes de mercado; role para consultar todas as colunas',
    );
    const table = el('table', '', 'market-reference-table');
    const tableHead = el('thead');
    const headerRow = el('tr');
    for (const label of [
      'Indicador',
      'Data inicial',
      'Data final',
      'Valor inicial',
      'Valor final',
      'Unidade',
      'Fonte',
    ]) {
      const cell = el('th', label);
      cell.scope = 'col';
      headerRow.append(cell);
    }
    tableHead.append(headerRow);
    const tableBody = el('tbody');
    table.append(tableHead, tableBody);
    tableWrap.append(table);
    referenceDetails.append(tableWrap);
    for (const indicator of context.market.indicators) {
      const values = indicator[selectedWindow];
      const quote = el('article', '', 'market-quote');
      quote.append(el('h3', indicator.label));
      if (!values) {
        quote.append(el('span', 'Indisponível', 'context-muted'));
        grid.append(quote);
        continue;
      }
      const value = Number(values.change_pct);
      quote.append(
        el(
          'strong',
          `${value > 0 ? '+' : ''}${number.format(value)}%`,
          value < 0 ? 'negative' : value > 0 ? 'positive' : '',
        ),
      );
      if (
        period &&
        (values.start_date !== period.start_date || values.end_date !== period.end_date)
      )
        quote.append(
          el('p', `${date(values.start_date)} → ${date(values.end_date)}`, 'market-quote-date'),
        );
      grid.append(quote);
      const row = el('tr');
      const name = el('th', indicator.label);
      name.scope = 'row';
      row.append(
        name,
        el('td', date(values.start_date)),
        el('td', date(values.end_date)),
        el('td', number.format(Number(values.start_value)), 'market-number'),
        el('td', number.format(Number(values.end_value)), 'market-number'),
        el('td', indicator.unit),
      );
      const sourceCell = el('td');
      sourceCell.append(link(indicator.source_label, indicator.source_url));
      row.append(sourceCell);
      tableBody.append(row);
    }
    if (context.market.missing_indicators?.length)
      referenceDetails.append(
        el(
          'p',
          `Indicadores indisponíveis: ${context.market.missing_indicators.join(', ')}.`,
          'context-muted',
        ),
      );
    marketPanel.append(grid, referenceDetails);
    const events = context.market.events || [];
    if (events.length) {
      const preview = el('section', '', 'market-event-preview');
      preview.append(
        el('h3', 'Acontecimentos da semana'),
        el(
          'p',
          `${date(context.market.calendar_week.start)} a ${date(context.market.calendar_week.end)}`,
          'market-period',
        ),
      );
      for (const event of events) {
        const row = el('article', '', 'market-event-headline');
        const headline = el('p', event.title);
        if (event.after_price_end)
          headline.append(el('span', 'Posterior ao fechamento final', 'market-event-timing'));
        const source = link('Fonte', event.source_url);
        source.setAttribute('aria-label', `${event.title}: ${event.source_label}`);
        row.append(el('span', event.date_label, 'market-event-date'), headline, source);
        preview.append(row);
      }
      const newsGroup = el('details', '', 'market-news');
      newsGroup.open = marketNewsOpen;
      newsGroup.append(el('summary', `Detalhes e fontes · ${events.length} acontecimentos`));
      const fullEvents = el('div', '', 'market-events');
      for (const event of events) {
        const card = el('article', '', 'market-card');
        card.append(
          el('p', event.date_label, 'context-muted'),
          el('h3', event.title),
          el('p', event.text),
          link(event.source_label, event.source_url),
        );
        if (event.after_price_end)
          card.append(
            el(
              'strong',
              `Depois do fechamento de ${date(context.company.price_end)}: não explica os retornos encerrados nessa data.`,
            ),
          );
        fullEvents.append(card);
      }
      newsGroup.append(fullEvents);
      preview.append(newsGroup);
      marketPanel.append(preview);
    }
    if (context.market.missing_event_topics?.length) {
      const coverage = el('details', '', 'market-reference-details');
      coverage.append(
        el('summary', 'Cobertura dos acontecimentos'),
        el(
          'p',
          `Sem acontecimentos confirmados nas fontes consultadas para: ${context.market.missing_event_topics.join(', ')}.`,
          'context-muted',
        ),
      );
      marketPanel.append(coverage);
    }
  }
  async function load(kind, selection, runId) {
    const generation = ++loadGeneration;
    context = null;
    renderedSelection = '';
    message =
      kind === 'featured'
        ? 'Carregando o contexto revisado…'
        : 'Consultando o contexto desta execução… O ranking já está disponível.';
    render(selection().ticker, selection().window);
    const endpoint =
      kind === 'featured' ? '/api/featured/context' : `/api/analyses/${runId}/context`;
    const started = Date.now();
    async function refresh() {
      try {
        const response = await fetch(endpoint);
        if (!response.ok) throw new Error('Context request failed');
        const payload = await response.json();
        if (generation !== loadGeneration) return;
        if (payload.status === 'available') context = payload;
        else message = payload.message;
        if (payload.status === 'processing' && Date.now() - started < 600000)
          setTimeout(refresh, 3000);
        else if (payload.status === 'processing')
          message =
            'O contexto ainda não foi concluído. Atualize esta página mais tarde; o ranking está disponível.';
      } catch {
        message =
          'Não foi possível carregar o contexto. O ranking e os gráficos continuam disponíveis.';
      }
      render(selection().ticker, selection().window);
    }
    await refresh();
  }
  window.rankingContext = { load, render };
})();
