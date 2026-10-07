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
  if (!document.getElementById('docs-context').dataset.archived) {
    document.getElementById('docs-context').hidden = false;
    document.getElementById('docs-context').textContent =
      'Documentação geral · confira datas e números na auditoria da sua análise.';
  }
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
    const link = event.target.closest('a');
    if (link && matchMedia('(max-width:800px)').matches) {
      menu.open = false;
      if (link.hash && new URL(link.href).pathname === location.pathname) {
        requestAnimationFrame(() =>
          requestAnimationFrame(() => {
            document
              .getElementById(decodeURIComponent(link.hash.slice(1)))
              ?.scrollIntoView({ block: 'start', behavior: 'instant' });
          }),
        );
      }
    }
  });
});

// O diálogo mantém o contexto da leitura e oferece ampliação sem sair do artigo.
const imageViewer = document.getElementById('docs-image-viewer');
if (imageViewer && typeof imageViewer.showModal === 'function') {
  const fullImage = document.getElementById('docs-image-full'),
    stage = document.getElementById('docs-image-stage'),
    scaleLabel = document.getElementById('docs-image-scale'),
    minus = document.getElementById('docs-image-minus'),
    plus = document.getElementById('docs-image-plus');
  const scales = [1, 1.5, 2, 3, 4, 6, 8];
  let scaleIndex = 0,
    opener,
    previousOverflow,
    previousPadding,
    readingPosition;
  function sizeImage() {
    if (!imageViewer.open || !fullImage.naturalWidth) return;
    const fit = Math.min(
      (stage.clientWidth - 32) / fullImage.naturalWidth,
      (stage.clientHeight - 32) / fullImage.naturalHeight,
      1,
    );
    fullImage.style.width = `${fullImage.naturalWidth * fit * scales[scaleIndex]}px`;
    scaleLabel.textContent = scaleIndex
      ? `${scales[scaleIndex].toLocaleString('pt-BR')}×`
      : 'Ajustada';
    minus.disabled = scaleIndex === 0;
    plus.disabled = scaleIndex === scales.length - 1;
  }
  function openImage(image, trigger) {
    opener = trigger;
    scaleIndex = 0;
    fullImage.alt = image.alt;
    fullImage.src = image.src;
    document.getElementById('docs-image-description').textContent = image.alt;
    previousOverflow = document.body.style.overflow;
    previousPadding = document.body.style.paddingRight;
    readingPosition = { top: window.scrollY, left: window.scrollX };
    const scrollbar = window.innerWidth - document.documentElement.clientWidth;
    if (scrollbar)
      document.body.style.paddingRight = `${parseFloat(getComputedStyle(document.body).paddingRight) + scrollbar}px`;
    document.body.style.overflow = 'hidden';
    imageViewer.showModal();
    sizeImage();
    stage.scrollTo(0, 0);
  }
  fullImage.addEventListener('load', () => {
    sizeImage();
    stage.scrollTo(0, 0);
  });
  new ResizeObserver(sizeImage).observe(stage);
  minus.addEventListener('click', () => {
    scaleIndex = Math.max(0, scaleIndex - 1);
    sizeImage();
  });
  plus.addEventListener('click', () => {
    scaleIndex = Math.min(scales.length - 1, scaleIndex + 1);
    sizeImage();
  });
  document.getElementById('docs-image-fit').addEventListener('click', () => {
    scaleIndex = 0;
    sizeImage();
    stage.scrollTo(0, 0);
  });
  document.getElementById('docs-image-close').addEventListener('click', () => imageViewer.close());
  imageViewer.addEventListener('click', (event) => {
    if (event.target !== imageViewer) return;
    const bounds = imageViewer.getBoundingClientRect();
    if (
      event.clientX < bounds.left ||
      event.clientX > bounds.right ||
      event.clientY < bounds.top ||
      event.clientY > bounds.bottom
    )
      imageViewer.close();
  });
  imageViewer.addEventListener('close', () => {
    document.body.style.overflow = previousOverflow;
    document.body.style.paddingRight = previousPadding;
    opener?.focus({ preventScroll: true });
    window.scrollTo({ ...readingPosition, behavior: 'instant' });
  });
  const links = [...document.querySelectorAll('.docs-article a[href]')];
  document.querySelectorAll('.docs-article img').forEach((image) => {
    const trigger = document.createElement('button');
    trigger.type = 'button';
    trigger.className = 'docs-image-trigger';
    trigger.setAttribute('aria-label', `Ampliar imagem: ${image.alt}`);
    image.before(trigger);
    trigger.append(image);
    trigger.addEventListener('click', () => openImage(image, trigger));
    links
      .filter((link) => link.href === image.src)
      .forEach((link) => {
        link.textContent = 'Ampliar imagem';
        link.setAttribute('aria-haspopup', 'dialog');
        link.addEventListener('click', (event) => {
          if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
          event.preventDefault();
          openImage(image, link);
        });
      });
  });
}
