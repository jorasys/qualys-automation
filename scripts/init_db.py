#!/usr/bin/env python3
"""
Database initialization script
Creates tables and sets up the database
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database import db_manager
from src.core.config import config
from src.models import Base
from datetime import datetime
from sqlalchemy import text


def init_database():
    """Initialize the database and create all tables"""
    
    print("🗄️  Initialisation de la base de données...")
    print("=" * 50)
    
    try:
        # Ensure data directory exists
        db_config = config.database
        if db_config.type == "sqlite":
            data_dir = Path(db_config.path).parent
            data_dir.mkdir(exist_ok=True)
            print(f"📁 Répertoire de données créé: {data_dir}")
        
        # Create all tables
        print("📊 Création des tables...")
        db_manager.create_tables()
        print("✅ Tables créées avec succès")
        
        # Test database connection
        print("🔗 Test de la connexion...")
        with db_manager.get_session() as session:
            # Simple test query
            result = session.execute(text("SELECT 1")).scalar()
            if result == 1:
                print("✅ Connexion à la base de données validée")
            else:
                raise Exception("Test de connexion échoué")
        
        # Display database info
        database_url = config.get_database_url()
        print(f"\n📋 Informations de la base de données:")
        print(f"   Type: {db_config.type}")
        print(f"   URL: {database_url}")
        if db_config.type == "sqlite":
            print(f"   Fichier: {db_config.path}")
        
        print("\n🎉 Base de données initialisée avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        return False


def reset_database():
    """Reset database by dropping and recreating all tables"""
    
    print("⚠️  RÉINITIALISATION DE LA BASE DE DONNÉES")
    print("=" * 50)
    print("⚠️  ATTENTION: Cette opération supprimera toutes les données!")
    
    response = input("Êtes-vous sûr de vouloir continuer? (oui/non): ").lower().strip()
    if response not in ['oui', 'yes', 'y', 'o']:
        print("❌ Opération annulée")
        return False
    
    try:
        print("🗑️  Suppression des tables existantes...")
        db_manager.drop_tables()
        print("✅ Tables supprimées")
        
        print("📊 Recréation des tables...")
        db_manager.create_tables()
        print("✅ Tables recréées")
        
        print("🎉 Base de données réinitialisée avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la réinitialisation: {e}")
        return False


def show_database_info():
    """Show database information and statistics"""
    
    print("📋 INFORMATIONS DE LA BASE DE DONNÉES")
    print("=" * 50)
    
    try:
        db_config = config.database
        database_url = config.get_database_url()
        
        print(f"Type: {db_config.type}")
        print(f"URL: {database_url}")
        
        if db_config.type == "sqlite":
            db_path = Path(db_config.path)
            if db_path.exists():
                size = db_path.stat().st_size
                print(f"Fichier: {db_config.path}")
                print(f"Taille: {size:,} bytes")
            else:
                print(f"Fichier: {db_config.path} (n'existe pas)")
        
        # Test connection and get table info
        with db_manager.get_session() as session:
            print(f"\n📊 Tables:")
            
            # Get table names (SQLite specific)
            if db_config.type == "sqlite":
                result = session.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ).fetchall()
                
                for (table_name,) in result:
                    count_result = session.execute(f"SELECT COUNT(*) FROM {table_name}").scalar()
                    print(f"   - {table_name}: {count_result:,} enregistrements")
            
            print("✅ Connexion réussie")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")


def main():
    """Main function with command line interface"""
    
    if len(sys.argv) < 2:
        print("Usage: python scripts/init_db.py [init|reset|info]")
        print("  init  - Initialiser la base de données")
        print("  reset - Réinitialiser la base de données (supprime toutes les données)")
        print("  info  - Afficher les informations de la base de données")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "init":
        success = init_database()
        sys.exit(0 if success else 1)
    
    elif command == "reset":
        success = reset_database()
        sys.exit(0 if success else 1)
    
    elif command == "info":
        show_database_info()
        sys.exit(0)
    
    else:
        print(f"❌ Commande inconnue: {command}")
        print("Commandes disponibles: init, reset, info")
        sys.exit(1)


if __name__ == "__main__":
    main()