// Keep reference-ui-* storage keys for existing browser preferences.
(() => {
  const { items } = JSON.parse(document.getElementById('catalog').textContent);
  const grid = document.getElementById('grid');
  const search = document.getElementById('search');
  const filters = document.getElementById('filters');
  const tags = document.getElementById('tags');
  const chapters = document.getElementById('chapters');
  const tagSelect = document.getElementById('tag-select');
  const platformSelect = document.getElementById('platform-select');
  const root = document.documentElement;
  const labels = { all: '전체 레퍼런스', web: '웹', desktop: '데스크톱', mobile: '모바일' };
  const categoryLabels = {all:'전체 자료', reference:'디자인 레퍼런스', library:'UI 컴포넌트/라이브러리', asset:'아이콘/에셋', 'design-system':'디자인 시스템', guideline:'UX 규칙', inbox:'수집함'};
  const descriptions = {all:'마음에 든 화면부터, 다음 작업에 쓸 아이콘과 규칙까지.', reference:'다시 보고 싶은 화면, 레이아웃과 인터랙션.', library:'화면을 만들 때 가져다 쓸 컴포넌트와 도구.', asset:'아이콘, 폰트, 일러스트처럼 손에 두고 쓸 소재.', 'design-system':'색상, 서체, 간격과 토큰을 일관되게 쓰는 방법.', guideline:'사용자가 덜 헤매고, 실수해도 이어갈 수 있게.', inbox:'일단 담아둔 자료. 분류와 메모는 나중에 붙여도 됩니다.'};
  items.sort((a, b) => Object.keys(categoryLabels).indexOf(a.category) - Object.keys(categoryLabels).indexOf(b.category));
  const initial = new URLSearchParams(location.search);
  let category = Object.hasOwn(categoryLabels, initial.get('chapter')) ? initial.get('chapter') : 'all';
  let platform = 'all';
  let selectedTag = '';
  if (Object.hasOwn(labels, initial.get('platform'))) platform = initial.get('platform');
  if (items.some(item => item.tags.includes(initial.get('tag')))) selectedTag = initial.get('tag');
  search.value = initial.get('q') || '';
  platformSelect.value = platform;
  const element = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text) node.textContent = text;
    if (className) node.className = className;
    return node;
  };
  const icon = name => {
    const shapes = {
      all: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
      web: 'M3 5h18v15H3z M3 10h18 M7 7.5h.01 M10 7.5h.01',
      desktop: 'M3 4h18v13H3z M12 17v4 M8 21h8',
      mobile: 'M7 2h10v20H7z M11 18h2',
      arrow: 'M6 18 18 6 M6 6h12v12',
      sun: 'M12 2v2 M12 20v2 M2 12h2 M20 12h2 M5 5l1.5 1.5 M17.5 17.5 19 19 M5 19l1.5-1.5 M17.5 6.5 19 5 M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0',
      moon: 'M20.5 13.5A9 9 0 0 1 10.5 3.5a9 9 0 1 0 10 10'
    };
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('aria-hidden', 'true');
    const path = document.createElementNS(svg.namespaceURI, 'path');
    path.setAttribute('d', shapes[name] || shapes.all);
    svg.append(path);
    return svg;
  };
  const link = (label, href) => {
    const node = element('a', label);
    node.href = href;
    return node;
  };
  const render = () => {
    const query = search.value.trim().toLocaleLowerCase();
    const matching = items.filter(item => (category === 'all' || item.category === category) && (!selectedTag || item.tags.includes(selectedTag)) && [item.title, item.summary, item.search_text || '', categoryLabels[item.category], ...item.platforms, ...item.platforms.map(name => labels[name] || name), ...item.tags].join(' ').toLocaleLowerCase().includes(query));
    const visible = matching.filter(item => platform === 'all' || item.platforms.includes(platform));
    grid.replaceChildren();
    grid.classList.toggle('single', visible.length === 1);
    for (const item of visible) {
      const article = element('article', '', 'reference');
      const isNote = item.record_type !== 'extraction';
      article.classList.toggle('book-note', isNote);
      const preview = link('', item.preview);
      preview.className = 'preview';
      preview.setAttribute('aria-label', `${item.title} 자료 보기`);
      if (item.thumbnail) {
        const img = element('img');
        img.src = item.thumbnail;
        img.alt = `${item.title} 미리보기`;
        img.loading = 'lazy';
        preview.append(img);
        const badge = element('span', '미리보기 열기', 'preview-label');
        badge.append(icon('arrow'));
        preview.append(badge);
      } else {
        preview.append(element('span', categoryLabels[item.category], 'preview-category'));
        preview.append(element('strong', item.source ? new URL(item.source).hostname.replace(/^www\./, '') : item.title));
        preview.classList.add('empty');
      }
      const content = element('div', '', 'item-content');
      content.append(element('div', categoryLabels[item.category] || '디자인 시스템', 'platform'));
      const title = element('h3');
      title.append(link(item.title, item.preview));
      content.append(title, element('p', item.summary, 'item-summary'));
      const itemTags = element('div', '', 'tags');
      for (const tag of item.tags) itemTags.append(element('span', tag, 'tag'));
      content.append(itemTags);
      const links = element('nav', '', 'links');
      links.setAttribute('aria-label', `${item.title} 자료`);
      const destinations = isNote ? [['자료 보기', item.preview], ['원본 열기', item.source]] : [['미리보기', item.preview], ['디자인 규칙', item.design], ['디자인 토큰', item.tokens]];
      for (const [label, href] of destinations) {
        if (!href) continue;
        const node = link(label, href);
        if (href.startsWith('http')) { node.target = '_blank'; node.rel = 'noopener noreferrer'; }
        node.append(icon('arrow'));
        links.append(node);
      }
      content.append(links);
      article.append(preview);
      article.append(content);
      grid.append(article);
    }
    document.getElementById('count').textContent = visible.length === items.length ? String(items.length).padStart(2, '0') : `${visible.length} / ${items.length}`;
    document.getElementById('empty').hidden = visible.length > 0;
    document.getElementById('clear').hidden = !query && platform === 'all' && !selectedTag && category === 'all';
    document.getElementById('view-label').textContent = categoryLabels[category];
    document.getElementById('chapter-title').textContent = category === 'all' ? '디자인 라이브러리' : categoryLabels[category];
    document.getElementById('chapter-description').textContent = descriptions[category];
    for (const button of chapters.children) button.setAttribute('aria-pressed', String(button.dataset.category === category));
    for (const button of filters.children) {
      button.setAttribute('aria-pressed', String(button.dataset.platform === platform));
      button.querySelector('.filter-count').textContent = matching.filter(item => button.dataset.platform === 'all' || item.platforms.includes(button.dataset.platform)).length;
    }
    for (const button of tags.children) button.setAttribute('aria-pressed', String(button.dataset.tag === selectedTag));
    tagSelect.value = selectedTag;
    document.querySelector('#empty p').textContent = category === 'inbox' && !query ? '수집함이 비어 있습니다.' : '일치하는 자료가 없습니다.';
    document.querySelector('#empty span').textContent = category === 'inbox' && !query ? '링크나 이미지를 보내주시면 여기에 먼저 보관합니다.' : '다른 검색어나 태그로 찾아보세요.';
    const params = new URLSearchParams();
    for (const [key, value] of [['chapter', category], ['platform', platform], ['tag', selectedTag], ['q', search.value.trim()]]) if (value && value !== 'all') params.set(key, value);
    history.replaceState(null, '', location.pathname + (params.size ? `?${params}` : '') + location.hash);
  };
  for (const [name, title] of Object.entries(categoryLabels)) {
    const button = element('button', title);
    button.type = 'button';
    button.dataset.category = name;
    button.append(element('span', String(name === 'all' ? items.length : items.filter(item => item.category === name).length), 'filter-count'));
    button.addEventListener('click', () => { category = name; render(); });
    chapters.append(button);
  }
  for (const name of ['all', ...new Set(items.flatMap(item => item.platforms))]) {
    const button = element('button');
    button.type = 'button';
    button.dataset.platform = name;
    button.append(icon(name), element('span', labels[name] || name), element('span', String(name === 'all' ? items.length : items.filter(item => item.platforms.includes(name)).length), 'filter-count'));
    button.addEventListener('click', () => { platform = name; platformSelect.value = name; render(); });
    filters.append(button);
  }
  for (const name of [...new Set(items.flatMap(item => item.tags))].sort()) {
    const button = element('button', name);
    button.type = 'button';
    button.dataset.tag = name;
    const option = element('option', name);
    option.value = name;
    tagSelect.append(option);
    button.addEventListener('click', () => { selectedTag = selectedTag === name ? '' : name; render(); });
    tags.append(button);
  }
  const preference = (name, value) => {
    try { if (value === undefined) return localStorage.getItem(`reference-ui-${name}`); localStorage.setItem(`reference-ui-${name}`, value); } catch { /* The UI also works when storage is unavailable. */ }
    return null;
  };
  const theme = document.getElementById('theme');
  const setTheme = dark => {
    root.classList.toggle('dark', dark);
    theme.replaceChildren(icon(dark ? 'sun' : 'moon'));
    const label = dark ? '밝은 테마로 전환' : '어두운 테마로 전환';
    theme.setAttribute('aria-label', label);
    theme.title = label;
  };
  const savedTheme = preference('theme');
  setTheme(savedTheme ? savedTheme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches);
  theme.addEventListener('click', () => { const dark = !root.classList.contains('dark'); setTheme(dark); preference('theme', dark ? 'dark' : 'light'); });
  const material = document.getElementById('material');
  const setMaterial = flat => { root.classList.toggle('flat', flat); material.setAttribute('aria-pressed', String(!flat)); material.textContent = flat ? '단색' : '글래스'; };
  setMaterial(preference('material') === 'flat');
  material.addEventListener('click', () => { const flat = !root.classList.contains('flat'); setMaterial(flat); preference('material', flat ? 'flat' : 'glass'); });
  const reset = () => { search.value = ''; platform = 'all'; platformSelect.value = 'all'; category = 'all'; selectedTag = ''; render(); search.focus(); };
  document.getElementById('reset').addEventListener('click', reset);
  document.getElementById('clear').addEventListener('click', reset);
  tagSelect.addEventListener('change', () => { selectedTag = tagSelect.value; render(); });
  platformSelect.addEventListener('change', () => { platform = platformSelect.value; render(); });
  search.addEventListener('input', render);
  render();
})();
