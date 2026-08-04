import type { Config, Context } from "@netlify/functions";
import { emailLeadViaFormSubmit } from "./_shared/lead-mail";

const DEFAULT_SCRIPT_URL =
  "https://script.google.com/macros/s/AKfycbyesKPUAUXA1uMMFvJLxy9Ysb0dR_kJ6XHN1QyzdUs/exec";

function scriptUrl(): string {
  const fromEnv = Netlify.env.get("GOOGLE_SCRIPT_URL") || Netlify.env.get("FG_GOOGLE_SCRIPT_URL");
  return String(fromEnv || DEFAULT_SCRIPT_URL).trim().replace(/\/dev\/?$/i, "/exec");
}

function str(value: unknown): string {
  return value == null ? "" : String(value).trim();
}

function corsHeaders(origin: string | null): HeadersInit {
  return {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": origin || "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
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
  return { ok, data };
}

export default async (req: Request, _context: Context) => {
  const headers = corsHeaders(req.headers.get("origin"));
  if (req.method === "OPTIONS") return new Response("", { status: 204, headers });
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
  if (!name || !phone) {
    return new Response(JSON.stringify({ ok: false, error: "Name and phone are required" }), {
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
  let emailed = false;
  try {
    const google = await forwardToGoogleScript(payload);
    googleOk = google.ok;
    emailed = Boolean(google.data && google.data.emailed);
  } catch (error) {
    console.warn("Google Script forward failed", error);
  }

  if (!emailed) {
    emailed = await emailLeadViaFormSubmit(payload);
  }

  if (!googleOk && !emailed) {
    return new Response(
      JSON.stringify({
        ok: false,
        error: "Lead could not be saved or emailed. Redeploy Google Apps Script (/exec, Anyone).",
      }),
      { status: 502, headers }
    );
  }

  return new Response(
    JSON.stringify({ ok: true, google_script: googleOk, emailed }),
    { status: 200, headers }
  );
};

export const config: Config = {
  path: "/api/submit",
};
