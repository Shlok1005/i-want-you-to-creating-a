import type { Config, Context } from "@netlify/functions";
import { emailLeadViaFormSubmit } from "./_shared/lead-mail";

const DEFAULT_SCRIPT_URL =
  "https://script.google.com/macros/s/AKfycbyesKPUAUXA1uMMFvJLxy9Ysb0dR_kJ6XHN1QyzdUs/exec";

function scriptUrl(): string {
  const fromEnv = Netlify.env.get("GOOGLE_SCRIPT_URL") || Netlify.env.get("FG_GOOGLE_SCRIPT_URL");
  const raw = String(fromEnv || DEFAULT_SCRIPT_URL).trim();
  return raw.replace(/\/dev\/?$/i, "/exec");
}

function corsHeaders(origin: string | null): HeadersInit {
  return {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": origin || "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}

function str(value: unknown): string {
  return value == null ? "" : String(value).trim();
}

async function forwardToGoogleScript(payload: Record<string, unknown>) {
  const upstream = await fetch(scriptUrl(), {
    method: "POST",
    redirect: "follow",
    headers: { "Content-Type": "text/plain;charset=utf-8" },
    body: JSON.stringify(payload),
  });
  const text = await upstream.text();
  let data: Record<string, unknown> = {};
  try {
    data = JSON.parse(text) as Record<string, unknown>;
  } catch {
    data = {};
  }

  const ok =
    Boolean(data.ok) ||
    Boolean(data.success) ||
    data.result === "success" ||
    (upstream.ok && !/unable to open|sign in|accounts\.google/i.test(text));

  return { ok, data, text };
}

export default async (req: Request, _context: Context) => {
  const headers = corsHeaders(req.headers.get("origin"));

  if (req.method === "OPTIONS") {
    return new Response("", { status: 204, headers });
  }

  if (req.method !== "POST") {
    return new Response(JSON.stringify({ ok: false, error: "Method not allowed" }), {
      status: 405,
      headers,
    });
  }

  let body: Record<string, unknown> = {};
  try {
    body = (await req.json()) as Record<string, unknown>;
  } catch {
    return new Response(JSON.stringify({ ok: false, error: "Invalid JSON body" }), {
      status: 400,
      headers,
    });
  }

  const formType = str(body.form_type) || "consultation";
  const name = str(body.name) || str(body.contact_name);
  const phone = str(body.phone);

  if (formType === "corporate_event") {
    if (!str(body.company) || !str(body.contact_name) || !str(body.email) || !phone || !str(body.event_type)) {
      return new Response(JSON.stringify({ ok: false, error: "Missing required fields" }), {
        status: 400,
        headers,
      });
    }
  } else if (!name || !phone) {
    return new Response(JSON.stringify({ ok: false, error: "Missing required fields" }), {
      status: 400,
      headers,
    });
  }

  const payload = {
    ...body,
    form_type: formType,
    name,
    phone,
    timestamp: str(body.timestamp) || new Date().toISOString(),
    source: str(body.source) || "netlify-function",
  };

  let googleOk = false;
  let googleData: Record<string, unknown> = {};
  try {
    const google = await forwardToGoogleScript(payload);
    googleOk = google.ok;
    googleData = google.data;
  } catch (error) {
    console.warn("Google Script forward failed", error);
  }

  // If Sheets/MailApp path failed, still email both inboxes via FormSubmit.
  let emailed = Boolean(googleOk && googleData.emailed);
  if (!googleOk || !emailed) {
    emailed = (await emailLeadViaFormSubmit(payload)) || emailed;
  }

  if (!googleOk && !emailed) {
    return new Response(
      JSON.stringify({
        ok: false,
        error:
          "Lead could not be saved or emailed. Redeploy Google Apps Script with Who has access: Anyone (/exec), and activate FormSubmit for both inboxes.",
      }),
      { status: 502, headers }
    );
  }

  return new Response(
    JSON.stringify({
      ok: true,
      via: googleOk ? "google-script" : "email",
      google_script: googleOk,
      emailed,
      data: googleData,
    }),
    { status: 200, headers }
  );
};

export const config: Config = {
  path: "/api/submit",
};
