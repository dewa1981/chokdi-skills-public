# Flarum password reset via direct DB (PHP container)

Flarum (forum.sayasuka99.com, Flarum 2.0, Docker `nginx` + `php` (PHP 8.4) on
163.61.44.61, nginx vhost fastcgi_pass `unix:/run/php/php-fpm.sock` = the `php`
container's socket — NOT `/run/php74`).

## Reset password without mail/token flow
```php
<?php
// run inside the php container: docker exec php php /tmp/reset.php
$newpass = 'NEWPASS';
$pdo = new PDO('mysql:host=mysql;dbname=forum_sayasuka99_com;charset=utf8mb4',
               'a87bfef5', 'DBPASS');   // from config.php
$hash = password_hash($newpass, PASSWORD_BCRYPT, ['cost' => 10]);
$stmt = $pdo->prepare("UPDATE flarum_users SET password = ? WHERE id = 1");
$stmt->execute([$hash]);
echo password_verify($newpass, $pdo->query("SELECT password FROM flarum_users WHERE id=1")->fetchColumn()) ? "OK\n" : "FAIL\n";
```
- **NEVER do this via shell one-liners with the hash inline** — the `$` chars of a
  bcrypt hash get eaten by the shell/quoting layers and the UPDATE silently writes an
  EMPTY/truncated password (symptom: `SELECT password` returns empty string, all logins
  401). Always compute + write inside a PHP file.
- Config: DB creds in `<forum>/config.php` (`database` array). DB user `a87bfef5`,
  password is stored PLAINTEXT in config.php.

## Login debugging notes (Flarum)
- CSRF flow: `GET /` HTML embeds `csrfToken":"..."`; login is
  `POST /login` form-urlencoded with `identification, password, remember, csrfToken`
  (+ `X-Requested-With: XMLHttpRequest`, `Origin`/`Referer` same-site), cookie jar
  required. 200 → `{"token":"...","userId":1}`.
- 400 + "You have been inactive for too long" = CSRF/session mismatch — see
  `cf-cache-breaks-login.md` (CF Cache Everything was the cause).
- "Your login details were incorrect" = credentials only.
- Session files: `storage/sessions/` (PHP file sessions, `gc_maxlifetime` 1440).
- Logs: `storage/logs/flarum-YYYY-MM-DD.log` (only written when debug/errors fire).

## This file's origin
Session 2026-08-10: login broken for months; reset password repeatedly via shell
(which silently nulled the hash), root cause was actually CF cache rule; fixed by user
disabling Cache Everything + Purge Everything. Backups made first:
`/opt/backup_forum/forum_db_clean_<ts>.sql` (mysqldump --no-tablespaces — plain
mysqldump needs PROCESS privilege) + `forum_files_<ts>.tar.gz`.
