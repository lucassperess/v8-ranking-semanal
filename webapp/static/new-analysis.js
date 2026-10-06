const $=id=>document.getElementById(id);
const day=value=>value.split('-').reverse().join('/');
const today=()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;};
let busy=false,fileReadVersion=0;
function message(value){$('form-message').textContent=value;}
function updateWeekPreview(){
  const raw=$('reference-date').value;if(!raw){$('week-preview').textContent='Escolha a referência para conferir a semana.';return;}
  const ref=new Date(`${raw}T12:00:00Z`);if(Number.isNaN(ref.getTime()))return;
  const start=new Date(ref);start.setUTCDate(ref.getUTCDate()-(ref.getUTCDay()+6)%7-7);const end=new Date(start);end.setUTCDate(start.getUTCDate()+6);
  $('week-preview').replaceChildren();const label=document.createElement('span');label.textContent='SEMANA QUE SERÁ ANALISADA';const dates=document.createElement('strong');dates.textContent=`${day(start.toISOString().slice(0,10))} a ${day(end.toISOString().slice(0,10))}`;$('week-preview').append(label,dates);
}
function validFile(file){if(!file||!file.name.toLowerCase().endsWith('.csv')){message('Escolha um arquivo .csv da Economatica.');return false;}if(file.size>10*1024*1024){message('O arquivo ultrapassa 10 MB. Exporte uma extração menor para continuar.');return false;}if(!file.size){message('O arquivo está vazio. Selecione uma extração com dados.');return false;}return true;}
async function onFile(){
  const version=++fileReadVersion;const file=$('csv-file').files[0];message('');$('date-suggestion').textContent='';
  if(!file){$('file-title').textContent='Selecionar arquivo CSV';$('file-description').textContent='ou arraste e solte aqui · até 10 MB';return;}
  $('file-title').textContent=file.name;$('file-description').textContent=`${new Intl.NumberFormat('pt-BR',{maximumFractionDigits:2}).format(file.size/1024)} KB · clique para trocar`;
  if(!validFile(file))return;
  const content=await file.text();if(version!==fileReadVersion)return;
  const iso=content.match(/\b20\d{2}-\d{2}-\d{2}\b/g)||[];
  const local=(content.match(/\b\d{2}\/\d{2}\/20\d{2}\b/g)||[]).map(raw=>raw.split('/').reverse().join('-'));
  const dates=[...iso,...local].filter(raw=>{const date=new Date(`${raw}T12:00:00Z`);return !Number.isNaN(date.getTime())&&date.toISOString().slice(0,10)===raw;});
  if(!dates.length)return;
  const latest=dates.reduce((a,b)=>a>b?a:b);const candidate=new Date(`${latest}T12:00:00Z`);const weekday=candidate.getUTCDay();if(weekday===5)candidate.setUTCDate(candidate.getUTCDate()+3);else if(weekday===6)candidate.setUTCDate(candidate.getUTCDate()+2);else if(weekday===0)candidate.setUTCDate(candidate.getUTCDate()+1);
  const suggestion=candidate.toISOString().slice(0,10);if(suggestion<=today()){$('reference-date').value=suggestion;$('date-suggestion').textContent=`Referência sugerida pela última data do arquivo (${day(latest)}). Confira a semana abaixo e ajuste se necessário.`;}else{$('date-suggestion').textContent=`A última data do arquivo é ${day(latest)}. Ela não permite uma sugestão de referência anterior a hoje; confira a data informada.`;}updateWeekPreview();
}
$('reference-date').value=today();$('reference-date').max=today();updateWeekPreview();
$('reference-date').addEventListener('change',updateWeekPreview);$('csv-file').addEventListener('change',()=>onFile().catch(()=>message('Não foi possível ler o arquivo selecionado. Selecione-o novamente.')));
const drop=$('file-drop');['dragenter','dragover'].forEach(event=>drop.addEventListener(event,e=>{e.preventDefault();if(!busy)drop.classList.add('dragging');}));['dragleave','drop'].forEach(event=>drop.addEventListener(event,e=>{e.preventDefault();drop.classList.remove('dragging');}));drop.addEventListener('drop',e=>{if(busy)return;const files=e.dataTransfer?.files;if(!files?.length)return;if(files.length!==1){message('Envie uma única extração por análise.');return;}$('csv-file').files=files;onFile().catch(()=>message('Não foi possível ler o arquivo selecionado.'));});
$('upload-form').addEventListener('submit',async event=>{
  event.preventDefault();if(busy||!validFile($('csv-file').files[0]))return;if($('reference-date').value>today()){message('A data de referência não pode estar no futuro.');return;}
  busy=true;const button=$('submit-button');button.disabled=true;button.textContent='Enviando e conferindo formato…';message('');
  try{const response=await fetch('/api/analyses',{method:'POST',body:new FormData($('upload-form'))});let payload;try{payload=await response.json();}catch{throw new Error('O servidor não respondeu como esperado. Tente novamente.');}if(!response.ok)throw new Error(typeof payload.detail==='string'?payload.detail:'Não foi possível enviar a extração. Confira o arquivo e a referência.');location.assign(payload.url);}
  catch(error){message(error.message);busy=false;button.disabled=false;button.textContent='Executar nova análise ↗';}
});
