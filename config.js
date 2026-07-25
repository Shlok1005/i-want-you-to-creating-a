/**
 * Fitness Gurukul — API endpoint config
 *
 * Hostinger static pages can save leads in two ways:
 *   1) Cloud Python API (Render/Railway/Fly) via FG_API_BASE
 *   2) Same-origin PHP endpoints in /api/*.php (works on Hostinger alone)
 *
 * Leave FG_API_BASE as "" for Hostinger PHP / local Python.
 * Set it only when you deploy server.py to the cloud.
 *
 * Example cloud API:
 *   window.FG_API_BASE = "https://fitness-gurukul-api.onrender.com";
 */
window.FG_API_BASE = window.FG_API_BASE || "";

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

    // Same-origin Python path when no remote base is configured.
    if (!w.FG_API_BASE && list.indexOf(clean) === -1) list.push(clean);

    // Hostinger PHP fallback (only when not forced to a remote cloud API).
    if (!w.FG_API_BASE && PHP_MAP[clean]) {
      var phpPath = PHP_MAP[clean];
      if (list.indexOf(phpPath) === -1) list.push(phpPath);
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
