<?php
header("X-Content-Type-Options: nosniff");

$config = require __DIR__ . "/config.php";
$dataDir = __DIR__ . "/data";
$storeFile = $dataDir . "/submissions.json";

if (!is_dir($dataDir)) {
  mkdir($dataDir, 0755, true);
}
if (!is_file($storeFile)) {
  file_put_contents($storeFile, "[]", LOCK_EX);
}

function fg_json_out($payload, $status = 200) {
  http_response_code($status);
  header("Content-Type: application/json; charset=utf-8");
  header("Cache-Control: no-store");
  echo json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
  exit;
}

function fg_read_json_body() {
  $raw = file_get_contents("php://input");
  if ($raw === false || $raw === "") {
    return $_POST ?: [];
  }
  $decoded = json_decode($raw, true);
  if (is_array($decoded)) {
    return $decoded;
  }
  // FormData / x-www-form-urlencoded fallback
  if (!empty($_POST)) {
    return $_POST;
  }
  $parsed = [];
  parse_str($raw, $parsed);
  return is_array($parsed) ? $parsed : [];
}

function fg_clip($value, $max) {
  $text = trim((string) $value);
  if (function_exists("mb_substr")) {
    return mb_substr($text, 0, $max);
  }
  return substr($text, 0, $max);
}

function fg_load_submissions($storeFile) {
  $raw = @file_get_contents($storeFile);
  $rows = json_decode($raw !== false ? $raw : "[]", true);
  return is_array($rows) ? $rows : [];
}

function fg_save_submissions($storeFile, $rows) {
  $ok = file_put_contents(
    $storeFile,
    json_encode(array_values($rows), JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
    LOCK_EX
  );
  return $ok !== false;
}

function fg_admin_token_from_request() {
  $header = $_SERVER["HTTP_X_ADMIN_TOKEN"] ?? "";
  if ($header) {
    return trim($header);
  }
  $auth = $_SERVER["HTTP_AUTHORIZATION"] ?? ($_SERVER["REDIRECT_HTTP_AUTHORIZATION"] ?? "");
  if (stripos($auth, "Bearer ") === 0) {
    return trim(substr($auth, 7));
  }
  return trim((string) ($_GET["token"] ?? ""));
}

function fg_require_admin($config) {
  $provided = fg_admin_token_from_request();
  $expected = (string) ($config["admin_token"] ?? "");
  if ($expected === "" || !hash_equals($expected, $provided)) {
    fg_json_out(["error" => "Unauthorized"], 401);
  }
}

function fg_save_submission($storeFile, $payload) {
  $formType = fg_clip($payload["form_type"] ?? "consultation", 64) ?: "consultation";
  $name = fg_clip($payload["name"] ?? ($payload["contact_name"] ?? ""), 120);
  $phone = fg_clip($payload["phone"] ?? "", 40);
  $email = fg_clip($payload["email"] ?? "", 160);
  $program = fg_clip($payload["program"] ?? "", 120);
  $goal = fg_clip($payload["goal"] ?? "", 200);
  $message = fg_clip($payload["message"] ?? "", 2000);
  $coach = fg_clip($payload["coach"] ?? "", 120);
  $company = fg_clip($payload["company"] ?? "", 160);
  $eventType = fg_clip($payload["event_type"] ?? "", 120);
  $attendees = fg_clip($payload["attendees"] ?? "", 80);
  $preferredDate = fg_clip($payload["preferred_date"] ?? "", 80);
  $budget = fg_clip($payload["budget"] ?? "", 80);
  $location = fg_clip($payload["location"] ?? "", 160);

  if ($formType === "corporate_event") {
    $missing = [];
    foreach ([
      "company" => $company,
      "contact_name" => $name,
      "email" => $email,
      "phone" => $phone,
      "event_type" => $eventType,
      "attendees" => $attendees,
    ] as $field => $value) {
      if ($value === "") {
        $missing[] = $field;
      }
    }
    if ($missing) {
      return [null, $missing];
    }
  } else {
    $missing = [];
    foreach ([
      "name" => $name,
      "phone" => $phone,
      "program" => $program,
      "goal" => $goal,
    ] as $field => $value) {
      if ($value === "") {
        $missing[] = $field;
      }
    }
    if ($missing) {
      return [null, $missing];
    }
  }

  $id = bin2hex(random_bytes(16));
  $row = [
    "id" => $id,
    "form_type" => $formType,
    "name" => $name,
    "phone" => $phone,
    "email" => $email,
    "program" => $program,
    "goal" => $goal,
    "message" => $message,
    "coach" => $coach,
    "company" => $company,
    "event_type" => $eventType,
    "attendees" => $attendees,
    "preferred_date" => $preferredDate,
    "budget" => $budget,
    "location" => $location,
    "status" => "new",
    "created_at" => time(),
    "source" => "hostinger-php",
  ];

  $rows = fg_load_submissions($storeFile);
  array_unshift($rows, $row);
  if (!fg_save_submissions($storeFile, $rows)) {
    return [null, ["storage"]];
  }
  return [$id, null];
}
