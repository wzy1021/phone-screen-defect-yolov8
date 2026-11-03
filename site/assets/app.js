/* 首页：灯箱 + GitHub 链接 */
(function () {
  // 自动推导 GitHub 仓库地址；本地打开时用占位地址
  let REPO_URL = 'https://github.com/your-name/phone-screen-defect-yolov8';
  if (location.hostname.endsWith('github.io')) {
    const user = location.hostname.split('.')[0];
    const repo = (location.pathname.split('/')[1] || '').trim();
    if (user && repo) REPO_URL = `https://github.com/${user}/${repo}`;
  }
  document.querySelectorAll('#repoLink, #repoLink2').forEach(a => { a.href = REPO_URL; });
  document.querySelectorAll('.repo-file').forEach(a => {
    a.href = REPO_URL + '/blob/main/' + a.dataset.path;
  });

  const box = document.getElementById('lightbox');
  if (!box) return;
  const img = box.querySelector('img');
  const close = box.querySelector('.lb-close');

  function open(src, alt) {
    img.src = src;
    img.alt = alt || '';
    box.hidden = false;
    document.body.style.overflow = 'hidden';
  }
  function hide() {
    box.hidden = true;
    img.src = '';
    document.body.style.overflow = '';
  }

  document.querySelectorAll('.shot').forEach(fig => {
    fig.addEventListener('click', () => {
      const src = fig.getAttribute('data-img') || fig.querySelector('img').src;
      open(src, fig.querySelector('figcaption')?.textContent);
    });
  });
  close.addEventListener('click', hide);
  box.addEventListener('click', e => { if (e.target === box) hide(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !box.hidden) hide(); });
})();
