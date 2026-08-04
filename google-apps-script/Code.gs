/**
 * PASTE THIS ENTIRE FILE into Google Apps Script, then:
 * 1) Save
 * 2) Deploy → New deployment → Web app
 * 3) Execute as: Me
 * 4) Who has access: Anyone
 * 5) Copy the /exec URL into the website (app.js / GOOGLE_SCRIPT_URL)
 *
 * Emails every lead to:
 *   contact@fitnessgurukul.co.in
 *   fitnessgurukul01@gmail.com
 */

var EMAILS = ["contact@fitnessgurukul.co.in", "fitnessgurukul01@gmail.com"];

function doGet() {
  return ContentService
    .createTextOutput(JSON.stringify({ ok: true, service: "Fitness Gurukul Leads" }))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  try {
    var data = {};
    if (e && e.postData && e.postData.contents) {
      try { data = JSON.parse(e.postData.contents); } catch (err) { data = e.parameter || {}; }
    } else {
      data = (e && e.parameter) || {};
    }

    var formType = String(data.form_type || "consultation");
    var name = String(data.name || data.contact_name || "").trim();
    var phone = String(data.phone || "").trim();
    if (!name || !phone) {
      return json_({ ok: false, error: "name and phone required" });
    }

    var ss = SpreadsheetApp.getActiveSpreadsheet();
    if (!ss) throw new Error("Open from a Google Sheet (Extensions → Apps Script)");

    var tab = "Consultations";
    if (formType.indexOf("challenge") >= 0) tab = "Challenge";
    if (formType.indexOf("corporate") >= 0) tab = "Corporate";

    var sheet = ss.getSheetByName(tab) || ss.insertSheet(tab);
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(["Timestamp","Form Type","Name","Phone","Email","Program","Goal","Message","Coach","Company","Event Type","Location","Source"]);
      sheet.setFrozenRows(1);
    }

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
      String(data.event_type || ""),
      String(data.location || ""),
      String(data.source || "")
    ]);

    var emailed = false;
    try {
      MailApp.sendEmail({
        to: EMAILS.join(","),
        subject: "[Fitness Gurukul] New lead — " + name,
        body: [
          "New website lead",
          "Type: " + formType,
          "Name: " + name,
          "Phone: " + phone,
          "Email: " + String(data.email || ""),
          "Program: " + String(data.program || ""),
          "Goal: " + String(data.goal || ""),
          "Coach: " + String(data.coach || ""),
          "Company: " + String(data.company || ""),
          "Event: " + String(data.event_type || ""),
          "Location: " + String(data.location || ""),
          "Message: " + String(data.message || ""),
          "Source: " + String(data.source || "")
        ].join("\n"),
        replyTo: String(data.email || EMAILS[0])
      });
      emailed = true;
    } catch (mailErr) {
      console.error(mailErr);
    }

    return json_({ ok: true, success: true, emailed: emailed, form_type: formType });
  } catch (err) {
    return json_({ ok: false, error: String(err.message || err) });
  }
}

function json_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
