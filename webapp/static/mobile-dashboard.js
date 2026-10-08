document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('comparison-toggle');
  const comparison = document.getElementById('summary-comparison');
  toggle.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    toggle.setAttribute('aria-expanded', String(open));
    comparison.classList.toggle('mobile-expanded', open);
  });

  const notice = document.getElementById('mobile-notice');
  const preferenceKey = 'ranking-mobile-notice-dismissed-v1';
  const dismissed = () => {
    try {
      return localStorage.getItem(preferenceKey) === 'true';
    } catch {
      return false;
    }
  };
  notice.addEventListener('close', () => {
    try {
      localStorage.setItem(preferenceKey, 'true');
    } catch {
      // The notice can still be dismissed when browser storage is unavailable.
    }
  });
  for (const id of ['mobile-notice-close', 'mobile-notice-continue']) {
    document.getElementById(id).addEventListener('click', () => notice.close());
  }
  notice.addEventListener('click', (event) => {
    const bounds = notice.getBoundingClientRect();
    if (
      event.target === notice &&
      (event.clientX < bounds.left ||
        event.clientX > bounds.right ||
        event.clientY < bounds.top ||
        event.clientY > bounds.bottom)
    )
      notice.close();
  });
  if (window.matchMedia('(max-width: 700px)').matches && !dismissed()) notice.showModal();
});
