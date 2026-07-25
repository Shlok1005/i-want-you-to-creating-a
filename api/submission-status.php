<?php
require __DIR__ . "/bootstrap.php";

if ($_SERVER["REQUEST_METHOD"] !== "POST" && $_SERVER["REQUEST_METHOD"] !== "PATCH") {
  fg_json_out(["error" => "Method not allowed"], 405);
}

fg_require_admin($config);
$payload = fg_read_json_body();
$id = fg_clip($payload["id"] ?? ($_GET["id"] ?? ""), 64);
$status = fg_clip($payload["status"] ?? "", 32);
$allowed = ["new", "contacted", "qualified", "closed"];

if ($id === "" || !in_array($status, $allowed, true)) {
  fg_json_out(["error" => "Invalid id or status"], 400);
}

$rows = fg_load_submissions($storeFile);
$found = false;
foreach ($rows as &$row) {
  if (($row["id"] ?? "") === $id) {
    $row["status"] = $status;
    $found = true;
    break;
  }
}
unset($row);

if (!$found) {
  fg_json_out(["error" => "Not found"], 404);
}
fg_save_submissions($storeFile, $rows);
fg_json_out(["ok" => true, "id" => $id, "status" => $status]);
