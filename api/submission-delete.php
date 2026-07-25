<?php
require __DIR__ . "/bootstrap.php";

if ($_SERVER["REQUEST_METHOD"] !== "POST" && $_SERVER["REQUEST_METHOD"] !== "DELETE") {
  fg_json_out(["error" => "Method not allowed"], 405);
}

fg_require_admin($config);
$payload = fg_read_json_body();
$id = fg_clip($payload["id"] ?? ($_GET["id"] ?? ""), 64);
if ($id === "") {
  fg_json_out(["error" => "Missing id"], 400);
}

$rows = fg_load_submissions($storeFile);
$next = array_values(array_filter($rows, function ($row) use ($id) {
  return ($row["id"] ?? "") !== $id;
}));

if (count($next) === count($rows)) {
  fg_json_out(["error" => "Not found"], 404);
}

fg_save_submissions($storeFile, $next);
fg_json_out(["ok" => true, "id" => $id]);
