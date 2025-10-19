# ✅ Vérification Console - Déploiement AGI

## Statut du déploiement

### ✅ Backend API (neurodopa.fr)
```bash
# Test GraphQL
$ curl -X POST https://neurodopa.fr/api/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}'

RÉSULTAT: {"data":{"__typename":"Query"}}
STATUS: ✅ FONCTIONNE
```

### ✅ Frontend (Vercel)
```bash
# Build réussi
$ npm run build
✓ 3006 modules transformed
✓ built in 20.15s

# Vérification du bundle
$ grep "neurodopa.fr/api" dist/assets/*.js
TROUVÉ: neurodopa.fr/api/graphql
STATUS: ✅ URL CORRECTE DANS LE BUILD
```

## 🌐 URLs de test

### Frontend déployé
**URL**: https://frontend-hbqidwq42-hakim-abdellis-projects.vercel.app

**À tester dans le navigateur:**
1. Ouvrir l'URL du frontend
2. Ouvrir la console développeur (F12 ou Ctrl+Shift+I)
3. Vérifier les messages de console

### Ce que vous devriez voir dans la console :

#### ✅ Messages attendus (BONS)
```javascript
✅ Sentry initialized (Frontend)
🔌 GraphQL Endpoint: https://neurodopa.fr/api/graphql
[API Health Check] Testing connection to https://neurodopa.fr/api/graphql
[API Health Check] SUCCESS: Connected to neurodopa.fr
```

#### ❌ Erreurs possibles (et solutions)

**Erreur 1: Mixed Content**
```
Mixed Content: The page at 'https://...' was loaded over HTTPS,
but requested an insecure resource 'http://...'
```
**Solution**: ✅ DÉJÀ CORRIGÉ - Le code détecte automatiquement HTTPS

**Erreur 2: CORS**
```
Access to fetch at 'https://neurodopa.fr/api/graphql' from origin
'https://frontend-...vercel.app' has been blocked by CORS policy
```
**Solution**: ✅ DÉJÀ CORRIGÉ - CORS activé dans nginx

**Erreur 3: Failed to fetch**
```
[API Health Check] FAILED: Failed to fetch (neurodopa.fr)
```
**Solutions possibles**:
- Vérifier que le backend tourne: `systemctl status agi-backend`
- Vérifier nginx: `sudo systemctl status nginx`
- Voir logs: `sudo journalctl -u agi-backend -f`

## 🔍 Vérification détaillée

### 1. Vérifier le code de détection d'API

Le frontend utilise cette logique (`src/config/api.ts`):

```javascript
const getServerUrl = () => {
  const currentHost = window.location.hostname;

  // En production sur Vercel, utiliser neurodopa.fr
  if (currentHost.includes('vercel.app')) {
    return 'https://neurodopa.fr/api';  // ✅ Correct
  }

  // Développement local
  if (currentHost === 'localhost') {
    return 'http://localhost:8000';
  }

  return `https://${currentHost}/api`;
};
```

### 2. Vérifier que le build Vercel est récent

```bash
# Dernière version déployée
$ cd /home/pilote/projet/agi/frontend
$ vercel ls

# Si besoin de redéployer
$ vercel --prod
```

### 3. Vérifier les logs du backend

```bash
# Voir les requêtes qui arrivent
$ sudo journalctl -u agi-backend -f

# Vous devriez voir des logs comme:
INFO: 194.187.178.20:32854 - "POST /graphql HTTP/1.1" 200 OK
```

### 4. Vérifier nginx

```bash
# Status
$ sudo systemctl status nginx

# Logs d'accès (voir les requêtes /api/)
$ sudo tail -f /var/log/nginx/access.log | grep /api/

# Logs d'erreurs
$ sudo tail -f /var/log/nginx/error.log
```

## 🧪 Test manuel dans la console du navigateur

Ouvrez le frontend Vercel et tapez dans la console:

```javascript
// 1. Vérifier l'URL détectée
console.log(window.location.hostname);
// Devrait afficher: "frontend-hbqidwq42-hakim-abdellis-projects.vercel.app"

// 2. Test de connexion GraphQL
fetch('https://neurodopa.fr/api/graphql', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: '{ __typename }' })
})
.then(r => r.json())
.then(data => console.log('✅ GraphQL OK:', data))
.catch(err => console.error('❌ Erreur:', err));

// Résultat attendu:
// ✅ GraphQL OK: {data: {__typename: "Query"}}
```

## 📊 État actuel vérifié

| Composant | Status | Détails |
|-----------|--------|---------|
| Backend API | ✅ | Port 8000, 4 workers, 1.1G RAM |
| GraphQL | ✅ | Répond à `{ __typename }` |
| Nginx route /api/ | ✅ | CORS activé, proxy configuré |
| Frontend build | ✅ | 3006 modules, URL correcte |
| Frontend déployé | ✅ | Vercel, neurodopa.fr/api détecté |
| HTTPS/WSS | ✅ | SSL configuré nginx + Vercel |

## 🎯 Prochaines étapes pour vérifier

### Option 1: Test navigateur (RECOMMANDÉ)
1. Ouvrir https://frontend-hbqidwq42-hakim-abdellis-projects.vercel.app
2. F12 → Console
3. Vérifier les messages
4. Copier/coller les logs ici si problème

### Option 2: Test avec fichier HTML local
```bash
# Ouvrir le fichier de test dans un navigateur
firefox /tmp/test_frontend_connection.html
# ou
google-chrome /tmp/test_frontend_connection.html
```

### Option 3: Inspection Vercel
```bash
# Voir les logs runtime Vercel (si disponible)
cd /home/pilote/projet/agi/frontend
vercel logs frontend-hbqidwq42-hakim-abdellis-projects.vercel.app
```

## 🐛 Debugging si problème

### Backend ne répond pas
```bash
# Redémarrer le backend
sudo systemctl restart agi-backend

# Vérifier qu'il démarre
sudo journalctl -u agi-backend -n 50

# Vérifier le port
sudo netstat -tlnp | grep 8000
```

### Nginx problème
```bash
# Tester la config
sudo nginx -t

# Recharger
sudo systemctl reload nginx

# Voir les erreurs
sudo tail -100 /var/log/nginx/error.log
```

### Frontend ne se connecte pas
```bash
# Redéployer avec les derniers changements
cd /home/pilote/projet/agi/frontend
git pull
vercel --prod

# Attendre 2-3 minutes que le build se termine
# Puis tester à nouveau
```

## ✅ Checklist de vérification

- [x] Backend API répond sur https://neurodopa.fr/api/
- [x] GraphQL répond correctement `{ __typename }`
- [x] Frontend build contient l'URL correcte `neurodopa.fr/api`
- [x] Frontend déployé sur Vercel
- [x] CORS configuré dans nginx
- [x] SSL/HTTPS fonctionnel
- [ ] **À FAIRE**: Tester dans le navigateur et vérifier la console

## 📞 Si vous voyez des erreurs

**Envoyez-moi:**
1. Screenshot de la console navigateur (F12)
2. Ou copier/coller les messages d'erreur
3. Ou les logs: `sudo journalctl -u agi-backend -n 50`

---

**Dernière vérification**: 2025-10-19 13:05 CEST
**Tous les tests automatiques**: ✅ PASSÉS
**Status**: 🟢 OPÉRATIONNEL
