const $ = (id) => document.getElementById(id);
const state = { data: null, window: 'primary', ticker: null, runId: null };
const nf = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2, minimumFractionDigits: 2 });
const money = (value) => nf.format(Number(value));
const preciseMoney = (value) => new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 6, minimumFractionDigits: 2 }).format(Number(value));
const pct = (value) => `${nf.format(Number(value))}%`;
const signedPct = (value) => `${Number(value)>0?'+':''}${pct(value)}`;
const day = (value) => { if (!value) return '—'; const [y,m,d]=value.split('-'); return `${d}/${m}/${y}`; };
const text = (id, value) => { $(id).textContent = value; };
function node(tag, className, value) { const e=document.createElement(tag); if(className)e.className=className; if(value!==undefined)e.textContent=value; return e; }
function clear(element) { element.replaceChildren(); }
function error(message) { $('error').hidden=false; $('error').textContent=message; $('loading').hidden=true; }
async function json(url, options) { const response=await fetch(url,options); let payload; try { payload=await response.json(); } catch { payload={detail:`Falha HTTP ${response.status}`}; } if(!response.ok) throw new Error(typeof payload.detail==='string'?payload.detail:JSON.stringify(payload.detail)); return payload; }

function render(data) {
  state.data=data; state.window='primary'; state.ticker=data.windows.primary.top20[0]?.ticker || null;
  $('loading').hidden=true; $('error').hidden=true; $('analysis-status').hidden=true; $('dashboard').hidden=false;
  text('run-kind',data.kind==='featured'?'Resultado de referência':'Nova análise');
  text('run-period',`Referência ${day(data.week.reference_date)} · ${day(data.week.week_start)} a ${day(data.week.week_end)}`);
  text('metric-alternative',pct(data.windows.alternative.mean_pct));
  text('input-hash',data.provenance.input_sha256);
  text('code-version',`${data.provenance.pipeline_version} · ${data.provenance.code_sha256.slice(0,16)}…`);
  const method=$('method-list'); clear(method); data.premises.forEach(item=>method.append(node('li','',item)));
  renderQuality(data); renderDownloads(data); renderWindow();
}

function renderWindow() {
  const data=state.data; if(!data)return;
  const current=data.windows[state.window]; const alt=state.window==='alternative';
  $('primary-button').classList.toggle('active',!alt); $('alternative-button').classList.toggle('active',alt);
  $('primary-button').setAttribute('aria-pressed',String(!alt)); $('alternative-button').setAttribute('aria-pressed',String(alt));
  text('window-explanation',alt?'Compara o primeiro e o último fechamento disponíveis dentro da semana.':'Inclui o movimento do primeiro pregão: compara o fechamento anterior à semana com o último fechamento dela.');
  $('ranking-download').href=`${data.kind==='featured'?'/api/featured/files':`/api/analyses/${state.runId}/files`}/${alt?'top20_alternativo.csv':'top20.csv'}`;
  text('metric-mean',pct(current.mean_pct)); text('metric-eligible',current.eligible.toLocaleString('pt-BR'));
  const b=current.breadth; text('metric-up',`${((b.up/b.denominator)*100).toFixed(1).replace('.',',')}%`);
  text('metric-up-note',`${b.up} de ${b.denominator} ações elegíveis`);
  text('ranking-subtitle',`${day(current.start_date)} → ${day(current.end_date)} · fechamento ajustado da Economatica · ${current.excluded} instrumentos excluídos`);
  if(!current.top20.some(row=>row.ticker===state.ticker)) state.ticker=current.top20[0]?.ticker||null;
  const select=$('asset-select');clear(select);current.top20.forEach(row=>{const option=node('option','',`${row.ticker} · ${signedPct(row.return_pct)}`);option.value=row.ticker;select.append(option);});select.value=state.ticker;
  renderTable(current.top20); renderDetail(); renderDistribution(b); renderHeatmap(current.top20); renderBreadth(b);
}

