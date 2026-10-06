const $ = (id) => document.getElementById(id);
const state = { data: null, window: 'primary', ticker: null, runId: null, chartMode: 'price' };
const nf = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2, minimumFractionDigits: 2 });
const money = (value) => nf.format(Number(value));
const preciseMoney = (value) =>
  new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 6, minimumFractionDigits: 2 }).format(
    Number(value),
  );
const pct = (value) => `${nf.format(Number(value))}%`;
const signedPct = (value) => `${Number(value) > 0 ? '+' : ''}${pct(value)}`;
const signedMoney = (value) =>
  `${Number(value) > 0 ? '+' : Number(value) < 0 ? '−' : ''}R$ ${preciseMoney(Math.abs(Number(value)))}`;
const day = (value) => {
  if (!value) return '—';
  const [y, m, d] = value.split('-');
  return `${d}/${m}/${y}`;
};
const text = (id, value) => {
  $(id).textContent = value;
};
function node(tag, className, value) {
  const e = document.createElement(tag);
  if (className) e.className = className;
  if (value !== undefined) e.textContent = value;
  return e;
}
function clear(element) {
  element.replaceChildren();
}
function error(message) {
  $('error').hidden = false;
  $('error').textContent = message;
  $('loading').hidden = true;
}
async function json(url, options) {
  const response = await fetch(url, options);
  let payload;
  try {
    payload = await response.json();
  } catch {
    payload = { detail: `Falha HTTP ${response.status}` };
  }
  if (!response.ok)
    throw new Error(
      typeof payload.detail === 'string' ? payload.detail : JSON.stringify(payload.detail),
    );
  return payload;
}

function render(data) {
  $('short-week-notice').hidden = !data.week.nonfriday_end_accepted;
  if (data.week.nonfriday_end_accepted)
    $('short-week-notice').textContent =
      `Semana encurtada aceita após revisão: último fechamento em ${day(data.week.last_week_close)}. Confira a decisão na auditoria desta execução.`;
  state.data = data;
  state.window = 'primary';
  state.ticker = data.windows.primary.top20[0]?.ticker || null;
  $('loading').hidden = true;
  $('error').hidden = true;
  $('analysis-status').hidden = true;
  $('dashboard').hidden = false;
  text('metric-alternative', pct(data.windows.alternative.mean_pct));
  renderWindow();
}

function renderWindow() {
  const data = state.data;
  if (!data) return;
  const current = data.windows[state.window];
  const alt = state.window === 'alternative';
  $('primary-button').classList.toggle('active', !alt);
  $('alternative-button').classList.toggle('active', alt);
  $('primary-button').setAttribute('aria-pressed', String(!alt));
  $('alternative-button').setAttribute('aria-pressed', String(alt));
  text(
    'window-explanation',
    alt
      ? 'Compara o primeiro e o último fechamento disponíveis dentro da semana.'
      : 'Inclui o movimento do primeiro pregão: compara o fechamento anterior à semana com o último fechamento dela.',
  );
  $('ranking-download').href =
    `${data.kind === 'featured' ? '/api/featured/files' : `/api/analyses/${state.runId}/files`}/${alt ? 'top20_alternativo.csv' : 'top20.csv'}`;
  text('metric-mean', pct(current.mean_pct));
  text('metric-eligible', current.eligible.toLocaleString('pt-BR'));
  const b = current.breadth;
  text('metric-up', `${((b.up / b.denominator) * 100).toFixed(1).replace('.', ',')}%`);
  text('metric-up-note', `${b.up} de ${b.denominator} ações elegíveis`);
  text(
    'ranking-subtitle',
    `${day(current.start_date)} → ${day(current.end_date)} · fechamento ajustado da Economatica · ${current.excluded} instrumentos excluídos`,
  );
  if (!current.top20.some((row) => row.ticker === state.ticker))
    state.ticker = current.top20[0]?.ticker || null;
  const select = $('asset-select');
  clear(select);
  current.top20.forEach((row) => {
    const option = node('option', '', `${row.ticker} · ${signedPct(row.return_pct)}`);
    option.value = row.ticker;
    select.append(option);
  });
  select.value = state.ticker;
  renderTable(current.top20);
  const interpretation = current.interpretation;
  if (interpretation?.leader) {
    const leader = interpretation.leader;
    text(
      'ranking-highlights',
      `${leader.ticker} lidera com ${signedPct(leader.return_pct)} (${signedMoney(leader.change_brl)} por ação). Os retornos deste top ${current.top20.length} vão de ${pct(interpretation.last_return_pct)} a ${pct(leader.return_pct)}.`,
    );
    text(
      'ranking-limits',
      `${interpretation.low_initial_price_count} de ${current.top20.length} ações começaram abaixo de R$ 1,00. Uma base de preço pequena pode ampliar a variação percentual; o ganho em R$ aparece no painel da ação.${interpretation.alerted_tickers.length ? ` Há alertas nas pontas para ${interpretation.alerted_tickers.join(', ')}; selecione a ação para conferir.` : ' Nenhum alerta registrado nas pontas do top desta janela.'}`,
    );
    text('negotiation-note', interpretation.negotiation_note);
  }
  renderDetail();
  renderDistribution(b);
  renderHeatmap(current.top20);
  renderBreadth(b);
}

