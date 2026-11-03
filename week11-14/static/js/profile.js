/* 个人资料页：昵称、头像 */
(function () {
  const avatarInput = document.getElementById('avatarInput');
  const chooseBtn = document.getElementById('chooseAvatar');
  const resetBtn = document.getElementById('resetAvatar');
  const nicknameInput = document.getElementById('nickname');
  const saveBtn = document.getElementById('saveProfile');

  function showPreview(src) {
    const el = document.getElementById('avatarPreview');
    if (!el) return;
    if (el.tagName === 'IMG') {
      el.src = src;
    } else {
      const img = document.createElement('img');
      img.id = 'avatarPreview';
      img.className = 'avatar-big avatar-img';
      img.src = src;
      el.replaceWith(img);
    }
  }

  chooseBtn.addEventListener('click', () => avatarInput.click());

  avatarInput.addEventListener('change', async () => {
    const file = avatarInput.files[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
      App.toast('头像不能超过 2MB', 'error');
      avatarInput.value = '';
      return;
    }
    showPreview(URL.createObjectURL(file));
    const fd = new FormData();
    fd.append('file', file);
    try {
      const data = await App.api('/api/profile/avatar', { method: 'POST', body: fd });
      App.toast('头像已更新');
      showPreview(data.avatar_url + '?t=' + Date.now());
      setTimeout(() => location.reload(), 600);
    } catch (err) {
      App.toast(err.message, 'error');
    } finally {
      avatarInput.value = '';
    }
  });

  resetBtn.addEventListener('click', async () => {
    if (!confirm('确定恢复默认头像吗？')) return;
    try {
      await App.api('/api/profile/avatar', { method: 'DELETE' });
      App.toast('已恢复默认头像');
      setTimeout(() => location.reload(), 500);
    } catch (err) {
      App.toast(err.message, 'error');
    }
  });

  saveBtn.addEventListener('click', async () => {
    const nickname = nicknameInput.value.trim();
    if (!nickname) {
      App.toast('昵称不能为空', 'error');
      return;
    }
    try {
      const data = await App.api('/api/profile', { method: 'PUT', body: { nickname } });
      App.toast('昵称已保存');
      const nameEl = document.querySelector('.user-name');
      if (nameEl) nameEl.textContent = data.nickname;
      setTimeout(() => location.reload(), 500);
    } catch (err) {
      App.toast(err.message, 'error');
    }
  });
})();
