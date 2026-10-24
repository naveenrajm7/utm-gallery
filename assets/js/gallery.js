(function () {
  'use strict';

  var PAGE_SIZE = 12;
  var VIEW_KEY = 'utm-gallery-view';
  var SORTS = ['featured', 'downloads-desc', 'downloads-asc', 'size-desc', 'size-asc', 'name-asc'];
  var VIEWS = ['grid', 'list'];

  var root = document.getElementById('gallery');
  if (!root || !window.fetch || !window.URLSearchParams) return;

  var toolbar = document.getElementById('gallery-toolbar');
  var searchInput = document.getElementById('gallery-search');
  var sourceInputs = Array.prototype.slice.call(toolbar.querySelectorAll('input[name="source"]'));
  var sortSelect = document.getElementById('gallery-sort');
  var viewInputs = Array.prototype.slice.call(toolbar.querySelectorAll('input[name="view"]'));
  var countEl = document.getElementById('gallery-count');
  var results = document.getElementById('gallery-results');
  var pagination = document.getElementById('gallery-pagination');
  var paginationList = pagination.querySelector('ul');
  var requestTemplate = document.getElementById('gallery-request-card');
  var allSources = sourceInputs.map(function (i) { return i.value; });

  var vms = [];
  var state = null;

  function storedView() {
    try { return localStorage.getItem(VIEW_KEY); } catch (e) { return null; }
  }

  function storeView(view) {
    try { localStorage.setItem(VIEW_KEY, view); } catch (e) { /* storage unavailable */ }
  }

  function readState() {
    var p = new URLSearchParams(window.location.search);
    var sources = allSources.slice();
    if (p.has('source')) {
      sources = p.get('source').split(',').filter(function (s) { return allSources.indexOf(s) !== -1; });
    }
    var sort = p.get('sort');
    var view = p.get('view') || storedView();
    var page = parseInt(p.get('page'), 10);
    return {
      q: p.get('q') || '',
      sources: sources,
      sort: SORTS.indexOf(sort) !== -1 ? sort : 'featured',
      view: VIEWS.indexOf(view) !== -1 ? view : 'grid',
      page: page > 0 ? page : 1
    };
  }

  function stateToQuery(s) {
    var p = new URLSearchParams();
    if (s.q) p.set('q', s.q);
    if (s.sources.length !== allSources.length) p.set('source', s.sources.join(','));
    if (s.sort !== 'featured') p.set('sort', s.sort);
    if (s.view !== 'grid') p.set('view', s.view);
    if (s.page > 1) p.set('page', String(s.page));
    var qs = p.toString();
    return window.location.pathname + (qs ? '?' + qs : '') + window.location.hash;
  }

  function writeUrl(replace) {
    var url = stateToQuery(state);
    if (url === window.location.pathname + window.location.search + window.location.hash) return;
    history[replace ? 'replaceState' : 'pushState'](null, '', url);
  }

  function syncControls() {
    if (searchInput.value !== state.q) searchInput.value = state.q;
    sourceInputs.forEach(function (i) { i.checked = state.sources.indexOf(i.value) !== -1; });
    sortSelect.value = state.sort;
    viewInputs.forEach(function (i) { i.checked = i.value === state.view; });
  }

  function escapeHtml(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function formatSize(bytes) {
    var mib = bytes / 1048576;
    if (mib >= 1024) return (mib / 1024).toFixed(2) + ' GB';
    return Math.round(mib) + ' MB';
  }

  function formatNumber(n) {
    return Number(n || 0).toLocaleString('en-US');
  }

  function sourceBadge(vm) {
    var cls = vm.source === 'utm' ? 'text-bg-primary' : 'text-bg-warning';
    return '<span class="badge rounded-pill ' + cls + '">' + escapeHtml(vm.source_label || vm.source) + '</span>';
  }

  function builderBadge(vm) {
    return vm.packer_builder
      ? ' <span class="badge rounded-pill text-bg-success">' + escapeHtml(vm.packer_builder) + '</span>'
      : '';
  }

  function matches(vm, terms) {
    if (state.sources.indexOf(vm.source) === -1) return false;
    if (!terms.length) return true;
    var haystack = [vm.name, vm.display_name, vm.description, vm.box_ref].join(' ').toLowerCase();
    return terms.every(function (t) { return haystack.indexOf(t) !== -1; });
  }

  var comparators = {
    'downloads-desc': function (a, b) { return b.downloads - a.downloads; },
    'downloads-asc': function (a, b) { return a.downloads - b.downloads; },
    'size-desc': function (a, b) { return b.size_bytes - a.size_bytes; },
    'size-asc': function (a, b) { return a.size_bytes - b.size_bytes; },
    'name-asc': function (a, b) {
      return a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' });
    }
  };

  function visibleVms() {
    var terms = state.q.toLowerCase().split(/\s+/).filter(Boolean);
    var list = vms.filter(function (vm) { return matches(vm, terms); });
    var cmp = comparators[state.sort];
    if (cmp) {
      list.sort(function (a, b) { return cmp(a, b) || a.index - b.index; });
    }
    return list;
  }

  function renderCard(vm) {
    return '<div class="col-lg-4 col-md-6 mb-4"><div class="card h-100">' +
      '<div class="card-body text-center">' +
        '<h4 class="card-title">' + escapeHtml(vm.name) + '</h4>' +
        '<p class="card-text d-flex flex-wrap justify-content-center align-items-center gap-3">' +
          '<span><img src="assets/icons/download.svg" alt="" class="icon me-1"> Downloads: ' + formatNumber(vm.downloads) + '</span>' +
          '<span><img src="assets/icons/hdd.svg" alt="" class="icon me-1"> Size: ' + formatSize(vm.size_bytes) + '</span>' +
        '</p>' +
        '<img src="' + escapeHtml(vm.icon_url) + '" alt="' + escapeHtml(vm.name) + '" class="img-fluid mb-3" loading="lazy">' +
        '<div class="mt-2">' + sourceBadge(vm) + builderBadge(vm) + '</div>' +
      '</div>' +
      '<div class="card-footer text-center">' +
        '<a href="' + escapeHtml(vm.url) + '" class="btn btn-primary">View Details</a>' +
      '</div>' +
    '</div></div>';
  }

  function renderRow(vm) {
    var size = formatSize(vm.size_bytes);
    var downloads = formatNumber(vm.downloads);
    return '<li class="list-group-item py-2">' +
      '<div class="row g-2 g-sm-3 align-items-center flex-nowrap">' +
        '<div class="col-auto"><img src="' + escapeHtml(vm.icon_url) + '" alt="" class="gallery-list-icon" loading="lazy"></div>' +
        '<div class="col min-w-0">' +
          '<div class="fw-semibold text-truncate" title="' + escapeHtml(vm.name) + '">' + escapeHtml(vm.name) + '</div>' +
          '<div class="small">' + sourceBadge(vm) + builderBadge(vm) +
            '<span class="d-md-none text-body-secondary ms-1 text-nowrap">' + size + ' · ' + downloads + ' dl</span>' +
          '</div>' +
        '</div>' +
        '<div class="col-2 d-none d-md-block text-end text-nowrap">' + size + '</div>' +
        '<div class="col-2 d-none d-md-block text-end text-nowrap">' + downloads + '</div>' +
        '<div class="col-auto"><a href="' + escapeHtml(vm.url) + '" class="btn btn-sm btn-outline-primary" aria-label="Details for ' + escapeHtml(vm.name) + '">Details</a></div>' +
      '</div>' +
    '</li>';
  }

  function listHeader() {
    return '<div class="d-none d-md-block px-3 pb-2 small fw-semibold text-body-secondary" aria-hidden="true">' +
      '<div class="row g-3 align-items-center flex-nowrap">' +
        '<div class="col-auto"><span class="d-inline-block gallery-list-icon"></span></div>' +
        '<div class="col">Name</div>' +
        '<div class="col-2 text-end">Size</div>' +
        '<div class="col-2 text-end">Downloads</div>' +
        '<div class="col-auto"><span class="btn btn-sm invisible">Details</span></div>' +
      '</div>' +
    '</div>';
  }

  function requestRow() {
    return '<li class="list-group-item py-3 d-flex flex-wrap align-items-center justify-content-between gap-2">' +
      '<span>Did not find the VM you were looking for?</span>' +
      '<a href="https://github.com/naveenrajm7/utm-box/issues/new?template=box-request.md" class="btn btn-sm btn-primary">Request or Contribute</a>' +
    '</li>';
  }

  function emptyState() {
    return '<div class="alert alert-secondary text-center" role="status">' +
      'No VMs match your search or filters. ' +
      '<button type="button" class="btn btn-link p-0 align-baseline" data-gallery-reset>Clear filters</button>' +
    '</div>';
  }

  function pageItem(label, page, opts) {
    opts = opts || {};
    var cls = 'page-item' + (opts.active ? ' active' : '') + (opts.disabled ? ' disabled' : '');
    if (opts.ellipsis) {
      return '<li class="page-item disabled"><span class="page-link">…</span></li>';
    }
    return '<li class="' + cls + '"' + (opts.active ? ' aria-current="page"' : '') + '>' +
      '<a class="page-link" href="#" data-page="' + page + '"' +
        (opts.aria ? ' aria-label="' + opts.aria + '"' : '') +
        (opts.disabled ? ' tabindex="-1" aria-disabled="true"' : '') + '>' + label + '</a></li>';
  }

  function renderPagination(totalPages) {
    if (totalPages <= 1) {
      pagination.hidden = true;
      paginationList.innerHTML = '';
      return;
    }
    var p = state.page;
    var html = pageItem('&laquo;', p - 1, { disabled: p === 1, aria: 'Previous page' });
    var last = 0;
    for (var i = 1; i <= totalPages; i++) {
      if (i === 1 || i === totalPages || Math.abs(i - p) <= 1) {
        if (last && i - last > 1) html += pageItem('', 0, { ellipsis: true });
        html += pageItem(String(i), i, { active: i === p });
        last = i;
      }
    }
    html += pageItem('&raquo;', p + 1, { disabled: p === totalPages, aria: 'Next page' });
    paginationList.innerHTML = html;
    pagination.hidden = false;
  }

  function render() {
    var list = visibleVms();
    var total = list.length;
    var totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
    if (state.page > totalPages) state.page = totalPages;
    var start = (state.page - 1) * PAGE_SIZE;
    var pageVms = list.slice(start, start + PAGE_SIZE);
    var isLastPage = state.page === totalPages;

    if (total === 0) {
      countEl.textContent = 'No VMs found';
    } else {
      countEl.textContent = 'Showing ' + (start + 1) + '–' + (start + pageVms.length) + ' of ' + total +
        ' VM' + (total === 1 ? '' : 's') + (total !== vms.length ? ' (filtered from ' + vms.length + ')' : '');
    }

    var html;
    if (state.view === 'list') {
      html = '';
      html = total === 0 ? emptyState() : listHeader();
      html += '<ul class="list-group gallery-list mb-4">' +
        pageVms.map(renderRow).join('') +
        (isLastPage ? requestRow() : '') +
        '</ul>';
    } else {
      html = (total === 0 ? emptyState() : '') + '<div class="row">' + pageVms.map(renderCard).join('');
      if (isLastPage) {
        html += '<div class="col-lg-4 col-md-6 mb-4">' + requestTemplate.innerHTML + '</div>';
      }
      html += '</div>';
    }
    results.innerHTML = html;
    renderPagination(totalPages);
  }

  function update(changes, opts) {
    opts = opts || {};
    Object.keys(changes).forEach(function (k) { state[k] = changes[k]; });
    if (!('page' in changes)) state.page = 1;
    if ('view' in changes) storeView(state.view);
    render();
    writeUrl(opts.replace);
  }

  var searchTimer = null;
  var searchPushed = false;
  searchInput.addEventListener('input', function () {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(function () {
      // One history entry per typing burst; later keystrokes in the burst replace it.
      update({ q: searchInput.value.trim() }, { replace: searchPushed });
      searchPushed = true;
    }, 150);
  });
  searchInput.addEventListener('blur', function () { searchPushed = false; });

  sourceInputs.forEach(function (input) {
    input.addEventListener('change', function () {
      update({
        sources: sourceInputs.filter(function (i) { return i.checked; }).map(function (i) { return i.value; })
      });
    });
  });

  sortSelect.addEventListener('change', function () { update({ sort: sortSelect.value }); });

  viewInputs.forEach(function (input) {
    input.addEventListener('change', function () {
      if (input.checked) update({ view: input.value, page: state.page });
    });
  });

  paginationList.addEventListener('click', function (e) {
    var link = e.target.closest('a[data-page]');
    if (!link) return;
    e.preventDefault();
    var page = parseInt(link.getAttribute('data-page'), 10);
    if (!page || page === state.page || link.parentNode.classList.contains('disabled')) return;
    update({ page: page });
    toolbar.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  results.addEventListener('click', function (e) {
    if (!e.target.closest('[data-gallery-reset]')) return;
    update({ q: '', sources: allSources.slice() });
    syncControls();
    searchInput.focus();
  });

  window.addEventListener('popstate', function () {
    state = readState();
    syncControls();
    render();
  });

  fetch(root.getAttribute('data-vms-url'))
    .then(function (res) {
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return res.json();
    })
    .then(function (data) {
      vms = data.map(function (vm, index) {
        vm.index = index;
        vm.downloads = Number(vm.downloads) || 0;
        vm.size_bytes = Number(vm.size_bytes) || 0;
        return vm;
      });
      state = readState();
      syncControls();
      toolbar.hidden = false;
      render();
      writeUrl(true);
    })
    .catch(function () {
      // Keep the server-rendered cards if the index can't be loaded.
    });
})();