function renderTable(rows) {
  const body = $('ranking-body');
  clear(body);
  rows.forEach((row, index) => {
    const tr = node('tr', row.ticker === state.ticker ? 'selected' : '');
    tr.tabIndex = 0;
    tr.setAttribute('aria-label', `${index + 1} ${row.ticker}, retorno ${pct(row.return_pct)}`);
    tr.setAttribute('aria-selected', String(row.ticker === state.ticker));
    [
      String(index + 1),
      row.ticker,
      row.instrument_type === 'acao_on' ? 'ON' : 'PN',
      `R$ ${money(row.start_close)}`,
      `R$ ${money(row.end_close)}`,
      signedPct(row.return_pct),
    ].forEach((value, i) =>
      tr.append(
        node('td', i === 5 ? (Number(row.return_pct) < 0 ? 'negative' : 'positive') : '', value),
      ),
    );
    if (row.issues?.length) {
      const marker = node('span', 'asset-issue-marker', 'ⓘ');
      marker.title = 'Alerta nesta janela. Selecione a ação para conferir.';
      marker.setAttribute('aria-label', 'Com alerta; selecione para conferir');
      tr.children[1].append(marker);
    }
    const select = () => {
      state.ticker = row.ticker;
      $('asset-select').value = row.ticker;
      renderTable(rows);
      renderDetail();
      if (matchMedia('(max-width: 800px)').matches) {
        $('asset-detail').scrollIntoView({
          behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth',
          block: 'start',
        });
      }
    };
    tr.addEventListener('click', select);
    tr.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        select();
        body.children[index].focus();
      }
    });
    body.append(tr);
  });
}

