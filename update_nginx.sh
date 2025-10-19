#!/bin/bash
# Script pour ajouter la route AGI API à nginx

echo "🔧 Mise à jour de la configuration nginx pour l'API AGI..."

# Backup
sudo cp /etc/nginx/sites-enabled/neurodopa.fr /etc/nginx/sites-enabled/neurodopa.fr.backup-$(date +%Y%m%d-%H%M%S)

# Ajouter la route /api/ avant la location / finale
sudo sed -i '/^    location \/ {$/i \    # AGI GraphQL API (Time Blocking System)\n    location /api/ {\n        proxy_pass http://127.0.0.1:8000/;\n        proxy_http_version 1.1;\n        proxy_set_header Host $host;\n        proxy_set_header X-Real-IP $remote_addr;\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto $scheme;\n\n        # CORS\n        add_header Access-Control-Allow-Origin * always;\n        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;\n        add_header Access-Control-Allow-Headers "Content-Type, Authorization, Content-Length" always;\n\n        if ($request_method = '\''OPTIONS'\'') {\n            add_header Access-Control-Allow-Origin * always;\n            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;\n            add_header Access-Control-Allow-Headers "Content-Type, Authorization, Content-Length" always;\n            add_header Content-Length 0;\n            return 204;\n        }\n    }\n' /etc/nginx/sites-enabled/neurodopa.fr

# Test de la configuration
echo "✅ Test de la configuration nginx..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Configuration valide ! Rechargement de nginx..."
    sudo systemctl reload nginx
    echo "✅ Nginx rechargé avec succès !"
    echo "🎉 L'API AGI est maintenant accessible sur https://neurodopa.fr/api/"
else
    echo "❌ Erreur de configuration ! Restauration du backup..."
    sudo cp /etc/nginx/sites-enabled/neurodopa.fr.backup-$(date +%Y%m%d-%H%M%S) /etc/nginx/sites-enabled/neurodopa.fr
    echo "❌ Configuration restaurée."
    exit 1
fi
