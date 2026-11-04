// Keep reference-ui-* storage keys for existing browser preferences.
(() => {
  const root = document.documentElement;
  const button = document.getElementById('reading-theme');
  let saved;
  try { saved = localStorage.getItem('reference-ui-theme'); } catch { /* Storage can be disabled. */ }
  const set = dark => {
    root.classList.toggle('dark', dark);
    button.textContent = dark ? '밝은 테마' : '어두운 테마';
    button.setAttribute('aria-label', `${button.textContent}로 전환`);
  };
  set(saved ? saved === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches);
  button.addEventListener('click', () => {
    const dark = !root.classList.contains('dark');
    set(dark);
    try { localStorage.setItem('reference-ui-theme', dark ? 'dark' : 'light'); } catch { /* Keep the current theme without persistence. */ }
  });
})();
