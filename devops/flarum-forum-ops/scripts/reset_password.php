<?php
// Reset password Flarum user by ID — aman dari shell $ mangling (satu proses PHP).
// Usage: php reset_password.php <user_id> <new_password>
// Jalankan di dalam container php: docker cp + docker exec php php /tmp/reset_password.php 1 'Passw0rd!'
$id = (int)($argv[1] ?? 0);
$pw = $argv[2] ?? '';
if (!$id || strlen($pw) < 8) { fwrite(STDERR, "Usage: reset_password.php <user_id> <new_password>\n"); exit(1); }

$cfg = include '/var/www/html/forum.sayasuka99.com/config.php';
$db = $cfg['database'];
$pdo = new PDO(
    "mysql:host={$db['host']};dbname={$db['database']};charset=utf8mb4",
    $db['username'], $db['password']
);
$hash = password_hash($pw, PASSWORD_BCRYPT, ['cost' => 10]);
$st = $pdo->prepare("UPDATE flarum_users SET password = ? WHERE id = ?");
$st->execute([$hash, $id]);

// self-verify
$row = $pdo->query("SELECT password FROM flarum_users WHERE id = $id")->fetch(PDO::FETCH_ASSOC);
echo password_verify($pw, $row['password']) ? "OK password user $id ter-reset & terverifikasi\n" : "GAGAL verify\n";
