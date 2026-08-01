#!/usr/bin/env python3
"""Patch live nginx for gzip + security headers (keeps Certbot SSL blocks)."""
from pathlib import Path
import re

NGINX = Path("/etc/nginx/nginx.conf")
SITE = Path("/etc/nginx/sites-enabled/safastyle")

nginx = NGINX.read_text()
if "font/woff2" in nginx:
    print("nginx.conf already has gzip_types")
else:
    pattern = re.compile(r"\tgzip on;\n\n(?:\t# gzip_[^\n]*\n)+", re.M)
    replacement = (
        "\tgzip on;\n"
        "\tgzip_vary on;\n"
        "\tgzip_proxied any;\n"
        "\tgzip_comp_level 5;\n"
        "\tgzip_min_length 256;\n"
        "\tgzip_types\n"
        "\t\ttext/plain\n"
        "\t\ttext/css\n"
        "\t\ttext/javascript\n"
        "\t\tapplication/javascript\n"
        "\t\tapplication/json\n"
        "\t\tapplication/xml\n"
        "\t\timage/svg+xml\n"
        "\t\tfont/woff2\n"
        "\t\tapplication/font-woff2;\n"
    )
    new, n = pattern.subn(replacement, nginx, count=1)
    if n != 1:
        raise SystemExit(f"Could not patch gzip block (n={n})")
    NGINX.write_text(new)
    print("Patched nginx.conf gzip")

site = SITE.read_text()
if "gzip_static on" in site and "Strict-Transport-Security" in site:
    print("site already patched")
else:
    needle = (
        "    location /static/ {\n"
        "        alias /var/www/safastyle/staticfiles/;\n"
        "        expires 30d;\n"
        '        add_header Cache-Control "public, immutable";\n'
        "    }"
    )
    repl = (
        "    add_header X-Content-Type-Options nosniff always;\n"
        "    add_header X-Frame-Options DENY always;\n"
        '    add_header Referrer-Policy "strict-origin-when-cross-origin" always;\n'
        '    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;\n'
        "\n"
        "    location /static/ {\n"
        "        alias /var/www/safastyle/staticfiles/;\n"
        "        expires 30d;\n"
        '        add_header Cache-Control "public, immutable";\n'
        "        access_log off;\n"
        "        gzip_static on;\n"
        "    }"
    )
    if needle not in site:
        raise SystemExit("static location block not found in site config")
    SITE.write_text(site.replace(needle, repl, 1))
    print("Patched sites-enabled/safastyle")

print("OK")
