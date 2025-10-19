# 🚀 Déploiement AGI - Résumé

## ✅ Ce qui a été fait

### 1. **Backend (VPS neurodopa.fr)**
- ✅ Backend AGI déjà en cours d'exécution sur le port 8000
- ✅ Service systemd `agi-backend.service` actif avec 4 workers
- ✅ Configuration nginx préparée pour router `/api/` vers le backend
- ✅ Script d'update automatique créé : `update_nginx.sh`

### 2. **Frontend (Vercel)**
- ✅ Déployé sur Vercel : https://frontend-1vnj333ps-hakim-abdellis-projects.vercel.app
- ✅ Configuration `.env.production` avec URL backend HTTPS
- ✅ `vercel.json` configuré avec SPA rewrites et cache headers
- ✅ GraphQL endpoint: `https://neurodopa.fr/api/graphql`
- ✅ WebSocket endpoint: `wss://neurodopa.fr/api/graphql`

## 📋 Étapes restantes à faire MANUELLEMENT

### Étape 1 : Activer la route nginx pour l'API

Exécutez le script d'update nginx :

```bash
cd /home/pilote/projet/agi
./update_nginx.sh
```

Ce script va :
1. Créer un backup de votre config nginx
2. Ajouter la route `/api/` qui proxy vers `http://127.0.0.1:8000`
3. Tester la configuration nginx
4. Recharger nginx si tout est OK

**OU manuellement :**

```bash
# Éditer la config nginx
sudo nano /etc/nginx/sites-enabled/neurodopa.fr

# Ajouter AVANT la ligne "location / {" (ligne ~406) :
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

# Tester et recharger
sudo nginx -t
sudo systemctl reload nginx
```

### Étape 2 : Vérifier que tout fonctionne

```bash
# Vérifier que l'API répond
curl https://neurodopa.fr/api/

# Vérifier le backend
systemctl status agi-backend

# Vérifier nginx
sudo nginx -t
systemctl status nginx
```

## 🌐 URLs finales

- **Frontend (Vercel):** https://frontend-1vnj333ps-hakim-abdellis-projects.vercel.app
- **Backend API:** https://neurodopa.fr/api/
- **GraphQL Endpoint:** https://neurodopa.fr/api/graphql
- **GraphQL Playground:** https://neurodopa.fr/api/graphql (GET request in browser)

## 🔧 Architecture

```
┌─────────────────┐
│  Vercel         │
│  (Frontend)     │
│  React + Vite   │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────────────┐
│  neurodopa.fr (VPS)     │
│  ┌────────────────┐     │
│  │  Nginx         │     │
│  │  - /api/ →     │     │
│  │    port 8000   │     │
│  └────┬───────────┘     │
│       │                 │
│  ┌────▼───────────┐     │
│  │  FastAPI       │     │
│  │  GraphQL       │     │
│  │  Port 8000     │     │
│  │  4 workers     │     │
│  └────┬───────────┘     │
│       │                 │
│  ┌────▼───────────┐     │
│  │  PostgreSQL    │     │
│  │  + pgvector    │     │
│  └────────────────┘     │
└─────────────────────────┘
```

## ⚠️ Notes importantes

1. Le backend tourne déjà sur le VPS (port 8000)
2. Nginx doit être mis à jour pour router `/api/` vers le backend
3. Le frontend est déjà déployé et configuré pour utiliser HTTPS
4. CORS est déjà configuré dans la route nginx

## 🐛 Troubleshooting

Si l'API ne répond pas après l'update nginx :

```bash
# Vérifier les logs nginx
sudo tail -f /var/log/nginx/error.log

# Vérifier les logs du backend
sudo journalctl -u agi-backend -f

# Vérifier que le backend écoute bien
sudo netstat -tlnp | grep 8000

# Redémarrer le backend si nécessaire
sudo systemctl restart agi-backend
```

## 📞 Support

- Logs frontend Vercel : https://vercel.com/hakim-abdellis-projects/frontend
- Backend VPS : `sudo journalctl -u agi-backend`
- Nginx VPS : `sudo tail -f /var/log/nginx/error.log`
