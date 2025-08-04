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

## 🚧 Prochaines Étapes (Phase 2)

- Interface web avec FastAPI
- Dashboard de visualisation
- API REST pour intégration
- Parser CSV pour vulnérabilités

## 🆘 Support

En cas de problème :
1. Vérifiez les logs dans `logs/qualys_automation.log`
2. Consultez `README_v03.md` pour la documentation complète
3. Utilisez `python scripts/init_db.py info` pour diagnostiquer la DB

---

**🎉 Votre projet est maintenant prêt pour la Phase 2 du développement !**