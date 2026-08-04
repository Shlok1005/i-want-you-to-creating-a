const express = require("express");
const cors = require("cors");
const initSqlJs = require("sql.js");
const fs = require("fs");
const path = require("path");

const app = express();
const PORT = Number(process.env.PORT || 3000);
const DB_PATH = path.join(__dirname, "fitness_gurukul.sqlite3");

function loadEnvFile() {
  const envPath = path.join(__dirname, ".env");
  if (!fs.existsSync(envPath)) return;
  fs.readFileSync(envPath, "utf-8").split(/\r?\n/).forEach((rawLine) => {
    const line = rawLine.trim();
    if (!line || line.startsWith("#") || !line.includes("=")) return;
    const index = line.indexOf("=");
    const key = line.slice(0, index).trim();
    const value = line.slice(index + 1).trim().replace(/^['"]|['"]$/g, "");
    if (key && process.env[key] == null) process.env[key] = value;
  });
}

loadEnvFile();

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(__dirname));

const OLLAMA_BASE_URL = (process.env.OLLAMA_BASE_URL || "http://127.0.0.1:11434").replace(/\/$/, "");
const OLLAMA_MODEL = process.env.OLLAMA_MODEL || "llama3.2";
const CHAT_PROVIDER = String(process.env.CHAT_PROVIDER || "auto").trim().toLowerCase();
let ollamaCache = { checkedAt: 0, available: false, model: OLLAMA_MODEL };

const CONTACT = {
  phone: "08042781491",
  whatsapp: "+917207113310",
  email: "contact@fitnessgurukul.co.in",
  address: "H.no.1-10/2, Lakshmi Nagar Colony, near Pochamma Temple, Manikonda, Hyderabad, 500089",
};

const GOOGLE_SCRIPT_URL = String(
  process.env.GOOGLE_SCRIPT_URL ||
  process.env.FG_GOOGLE_SCRIPT_URL ||
  "https://script.google.com/macros/s/AKfycbyesKPUAUXA1uMMFvJLxy9Ysb0dR_kJ6XHN1QyzdUs/exec"
).trim().replace(/\/dev\/?$/i, "/exec");

const LEAD_NOTIFY_EMAILS = String(
  process.env.LEAD_NOTIFY_EMAIL ||
  process.env.FG_LEAD_EMAIL ||
  "contact@fitnessgurukul.co.in,fitnessgurukul01@gmail.com"
)
  .split(/[,;\s]+/)
  .map((email) => email.trim())
  .filter(Boolean);

function leadLabel(formType) {
  if (formType === "transformation_challenge" || formType === "challenge_leads") return "challenge lead";
  if (formType === "corporate_event" || formType === "corporate_events") return "corporate inquiry";
  return "consultation lead";
}

function buildLeadEmailBody(submission) {
  const formType = String(submission.form_type || "consultation");
  const label = leadLabel(formType);
  const name = String(submission.name || submission.contact_name || "");
  const phone = String(submission.phone || "");
  const subject = `[Fitness Gurukul] New ${label} — ${name || phone || "lead"}`;
  const body = [
    "New lead received from the Fitness Gurukul website.",
    "",
    `Type: ${label}`,
    `Name: ${name}`,
    `Phone: ${phone}`,
    `Email: ${submission.email || ""}`,
    `Program: ${submission.program || ""}`,
    `Goal: ${submission.goal || ""}`,
    `Coach: ${submission.coach || ""}`,
    `Company: ${submission.company || ""}`,
    `Contact name: ${submission.contact_name || ""}`,
    `Event type: ${submission.event_type || ""}`,
    `Attendees: ${submission.attendees || ""}`,
    `Preferred date: ${submission.preferred_date || ""}`,
    `Budget: ${submission.budget || ""}`,
    `Location: ${submission.location || ""}`,
    `Message: ${submission.message || ""}`,
    `Source: ${submission.source || "node-server"}`,
    `Timestamp: ${submission.timestamp || new Date().toISOString()}`,
  ].join("\n");
  return { subject, body, name, phone };
}

async function emailLeadViaFormSubmit(submission) {
  if (String(process.env.FORMSUBMIT_DISABLE || "").trim() === "1") return false;
  if (!LEAD_NOTIFY_EMAILS.length) return false;

  const { subject, body, name, phone } = buildLeadEmailBody(submission);
  const replyTo = String(submission.email || LEAD_NOTIFY_EMAILS[0]);
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
        const response = await fetch(`https://formsubmit.co/ajax/${encodeURIComponent(to)}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify(formPayload),
        });
        if (!response.ok) {
          console.warn(`FormSubmit failed for ${to}:`, response.status);
          return false;
        }
        console.log(`Lead email sent via FormSubmit → ${to}`);
        return true;
      } catch (error) {
        console.warn(`FormSubmit error for ${to}:`, error.message || error);
        return false;
      }
    })
  );

  return results.some(Boolean);
}

async function forwardLeadToGoogleScript(submission) {
  if (!GOOGLE_SCRIPT_URL) return { ok: false, skipped: true };
  try {
    const response = await fetch(GOOGLE_SCRIPT_URL, {
      method: "POST",
      redirect: "follow",
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify({
        ...submission,
        source: submission.source || "node-server",
      }),
    });
    const text = await response.text();
    let data = {};
    try { data = JSON.parse(text); } catch (_) { data = {}; }
    const ok = Boolean(data.ok || data.success || data.result === "success");
    if (!ok) {
      console.warn("Google Script forward failed:", (data && data.error) || text.slice(0, 160));
    }
    return { ok, data };
  } catch (error) {
    console.warn("Google Script forward error:", error.message || error);
    return { ok: false, error: error.message || String(error) };
  }
}

async function notifyLeadChannels(submission) {
  const google = await forwardLeadToGoogleScript(submission);
  let emailed = Boolean(google && google.ok && google.data && google.data.emailed);
  if (!google.ok || !emailed) {
    emailed = (await emailLeadViaFormSubmit(submission)) || emailed;
  }
  return { google, emailed };
}

const CHAT_SUGGESTIONS = [
  "Which plan is best for weight loss?",
  "Compare Core, Prime and Signature",
  "Do you have running or Hyrox plans?",
  "Which coach is best for yoga?",
];

const PLANS = [
  { name: "Fitness Gurukul Core", tag: "1-on-1 Coaching", category: "core", summary: "Dedicated fitness and nutrition coach with hyper-personalized workout plans, tailored Indian nutrition, and weekly video check-ins.", price: "From INR 5,999/month", sessions: "1 session/week", points: ["Dedicated coach", "Custom meal plan", "Video check-ins", "In-person PT", "App check-in"] },
  { name: "Fitness Gurukul Prime", tag: "Advanced Coaching", category: "prime", summary: "Complete fitness and nutrition coaching with 3x/week in-person personal training, posture correction, nutrition planning, and mandatory app check-ins.", price: "From INR 9,500/month", sessions: "3 sessions/week", points: ["1:1 coach + PT", "Nutrition plan", "Video check-ins", "Structural assessment", "App check-in"] },
  { name: "Fitness Gurukul Signature", tag: "Intensive Coaching", category: "signature", summary: "Intensive transformation plan to build strength, correct movement, and transform physique with 5x/week in-person training.", price: "INR 15,999/month", sessions: "5 sessions/week", points: ["1:1 coach", "In-person PT", "Nutrition plan", "Structural assessment", "App check-in"] },
  { name: "Fitness Gurukul Endurance", tag: "Running Coaching", category: "endurance", summary: "Professional running coaching for beginners through advanced PR-seekers with periodized training, strength and conditioning, endurance nutrition, and race-day strategy.", price: "INR 1,199/month", sessions: "Virtual", points: ["Dedicated running coach", "Periodized running program", "Runner-specific S&C", "Endurance nutrition", "Race strategy", "Daily chat support"] },
  { name: "Fitness Gurukul Forge", tag: "Hyrox / OCR Prep", category: "forge", summary: "Functional fitness racing prep for Hyrox and OCR athletes with compounded S&C, engine building, grip strength, explosive power, and compromised running stamina.", price: "INR 999/month", sessions: "Virtual", points: ["Dedicated S&C coach", "Compounded S&C workouts", "Functional engine building", "Agility and grip strength", "Explosive power drills"] },
  { name: "Virtual 1:1 Elite Transformation", tag: "Weight Loss & Muscle Gain", category: "elite", summary: "Remote 1:1 fitness and nutrition coaching for weight loss, lean muscle gain, or lifestyle overhaul with hyper-personalized plans.", price: "From INR 1,999/month", sessions: "Virtual", points: ["Dedicated coach", "Custom workout plans", "Indian nutrition plan", "Video check-ins", "Daily chat support", "Progressive overload"] },
];

let db;

async function initDatabase() {
  const SQL = await initSqlJs();
  if (fs.existsSync(DB_PATH)) {
    const buffer = fs.readFileSync(DB_PATH);
    db = new SQL.Database(buffer);
  } else {
    db = new SQL.Database();
  }
  db.run(`CREATE TABLE IF NOT EXISTS submissions (
    id TEXT PRIMARY KEY,
    form_type TEXT DEFAULT 'consultation',
    name TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    email TEXT DEFAULT '',
    program TEXT DEFAULT '',
    goal TEXT DEFAULT '',
    message TEXT DEFAULT '',
    coach TEXT DEFAULT '',
    company TEXT DEFAULT '',
    contact_name TEXT DEFAULT '',
    event_type TEXT DEFAULT '',
    attendees TEXT DEFAULT '',
    preferred_date TEXT DEFAULT '',
    budget TEXT DEFAULT '',
    location TEXT DEFAULT '',
    timestamp TEXT DEFAULT '',
    ip TEXT DEFAULT ''
  )`);
  saveDatabase();
}

function saveDatabase() {
  const data = db.export();
  const buffer = Buffer.from(data);
  fs.writeFileSync(DB_PATH, buffer);
}

function readSubmissions() {
  const results = db.exec("SELECT * FROM submissions ORDER BY rowid DESC");
  if (!results.length) return [];
  const cols = results[0].columns;
  return results[0].values.map((row) => {
    const obj = {};
    cols.forEach((col, i) => { obj[col] = row[i]; });
    return obj;
  });
}

function insertSubmission(s) {
  db.run(
    `INSERT INTO submissions (id, form_type, name, phone, email, program, goal, message, coach, company, contact_name, event_type, attendees, preferred_date, budget, location, timestamp, ip) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [s.id, s.form_type, s.name, s.phone, s.email, s.program, s.goal, s.message, s.coach, s.company, s.contact_name, s.event_type, s.attendees, s.preferred_date, s.budget, s.location, s.timestamp, s.ip]
  );
  saveDatabase();
}

function deleteSubmission(id) {
  db.run("DELETE FROM submissions WHERE id = ?", [id]);
  saveDatabase();
}

function normalizeChatText(value) {
  return String(value || "").trim().replace(/\s+/g, " ");
}

function chatContainsAny(text, words) {
  return words.some((word) => text.includes(word));
}

function planScore(plan, text) {
  const haystack = [
    plan.name, plan.tag, plan.category, plan.summary, plan.price, plan.sessions, plan.points.join(" "),
  ].join(" ").toLowerCase();
  const tokens = text.toLowerCase().split(/[^a-z0-9]+/).filter((token) => token.length > 2);
  let score = tokens.reduce((total, token) => total + (haystack.includes(token) ? 1 : 0), 0);
  if (chatContainsAny(text, ["weight", "fat", "loss", "slim", "transform", "muscle", "body", "lifestyle"]) && ["elite", "core", "prime", "signature"].includes(plan.category)) score += 3;
  if (chatContainsAny(text, ["home", "doorstep", "personal", "offline", "trainer", "pt", "in person", "session"]) && ["core", "prime", "signature"].includes(plan.category)) score += 3;
  if (chatContainsAny(text, ["run", "running", "marathon", "race", "endurance", "5k", "10k"]) && plan.category === "endurance") score += 6;
  if (chatContainsAny(text, ["hyrox", "ocr", "obstacle", "functional", "forge"]) && plan.category === "forge") score += 6;
  if (chatContainsAny(text, ["budget", "cheap", "low", "affordable", "online", "virtual"]) && ["elite", "forge", "endurance"].includes(plan.category)) score += 3;
  if (chatContainsAny(text, ["daily", "intense", "fast", "maximum", "premium", "five", "5"]) && plan.category === "signature") score += 5;
  if (chatContainsAny(text, ["three", "3", "advanced", "complete"]) && plan.category === "prime") score += 4;
  if (chatContainsAny(text, ["one", "1", "weekly", "starter", "beginner", "basic", "core"]) && plan.category === "core") score += 4;
  return score;
}

function findMatchingPlans(text) {
  const ranked = PLANS
    .map((plan) => ({ plan, score: planScore(plan, text) }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score);
  return (ranked.length ? ranked.map((item) => item.plan) : PLANS).slice(0, 3);
}

function formatPlanReply(plans, intro = "Here are the best-fit Fitness Gurukul plans:") {
  const lines = [intro];
  plans.slice(0, 3).forEach((plan) => {
    lines.push(`${plan.name} - ${plan.price}, ${plan.sessions}. ${plan.summary} Key inclusions: ${plan.points.slice(0, 3).join(", ")}.`);
  });
  lines.push("For the exact fit, share your goal, schedule, location, and whether you prefer virtual or in-person coaching.");
  return lines.join(" ");
}

function compareCorePrimeSignatureReply() {
  const core = PLANS.find((plan) => plan.category === "core");
  const prime = PLANS.find((plan) => plan.category === "prime");
  const signature = PLANS.find((plan) => plan.category === "signature");
  return `${core.name} is the starter personalized plan: ${core.price} with ${core.sessions}. ${prime.name} is more hands-on: ${prime.price} with ${prime.sessions} and fuller fitness plus nutrition support. ${signature.name} is the intensive option: ${signature.price} with ${signature.sessions} for faster transformation, in-person PT, nutrition, posture assessment, and app check-ins.`;
}

function buildChatSystemPrompt() {
  const planLines = PLANS.map((plan) => `- ${plan.name} (${plan.price}, ${plan.sessions}): ${plan.summary} Highlights: ${plan.points.join(", ")}.`);
  return [
    "You are the Fitness Gurukul AI assistant for a premium fitness studio in Hyderabad, India.",
    "Behave like a helpful fitness consultant, not a scripted FAQ bot. Ask one useful follow-up question when the user's goal is vague.",
    "Recommend relevant website plans, services, coaches, or next steps. Never invent prices, coaches, dates, medical claims, or contact details.",
    "For medical, injury, pregnancy, or disease-related questions, give general fitness guidance only and recommend speaking with a qualified professional.",
    "Answer clearly, warmly, and concisely in 2-5 short sentences unless the user asks for detail.",
    "If unsure, invite the user to book a free consultation.",
    `Contact phone: ${CONTACT.phone}. WhatsApp: ${CONTACT.whatsapp}. Email: ${CONTACT.email}. Address: ${CONTACT.address}.`,
    "Current coaching plans from the website:",
    ...planLines,
  ].join("\n");
}

function extractOpenAIText(payload) {
  if (typeof payload.output_text === "string") return normalizeChatText(payload.output_text);
  const parts = [];
  (payload.output || []).forEach((item) => {
    (item.content || []).forEach((content) => {
      if (typeof content.text === "string") parts.push(content.text);
    });
  });
  return normalizeChatText(parts.join(" "));
}

async function getOllamaStatus(force = false) {
  const now = Date.now();
  if (!force && now - ollamaCache.checkedAt < 15000) return ollamaCache;
  try {
    const response = await fetch(`${OLLAMA_BASE_URL}/api/tags`, { signal: AbortSignal.timeout(2500) });
    if (!response.ok) throw new Error(`Ollama status failed: ${response.status}`);
    const payload = await response.json();
    const models = Array.isArray(payload.models) ? payload.models : [];
    const names = models.map((item) => String(item.name || item.model || ""));
    const preferred = names.find((name) => name === OLLAMA_MODEL || name.startsWith(`${OLLAMA_MODEL}:`)) || names[0] || OLLAMA_MODEL;
    ollamaCache = { checkedAt: now, available: names.length > 0, model: preferred };
  } catch (error) {
    ollamaCache = { checkedAt: now, available: false, model: OLLAMA_MODEL };
  }
  return ollamaCache;
}

async function callOllamaChat(message, history = []) {
  const status = await getOllamaStatus();
  if (!status.available) return null;
  try {
    const messages = [
      { role: "system", content: buildChatSystemPrompt() },
      ...history.slice(-8).filter((item) => ["user", "assistant"].includes(item.role)).map((item) => ({
        role: item.role,
        content: normalizeChatText(item.content),
      })),
      { role: "user", content: normalizeChatText(message) },
    ];
    const response = await fetch(`${OLLAMA_BASE_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: AbortSignal.timeout(60000),
      body: JSON.stringify({
        model: status.model,
        stream: false,
        messages,
        options: { temperature: 0.35, num_predict: 450 },
      }),
    });
    if (!response.ok) throw new Error(`Ollama request failed: ${response.status}`);
    const payload = await response.json();
    return normalizeChatText(payload.message && payload.message.content);
  } catch (error) {
    console.warn("Ollama chat error:", error.message);
    ollamaCache = { ...ollamaCache, checkedAt: 0, available: false };
    return null;
  }
}

function generateLocalChatReply(message) {
  const text = normalizeChatText(message).toLowerCase();
  if (!text) return "Ask me about training plans, coaches, pricing, events, or how to book a free consultation.";
  if (/^(hi|hello|hey|namaste)\b/.test(text)) {
    return "Hi! I am the Fitness Gurukul assistant. I can help with plans, coach matching, pricing, events, and booking a free consultation in Hyderabad.";
  }
  if (chatContainsAny(text, ["contact", "phone", "call", "whatsapp", "email", "address", "location", "where"])) {
    return `You can call ${CONTACT.phone}, WhatsApp ${CONTACT.whatsapp}, or email ${CONTACT.email}. Studio address: ${CONTACT.address}.`;
  }
  if (chatContainsAny(text, ["compare", "difference", "core", "prime", "signature"])) {
    return compareCorePrimeSignatureReply();
  }
  if (chatContainsAny(text, ["price", "cost", "fee", "how much", "pricing", "plan", "package", "program", "weight", "muscle", "hyrox", "running", "virtual", "online", "fitness", "strength", "transformation"])) {
    return formatPlanReply(findMatchingPlans(text));
  }
  if (chatContainsAny(text, ["doorstep", "home", "in person", "personal trainer"])) {
    return formatPlanReply(findMatchingPlans("in person personal training core prime signature"), "Yes. For in-person or doorstep-style coaching, these are the closest plan fits:");
  }
  if (chatContainsAny(text, ["yoga", "coach", "trainer", "instructor"])) {
    return "We have yoga, fitness, sports, kids, rehab, and special-needs coaches. For yoga, ask for Aditya Gururani, Nitu Arya, Rahul Bisht, Rahul Singh Pawar, or Parul Danu; for strength or weight loss, the team can match you after a free consultation.";
  }
  if (chatContainsAny(text, ["event", "marathon", "cycling", "ride", "camp", "born star", "obstacle"])) {
    return "Fitness Gurukul supports running events, cycling events, corporate wellness, group training, bootcamps, and community runs. Share the event type and team size to get a custom quote.";
  }
  return "I can help with Fitness Gurukul plans, coach recommendations, pricing, events, and booking. Try asking about weight loss, Core vs Prime, Signature, running, Hyrox, or virtual coaching.";
}

async function callOpenAIChat(message, history = []) {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) return null;
  const model = process.env.OPENAI_MODEL || "gpt-5.6";
  try {
    const input = [
      ...history.slice(-8).filter((item) => ["user", "assistant"].includes(item.role)).map((item) => ({ role: item.role, content: normalizeChatText(item.content) })),
      { role: "user", content: normalizeChatText(message) },
    ];
    const response = await fetch("https://api.openai.com/v1/responses", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model,
        instructions: buildChatSystemPrompt(),
        input,
        max_output_tokens: 450,
      }),
    });
    if (!response.ok) throw new Error(`OpenAI request failed: ${response.status}`);
    const payload = await response.json();
    return extractOpenAIText(payload);
  } catch (error) {
    console.warn("OpenAI chat error:", error.message);
    return null;
  }
}

async function resolveChatEngine() {
  const ollama = await getOllamaStatus();
  const allowOpenAI = CHAT_PROVIDER === "openai" || process.env.CHAT_ALLOW_OPENAI === "true";

  if (CHAT_PROVIDER === "local") {
    return { aiEnabled: false, engine: "local", model: "fitness-gurukul-local", free: true };
  }
  if ((CHAT_PROVIDER === "ollama" || CHAT_PROVIDER === "auto") && ollama.available) {
    return { aiEnabled: true, engine: "ollama", model: ollama.model, free: true };
  }
  if (allowOpenAI && process.env.OPENAI_API_KEY) {
    return { aiEnabled: true, engine: "openai", model: process.env.OPENAI_MODEL || "gpt-5.6", free: false };
  }
  return { aiEnabled: false, engine: "local", model: "fitness-gurukul-local", free: true };
}

async function generateChatReply(message, history = []) {
  const engine = await resolveChatEngine();

  if (engine.engine === "ollama") {
    const ollamaReply = await callOllamaChat(message, history);
    if (ollamaReply) return { reply: ollamaReply, source: "ollama" };
  }

  if (engine.engine === "openai") {
    const openaiReply = await callOpenAIChat(message, history);
    if (openaiReply) return { reply: openaiReply, source: "openai" };
  }

  return { reply: generateLocalChatReply(message), source: "local" };
}

app.get("/api/health", async (req, res) => {
  const chat = await resolveChatEngine();
  res.json({ ok: true, engine: "node", aiEnabled: chat.aiEnabled, chatEngine: chat.engine, free: chat.free });
});

app.get("/api/content", (req, res) => {
  res.json({ ok: true, plans: PLANS, contact: CONTACT });
});

app.get("/api/chat/status", async (req, res) => {
  const chat = await resolveChatEngine();
  res.json({
    ok: true,
    aiEnabled: chat.aiEnabled,
    engine: chat.engine,
    model: chat.model,
    free: chat.free,
    suggestions: CHAT_SUGGESTIONS,
  });
});

app.post("/api/chat", async (req, res) => {
  const message = normalizeChatText(req.body.message);
  if (!message) return res.status(400).json({ ok: false, error: "Message is required" });
  if (message.length > 2000) return res.status(400).json({ ok: false, error: "Message is too long" });

  const history = Array.isArray(req.body.history) ? req.body.history : [];
  const { reply, source } = await generateChatReply(message, history);

  res.json({
    ok: true,
    reply,
    source,
    aiEnabled: source === "ollama" || source === "openai",
    free: source !== "openai",
    suggestions: CHAT_SUGGESTIONS,
  });
});

app.post("/api/submit", async (req, res) => {
  const { name, phone, email, program, goal, message, coach, form_type, company, contact_name, event_type, attendees, preferred_date, budget, location } = req.body;

  if (form_type === "corporate_event") {
    if (!company || !contact_name || !email || !phone || !event_type || !attendees) {
      return res.status(400).json({ ok: false, error: "Missing required fields" });
    }
  } else {
    if (!name || !phone || !program || !goal) {
      return res.status(400).json({ ok: false, error: "Missing required fields" });
    }
  }

  const submission = {
    id: Date.now().toString(36) + Math.random().toString(36).slice(2, 7),
    form_type: String(form_type || "consultation"),
    name: String(name || contact_name || ""),
    phone: String(phone || ""),
    email: String(email || ""),
    program: String(program || ""),
    goal: String(goal || ""),
    message: String(message || ""),
    coach: String(coach || ""),
    company: String(company || ""),
    contact_name: String(contact_name || ""),
    event_type: String(event_type || ""),
    attendees: String(attendees || ""),
    preferred_date: String(preferred_date || ""),
    budget: String(budget || ""),
    location: String(location || ""),
    timestamp: String(new Date().toISOString()),
    ip: String(req.headers["x-forwarded-for"] || req.socket.remoteAddress || ""),
  };

  insertSubmission(submission);

  const notify = await notifyLeadChannels(submission);

  console.log(`[NEW SUBMISSION] ${submission.name} — ${submission.program} — ${submission.timestamp}`);
  res.json({
    ok: true,
    id: submission.id,
    google_script: Boolean(notify.google && notify.google.ok),
    emailed: Boolean(notify.emailed),
  });
});

app.get("/api/submissions", (req, res) => {
  const submissions = readSubmissions();
  res.json({ ok: true, count: submissions.length, data: submissions });
});

app.delete("/api/submissions/:id", (req, res) => {
  const { id } = req.params;
  deleteSubmission(id);
  res.json({ ok: true });
});

app.get("/admin", (req, res) => {
  res.sendFile(path.join(__dirname, "admin.html"));
});

app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "index.html"));
});

initDatabase().then(async () => {
  const chat = await resolveChatEngine();
  app.listen(PORT, () => {
    console.log(`\n  Fitness Gurukul Server running at:\n`);
    console.log(`  Local:   http://localhost:${PORT}`);
    console.log(`  Admin:   http://localhost:${PORT}/admin`);
    console.log(`  Chat:    ${chat.engine}${chat.aiEnabled ? ` (${chat.model})` : " FAQ fallback"} — ${chat.free ? "free" : "paid API"}`);
    console.log(`\n  Submissions stored in: fitness_gurukul.sqlite3\n`);
    if (!chat.aiEnabled) {
      console.log("  Tip: install Ollama + run `ollama pull llama3.2` for free local AI chat.\n");
    }
  });
}).catch((err) => {
  console.error("Failed to initialize database:", err);
  process.exit(1);
});
