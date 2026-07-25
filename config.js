/**
 * Fitness Gurukul — API endpoint config
 *
 * IMPORTANT: This URL is where ALL form leads are saved, and where
 * backend.html reads them from. Website on Hostinger + API in the cloud
 * share the same database through this setting.
 *
 * Steps:
 *   1. Deploy server.py to Render / Railway / Fly.io
 *   2. Paste the public HTTPS URL below (no trailing slash)
 *   3. Redeploy/upload this file to Hostinger
 *
 * Example:
 *   window.FG_API_BASE = "https://fitness-gurukul-api.onrender.com";
 *
 * Leave "" only for local same-origin python server.py.
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