function svg(tag, attributes = {}) {
  const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const [k, v] of Object.entries(attributes)) el.setAttribute(k, v);
  return el;
}
function renderDetail() {
  if (!state.ticker) return;
  const row = state.data.windows[state.window].top20.find((item) => item.ticker === state.ticker);
  text('detail-ticker', row.ticker);
  text('detail-kind', row.instrument_type === 'acao_on' ? 'AÇÃO ORDINÁRIA' : 'AÇÃO PREFERENCIAL');
  text('detail-return', signedPct(row.return_pct));
  $('detail-return').classList.toggle('negative', Number(row.return_pct) < 0);
  text('detail-start', `R$ ${preciseMoney(row.start_close)}`);
  text('detail-end', `R$ ${preciseMoney(row.end_close)}`);
  text('detail-change', signedMoney(row.change_brl));
  const alerts = $('detail-alerts');
  clear(alerts);
  alerts.hidden = !row.issues?.length;
  const labels = {
    close: 'Fechamento',
    average: 'Preço médio',
    raw_volume: 'Volume bruto',
    adjusted_quantity: 'Quantidade ajustada',
    high: 'Máximo',
    low: 'Mínimo',
    open: 'Abertura',
  };
  for (const issue of row.issues || []) {
    alerts.append(
      node(
        'p',
        '',
        `${day(issue.trade_date)} · ${labels[issue.field] || issue.field}: ${issue.reason}. ${issue.field === 'close' ? 'Afeta o fechamento usado no retorno; o valor foi preservado, sem correção automática.' : 'Este campo não entra na fórmula do retorno; o fechamento foi preservado.'}`,
      ),
    );
  }
  const returns = state.chartMode === 'returns';
  $('chart-price').classList.toggle('active', !returns);
  $('chart-returns').classList.toggle('active', returns);
  $('chart-price').setAttribute('aria-pressed', String(!returns));
  $('chart-returns').setAttribute('aria-pressed', String(returns));
  text(
    'detail-note',
    `${returns ? 'Retorno entre fechamentos ajustados de datas consecutivas da extração. Uma lacuna indica ausência de comparação válida.' : 'Preço de fechamento ajustado em reais (R$) por ação.'} O ranking compara os fechamentos de ${day(row.start_date)} e ${day(row.end_date)}. Variação em R$ = final − inicial, por ação ajustada; não representa o resultado de uma operação com custos.`,
  );
  const box = $('detail-chart');
  clear(box);
  const series = returns
    ? (state.data.daily.heatmap[row.ticker] || []).map((p) => ({
        date: p.date,
        value: p.return_pct,
      }))
    : (state.data.daily.series[row.ticker] || []).map((p) => ({ date: p.date, value: p.close }));
  const points = series.filter((p) => p.value !== null && Number.isFinite(Number(p.value)));
  if (points.length < (returns ? 1 : 2)) {
    box.append(
      node(
        'div',
        'chart-empty',
        returns
          ? 'Sem comparações válidas para os retornos diários.'
          : 'Série diária indisponível para este ativo.',
      ),
    );
    return;
  }
  const lineColor = Number(row.return_pct) < 0 ? '#f4475b' : '#3cdaa8';
  const values = points.map((p) => Number(p.value));
  const min = Math.min(...values, ...(returns ? [0] : [])),
    max = Math.max(...values, ...(returns ? [0] : [])),
    pad = Math.max((max - min) * 0.18, Math.abs(max) * 0.04, returns ? 0.5 : 0.01);
  const lower = returns ? min - pad : Math.max(0, min - pad),
    upper = max + pad,
    w = Math.max(240, box.clientWidth),
    h = Math.max(240, Math.min(320, w * 0.48)),
    left = w < 450 ? 64 : 80,
    right = w < 450 ? 20 : 25,
    top = 32,
    bottom = 40;
  const tickStep = (upper - lower) / 4;
  const tickFormat = new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: tickStep < 0.01 ? 5 : tickStep < 0.1 ? 3 : 2,
  });
  const allDates = returns ? state.data.daily.dates.slice(1) : state.data.daily.dates;
  const plotWidth = w - left - right;
  const x = (d) =>
    returns
      ? left + ((allDates.indexOf(d) + 0.5) / Math.max(1, allDates.length)) * plotWidth
      : left + (allDates.indexOf(d) / Math.max(1, allDates.length - 1)) * plotWidth;
  const y = (v) => top + ((upper - v) / (upper - lower)) * (h - top - bottom);
  const chart = svg('svg', {
    viewBox: `0 0 ${w} ${h}`,
    role: 'group',
    'aria-label': `${returns ? 'Retornos diários em percentual' : 'Fechamento ajustado em reais por ação'} de ${row.ticker}; toque, passe o cursor ou foque uma observação para ver o valor`,
  });
  const axisLabel = (content, attributes) => {
    const label = svg('text', attributes);
    label.textContent = content;
    chart.append(label);
  };
  if (returns)
    axisLabel('RETORNO DIÁRIO (%)', {
      x: returns ? 0 : left - 9,
      y: 12,
      fill: '#a4a8af',
      'font-size': 12,
      'text-anchor': returns ? 'start' : 'end',
    });
  chart.append(svg('line', { x1: left, y1: top, x2: left, y2: h - bottom, stroke: '#55595f' }));
  chart.append(
    svg('line', { x1: left, y1: h - bottom, x2: w - right, y2: h - bottom, stroke: '#55595f' }),
  );
  for (let i = 0; i <= 4; i++) {
    const yy = top + (i / 4) * (h - top - bottom),
      tick = upper - (i / 4) * (upper - lower);
    if (returns && Math.abs(yy - y(0)) < 16) continue;
    chart.append(svg('line', { x1: left - 5, y1: yy, x2: left, y2: yy, stroke: '#55595f' }));
    axisLabel(`${returns ? '' : 'R$ '}${tickFormat.format(tick)}${returns ? '%' : ''}`, {
      x: left - 9,
      y: yy + 4,
      fill: '#a4a8af',
      'font-size': 12,
      'text-anchor': 'end',
    });
  }
  const dateStep = Math.max(
    1,
    Math.ceil(allDates.length / Math.max(2, Math.floor(plotWidth / 55))),
  );
  allDates.forEach((d, i) => {
    if (i !== 0 && i !== allDates.length - 1 && i % dateStep !== 0) return;
    const xx = x(d);
    chart.append(
      svg('line', { x1: xx, y1: h - bottom, x2: xx, y2: h - bottom + 5, stroke: '#4c4f55' }),
    );
    axisLabel(day(d).slice(0, 5), {
      x: xx,
      y: h - 12,
      fill: '#a4a8af',
      'font-size': 12,
      'text-anchor': 'middle',
    });
  });
  const byDate = new Map(series.map((p) => [p.date, p.value]));
  let segment = [];
  if (!returns) {
    const defs = svg('defs'),
      gradient = svg('linearGradient', { id: 'price-area', x1: '0', y1: '0', x2: '0', y2: '1' });
    gradient.append(
      svg('stop', { offset: '0%', 'stop-color': lineColor, 'stop-opacity': 0.22 }),
      svg('stop', { offset: '100%', 'stop-color': lineColor, 'stop-opacity': 0 }),
    );
    defs.append(gradient);
    chart.append(defs);
  }
  const drawSegment = () => {
    if (segment.length > 1) {
      const first = segment[0],
        last = segment[segment.length - 1];
      chart.append(
        svg('polygon', {
          points: [...segment, [last[0], h - bottom], [first[0], h - bottom]]
            .map((p) => p.join(','))
            .join(' '),
          fill: 'url(#price-area)',
        }),
      );
      chart.append(
        svg('polyline', {
          points: segment.map((p) => p.join(',')).join(' '),
          fill: 'none',
          stroke: lineColor,
          'stroke-width': '2.5',
          'stroke-linejoin': 'round',
        }),
      );
    }
    segment = [];
  };
  if (returns) {
    chart.append(
      svg('line', {
        x1: left,
        y1: y(0),
        x2: w - right,
        y2: y(0),
        stroke: '#777d86',
        'stroke-width': 1,
      }),
    );
    axisLabel('0%', {
      x: left - 9,
      y: y(0) + 4,
      fill: '#d0d3d8',
      'font-size': 12,
      'text-anchor': 'end',
    });
  } else {
    allDates.forEach((d) => {
      const close = byDate.get(d);
      if (close === null || close === undefined) {
        drawSegment();
        return;
      }
      segment.push([x(d), y(Number(close))]);
    });
    drawSegment();
  }
  const guide = svg('line', {
    x1: 0,
    y1: top,
    x2: 0,
    y2: h - bottom,
    stroke: '#8e949c',
    'stroke-dasharray': '3 4',
    visibility: 'hidden',
  });
  chart.append(guide);
  const tip = node('div', 'chart-tooltip');
  tip.hidden = true;
  tip.setAttribute('role', 'status');
  const show = (p, xx) => {
    guide.setAttribute('x1', xx);
    guide.setAttribute('x2', xx);
    guide.setAttribute('visibility', 'visible');
    tip.textContent = `${day(p.date)} · ${returns ? signedPct(p.value) : `R$ ${preciseMoney(p.value)} / ação`}`;
    tip.style.left = `${Math.min(72, Math.max(28, (xx / w) * 100))}%`;
    tip.style.top = `${(Math.max(30, y(Number(p.value))) / h) * 100}%`;
    tip.hidden = false;
  };
  const hide = () => {
    guide.setAttribute('visibility', 'hidden');
    tip.hidden = true;
  };
  points.forEach((p) => {
    const value = Number(p.value),
      xx = x(p.date),
      yy = y(value),
      barWidth = Math.min(42, (plotWidth / Math.max(1, allDates.length)) * 0.55);
    if (returns) {
      chart.append(
        svg('rect', {
          x: xx - barWidth / 2,
          y: Math.min(yy, y(0)),
          width: barWidth,
          height: Math.max(2, Math.abs(yy - y(0))),
          fill: value < 0 ? '#f4475b' : value > 0 ? '#3cdaa8' : '#9a9da5',
        }),
      );
    } else {
      chart.append(svg('circle', { cx: xx, cy: yy, r: 4, fill: lineColor }));
    }
    const attrs = returns
      ? { x: xx - barWidth / 2 - 5, y: top, width: barWidth + 10, height: h - top - bottom }
      : {
          x: Math.max(left - 14, xx - plotWidth / Math.max(1, allDates.length - 1) / 2),
          y: top,
          width:
            Math.min(w - right + 14, xx + plotWidth / Math.max(1, allDates.length - 1) / 2) -
            Math.max(left - 14, xx - plotWidth / Math.max(1, allDates.length - 1) / 2),
          height: h - top - bottom,
        };
    const hit = svg('rect', {
      ...attrs,
      fill: 'transparent',
      tabindex: 0,
      role: 'button',
      'aria-label': `${day(p.date)}: ${returns ? `retorno diário ${signedPct(p.value)}` : `fechamento ajustado R$ ${preciseMoney(p.value)}`}`,
    });
    hit.addEventListener('pointerenter', () => show(p, xx));
    hit.addEventListener('pointerleave', hide);
    hit.addEventListener('click', () => show(p, xx));
    hit.addEventListener('focus', () => show(p, xx));
    hit.addEventListener('blur', hide);
    hit.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        show(p, xx);
      }
      if (e.key === 'Escape') hide();
    });
    chart.append(hit);
  });
  if (!returns) {
    [points[0], points[points.length - 1]].forEach((p, index) =>
      axisLabel(`R$ ${money(p.value)}`, {
        x: x(p.date),
        y: y(Number(p.value)) - 14,
        fill: lineColor,
        'font-size': 14,
        'font-weight': 600,
        'text-anchor': index === 0 ? 'start' : 'end',
        stroke: '#050506',
        'stroke-width': 4,
        'paint-order': 'stroke',
        class: 'endpoint-value',
      }),
    );
  }
  chart.style.aspectRatio = `${w} / ${h}`;
  box.append(chart, tip);
}

