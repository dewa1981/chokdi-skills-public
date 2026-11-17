#!/usr/bin/env python3
"""One-shot: reset a Flarum user's password via direct DB update, safely.
Usage (inside the php container): docker exec php php /tmp/flarum_reset_pw.php <user_id> <newpass>
Then verify by logging in with the CSRF flow.
"""
import sys, json, os

def main():
    if len(sys.argv) != 3:
        print("usage: flarum_reset_pw.php <user_id> <newpass>")
        sys.exit(1)
    uid, newpass = sys.argv[1], sys.argv[2]
    # read config.php (PHP file) — parse the return array
    cfg_path = "/var/www/html/forum.sayasuka99.com/config.php"
    # config.php is PHP; parse via regex for the database array
    txt = open(cfg_path).read()
    def grab(key):
        m = __import__("re").search(r"'" + key + r"'\s*=>\s*'([^']*)'", txt)
        return m.group(1) if m else None
    db, user, pw = grab("database"), grab("username"), grab("password")
    host, port = "mysql", 3306
    print(f"target db={db} user={user}")
    import hashlib
    # This helper runs INSIDE the PHP container where PHP is available.
    # Compute the bcrypt hash using PHP itself to avoid any Python-vs-PHP salt mismatch:
    os.system(f'php -r "echo password_hash(\'{newpass}\', PASSWORD_BCRYPT, [\'cost\'=>10]);" > /tmp/.hash')
    with open("/tmp/.hash") as f:
        h = f.read().strip()
    print("hash computed (len", len(h), ")")
    # write a tiny PHP runner to do the UPDATE (avoids shell-quoting $ in hash)
    runner = f"""<?php
$pdo = new PDO('mysql:host={host};dbname={db};charset=utf8mb4', '{user}', '{pw}');
$stmt = $pdo->prepare('UPDATE flarum_users SET password = ? WHERE id = {uid}');
$stmt->execute(['{h}']);
echo password_verify('{newpass}', $pdo->query('SELECT password FROM flarum_users WHERE id={uid}')->fetchColumn()) ? 'VERIFY_OK' : 'VERIFY_FAIL';
"""
    open("/tmp/flarum_pw_runner.php", "w").write(runner)
    os.system("php /tmp/flarum_pw_runner.php")

if __name__ == "__main__":
    main()
