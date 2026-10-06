const el = (id) => document.getElementById(id);
const put = (id, value) => {
  el(id).textContent = value;
};
const format = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
const dateLabel = (value) => value.split('-').reverse().join('/');
function item(tag, cls, value) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (value !== undefined) n.textContent = value;
  return n;
}
function auditTable(target, headers, rows) {
  target.replaceChildren();
  if (!rows.length) {
    target.append(item('p', 'doc-note', 'Nenhum registro nesta seleção.'));
    return;
  }
  const wrap = item('div', 'audit-table-wrap'),
    table = item('table', 'audit-table'),
    caption = item('caption', '', target.dataset.caption);
  const head = item('thead'),
    header = item('tr');
  headers.forEach((label) => {
    const cell = item('th', '', label);
    cell.scope = 'col';
    header.append(cell);
  });
  head.append(header);
  const body = item('tbody');
  rows.forEach((values) => {
    const row = item('tr');
    values.forEach((value) => row.append(item('td', '', String(value))));
    body.append(row);
  });
  table.append(caption, head, body);
  wrap.append(table);
  target.append(wrap);
}
function showAudit(data) {
  const audit = data.audit;
  if (!audit?.available) {
    put(
      'audit-availability',
      audit?.note || 'Esta execução não contém evidências detalhadas publicadas.',
    );
    el('audit-detail-controls').hidden = true;
    return;
  }
  const s = audit.summary;
  put(
    'audit-availability',
    `${s.rows_input.toLocaleString('pt-BR')} linhas recebidas · ${s.rows_output.toLocaleString('pt-BR')} preservadas · ${s.distinct_tickers} códigos · ${s.missing_close.toLocaleString('pt-BR')} fechamentos ausentes na extração inteira.`,
  );
  put('audit-count-note', audit.note);
  const labels = {
    INSTRUMENT_AMBIGUOUS: 'Tipo provisório no tratamento',
    MISSING_VALUE: 'Campo ausente',
    OUTSIDE_DAILY_RANGE: 'Preço fora do intervalo diário',
    VOLUME_PRICE_DIVERGENCE: 'Volume e preço médio divergentes',
    DATE_WITHOUT_QUOTES: 'Data sem cotação',
  };
  const typeLabels = { unit: 'Unit', bdr: 'BDR', acao_on: 'ON', acao_pn: 'PN', outro: 'Outro' };
  const fieldLabels = {
    average: 'Preço médio',
    close: 'Fechamento',
    open: 'Abertura',
    high: 'Máximo',
    low: 'Mínimo',
    adjusted_quantity: 'Quantidade ajustada',
    raw_volume: 'Volume bruto',
    instrument_type: 'Espécie',
  };
  const render = () => {
    const key = el('audit-window').value,
      w = audit.windows[key];
    el('audit-quality-counts').dataset.caption =
      `Ocorrências por campo e linha · ${key === 'primary' ? 'principal' : 'alternativa'} · ${w.dates.map(dateLabel).join(' → ')}`;
    el('audit-eligible-issues').dataset.caption =
      `Alertas nas ações elegíveis · ${key === 'primary' ? 'principal' : 'alternativa'} · ${w.dates.map(dateLabel).join(' → ')}`;
    put(
      'audit-window-context',
      `${key === 'primary' ? 'Janela principal' : 'Janela alternativa'} · ${w.dates.map(dateLabel).join(' → ')}. As tabelas de exclusões e qualidade abaixo usam esta janela.`,
    );
    auditTable(
      el('type-exclusions'),
      ['Código', 'Espécie oficial', 'Decisão', 'Motivo'],
      w.type_exclusions.map((row) => [
        row.ticker,
        row.official_types
          .split('; ')
          .map((v) => typeLabels[v] || v)
          .join(', '),
        row.decision === 'excluir' ? 'Excluído' : row.decision,
        row.reason,
      ]),
    );
    auditTable(
      el('audit-quality-counts'),
      ['Ocorrência', 'Extração inteira', 'Duas pontas', 'ON/PN elegíveis', 'Top 20'],
      w.issue_counts.map((row) => [
        labels[row.code] || row.code,
        row.file_occurrences,
        row.endpoint_occurrences,
        row.eligible_occurrences,
        row.top20_occurrences,
      ]),
    );
    auditTable(
      el('audit-eligible-issues'),
      ['Linha CSV', 'Código / data', 'Campo', 'Ocorrência', 'Efeito no cálculo'],
      w.eligible_issues.map((row) => [
        row.source_line,
        `${row.ticker} · ${dateLabel(row.trade_date)}`,
        fieldLabels[row.field] || row.field,
        `${row.explanation.observed} ${row.explanation.context}`,
        row.impact,
      ]),
    );
    auditTable(
      el('audit-sources'),
      ['Fonte', 'Data', 'Arquivo', 'Obtenção'],
      w.sources.map((row) => [
        row.kind === 'registry' ? 'Cadastro B3' : 'COTAHIST',
        dateLabel(row.source_date),
        row.file,
        row.status === 'available' ? 'Arquivo disponível' : row.status,
      ]),
    );
  };
  el('audit-window').addEventListener('change', render);
  render();
}
async function showMethod() {
  const match = location.pathname.match(/^\/analise\/([0-9a-f]{32})\/metodologia$/);
  const resultHref = match ? `/analise/${match[1]}` : '/';
  el('nav-result').href = resultHref;
  el('back-result').href = resultHref;
  el('nav-method').href = match ? `/documentacao?analise=${match[1]}` : '/documentacao';
  el('read-method').href = match
    ? `/documentacao/metodologia?analise=${match[1]}`
    : '/documentacao/metodologia';
  const response = await fetch(match ? `/api/analyses/${match[1]}/result` : '/api/featured');
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Não foi possível carregar esta execução.');
  const primary = data.windows.primary,
    alternative = data.windows.alternative;
  put(
    'method-context',
    `${match ? 'Análise enviada' : 'Resultado de referência'} · referência ${dateLabel(data.week.reference_date)}`,
  );
  put('reference-value', dateLabel(data.week.reference_date));
  put('week-value', `${dateLabel(data.week.week_start)} a ${dateLabel(data.week.week_end)}`);
  if (data.week.nonfriday_end_accepted) {
    el('week-decision').hidden = false;
    const options = data.submission?.options;
    put(
      'week-decision',
      `Semana encurtada aceita explicitamente: último fechamento em ${dateLabel(data.week.last_week_close)}. ` +
        (options?.accepted_at
          ? `Confirmação no formulário em ${new Date(options.accepted_at).toLocaleString('pt-BR')}. A decisão está no registro do envio para download.`
          : 'A aceitação está registrada no relatório do pipeline; esta execução não possui registro de confirmação pelo formulário.') +
        ' Isso não comprova feriado. Os controles de cobertura, preços e classificação foram mantidos.',
    );
  }
  for (const [key, window] of [
    ['primary', primary],
    ['alternative', alternative],
  ]) {
    put(`${key}-start`, dateLabel(window.start_date));
    put(`${key}-end`, dateLabel(window.end_date));
    put(
      `${key}-summary`,
      `${window.top20.length} ações no top · média ${format.format(window.mean_pct)}%`,
    );
  }
  const total = primary.eligible + primary.excluded + data.exclusions.count;
  const groups = [
    [
      'Códigos avaliados',
      total,
      'Todos os códigos da extração, incluindo os sem preços utilizáveis.',
    ],
    [
      'Com duas pontas válidas',
      primary.eligible + primary.excluded,
      `${data.exclusions.count} códigos ficaram sem comparação válida.`,
    ],
    [
      'Ações ON/PN elegíveis',
      primary.eligible,
      `${primary.excluded} instrumentos com preços válidos ficaram fora da definição de ação adotada.`,
    ],
    ['Top do ranking', primary.top20.length, 'Maiores retornos entre as ações elegíveis.'],
  ];
  groups.forEach(([label, count, description]) => {
    const wrap = item('div', 'universe-step');
    const heading = item('div', 'universe-heading');
    heading.append(item('strong', '', count.toLocaleString('pt-BR')), item('span', '', label));
    const track = item('div', 'universe-track');
    const fill = item('span', '');
    fill.style.width = `${total ? (count / total) * 100 : 0}%`;
    track.append(fill);
    wrap.append(heading, track, item('p', '', description));
    el('universe-flow').append(wrap);
  });
  Object.entries(data.exclusions.reasons).forEach(([reason, count]) => {
    const row = item('div', 'reason-row');
    row.append(item('strong', '', String(count)), item('span', '', reason));
    el('exclusion-reasons').append(row);
  });
  const first = primary.top20[0];
  if (first) {
    const example = el('return-example');
    example.append(item('div', 'example-ticker', first.ticker));
    [
      ['Fechamento inicial', `R$ ${format.format(first.start_close)}`, dateLabel(first.start_date)],
      ['Fechamento final', `R$ ${format.format(first.end_close)}`, dateLabel(first.end_date)],
      ['Retorno semanal', `${format.format(first.return_pct)}%`, 'Final ÷ inicial − 1'],
    ].forEach(([label, value, note]) => {
      const part = item('div', 'example-part');
      part.append(item('span', '', label), item('strong', '', value), item('small', '', note));
      example.append(part);
    });
  }
  const fieldNames = {
    average: 'Preço médio',
    close: 'Fechamento',
    open: 'Abertura',
    high: 'Máximo',
    low: 'Mínimo',
    adjusted_quantity: 'Quantidade',
    raw_volume: 'Volume',
  };
  const issues = data.quality.top20_issues || [];
  if (!issues.length)
    el('method-quality').append(
      item('p', 'doc-note', 'Nenhuma ocorrência específica no top 20 principal desta execução.'),
    );
  issues.forEach((issue) => {
    const line = item('div', 'quality-card');
    line.append(
      item('strong', '', `${issue.ticker} · ${dateLabel(issue.trade_date)}`),
      item(
        'span',
        '',
        `${fieldNames[issue.field] || issue.field}: ${issue.explanation.observed} ${issue.explanation.context}`,
      ),
      item('span', '', issue.explanation.impact),
    );
    el('method-quality').append(line);
  });
  const base = match ? `/api/analyses/${match[1]}/files` : '/api/featured/files';
  showAudit(data);
  const files = {
    'top20.csv': ['Ranking principal', 'Os maiores retornos, suas pontas e posições.', 'CSV'],
    'all_returns.csv': [
      'Universo completo',
      'Todos os retornos das ações elegíveis na janela principal.',
      'CSV',
    ],
    'top20_alternativo.csv': [
      'Ranking alternativo',
      'Compare o resultado dentro da semana.',
      'CSV',
    ],
    'all_returns_alternativo.csv': [
      'Universo alternativo',
      'Todos os retornos na janela alternativa.',
      'CSV',
    ],
    'candidate_exclusions.csv': [
      'Exclusões das pontas',
      'Códigos sem duas pontas válidas e seus motivos.',
      'CSV',
    ],
    'quality_context.json': [
      'Contexto de qualidade',
      'Ocorrências relacionadas aos dados utilizados.',
      'JSON',
    ],
    'ranking_report.json': [
      'Relatório da execução',
      'Datas, regras, contagens e assinaturas dos arquivos.',
      'JSON',
    ],
    'analysis_request.json': [
      'Registro do envio',
      'Referência, datas revisadas e aceitação explícita de semana encurtada.',
      'JSON',
    ],
    'README.md': [
      'Leia-me da execução',
      'Decisões e instruções para interpretar os resultados.',
      'MD',
    ],
  };
  const auditFiles = {
    ranking_universe: ['Decisões do universo', 'Inclusão, exclusão ou revisão por código.'],
    period_classification: [
      'Classificação nas pontas',
      'Espécie confirmada e resultado da conciliação.',
    ],
    b3_evidence: ['Evidências oficiais B3', 'Espécie, ISIN, data e identificação da fonte.'],
    classification_manifest: [
      'Manifesto da classificação',
      'Versões e assinaturas das fontes e derivados.',
    ],
    source_acquisition: [
      'Aquisição de fontes',
      'Arquivos, datas, endereços oficiais e disponibilidade.',
    ],
    classification_summary: [
      'Resumo da classificação',
      'Contagens e pendências da confirmação oficial.',
    ],
    ranking_universe_summary: ['Resumo do universo', 'Decisões e motivos agregados.'],
    quality_context: ['Qualidade nas pontas', 'Ocorrências da janela e do top 20.'],
    candidate_exclusions: ['Ausência de duas pontas', 'Códigos sem comparação válida e motivo.'],
  };
  Object.entries(auditFiles).forEach(([stem, [title, description]]) => {
    for (const suffix of ['', '_alternativo']) {
      const type = [
        'ranking_universe',
        'period_classification',
        'b3_evidence',
        'candidate_exclusions',
      ].includes(stem)
        ? 'CSV'
        : 'JSON';
      const name = `${stem}${suffix}.${type.toLowerCase()}`;
      if (!files[name])
        files[name] = [`${title} · ${suffix ? 'alternativa' : 'principal'}`, description, type];
    }
  });
  Object.assign(files, {
    'etl_manifest.json': [
      'Manifesto do tratamento',
      'Entrada, codificação, parâmetros, versões e assinaturas.',
      'JSON',
    ],
    'quality_summary.json': [
      'Qualidade da extração inteira',
      'Contagens e cobertura, incluindo datas fora da semana.',
      'JSON',
    ],
    'quality_by_date.csv': [
      'Cobertura por data',
      'Linhas, códigos e fechamentos disponíveis em cada data.',
      'CSV',
    ],
    'quality_issues.csv': [
      'Ocorrências por linha',
      'Linha original, código, data, campo e motivo; não inclui o CSV bruto.',
      'CSV',
    ],
  });
  const fileGroups = new Map();
  const groupFor = (name) => {
    if (/^(top20|all_returns)/.test(name)) return 'Rankings e retornos';
    if (/^(quality|candidate_exclusions)/.test(name)) return 'Qualidade e exclusões';
    if (
      /^(ranking_universe|period_classification|b3_evidence|classification|source_acquisition)/.test(
        name,
      )
    )
      return 'Classificação e fontes B3';
    return 'Execução e reprodução';
  };
  data.downloads
    .filter((name) => files[name])
    .forEach((name) => {
      const [title, description, type] = files[name];
      const link = item('a', 'audit-file');
      link.href = `${base}/${name}`;
      link.download = name;
      const content = item('div', '');
      content.append(item('strong', '', title), item('p', '', description));
      link.append(content, item('span', 'file-type', `${type} ↓`));
      const groupName = groupFor(name);
      if (!fileGroups.has(groupName)) {
        const details = item('details', 'audit-file-group');
        details.open =
          !matchMedia('(max-width: 800px)').matches || groupName === 'Rankings e retornos';
        details.append(item('summary', '', groupName));
        const body = item('div', '');
        details.append(body);
        fileGroups.set(groupName, body);
        el('audit-files').append(details);
      }
      fileGroups.get(groupName).append(link);
    });
  put('method-hash', data.provenance.input_sha256);
  put('method-version', `${data.provenance.pipeline_version} · ${data.provenance.code_sha256}`);
  el('method-loading').hidden = true;
  el('method-body').hidden = false;
  const picker = document.querySelector('.audit-section-picker');
  picker.addEventListener('change', () => {
    document.getElementById(picker.value).scrollIntoView({
      behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth',
      block: 'start',
    });
    history.replaceState(null, '', `#${picker.value}`);
  });
  const sectionObserver = new IntersectionObserver(
    (entries) => {
      const current = entries.find((entry) => entry.isIntersecting);
      if (current) picker.value = current.target.id;
    },
    { rootMargin: '-80px 0px -65% 0px' },
  );
  document.querySelectorAll('.doc-section').forEach((section) => sectionObserver.observe(section));
}
showMethod().catch((error) => {
  el('method-loading').hidden = true;
  el('method-error').hidden = false;
  put('method-error', error.message);
  put('method-context', 'Execução indisponível');
});
