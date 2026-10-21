// Opens a <details> the URL's #fragment points at, and every <details> before printing.
export function openFragment() {
  if (!location.hash) return;
  // The first build's #cell-<engine> fragments (kept by the legacy redirects) name #<engine> now.
  if (/^#cell-[a-z0-9-]+$/.test(location.hash)) {
    history.replaceState(null, "", location.pathname + location.search + location.hash.replace("#cell-", "#"));
    const el = document.getElementById(location.hash.slice(1));
    if (el) el.scrollIntoView();
  }
  const target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
  if (target && target.tagName === "DETAILS") target.open = true;
}

export function watchFragment() {
  openFragment();
  window.addEventListener("hashchange", openFragment);
  window.addEventListener("beforeprint", () => document.querySelectorAll("details").forEach((d) => (d.open = true)));
}
