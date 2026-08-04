/**
 * Fitness Gurukul — Google Sheets lead collector + email alerts
 *
 * Setup:
 * 1. Create/open a Google Sheet.
 * 2. Extensions → Apps Script → paste this file → Save.
 * 3. Deploy → New deployment → Type: Web app
 *    - Execute as: Me
 *    - Who has access: Anyone
 * 4. Copy the /exec URL (not /dev) into the website.
 *
 * Sheet tabs are created automatically: Consultations, Challenge, Corporate, Other.
 * Every accepted lead emails:
 *   contact@fitnessgurukul.co.in
 *   fitnessgurukul01@gmail.com
 */

var LEAD_NOTIFY_EMAILS = [
  "contact@fitnessgurukul.co.in",
  "fitnessgurukul01@gmail.com"
];

var SHEET_TABS = {
  consultation: "Consultations",
  transformation_challenge: "Challenge",
  challenge_leads: "Challenge",
  corporate_event: "Corporate",
  corporate_events: "Corporate"
};

var HEADERS = [
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
  "Source",
  "Raw JSON"
];

function doGet() {
  return json_({ ok: true, service: "Fitness Gurukul Leads", hint: "POST JSON leads here" });
}

function doPost(e) {
  try {
    var data = parseBody_(e);
    var formType = String(data.form_type || data.formType || "consultation").trim() || "consultation";
    var name = String(data.name || data.contact_name || "").trim();
    var phone = String(data.phone || "").trim();

    if (formType === "corporate_event" || formType === "corporate_events") {
      if (!String(data.company || "").trim() || !String(data.contact_name || name).trim() || !phone) {
        return json_({ ok: false, error: "Missing required corporate fields" });
      }
    } else if (!name || !phone) {
      return json_({ ok: false, error: "Missing required fields: name, phone" });
    }

    var sheet = getOrCreateSheet_(SHEET_TABS[formType] || "Other");
    ensureHeaders_(sheet);

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
      String(data.source || ""),
      JSON.stringify(data)
    ]);

    var emailed = notifyLeadEmail_(data, formType, name, phone);
    return json_({ ok: true, success: true, form_type: formType, emailed: emailed });
  } catch (err) {
    return json_({ ok: false, error: String(err && err.message ? err.message : err) });
  }
}

function notifyLeadEmail_(data, formType, name, phone) {
  try {
    var label = leadLabel_(formType);
    var subject = "[Fitness Gurukul] New " + label + " — " + (name || phone || "lead");
    var lines = [
      "New lead received from the Fitness Gurukul website.",
      "",
      "Type: " + label,
      "Name: " + (name || ""),
      "Phone: " + (phone || ""),
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
      "Timestamp: " + String(data.timestamp || new Date().toISOString()),
      "",
      "Open your Fitness Gurukul Leads Google Sheet for the full row."
    ];

    MailApp.sendEmail({
      to: LEAD_NOTIFY_EMAILS.join(","),
      subject: subject,
      body: lines.join("\n"),
      replyTo: String(data.email || LEAD_NOTIFY_EMAILS[0])
    });
    return true;
  } catch (err) {
    console.error("Lead email failed: " + (err && err.message ? err.message : err));
    return false;
  }
}

function leadLabel_(formType) {
  if (formType === "transformation_challenge" || formType === "challenge_leads") return "challenge lead";
  if (formType === "corporate_event" || formType === "corporate_events") return "corporate inquiry";
  return "consultation lead";
}

function parseBody_(e) {
  if (!e) return {};
  if (e.postData && e.postData.contents) {
    var raw = String(e.postData.contents || "").trim();
    if (!raw) return e.parameter || {};
    try {
      return JSON.parse(raw);
    } catch (err) {
      return e.parameter || {};
    }
  }
  return e.parameter || {};
}

function getOrCreateSheet_(tabName) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) {
    throw new Error("Open this script from a Google Sheet (Extensions → Apps Script).");
  }
  var sheet = ss.getSheetByName(tabName);
  if (!sheet) sheet = ss.insertSheet(tabName);
  return sheet;
}

function ensureHeaders_(sheet) {
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(HEADERS);
    sheet.setFrozenRows(1);
    return;
  }
  var first = sheet.getRange(1, 1, 1, HEADERS.length).getValues()[0];
  if (String(first[0] || "") !== HEADERS[0]) {
    sheet.insertRowBefore(1);
    sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
    sheet.setFrozenRows(1);
  }
}

function json_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
