/**
 * Vercel serverless lead endpoint.
 * POST /api/submit  → Google Sheet (Apps Script) + email both inboxes.
 */
const GOOGLE_SCRIPT_URL = String(
  process.env.GOOGLE_SCRIPT_URL ||
    "https://script.google.com/macros/s/AKfycbyLBGzE5Fk5xcmn3D6mDsIeY0GvjPiAJXCv_6Y58Dxv-9mVNnND0Jh1jSyjXqqovNSA/exec"
).replace(/\/dev\/?$/i, "/exec");

const LEAD_EMAILS = String(
  process.env.LEAD_NOTIFY_EMAIL ||
    "contact@fitnessgurukul.co.in,fitnessgurukul01@gmail.com"
)
  .split(/[,;\s]+/)
  .map((e) => e.trim())
  .filter(Boolean);

function str(v) {
  return v == null ? "" : String(v).trim();
}

function label(formType) {
  if (formType === "transformation_challenge" || formType === "challenge_leads") return "challenge lead";
  if (formType === "corporate_event" || formType === "corporate_events") return "corporate inquiry";
  return "consultation lead";
}

async function forwardGoogle(payload) {
  try {
    const res = await fetch(GOOGLE_SCRIPT_URL, {
      method: "POST",
      redirect: "follow",
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify(payload),
    });
    const text = await res.text();
    let data = {};
    try {
      data = JSON.parse(text);
    } catch (_) {
      data = {};
    }
    const ok =
      Boolean(data.ok || data.success || data.result === "success") &&
      !/not found: doPost|unable to open|ServiceLogin/i.test(text);
    return { ok, emailed: Boolean(data.emailed), detail: text.slice(0, 160) };
  } catch (err) {
    return { ok: false, emailed: false, detail: String(err.message || err) };
  }
}

async function emailFormSubmit(payload) {
  const formType = str(payload.form_type) || "consultation";
  const name = str(payload.name) || str(payload.contact_name) || "Website lead";
  const phone = str(payload.phone);
  const replyTo = str(payload.email) || LEAD_EMAILS[0];
  const subject = `[Fitness Gurukul] New ${label(formType)} — ${name}`;
  const message = [
    `Type: ${label(formType)}`,
    `Name: ${name}`,
    `Phone: ${phone}`,
    `Email: ${str(payload.email)}`,
    `Program: ${str(payload.program)}`,
    `Goal: ${str(payload.goal)}`,
    `Coach: ${str(payload.coach)}`,
    `Company: ${str(payload.company)}`,
    `Event: ${str(payload.event_type)}`,
    `Location: ${str(payload.location)}`,
    `Message: ${str(payload.message)}`,
    `Source: ${str(payload.source)}`,
    `Time: ${str(payload.timestamp) || new Date().toISOString()}`,
  ].join("\n");

  const body = {
    name,
    phone,
    email: replyTo,
    message,
    _subject: subject,
    _template: "table",
    _captcha: "false",
    _replyto: replyTo,
  };

  const results = await Promise.all(
    LEAD_EMAILS.map(async (to) => {
      try {
        const res = await fetch(`https://formsubmit.co/ajax/${encodeURIComponent(to)}`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify(body),
        });
        const data = await res.json().catch(() => ({}));
        return Boolean(res.ok && (data.success === true || data.success === "true"));
      } catch (_) {
        return false;
      }
    })
  );
  return results.some(Boolean);
}

module.exports = async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") return res.status(204).end();
  if (req.method !== "POST") return res.status(405).json({ ok: false, error: "POST only" });

  const raw = typeof req.body === "string" ? JSON.parse(req.body || "{}") : req.body || {};
  const formType = str(raw.form_type) || "consultation";
  const name = str(raw.name) || str(raw.contact_name);
  const phone = str(raw.phone);

  if (!name || !phone) {
    return res.status(400).json({ ok: false, error: "Name and phone are required" });
  }

  const payload = {
    ...raw,
    form_type: formType,
    name,
    phone,
    timestamp: str(raw.timestamp) || new Date().toISOString(),
    source: str(raw.source) || "vercel-api",
  };

  const google = await forwardGoogle(payload);
  let emailed = google.emailed;
  if (!emailed) emailed = await emailFormSubmit(payload);

  if (!google.ok && !emailed) {
    return res.status(502).json({
      ok: false,
      error: "Lead not saved. Paste google-apps-script/Code.gs and redeploy web app (Anyone, /exec).",
      google_detail: google.detail,
    });
  }

  return res.status(200).json({
    ok: true,
    google_script: google.ok,
    emailed,
  });
};
