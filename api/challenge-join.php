<?php
require __DIR__ . "/bootstrap.php";

if ($_SERVER["REQUEST_METHOD"] !== "POST") {
  fg_json_out(["error" => "Method not allowed"], 405);
}

$payload = fg_read_json_body();
$challengeId = fg_clip($payload["challengeId"] ?? ($payload["challenge"] ?? ""), 80);
$challengeName = $challengeId !== "" ? $challengeId : "Transformation Challenge";

$join = [
  "form_type" => "challenge-join",
  "name" => $payload["name"] ?? "",
  "phone" => $payload["phone"] ?? "",
  "email" => $payload["email"] ?? "",
  "program" => $challengeName,
  "goal" => $payload["goal"] ?? "transformation",
  "message" => $payload["message"] ?? ("Joined challenge: " . $challengeName),
  "coach" => "",
];

list($id, $missing) = fg_save_submission($storeFile, $join);
if ($missing) {
  fg_json_out(["ok" => false, "error" => "Missing fields", "missing" => $missing], 400);
}

$rows = fg_load_submissions($storeFile);
$joined = 0;
foreach ($rows as $row) {
  if (($row["form_type"] ?? "") === "challenge-join") {
    $joined++;
  }
}

fg_json_out([
  "ok" => true,
  "message" => "You are in. A coach will reach out soon.",
  "id" => $id,
  "challenge" => ["id" => $challengeId, "name" => $challengeName],
  "stats" => ["totalJoined" => $joined],
  "engine" => "hostinger-php",
], 201);
