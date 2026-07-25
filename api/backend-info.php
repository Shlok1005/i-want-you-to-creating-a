<?php
require __DIR__ . "/bootstrap.php";

fg_json_out([
  "ok" => true,
  "engine" => "hostinger-php",
  "mode" => "hostinger",
  "localDefaultPassword" => true,
  "hint" => "Use the owner password from api/config.php (default: fitnessgurukul). Change it after first login.",
  "database" => "api/data/submissions.json",
]);
