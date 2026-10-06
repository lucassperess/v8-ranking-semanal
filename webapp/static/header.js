document.addEventListener('DOMContentLoaded', () => {
  const button = document.getElementById('fullscreen-button'),
    message = document.getElementById('fullscreen-message');
  if (!button) return;
  const sync = () => {
    const active = Boolean(document.fullscreenElement);
    const label = active ? 'Sair da tela cheia' : 'Entrar em tela cheia';
    button.setAttribute('aria-pressed', String(active));
    button.setAttribute('aria-label', label);
    button.title = label;
  };
  button.addEventListener('click', async () => {
    message.hidden = true;
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else if (document.documentElement.requestFullscreen)
        await document.documentElement.requestFullscreen();
      else throw new Error('unsupported');
    } catch {
      message.textContent = 'Este navegador não permitiu a tela cheia. Use F11 no computador.';
      message.hidden = false;
    }
    sync();
  });
  document.addEventListener('fullscreenchange', sync);
  sync();
});
