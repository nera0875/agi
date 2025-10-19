#!/bin/bash
# One-liner pour ajouter la route /api/ à nginx
# Exécutez: bash INSTALL_NGINX_ROUTE.sh

echo "🔧 Installation de la route /api/ dans nginx..."

# Créer un fichier temporaire avec la route à insérer
cat > /tmp/agi_api_route.conf << 'ROUTE_EOF'

    # AGI GraphQL API (Time Blocking System)
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
ROUTE_EOF

# Vérifier si la route existe déjà
if sudo grep -q "location /api/" /etc/nginx/sites-enabled/neurodopa.fr; then
    echo "✅ La route /api/ existe déjà!"
    exit 0
fi

# Backup
echo "📦 Création du backup..."
sudo cp /etc/nginx/sites-enabled/neurodopa.fr /etc/nginx/sites-enabled/neurodopa.fr.backup-$(date +%Y%m%d-%H%M%S)

# Insérer la route AVANT "location / {" (dernière occurrence)
echo "✏️  Insertion de la route..."
sudo sed -i '/^    location \/ {$/e cat /tmp/agi_api_route.conf' /etc/nginx/sites-enabled/neurodopa.fr

# Test
echo "🧪 Test de la configuration..."
if sudo nginx -t; then
    echo "✅ Configuration valide!"
    echo "🔄 Rechargement de nginx..."
    sudo systemctl reload nginx
    echo "🎉 Installation terminée!"
    echo ""
    echo "L'API est maintenant accessible sur:"
    echo "  https://neurodopa.fr/api/"
    echo "  https://neurodopa.fr/api/graphql"
else
    echo "❌ Erreur de configuration!"
    echo "Restauration du backup..."
    sudo cp /etc/nginx/sites-enabled/neurodopa.fr.backup-$(date +%Y%m%d-%H%M%S) /etc/nginx/sites-enabled/neurodopa.fr
    exit 1
fi
