/**
 * Fitness Gurukul — API endpoint config
 *
 * Hostinger (static site) + cloud API (Render / Railway / Fly.io):
 *   1. Deploy server.py to Render/Railway/Fly
 *   2. Paste the public HTTPS URL below
 *   3. Re-upload/redeploy this config.js with your Hostinger site
 *
 * Leave empty ("") for same-origin / local python server.py.
 */
window.FG_API_BASE = window.FG_API_BASE || "";

(function (w) {
  w.fgApiUrl = function (path) {
    var base = String(w.FG_API_BASE || "").replace(/\/$/, "");
    if (!path) return base || "/";
    if (/^https?:\/\//i.test(path)) return path;
    if (!base) return path.charAt(0) === "/" ? path : "/" + path;
    return base + (path.charAt(0) === "/" ? path : "/" + path);
  };
})(window);
