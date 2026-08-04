import type { Config, Context } from "@netlify/functions";

const DEFAULT_SCRIPT_URL =
  "https://script.google.com/macros/s/AKfycbyesKPUAUXA1uMMFvJLxy9Ysb0dR_kJ6XHN1QyzdUs/exec";

function scriptUrl(): string {
  const fromEnv = Netlify.env.get("GOOGLE_SCRIPT_URL") || Netlify.env.get("FG_GOOGLE_SCRIPT_URL");
  const raw = String(fromEnv || DEFAULT_SCRIPT_URL).trim();
  // /dev requires the owner to be logged in; public forms must use /exec.
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

  try {
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

    if (!ok) {
      return new Response(
        JSON.stringify({
          ok: false,
          error:
            "Google Script is not publicly reachable. Redeploy the web app with Who has access: Anyone, and use the /exec URL.",
          detail: str(data.error) || text.slice(0, 180),
        }),
        { status: 502, headers }
      );
    }

    return new Response(JSON.stringify({ ok: true, via: "google-script", data }), {
      status: 200,
      headers,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Upstream request failed";
    return new Response(JSON.stringify({ ok: false, error: message }), {
      status: 502,
      headers,
    });
  }
};

export const config: Config = {
  path: "/api/submit",
};
