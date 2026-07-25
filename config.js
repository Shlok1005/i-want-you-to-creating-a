/**
 * Fitness Gurukul — API endpoint config
 *
 * Lead save order:
 *   1) Cloud Python API via FG_API_BASE (Render / Railway / Fly / tunnel)
 *   2) Same-origin /api/* (local python server.py)
 *   3) Same-origin /api/*.php (Hostinger shared hosting)
 *   4) WhatsApp prefilled fallback in app.js
 *
 * Permanent cloud deploy (recommended):
 *   1. Open https://render.com/deploy?repo=https://github.com/saikrishnacoder/i-want-you-to-creating-a
 *   2. Create free Web Service from render.yaml
 *   3. Paste the https://….onrender.com URL below
 *   4. Redeploy Hostinger / push to main
 */
window.FG_API_BASE = window.FG_API_BASE || "https://functional-sections-implement-handles.trycloudflare.com";

(function (w) {
  var PHP_MAP = {
    "/api/submit": "/api/submit.php",
    "/api/leads": "/api/submit.php",
    "/api/admin-data": "/api/admin-data.php",
    "/api/backend-info": "/api/backend-info.php",
    "/api/challenge-join": "/api/challenge-join.php",
  };

  w.fgApiUrl = function (path) {
    var base = String(w.FG_API_BASE || "").replace(/\/$/, "");
    if (!path) return base || "/";
    if (/^https?:\/\//i.test(path)) return path;
    if (!base) return path.charAt(0) === "/" ? path : "/" + path;
    return base + (path.charAt(0) === "/" ? path : "/" + path);
  };

  /** Ordered endpoints to try for a logical API path. */
  w.fgApiCandidates = function (path) {
    var clean = path.charAt(0) === "/" ? path : "/" + path;
    var list = [];
    var primary = w.fgApiUrl(clean);
    if (primary) list.push(primary);

    // Same-origin Python path (local server.py / same-host API).
    if (list.indexOf(clean) === -1) list.push(clean);

    // Hostinger PHP fallback — always available if cloud/local API is down.
    if (PHP_MAP[clean] && list.indexOf(PHP_MAP[clean]) === -1) {
      list.push(PHP_MAP[clean]);
    }
    return list;
  };

  w.fgWhatsAppLeadUrl = function (payload) {
    var p = payload || {};
    var lines = ["New Fitness Gurukul website lead"];
    var name = p.name || p.contact_name || "";
    if (name) lines.push("Name: " + name);
    if (p.phone) lines.push("Phone: " + p.phone);
    if (p.email) lines.push("Email: " + p.email);
    if (p.program) lines.push("Program: " + p.program);
    if (p.goal) lines.push("Goal: " + p.goal);
    if (p.coach) lines.push("Coach: " + p.coach);
    if (p.company) lines.push("Company: " + p.company);
    if (p.event_type) lines.push("Event: " + p.event_type);
    if (p.form_type) lines.push("Type: " + p.form_type);
    if (p.message) lines.push("Notes: " + p.message);
    return "https://wa.me/917207113310?text=" + encodeURIComponent(lines.join("\n"));
  };
})(window);
