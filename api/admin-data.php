<?php
require __DIR__ . "/bootstrap.php";

if ($_SERVER["REQUEST_METHOD"] !== "GET") {
  fg_json_out(["error" => "Method not allowed"], 405);
}

fg_require_admin($config);
$rows = fg_load_submissions($storeFile);

fg_json_out([
  "ok" => true,
  "engine" => "hostinger-php",
  "database" => "api/data/submissions.json",
  "submissionCount" => count($rows),
  "submissions" => $rows,
  "leads" => array_map(function ($row) {
    return [
      "name" => $row["name"] ?? "",
      "phone" => $row["phone"] ?? "",
      "goal" => $row["goal"] ?? "",
      "program" => $row["program"] ?? "",
      "message" => $row["message"] ?? "",
      "created_at" => $row["created_at"] ?? null,
    ];
  }, $rows),
]);
