/**
 * Fitness Gurukul — Google Sheet lead collector + email
 *
 * SETUP (once):
 * 1. Open your Google Sheet (or create one named "Fitness Gurukul Leads")
 * 2. Extensions → Apps Script
 * 3. Delete any default code, paste THIS ENTIRE file, Save (Ctrl/Cmd+S)
 * 4. Deploy → New deployment
 *    - Type: Web app
 *    - Execute as: Me
 *    - Who has access: Anyone
 * 5. Deploy → copy the /exec URL
 * 6. Website already points at your /exec URL in app.js
 *
 * After any Code.gs edit: Deploy → Manage deployments → Edit (pencil) → New version → Deploy
 *
 * Result:
 * - New rows in tabs: Consultations / Challenge / Corporate
 * - Email to contact@fitnessgurukul.co.in AND fitnessgurukul01@gmail.com
 */

var EMAILS = [
  "contact@fitnessgurukul.co.in",
  "fitnessgurukul01@gmail.com"
];

function doGet() {
  return json_({
    ok: true,
    service: "Fitness Gurukul Leads",
    hint: "POST JSON leads here from the website forms"
  });
}

function doPost(e) {
  try {
    var data = parseBody_(e);
    var formType = String(data.form_type || "consultation").trim() || "consultation";
    var name = String(data.name || data.contact_name || "").trim();
    var phone = String(data.phone || "").trim();

    if (!name || !phone) {
      return json_({ ok: false, error: "name and phone required" });
    }

    var tab = sheetTab_(formType);
    var sheet = getSheet_(tab);
    ensureHeader_(sheet);

    sheet.appendRow([
      String(data.timestamp || new Date().toISOString()),
      formType,
      name,
      phone,
      String(data.email || ""),
      String(data.program || ""),
      String(data.goal || ""),
      String(data.message || ""),
      String(data.coach || ""),
      String(data.company || ""),
      String(data.contact_name || ""),
      String(data.event_type || ""),
      String(data.attendees || ""),
      String(data.preferred_date || ""),
      String(data.budget || ""),
      String(data.location || ""),
      String(data.source || "")
    ]);

    var emailed = sendLeadEmail_(data, formType, name, phone);
    return json_({ ok: true, success: true, emailed: emailed, form_type: formType, sheet: tab });
  } catch (err) {
    return json_({ ok: false, error: String(err && err.message ? err.message : err) });
  }
}

function parseBody_(e) {
  if (!e) return {};
  if (e.postData && e.postData.contents) {
    try {
      return JSON.parse(String(e.postData.contents));
    } catch (err) {
      return e.parameter || {};
    }
  }
  return e.parameter || {};
}

function sheetTab_(formType) {
  if (formType.indexOf("challenge") >= 0) return "Challenge";
  if (formType.indexOf("corporate") >= 0) return "Corporate";
  return "Consultations";
}

function getSheet_(tabName) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) {
    throw new Error("Open this script from a Google Sheet (Extensions → Apps Script)");
  }
  return ss.getSheetByName(tabName) || ss.insertSheet(tabName);
}

function ensureHeader_(sheet) {
  if (sheet.getLastRow() > 0) return;
  sheet.appendRow([
    "Timestamp",
    "Form Type",
    "Name",
    "Phone",
    "Email",
    "Program",
    "Goal",
    "Message",
    "Coach",
    "Company",
    "Contact Name",
    "Event Type",
    "Attendees",
    "Preferred Date",
    "Budget",
    "Location",
    "Source"
  ]);
  sheet.setFrozenRows(1);
}

function sendLeadEmail_(data, formType, name, phone) {
  try {
    var label = formType.indexOf("challenge") >= 0
      ? "challenge lead"
      : (formType.indexOf("corporate") >= 0 ? "corporate inquiry" : "consultation lead");

    MailApp.sendEmail({
      to: EMAILS.join(","),
      subject: "[Fitness Gurukul] New " + label + " — " + name,
      body: [
        "New website lead",
        "",
        "Type: " + label,
        "Name: " + name,
        "Phone: " + phone,
        "Email: " + String(data.email || ""),
        "Program: " + String(data.program || ""),
        "Goal: " + String(data.goal || ""),
        "Coach: " + String(data.coach || ""),
        "Company: " + String(data.company || ""),
        "Contact name: " + String(data.contact_name || ""),
        "Event type: " + String(data.event_type || ""),
        "Attendees: " + String(data.attendees || ""),
        "Preferred date: " + String(data.preferred_date || ""),
        "Budget: " + String(data.budget || ""),
        "Location: " + String(data.location || ""),
        "Message: " + String(data.message || ""),
        "Source: " + String(data.source || ""),
        "Time: " + String(data.timestamp || new Date().toISOString()),
        "",
        "Also saved in your Google Sheet."
      ].join("\n"),
      replyTo: String(data.email || EMAILS[0])
    });
    return true;
  } catch (err) {
    console.error("MailApp failed: " + err);
    return false;
  }
}

function json_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
