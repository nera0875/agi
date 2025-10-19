#!/bin/bash
# Install AGI Backend systemd service

set -e

echo "🚀 Installation du service AGI Backend systemd..."

# Copier le fichier service
echo "📋 Copie du fichier service..."
sudo cp /home/pilote/projet/agi/systemd/agi-backend.service /etc/systemd/system/

# Recharger systemd
echo "🔄 Rechargement de systemd..."
sudo systemctl daemon-reload

# Activer le service
echo "✅ Activation du service..."
sudo systemctl enable agi-backend

# Démarrer le service
echo "▶️  Démarrage du service..."
sudo systemctl start agi-backend

# Attendre 5 secondes
sleep 5

# Vérifier le statut
echo ""
echo "📊 Statut du service:"
sudo systemctl status agi-backend --no-pager -l

echo ""
echo "✅ Installation terminée!"
echo ""
echo "Commandes utiles:"
echo "  - Voir les logs:    journalctl -u agi-backend -f"
echo "  - Stopper:          sudo systemctl stop agi-backend"
echo "  - Redémarrer:       sudo systemctl restart agi-backend"
echo "  - Désactiver:       sudo systemctl disable agi-backend"
echo "  - Test API:         wget -qO- http://localhost:8000/health"
