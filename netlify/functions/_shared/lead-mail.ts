export const LEAD_NOTIFY_EMAILS = [
  "contact@fitnessgurukul.co.in",
  "fitnessgurukul01@gmail.com",
] as const;

function str(value: unknown): string {
  return value == null ? "" : String(value).trim();
}

function leadLabel(formType: string): string {
  if (formType === "transformation_challenge" || formType === "challenge_leads") return "challenge lead";
  if (formType === "corporate_event" || formType === "corporate_events") return "corporate inquiry";
  return "consultation lead";
}

export function buildLeadEmail(payload: Record<string, unknown>) {
  const formType = str(payload.form_type) || "consultation";
  const name = str(payload.name) || str(payload.contact_name);
  const phone = str(payload.phone);
  const label = leadLabel(formType);
  const subject = `[Fitness Gurukul] New ${label} — ${name || phone || "lead"}`;
  const body = [
    "New lead received from the Fitness Gurukul website.",
    "",
    `Type: ${label}`,
    `Name: ${name}`,
    `Phone: ${phone}`,
    `Email: ${str(payload.email)}`,
    `Program: ${str(payload.program)}`,
    `Goal: ${str(payload.goal)}`,
    `Coach: ${str(payload.coach)}`,
    `Company: ${str(payload.company)}`,
    `Contact name: ${str(payload.contact_name)}`,
    `Event type: ${str(payload.event_type)}`,
    `Attendees: ${str(payload.attendees)}`,
    `Preferred date: ${str(payload.preferred_date)}`,
    `Budget: ${str(payload.budget)}`,
    `Location: ${str(payload.location)}`,
    `Message: ${str(payload.message)}`,
    `Source: ${str(payload.source)}`,
    `Timestamp: ${str(payload.timestamp) || new Date().toISOString()}`,
  ].join("\n");

  return { subject, body, formType, name, phone, label };
}

/** Keyless FormSubmit fallback — emails each inbox. Activate once per address. */
export async function emailLeadViaFormSubmit(payload: Record<string, unknown>): Promise<boolean> {
  if (Netlify.env.get("FORMSUBMIT_DISABLE") === "1") return false;

  const { subject, body, name, phone } = buildLeadEmail(payload);
  const replyTo = str(payload.email) || LEAD_NOTIFY_EMAILS[0];
  const formPayload = {
    name: name || "Website lead",
    phone: phone || "",
    email: replyTo,
    message: body,
    _subject: subject,
    _template: "table",
    _captcha: "false",
    _replyto: replyTo,
  };

  const results = await Promise.all(
    LEAD_NOTIFY_EMAILS.map(async (to) => {
      try {
        const res = await fetch(`https://formsubmit.co/ajax/${encodeURIComponent(to)}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify(formPayload),
        });
        const data = (await res.json().catch(() => ({}))) as { success?: boolean | string };
        return Boolean(res.ok && (data.success === true || data.success === "true"));
      } catch {
        return false;
      }
    })
  );

  return results.some(Boolean);
}
