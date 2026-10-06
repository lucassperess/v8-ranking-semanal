const el=id=>document.getElementById(id);
const put=(id,value)=>{el(id).textContent=value;};
const format=new Intl.NumberFormat('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
const dateLabel=value=>value.split('-').reverse().join('/');
function item(tag,cls,value){const n=document.createElement(tag);if(cls)n.className=cls;if(value!==undefined)n.textContent=value;return n;}
async function showMethod(){
  const match=location.pathname.match(/^\/analise\/([0-9a-f]{32})\/metodologia$/);
  const resultHref=match?`/analise/${match[1]}`:'/';
  el('nav-result').href=resultHref;el('back-result').href=resultHref;
  el('nav-method').href=location.pathname;
  const response=await fetch(match?`/api/analyses/${match[1]}/result`:'/api/featured');
  const data=await response.json();if(!response.ok)throw new Error(data.detail||'Não foi possível carregar esta execução.');
  const primary=data.windows.primary,alternative=data.windows.alternative;
  put('method-context',`${match?'Análise enviada':'Resultado de referência'} · referência ${dateLabel(data.week.reference_date)}`);
  put('reference-value',dateLabel(data.week.reference_date));put('week-value',`${dateLabel(data.week.week_start)} a ${dateLabel(data.week.week_end)}`);
  for(const [key,window] of [['primary',primary],['alternative',alternative]]){put(`${key}-start`,dateLabel(window.start_date));put(`${key}-end`,dateLabel(window.end_date));put(`${key}-summary`,`${window.top20.length} ações no top · média ${format.format(window.mean_pct)}%`);}
  const total=primary.eligible+primary.excluded+data.exclusions.count;
  const groups=[['Códigos avaliados',total,'Todos os códigos da extração, incluindo os sem preços utilizáveis.'],['Com duas pontas válidas',primary.eligible+primary.excluded,`${data.exclusions.count} códigos ficaram sem comparação válida.`],['Ações ON/PN elegíveis',primary.eligible,`${primary.excluded} instrumentos com preços válidos ficaram fora da definição de ação adotada.`],['Top do ranking',primary.top20.length,'Maiores retornos entre as ações elegíveis.']];
  groups.forEach(([label,count,description])=>{const wrap=item('div','universe-step');const heading=item('div','universe-heading');heading.append(item('strong','',count.toLocaleString('pt-BR')),item('span','',label));const track=item('div','universe-track');const fill=item('span','');fill.style.width=`${total?count/total*100:0}%`;track.append(fill);wrap.append(heading,track,item('p','',description));el('universe-flow').append(wrap);});
  Object.entries(data.exclusions.reasons).forEach(([reason,count])=>{const row=item('div','reason-row');row.append(item('strong','',String(count)),item('span','',reason));el('exclusion-reasons').append(row);});
  const first=primary.top20[0];if(first){const example=el('return-example');example.append(item('div','example-ticker',first.ticker));[['Fechamento inicial',`R$ ${format.format(first.start_close)}`,dateLabel(first.start_date)],['Fechamento final',`R$ ${format.format(first.end_close)}`,dateLabel(first.end_date)],['Retorno semanal',`${format.format(first.return_pct)}%`,'Final ÷ inicial − 1']].forEach(([label,value,note])=>{const part=item('div','example-part');part.append(item('span','',label),item('strong','',value),item('small','',note));example.append(part);});}
  const fieldNames={average:'Preço médio',close:'Fechamento',open:'Abertura',high:'Máximo',low:'Mínimo',adjusted_quantity:'Quantidade',raw_volume:'Volume'};
  const issues=data.quality.top20_issues||[];
  if(!issues.length)el('method-quality').append(item('p','doc-note','Nenhuma ocorrência específica no top 20 principal desta execução.'));
  issues.forEach(issue=>{const line=item('div','quality-card');line.append(item('strong','',`${issue.ticker} · ${dateLabel(issue.trade_date)}`),item('span','',`${fieldNames[issue.field]||issue.field}: ${issue.reason}`));el('method-quality').append(line);});
  const base=match?`/api/analyses/${match[1]}/files`:'/api/featured/files';
  const files={'top20.csv':['Ranking principal','Os maiores retornos, suas pontas e posições.','CSV'],'all_returns.csv':['Universo completo','Todos os retornos das ações elegíveis na janela principal.','CSV'],'top20_alternativo.csv':['Ranking alternativo','Compare o resultado dentro da semana.','CSV'],'all_returns_alternativo.csv':['Universo alternativo','Todos os retornos na janela alternativa.','CSV'],'candidate_exclusions.csv':['Exclusões das pontas','Códigos sem duas pontas válidas e seus motivos.','CSV'],'quality_context.json':['Contexto de qualidade','Ocorrências relacionadas aos dados utilizados.','JSON'],'ranking_report.json':['Relatório da execução','Datas, regras, contagens e assinaturas dos arquivos.','JSON'],'README.md':['Leia-me da execução','Decisões e instruções para interpretar os resultados.','MD']};
  data.downloads.filter(name=>files[name]).forEach(name=>{const [title,description,type]=files[name];const link=item('a','audit-file');link.href=`${base}/${name}`;link.download=name;const content=item('div','');content.append(item('strong','',title),item('p','',description));link.append(content,item('span','file-type',`${type} ↓`));el('audit-files').append(link);});
  put('method-hash',data.provenance.input_sha256);put('method-version',`${data.provenance.pipeline_version} · ${data.provenance.code_sha256}`);
  el('method-loading').hidden=true;el('method-body').hidden=false;
}
showMethod().catch(error=>{el('method-loading').hidden=true;el('method-error').hidden=false;put('method-error',error.message);put('method-context','Execução indisponível');});
