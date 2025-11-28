(function () {
  const loader = document.getElementById('global-loader');
  if (!loader) return;

  function showLoader() { loader.classList.remove('hidden'); }
  function hideLoader() { loader.classList.add('hidden'); }

  let pending = 0;
  function inc() { pending += 1; if (pending === 1) showLoader(); }
  function dec() { pending = Math.max(0, pending - 1); if (pending === 0) hideLoader(); }

  const _fetch = window.fetch;

  // Add/adjust patterns if your endpoints differ
  const LOADING_PATTERNS = [
    /\/api\/generate/i,
    /\/api\/draft/i,
    /\/api\/edit/i,
    /\/api\/revise/i,
    /\/api\/render/i,
    /\/generate-report/i  // covers GET routes that still trigger processing
  ];

  function shouldShowLoader(input, init) {
    try {
      const url = (typeof input === 'string') ? input : input.url;
      const method = (init && init.method) || (typeof input !== 'string' && input.method) || 'GET';
      if (method.toUpperCase() !== 'GET') return true; // any non-GET likely processes
      return LOADING_PATTERNS.some(p => p.test(url));  // GETs that still kick off work
    } catch { return true; }
  }

  window.fetch = async function(input, init) {
    const show = shouldShowLoader(input, init);
    if (show) inc();
    try {
      return await _fetch(input, init);
    } finally {
      if (show) dec();
    }
  };
})();