function renderDistribution(breadth) {
  const box = $('distribution');
  clear(box);
  const maximum = Math.max(1, ...breadth.bins.map((b) => b.count));
  breadth.bins.forEach((bin) => {
    const row = node('div', 'dist-row');
    row.append(node('span', '', bin.label));
    const track = node('div', 'dist-track');
    const fill = node('div', 'dist-fill');
    fill.style.width = `${(bin.count / maximum) * 100}%`;
    track.append(fill);
    row.append(track);
    row.append(node('span', 'dist-count', String(bin.count)));
    box.append(row);
  });
}
function renderBreadth(b) {
  const box = $('breadth-counts');
  clear(box);
  [
    ['Em alta', b.up, 'positive'],
    ['Em baixa', b.down, 'negative'],
    ['Estáveis', b.flat, ''],
  ].forEach(([label, count, cls]) => {
    const wrap = node('div', 'breadth-stat');
    wrap.append(node('strong', cls, String(count)));
    wrap.append(node('span', '', label));
    box.append(wrap);
  });
  const bar = $('breadth-bar');
  clear(bar);
  [
    ['up', b.up],
    ['down', b.down],
    ['flat', b.flat],
  ].forEach(([cls, count]) => {
    const span = node('span', cls);
    span.style.width = `${(count / Math.max(1, b.denominator)) * 100}%`;
    bar.append(span);
  });
  text(
    'breadth-note',
    `Base: ${b.denominator} ações elegíveis com fechamento válido nas duas pontas. Não representa todo o mercado da B3.`,
  );
}
function heatColor(raw) {
  if (raw === null) return null;
  const n = Number(raw);
  const alpha = Math.min(0.83, 0.14 + (Math.abs(n) / 15) * 0.65);
  return n > 0 ? `rgba(19,147,109,${alpha})` : n < 0 ? `rgba(201,54,73,${alpha})` : '#26343f';
}
function renderHeatmap(rows) {
  const wrap = $('heatmap');
  clear(wrap);
  const dates = state.data.daily.dates.slice(1);
  if (!dates.length) {
    wrap.append(node('p', 'muted', 'Sem série diária disponível para esta extração.'));
    return;
  }
  const grid = node('div', 'heatmap-grid');
  grid.style.gridTemplateColumns = `95px repeat(${dates.length},minmax(75px,1fr))`;
  grid.append(node('span', 'head', 'ATIVO'));
  dates.forEach((d) => grid.append(node('span', 'head', day(d).slice(0, 5))));
  rows.forEach((row) => {
    const ticker = node('button', 'ticker', row.ticker);
    ticker.type = 'button';
    ticker.addEventListener('click', () => {
      state.ticker = row.ticker;
      $('asset-select').value = row.ticker;
      renderTable(rows);
      renderDetail();
      document.querySelector('.detail-panel').scrollIntoView({
        behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches
          ? 'instant'
          : 'smooth',
        block: 'nearest',
      });
    });
    grid.append(ticker);
    const changes = new Map(
      (state.data.daily.heatmap[row.ticker] || []).map((c) => [c.date, c.return_pct]),
    );
    dates.forEach((d) => {
      const raw = changes.get(d) ?? null;
      const cell = node(
        'span',
        `heat-cell${raw === null ? ' missing' : ''}`,
        raw === null ? '—' : `${Number(raw) > 0 ? '+' : ''}${pct(raw)}`,
      );
      const color = heatColor(raw);
      if (color) cell.style.background = color;
      cell.title = `${row.ticker} · ${day(d)}: ${raw === null ? 'sem comparação válida' : pct(raw)}`;
      grid.append(cell);
    });
  });
  wrap.append(grid);
}
async function loadRun(id) {
  state.runId = id;
  $('dashboard').hidden = true;
  $('loading').hidden = true;
  $('analysis-status').hidden = false;
  try {
    const job = await json(`/api/analyses/${id}`);
    const names = {
      queued: 'Aguardando',
      running: 'Processando',
      completed: 'Concluída',
      failed: 'Falhou',
    };
    const panel = $('analysis-status');
    clear(panel);
    panel.classList.toggle('failed', job.status === 'failed');
    panel.append(
      node('div', 'eyebrow', 'EXECUÇÃO INDEPENDENTE'),
      node(
        'h2',
        '',
        job.status === 'failed'
          ? 'A análise não pôde ser concluída'
          : job.status === 'queued'
            ? 'Sua análise está na fila'
            : 'Preparando sua análise',
      ),
    );
    panel.append(
      node(
        'p',
        'execution-current',
        job.error || `${names[job.status] || job.status} · ${job.stage}`,
      ),
    );
    if (job.problem?.guidance) panel.append(node('p', 'doc-note', job.problem.guidance));
    if (job.status !== 'failed') {
      const steps = node('ol', 'execution-steps');
      const current =
        job.status === 'queued'
          ? 0
          : job.stage === 'Preparando resultado'
            ? 3
            : job.stage.includes('Calculando')
              ? 2
              : job.stage.includes('B3') || job.stage.includes('Classificando')
                ? 1
                : 0;
      [
        'Leitura e tratamento',
        'Classificação pela B3',
        'Cálculo dos rankings',
        'Preparação do resultado',
      ].forEach((label, index) => {
        const step = node(
          'li',
          job.status === 'queued'
            ? ''
            : index < current
              ? 'done'
              : index === current
                ? 'current'
                : '',
        );
        step.append(
          node('span', '', String(index + 1).padStart(2, '0')),
          node('strong', '', label),
        );
        if (index === current && job.status === 'running')
          step.setAttribute('aria-current', 'step');
        steps.append(step);
      });
      panel.append(steps);
    }
    panel.append(
      node(
        'p',
        'muted',
        job.status === 'failed'
          ? 'Confira o motivo acima antes de reenviar. O resultado de referência continua disponível.'
          : 'Esta página acompanha o processamento automaticamente. Guarde seu endereço para voltar à mesma execução. O limite de processamento é de dez minutos; o resultado ficará disponível por sete dias.',
      ),
    );
    const links = node('div', 'page-context');
    for (const [label, href] of [
      ['Enviar outra base ↗', '/nova-analise'],
      ['Ver resultado de referência ↗', '/'],
    ]) {
      const link = node('a', '', label);
      link.href = href;
      links.append(link);
    }
    panel.append(links);
    if (job.status === 'completed') {
      const result = await json(`/api/analyses/${id}/result`);
      render(result);
      return;
    }
    if (job.status === 'failed') return;
    setTimeout(() => loadRun(id), 1800);
  } catch (exc) {
    error(exc.message);
    $('analysis-status').hidden = true;
  }
}
document.addEventListener('DOMContentLoaded', () => {
  $('asset-select').addEventListener('change', (event) => {
    state.ticker = event.target.value;
    renderTable(state.data.windows[state.window].top20);
    renderDetail();
  });
  $('chart-price').addEventListener('click', () => {
    state.chartMode = 'price';
    renderDetail();
  });
  $('chart-returns').addEventListener('click', () => {
    state.chartMode = 'returns';
    renderDetail();
  });
  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      if (state.data) renderDetail();
    }, 100);
  });
  $('primary-button').addEventListener('click', () => {
    state.window = 'primary';
    renderWindow();
  });
  $('alternative-button').addEventListener('click', () => {
    state.window = 'alternative';
    renderWindow();
  });
  const match = window.location.pathname.match(/^\/analise\/([0-9a-f]{32})$/);
  if (match) {
    $('nav-result').href = `/analise/${match[1]}`;
    $('nav-method').href = `/documentacao?analise=${match[1]}`;
    $('execution-audit').href = `/analise/${match[1]}/metodologia`;
    loadRun(match[1]);
  } else
    json('/api/featured')
      .then(render)
      .catch((exc) => error(exc.message));
});
