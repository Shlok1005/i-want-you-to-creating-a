/**
 * Fitness Gurukul — Google Sheet lead collector + email
 *
 * SETUP (once):
 * 1. Open your Google Sheet → Extensions → Apps Script
 * 2. Paste THIS ENTIRE file → Save
 * 3. Select function testSetup → Run → click Allow
 * 4. Deploy → New deployment → Web app
 *    - Execute as: Me
 *    - Who has access: Anyone
 * 5. Copy the /exec URL into the website (app.js)
 *
 * After edits: Deploy → Manage deployments → pencil → New version → Deploy
 */

var EMAILS = [
  "contact@fitnessgurukul.co.in",
  "fitnessgurukul01@gmail.com"
];

/** Optional: paste Sheet ID from the Sheet URL (/d/SHEET_ID/edit). Leave blank if script is bound to the Sheet. */
var SPREADSHEET_ID = "";

/** Run this once from the Apps Script editor to grant Sheets + Gmail permission. */
function testSetup() {
  var ss = getSpreadsheet_();
  var sheet = getSheet_(ss, "Consultations");
  ensureHeader_(sheet);
  MailApp.sendEmail({
    to: EMAILS.join(","),
    subject: "[Fitness Gurukul] Apps Script setup OK",
    body: "Lead collector is authorized.\nSheet: " + ss.getUrl()
  });
  Logger.log("Setup OK: " + ss.getUrl());
}

function doGet(e) {
  var params = (e && e.parameter) || {};
  // Primary path: website + /api/submit use GET write (POST /exec is unreliable).
  if (params.write === "1" || (params.name && params.phone)) {
    return handleLead_(params);
  }
  return json_({
    ok: true,
    service: "Fitness Gurukul Leads",
    hint: "Send name+phone (GET or POST) to save a lead"
  });
}

function doPost(e) {
  try {
    return handleLead_(parseBody_(e));
  } catch (err) {
    return json_({ ok: false, error: String(err && err.message ? err.message : err) });
  }
}

function handleLead_(data) {
  data = data || {};
  var formType = String(data.form_type || "consultation").trim() || "consultation";
  var name = String(data.name || data.contact_name || "").trim();
  var phone = String(data.phone || "").trim();

  if (!name || !phone) {
    return json_({ ok: false, error: "name and phone required" });
  }

  var ss = getSpreadsheet_();
  var tab = sheetTab_(formType);
  var sheet = getSheet_(ss, tab);
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
  if (String(formType).indexOf("challenge") >= 0) return "Challenge";
  if (String(formType).indexOf("corporate") >= 0) return "Corporate";
  return "Consultations";
}

function getSpreadsheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  if (ss) return ss;
  if (SPREADSHEET_ID) return SpreadsheetApp.openById(SPREADSHEET_ID);
  throw new Error(
    "No spreadsheet bound. Open Apps Script from the Sheet (Extensions → Apps Script), or set SPREADSHEET_ID in Code.gs"
  );
}

function getSheet_(ss, tabName) {
  return ss.getSheetByName(tabName) || ss.insertSheet(tabName);
}

function ensureHeader_(sheet) {
  if (sheet.getLastRow() > 0) return;
  sheet.appendRow([
    "Timestamp", "Form Type", "Name", "Phone", "Email", "Program", "Goal", "Message",
    "Coach", "Company", "Contact Name", "Event Type", "Attendees", "Preferred Date",
    "Budget", "Location", "Source"
  ]);
  sheet.setFrozenRows(1);
}

function sendLeadEmail_(data, formType, name, phone) {
  try {
    var label = String(formType).indexOf("challenge") >= 0
      ? "challenge lead"
      : (String(formType).indexOf("corporate") >= 0 ? "corporate inquiry" : "consultation lead");

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