function renderTable(rows) {
  const body=$('ranking-body'); clear(body);
  rows.forEach((row,index)=>{
    const tr=node('tr',row.ticker===state.ticker?'selected':''); tr.tabIndex=0;
    tr.setAttribute('aria-label',`${index+1} ${row.ticker}, retorno ${pct(row.return_pct)}`);
    tr.setAttribute('aria-selected',String(row.ticker===state.ticker));
    [String(index+1),row.ticker,row.instrument_type==='acao_on'?'ON':'PN',money(row.start_close),money(row.end_close),signedPct(row.return_pct)].forEach((value,i)=>tr.append(node('td',i===5?(Number(row.return_pct)<0?'negative':'positive'):'',value)));
    const select=()=>{state.ticker=row.ticker;$('asset-select').value=row.ticker;renderTable(rows);renderDetail();};
    tr.addEventListener('click',select); tr.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select();body.children[index].focus();}});
    body.append(tr);
  });
}

function svg(tag,attributes={}) { const el=document.createElementNS('http://www.w3.org/2000/svg',tag); for(const [k,v] of Object.entries(attributes))el.setAttribute(k,v); return el; }
function renderDetail() {
  if(!state.ticker)return;
  const row=state.data.windows[state.window].top20.find(item=>item.ticker===state.ticker);
  text('detail-ticker',row.ticker); text('detail-kind',row.instrument_type==='acao_on'?'AÇÃO ORDINÁRIA':'AÇÃO PREFERENCIAL');
  text('detail-return',signedPct(row.return_pct));$('detail-return').classList.toggle('negative',Number(row.return_pct)<0); text('detail-start',`${day(row.start_date)} · ${money(row.start_close)}`);
  text('detail-end',`${day(row.end_date)} · ${money(row.end_close)}`);
  const note=state.data.quality.top20_issues.filter(item=>item.ticker===row.ticker);
  text('detail-note',`${note.length?`Atenção: ${note.map(item=>`${day(item.trade_date)} · ${item.field}: ${item.reason}`).join('; ')}. `:''}Preço ajustado por ação, na moeda original do ativo. A extração não identifica o código da moeda. A série diária é contexto; o ranking usa as duas pontas acima.`);
  const box=$('detail-chart'); clear(box);
  const series=state.data.daily.series[row.ticker]||[];
  const points=series.filter(p=>p.close!==null);
  if(points.length<2){box.append(node('div','chart-empty','Série diária indisponível para este ativo.'));return;}
  const lineColor=Number(row.return_pct)<0?'#f4475b':'#3cdaa8';
  const values=points.map(p=>Number(p.close));const min=Math.min(...values),max=Math.max(...values),pad=Math.max((max-min)*.18,max*.04,.01);
  const lower=Math.max(0,min-pad),upper=max+pad,w=600,h=250,left=66,right=18,top=28,bottom=38;
  const tickStep=(upper-lower)/4;
  const tickFormat=new Intl.NumberFormat('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:tickStep<.01?5:tickStep<.1?3:2});
  const allDates=state.data.daily.dates; const x=d=>left+(allDates.indexOf(d)/Math.max(1,allDates.length-1))*(w-left-right);
  const y=v=>top+(upper-v)/(upper-lower)*(h-top-bottom);
  const chart=svg('svg',{viewBox:`0 0 ${w} ${h}`,role:'img','aria-label':`Fechamento ajustado de ${row.ticker}, em moeda original por ação, por data; passe o cursor ou foque um ponto para ver o valor`});
  const axisLabel=(content,attributes)=>{const label=svg('text',attributes);label.textContent=content;chart.append(label);};
  axisLabel('PREÇO · MOEDA ORIGINAL / AÇÃO',{x:0,y:12,fill:'#a4a8af','font-size':12});
  chart.append(svg('line',{x1:left,y1:top,x2:left,y2:h-bottom,stroke:'#55595f'}));
  chart.append(svg('line',{x1:left,y1:h-bottom,x2:w-right,y2:h-bottom,stroke:'#55595f'}));
  for(let i=0;i<=4;i++){
    const yy=top+(i/4)*(h-top-bottom), tick=upper-(i/4)*(upper-lower);
    chart.append(svg('line',{x1:left-5,y1:yy,x2:left,y2:yy,stroke:'#55595f'}));
    axisLabel(tickFormat.format(tick),{x:left-9,y:yy+4,fill:'#a4a8af','font-size':12,'text-anchor':'end'});
  }
  allDates.forEach(d=>{const xx=x(d);chart.append(svg('line',{x1:xx,y1:h-bottom,x2:xx,y2:h-bottom+5,stroke:'#4c4f55'}));axisLabel(day(d).slice(0,5),{x:xx,y:h-12,fill:'#a4a8af','font-size':12,'text-anchor':'middle'});});
  const byDate=new Map(series.map(p=>[p.date,p.close]));let segment=[];
  const drawSegment=()=>{if(segment.length>1){chart.append(svg('polyline',{points:segment.map(p=>p.join(',')).join(' '),fill:'none',stroke:lineColor,'stroke-width':'2.5','stroke-linejoin':'round'}));}segment=[];};
  allDates.forEach(d=>{const close=byDate.get(d);if(close===null||close===undefined){drawSegment();return;}segment.push([x(d),y(Number(close))]);});drawSegment();
  const guide=svg('line',{x1:0,y1:top,x2:0,y2:h-bottom,stroke:'#8e949c','stroke-dasharray':'3 4',visibility:'hidden'});chart.append(guide);
  const tip=node('div','chart-tooltip');tip.hidden=true;tip.setAttribute('role','status');
  const show=(p,xx)=>{guide.setAttribute('x1',xx);guide.setAttribute('x2',xx);guide.setAttribute('visibility','visible');tip.textContent=`${day(p.date)} · ${preciseMoney(p.close)} moeda orig./ação`;tip.style.left=`${Math.min(72,Math.max(28,xx/w*100))}%`;tip.style.top=`${y(Number(p.close))/h*100}%`;tip.hidden=false;};
  const hide=()=>{guide.setAttribute('visibility','hidden');tip.hidden=true;};
  points.forEach(p=>{const xx=x(p.date),yy=y(Number(p.close));chart.append(svg('circle',{cx:xx,cy:yy,r:4,fill:lineColor}));const hit=svg('circle',{cx:xx,cy:yy,r:13,fill:'transparent',tabindex:0,role:'button','aria-label':`${day(p.date)}: fechamento ajustado ${preciseMoney(p.close)}`});hit.addEventListener('pointerenter',()=>show(p,xx));hit.addEventListener('pointerleave',hide);hit.addEventListener('focus',()=>show(p,xx));hit.addEventListener('blur',hide);chart.append(hit);});
  box.append(chart,tip);
}

function renderDistribution(breadth) {
  const box=$('distribution');clear(box);const maximum=Math.max(1,...breadth.bins.map(b=>b.count));
  breadth.bins.forEach(bin=>{const row=node('div','dist-row');row.append(node('span','',bin.label));const track=node('div','dist-track');const fill=node('div','dist-fill');fill.style.width=`${bin.count/maximum*100}%`;track.append(fill);row.append(track);row.append(node('span','dist-count',String(bin.count)));box.append(row);});
}
function renderBreadth(b) {
  const box=$('breadth-counts');clear(box);
  [['Em alta',b.up,'positive'],['Em baixa',b.down,'negative'],['Estáveis',b.flat,'']].forEach(([label,count,cls])=>{const wrap=node('div','breadth-stat');wrap.append(node('strong',cls,String(count)));wrap.append(node('span','',label));box.append(wrap);});
  const bar=$('breadth-bar');clear(bar);[['up',b.up],['down',b.down],['flat',b.flat]].forEach(([cls,count])=>{const span=node('span',cls);span.style.width=`${count/Math.max(1,b.denominator)*100}%`;bar.append(span);});
  text('breadth-note',`Base: ${b.denominator} ações elegíveis com fechamento válido nas duas pontas. Não representa todo o mercado da B3.`);
}
function heatColor(raw) {
  if(raw===null)return null;const n=Number(raw);const alpha=Math.min(.83,.14+Math.abs(n)/15*.65);
  return n>0?`rgba(19,147,109,${alpha})`:n<0?`rgba(201,54,73,${alpha})`:'#26343f';
}
function renderHeatmap(rows) {
  const wrap=$('heatmap');clear(wrap);const dates=state.data.daily.dates.slice(1);
  if(!dates.length){wrap.append(node('p','muted','Sem série diária disponível para esta extração.'));return;}
  const grid=node('div','heatmap-grid');grid.style.gridTemplateColumns=`95px repeat(${dates.length},minmax(75px,1fr))`;
  grid.append(node('span','head','ATIVO'));dates.forEach(d=>grid.append(node('span','head',day(d).slice(0,5))));
  rows.forEach(row=>{const ticker=node('button','ticker',row.ticker);ticker.type='button';ticker.addEventListener('click',()=>{state.ticker=row.ticker;$('asset-select').value=row.ticker;renderTable(rows);renderDetail();document.querySelector('.detail-panel').scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'nearest'});});grid.append(ticker);
    const changes=new Map((state.data.daily.heatmap[row.ticker]||[]).map(c=>[c.date,c.return_pct]));
    dates.forEach(d=>{const raw=changes.get(d)??null;const cell=node('span',`heat-cell${raw===null?' missing':''}`,raw===null?'—':`${Number(raw)>0?'+':''}${pct(raw)}`);const color=heatColor(raw);if(color)cell.style.background=color;cell.title=`${row.ticker} · ${day(d)}: ${raw===null?'sem comparação válida':pct(raw)}`;grid.append(cell);});
  });wrap.append(grid);
}
function renderQuality(data) {
  const box=$('quality-list');clear(box);const issues=data.quality.top20_issues||[];
  if(!issues.length)box.append(node('div','quality-item','Nenhum alerta específico nos 20 ativos desta janela.'));
  issues.forEach(item=>{const line=node('div','quality-item');line.append(node('strong','',`${item.ticker} · ${day(item.trade_date)} `));line.append(document.createTextNode(`${item.field}: ${item.reason}`));box.append(line);});
  const exclusions=$('exclusion-list');clear(exclusions);exclusions.append(node('h4','',`${data.exclusions.count} códigos sem duas pontas válidas`));
  Object.entries(data.exclusions.reasons).slice(0,4).forEach(([reason,count])=>exclusions.append(node('div','exclusion-item',`${count} · ${reason}`)));
  exclusions.append(node('div','exclusion-item',`${data.windows.primary.excluded} instrumentos com duas pontas ficaram fora por não serem ações ON/PN.`));
}
function renderDownloads(data) {
  const box=$('downloads');clear(box);const base=data.kind==='featured'?'/api/featured/files':`/api/analyses/${state.runId}/files`;
  const labels={'top20.csv':'Top 20 · CSV','all_returns.csv':'Todos os retornos · CSV','top20_alternativo.csv':'Janela alternativa · CSV','candidate_exclusions.csv':'Exclusões · CSV','quality_context.json':'Alertas · JSON','ranking_report.json':'Relatório · JSON','README.md':'Leia-me da execução'};
  data.downloads.filter(name=>labels[name]).forEach(name=>{const a=node('a','',`${labels[name]} ↗`);a.href=`${base}/${name}`;a.download=name;box.append(a);});
}
async function loadRun(id) {
  state.runId=id; $('dashboard').hidden=true;$('loading').hidden=true;$('analysis-status').hidden=false;
  try {const job=await json(`/api/analyses/${id}`);const names={queued:'Aguardando',running:'Processando',completed:'Concluída',failed:'Falhou'};
    $('analysis-status').textContent=`${names[job.status]||job.status} · ${job.stage}${job.error?` — ${job.error}`:''}`;
    if(job.status==='completed'){const result=await json(`/api/analyses/${id}/result`);render(result);return;}
    if(job.status==='failed'){$('analysis-status').classList.add('status-error');return;}
    setTimeout(()=>loadRun(id),1800);
  }catch(exc){error(exc.message);$('analysis-status').hidden=true;}
}
async function submit(event) {
  event.preventDefault();const file=$('csv-file').files[0];
  if(!file||!file.name.toLowerCase().endsWith('.csv')){text('form-message','Escolha um arquivo .csv da Economatica.');return;}
  if(file.size>10*1024*1024){text('form-message','O arquivo ultrapassa 10 MB. Exporte uma extração menor para continuar.');return;}
  const button=$('submit-button');button.disabled=true;button.textContent='Enviando arquivo…';text('form-message','');
  try{const response=await json('/api/analyses',{method:'POST',body:new FormData($('upload-form'))});window.location.assign(response.url);}
  catch(exc){text('form-message',exc.message);button.disabled=false;button.textContent='Executar análise ↗';}
}
function todayLocal(){const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;}
function updateWeekPreview(){
  const raw=$('reference-date').value;if(!raw){text('week-preview','Escolha a data de referência para conferir a semana.');return;}
  const ref=new Date(`${raw}T12:00:00Z`);if(Number.isNaN(ref.getTime()))return;
  const offset=(ref.getUTCDay()+6)%7;const start=new Date(ref);start.setUTCDate(ref.getUTCDate()-offset-7);const end=new Date(start);end.setUTCDate(start.getUTCDate()+6);
  text('week-preview',`Semana a analisar: ${day(start.toISOString().slice(0,10))} a ${day(end.toISOString().slice(0,10))}. Os fechamentos exatos serão determinados pelos dados disponíveis.`);
}
async function suggestReferenceDate(){
  const file=$('csv-file').files[0];if(!file||file.size>10*1024*1024)return;
  const content=await file.text();const matches=content.match(/20\d{2}-\d{2}-\d{2}/g);if(!matches?.length)return;
  const latest=matches.reduce((a,b)=>a>b?a:b);const candidate=new Date(`${latest}T12:00:00Z`);
  if(Number.isNaN(candidate.getTime()))return;
  const weekday=candidate.getUTCDay();if(weekday===5)candidate.setUTCDate(candidate.getUTCDate()+3);
  else if(weekday===6)candidate.setUTCDate(candidate.getUTCDate()+2);
  else if(weekday===0)candidate.setUTCDate(candidate.getUTCDate()+1);
  const suggestion=candidate.toISOString().slice(0,10);
  if(suggestion<=todayLocal())$('reference-date').value=suggestion;
  updateWeekPreview();
  document.querySelector('#reference-date + small').textContent=`Sugestão baseada na última data do arquivo (${day(latest)}). Confira a semana antes de executar.`;
}
document.addEventListener('DOMContentLoaded',()=>{
  $('reference-date').value=todayLocal();$('reference-date').max=todayLocal();$('upload-form').addEventListener('submit',submit);
  updateWeekPreview();$('reference-date').addEventListener('change',updateWeekPreview);
  $('asset-select').addEventListener('change',event=>{state.ticker=event.target.value;renderTable(state.data.windows[state.window].top20);renderDetail();});
  $('csv-file').addEventListener('change',()=>suggestReferenceDate().catch(()=>{}));
  $('primary-button').addEventListener('click',()=>{state.window='primary';renderWindow();});
  $('alternative-button').addEventListener('click',()=>{state.window='alternative';renderWindow();});
  const match=window.location.pathname.match(/^\/analise\/([0-9a-f]{32})$/);
  if(match)loadRun(match[1]);else json('/api/featured').then(render).catch(exc=>error(exc.message));
});
