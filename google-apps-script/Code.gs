/**
 * Fitness Gurukul — Google Sheets lead collector
 *
 * Setup:
 * 1. Create a Google Sheet named "Fitness Gurukul Leads" (or any name).
 * 2. Extensions → Apps Script → paste this file → Save.
 * 3. Deploy → New deployment → Type: Web app
 *    - Execute as: Me
 *    - Who has access: Anyone
 * 4. Copy the /exec URL (not /dev) into the website as FG_GOOGLE_SCRIPT_URL.
 *
 * Sheet tabs are created automatically: Consultations, Challenge, Corporate, Other.
 */

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

    return json_({ ok: true, success: true, form_type: formType });
  } catch (err) {
    return json_({ ok: false, error: String(err && err.message ? err.message : err) });
  }
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
