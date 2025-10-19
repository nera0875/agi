#!/usr/bin/env python3
"""
Script pour injecter la route /api/ dans la configuration nginx
Nécessite les droits sudo
"""

import subprocess
import sys
from datetime import datetime

NGINX_CONFIG = "/etc/nginx/sites-enabled/neurodopa.fr"
BACKUP_SUFFIX = f".backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

ROUTE_TO_ADD = '''    # AGI GraphQL API (Time Blocking System)
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # CORS
        add_header Access-Control-Allow-Origin * always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization, Content-Length" always;

        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin * always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
            add_header Access-Control-Allow-Headers "Content-Type, Authorization, Content-Length" always;
            add_header Content-Length 0;
            return 204;
        }
    }

'''

def main():
    print("🔧 Mise à jour de la configuration nginx...")

    # 1. Lire le fichier actuel
    try:
        with open(NGINX_CONFIG, 'r') as f:
            content = f.read()
    except PermissionError:
        print("❌ Permission denied. Réessayez avec sudo:")
        print(f"   sudo python3 {sys.argv[0]}")
        sys.exit(1)

    # 2. Vérifier si la route existe déjà
    if 'location /api/' in content:
        print("✅ La route /api/ existe déjà dans la configuration nginx")
        return

    # 3. Backup
    backup_path = NGINX_CONFIG + BACKUP_SUFFIX
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"✅ Backup créé: {backup_path}")

    # 4. Trouver où insérer (avant "location / {")
    lines = content.split('\n')
    insert_index = -1

    for i, line in enumerate(lines):
        if line.strip() == 'location / {':
            insert_index = i
            break

    if insert_index == -1:
        print("❌ Impossible de trouver 'location / {' dans le fichier")
        sys.exit(1)

    # 5. Insérer la nouvelle route
    new_lines = lines[:insert_index] + ROUTE_TO_ADD.split('\n') + lines[insert_index:]
    new_content = '\n'.join(new_lines)

    # 6. Écrire le nouveau contenu
    with open(NGINX_CONFIG, 'w') as f:
        f.write(new_content)
    print("✅ Configuration mise à jour")

    # 7. Tester la configuration
    print("✅ Test de la configuration nginx...")
    result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)

    if result.returncode != 0:
        print("❌ Erreur de configuration nginx!")
        print(result.stderr)
        print("Restauration du backup...")
        with open(backup_path, 'r') as f:
            with open(NGINX_CONFIG, 'w') as out:
                out.write(f.read())
        print("❌ Configuration restaurée")
        sys.exit(1)

    print("✅ Configuration valide!")

    # 8. Recharger nginx
    print("✅ Rechargement de nginx...")
    result = subprocess.run(['systemctl', 'reload', 'nginx'], capture_output=True, text=True)

    if result.returncode != 0:
        print("❌ Erreur lors du rechargement de nginx!")
        print(result.stderr)
        sys.exit(1)

    print("✅ Nginx rechargé avec succès!")
    print("🎉 L'API AGI est maintenant accessible sur https://neurodopa.fr/api/")

if __name__ == '__main__':
    main()
