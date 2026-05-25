// User menu dropdown (dashboard + chat header)
document.addEventListener('DOMContentLoaded', () => {
  const menu = document.getElementById('userMenu');
  const btn = document.getElementById('userMenuBtn');
  const dropdown = document.getElementById('userMenuDropdown');
  if (!menu || !btn || !dropdown) return;

  function closeMenu() {
    menu.classList.remove('is-open');
    btn.setAttribute('aria-expanded', 'false');
    dropdown.hidden = true;
  }

  function openMenu() {
    menu.classList.add('is-open');
    btn.setAttribute('aria-expanded', 'true');
    dropdown.hidden = false;
  }

  function toggleMenu(e) {
    e.stopPropagation();
    if (dropdown.hidden) openMenu();
    else closeMenu();
  }

  btn.addEventListener('click', toggleMenu);

  document.addEventListener('click', (e) => {
    if (!menu.contains(e.target)) closeMenu();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeMenu();
  });
});
