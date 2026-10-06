const search = document.getElementById('docs-search'),
  results = document.getElementById('docs-search-results');
const normalize = (value) =>
  value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();
let documents;
const context =
  new URLSearchParams(location.search).get('analise') ||
  location.pathname.match(/^\/analise\/([0-9a-f]{32})\/documentacao\//)?.[1];
const id = context && /^[0-9a-f]{32}$/.test(context) ? context : null;
if (id) {
  document.getElementById('docs-audit').href = `/analise/${id}/metodologia`;
  document.getElementById('docs-audit').textContent = 'Auditoria da sua análise ↗';
  document.getElementById('nav-result').href = `/analise/${id}`;
  if (!document.getElementById('docs-context').dataset.archived)
    document.getElementById('docs-context').textContent =
      'Documentação geral · confira datas e números na auditoria da sua análise.';
}
function keepContext() {
  if (id)
    document.querySelectorAll('a[href^="/documentacao"]').forEach((link) => {
      const url = new URL(link.href);
      url.searchParams.set('analise', id);
      link.href = url.pathname + url.search + url.hash;
    });
}
keepContext();
let revision = 0;
search.addEventListener('input', async () => {
  const current = ++revision,
    query = normalize(search.value.trim());
  results.replaceChildren();
  results.hidden = !query;
  if (!query) return;
  try {
    if (!documents) {
      const response = await fetch('/api/documentation');
      if (!response.ok) throw new Error();
      documents = await response.json();
    }
    if (current !== revision) return;
    const terms = query.split(/\s+/);
    const matches = documents.filter((doc) =>
      terms.every((term) =>
        normalize(doc.title + ' ' + doc.description + ' ' + doc.text).includes(term),
      ),
    );
    if (!matches.length) {
      results.textContent = 'Nenhum artigo encontrado. Tente “cotação”, “formato” ou “semana”.';
      return;
    }
    matches.forEach((doc) => {
      const link = document.createElement('a'),
        title = document.createElement('strong'),
        description = document.createElement('span');
      link.href = doc.url;
      title.textContent = doc.title;
      description.textContent = doc.description;
      link.append(title, description);
      results.append(link);
    });
    keepContext();
  } catch {
    results.textContent = 'Não foi possível carregar a busca. Use o menu de assuntos.';
  }
});
search.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    search.value = '';
    revision++;
    results.hidden = true;
    results.replaceChildren();
  }
});
const sections = [...document.querySelectorAll('.docs-article h2[id],.docs-article h3[id]')];
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      const entry = entries.find((item) => item.isIntersecting);
      if (entry)
        document
          .querySelectorAll('.docs-outline a')
          .forEach((link) =>
            link.classList.toggle(
              'reading',
              decodeURIComponent(link.hash.slice(1)) === entry.target.id,
            ),
          );
    },
    { rootMargin: '-10% 0px -65% 0px' },
  );
  sections.forEach((section) => observer.observe(section));
}

if (matchMedia('(max-width:800px)').matches) document.querySelector('.docs-menu').open = false;
if (matchMedia('(max-width:1250px)').matches) document.querySelector('.docs-outline').open = false;

// A navegação recolhível muda a altura da página depois da primeira leitura do fragmento.
window.addEventListener(
  'load',
  () => {
    if (!location.hash) return;
    let id;
    try {
      id = decodeURIComponent(location.hash.slice(1));
    } catch {
      return;
    }
    document.getElementById(id)?.scrollIntoView({ block: 'start', behavior: 'instant' });
  },
  { once: true },
);
document.querySelectorAll('.docs-menu,.docs-outline').forEach((menu) => {
  menu.addEventListener('toggle', () => {
    if (menu.open && matchMedia('(max-width:800px)').matches) {
      document.querySelectorAll('.docs-menu,.docs-outline').forEach((other) => {
        if (other !== menu) other.open = false;
      });
    }
  });
  menu.addEventListener('click', (event) => {
    if (event.target.closest('a') && matchMedia('(max-width:800px)').matches) menu.open = false;
  });
});
