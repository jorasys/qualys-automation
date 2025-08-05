# 🚀 Guide de Démarrage Rapide - Qualys Automation v0.3

## Installation et Configuration (5 minutes)

### 1. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 2. Configurer les credentials
```bash
# Copier le fichier d'exemple
copy .env.example .env

# Éditer .env avec vos credentials Qualys
QUALYS_USERNAME=votre_nom_utilisateur
QUALYS_PASSWORD=votre_mot_de_passe
```

### 3. Initialiser la base de données
```bash
python scripts/init_db.py init
```

### 4. (Optionnel) Migrer les données existantes
Si vous avez des fichiers `scan_results.json` ou `selected_scans.json` :
```bash
python scripts/migrate_existing_data.py migrate
```

## 🎯 Lancement

### Utiliser la nouvelle version
```bash
python main_v03.py
```

### Workflow automatique
1. **Récupération** des scans depuis Qualys
2. **Sélection interactive** avec cases à cocher
3. **Génération** des rapports PDF/CSV
4. **Téléchargement automatique** dans Downloads

## 🔧 Scripts Utilitaires

### Gestion de la base de données
```bash
# Voir les informations de la DB
python scripts/init_db.py info

# Réinitialiser la DB (supprime tout)
python scripts/init_db.py reset
```

### Migration des données
```bash
# Voir le statut de la migration
python scripts/migrate_existing_data.py status
```

### 🆕 Monitoring API (Nouveauté v0.3)
```bash
# Vérifier le statut de l'API Qualys
python scripts/api_monitor.py status

# Attendre que des slots soient disponibles
python scripts/api_monitor.py wait 2

# Tester la connexion API
python scripts/api_monitor.py test
```

## 📁 Structure Créée

```
qualys-automation/
├── src/                    # Code source refactorisé
├── config/                 # Configuration externalisée
├── scripts/                # Scripts d'initialisation
├── data/                   # Base de données SQLite
├── logs/                   # Fichiers de logs
├── main_v03.py            # Nouveau point d'entrée
├── requirements.txt        # Dépendances mises à jour
└── README_v03.md          # Documentation complète
```

## ✅ Avantages de la v0.3

- ✅ **Sécurité** : Plus de credentials hardcodés
- ✅ **Persistance** : Base de données SQLite
- ✅ **Modularité** : Architecture propre et extensible
- ✅ **Robustesse** : Gestion d'erreurs et retry logic
- ✅ **Interface** : Menus interactifs améliorés
- ✅ **Migration** : Préservation des données existantes
- 🆕 **Contrôles API** : Respect des limitations Qualys
- 🆕 **Rate Limiting** : Suivi du quota 300 req/heure
- 🆕 **Slots Management** : Max 8 rapports simultanés
- 🆕 **Monitoring** : Scripts de surveillance API

## 🚧 Prochaines Étapes (Phase 2)

- Interface web avec FastAPI
- Dashboard de visualisation
- API REST pour intégration
- Parser CSV pour vulnérabilités

## 🚨 Contrôles API Critiques

### Avant de lancer des rapports
```bash
# Toujours vérifier le statut API
python scripts/api_monitor.py status
```

### Si vous voyez des alertes
- **⚠️ Quota faible** : Attendez ou réduisez le nombre de rapports
- **🛑 Pas de slots** : Attendez qu'un rapport se termine
- **❌ Erreur API** : Vérifiez la connectivité et credentials

### Bonnes pratiques
- **Surveillez** le quota API (300 req/heure)
- **Respectez** la limite de 8 rapports simultanés
- **Utilisez** les scripts de monitoring avant gros traitements

## 🆘 Support

En cas de problème :
1. Vérifiez les logs dans `logs/qualys_automation.log`
2. Consultez `README_v03.md` pour la documentation complète
3. Utilisez `python scripts/api_monitor.py status` pour l'état API
4. Consultez `API_CONTROLS_v03.md` pour les contrôles détaillés

---

**🎉 Votre projet respecte maintenant les limitations Qualys et est prêt pour la Phase 2 !**