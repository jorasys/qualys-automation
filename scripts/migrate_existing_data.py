#!/usr/bin/env python3
"""
Migration script for existing data
Migrates JSON files and existing data to the new database structure
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database import db_manager
from src.models.scan_report import ScanReport
from src.models.sync_log import SyncLog


def migrate_scan_results():
    """Migrate scan_results.json to database"""
    
    scan_results_file = Path("scan_results.json")
    
    if not scan_results_file.exists():
        print("📄 scan_results.json non trouvé - ignoré")
        return 0
    
    print("📄 Migration de scan_results.json...")
    
    try:
        with open(scan_results_file, 'r', encoding='utf-8') as f:
            scan_data = json.load(f)
        
        migrated_count = 0
        
        with db_manager.get_session() as session:
            for title, dates in scan_data.items():
                for date_str, scan_id in dates.items():
                    # Check if already exists
                    existing = session.query(ScanReport).filter(
                        ScanReport.qualys_report_id == scan_id
                    ).first()
                    
                    if existing:
                        print(f"   ⚠️  Scan {scan_id} déjà existant - ignoré")
                        continue
                    
                    try:
                        scan_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
                    except ValueError:
                        scan_date = datetime.now()
                    
                    scan_report = ScanReport(
                        qualys_report_id=scan_id,
                        report_type="scan",
                        scan_date=scan_date,
                        status="historical"
                    )
                    session.add(scan_report)
                    migrated_count += 1
        
        print(f"   ✅ {migrated_count} scans migrés")
        return migrated_count
        
    except Exception as e:
        print(f"   ❌ Erreur lors de la migration: {e}")
        return 0


def migrate_selected_scans():
    """Migrate selected_scans.json to database"""
    
    selected_scans_file = Path("selected_scans.json")
    
    if not selected_scans_file.exists():
        print("📄 selected_scans.json non trouvé - ignoré")
        return 0
    
    print("📄 Migration de selected_scans.json...")
    
    try:
        with open(selected_scans_file, 'r', encoding='utf-8') as f:
            selected_data = json.load(f)
        
        selected_scans = selected_data.get('selected_scans', [])
        migrated_count = 0
        
        with db_manager.get_session() as session:
            for scan in selected_scans:
                scan_id = scan.get('scan_id')
                if not scan_id:
                    continue
                
                # Check if already exists
                existing = session.query(ScanReport).filter(
                    ScanReport.qualys_report_id == scan_id
                ).first()
                
                if existing:
                    # Update status to indicate it was selected
                    existing.status = "selected"
                    migrated_count += 1
                else:
                    # Create new entry
                    try:
                        scan_date = datetime.strptime(scan['date'], "%Y-%m-%dT%H:%M:%SZ")
                    except (ValueError, KeyError):
                        scan_date = datetime.now()
                    
                    scan_report = ScanReport(
                        qualys_report_id=scan_id,
                        report_type="scan",
                        scan_date=scan_date,
                        status="selected"
                    )
                    session.add(scan_report)
                    migrated_count += 1
        
        print(f"   ✅ {migrated_count} scans sélectionnés migrés")
        return migrated_count
        
    except Exception as e:
        print(f"   ❌ Erreur lors de la migration: {e}")
        return 0


def create_migration_log(total_migrated: int):
    """Create a log entry for the migration"""
    
    with db_manager.get_session() as session:
        sync_log = SyncLog(
            source="migration",
            operation="migrate_existing_data",
            timestamp=datetime.now(),
            status="success" if total_migrated > 0 else "warning",
            details=f"Migration des données JSON vers SQLite - {total_migrated} enregistrements traités",
            records_processed=total_migrated
        )
        session.add(sync_log)
    
    print(f"📝 Log de migration créé")


def backup_existing_files():
    """Backup existing JSON files before migration"""
    
    backup_dir = Path("backup")
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    files_to_backup = ["scan_results.json", "selected_scans.json"]
    backed_up = []
    
    for filename in files_to_backup:
        source_file = Path(filename)
        if source_file.exists():
            backup_file = backup_dir / f"{filename}.{timestamp}.bak"
            
            try:
                import shutil
                shutil.copy2(source_file, backup_file)
                backed_up.append(str(backup_file))
                print(f"💾 Sauvegarde créée: {backup_file}")
            except Exception as e:
                print(f"⚠️  Erreur lors de la sauvegarde de {filename}: {e}")
    
    return backed_up


def migrate_existing_data():
    """Main migration function"""
    
    print("📦 MIGRATION DES DONNÉES EXISTANTES")
    print("=" * 50)
    
    # Create backup first
    print("💾 Création des sauvegardes...")
    backed_up_files = backup_existing_files()
    
    if backed_up_files:
        print(f"✅ {len(backed_up_files)} fichier(s) sauvegardé(s)")
    
    # Migrate data
    total_migrated = 0
    
    total_migrated += migrate_scan_results()
    total_migrated += migrate_selected_scans()
    
    # Create migration log
    create_migration_log(total_migrated)
    
    print(f"\n📊 RÉSUMÉ DE LA MIGRATION:")
    print(f"   📁 Fichiers sauvegardés: {len(backed_up_files)}")
    print(f"   📊 Enregistrements migrés: {total_migrated}")
    
    if total_migrated > 0:
        print("✅ Migration terminée avec succès!")
    else:
        print("⚠️  Aucune donnée à migrer trouvée")
    
    return total_migrated > 0


def show_migration_status():
    """Show current migration status"""
    
    print("📋 STATUT DE LA MIGRATION")
    print("=" * 50)
    
    # Check for existing files
    files_to_check = ["scan_results.json", "selected_scans.json"]
    
    print("📄 Fichiers JSON:")
    for filename in files_to_check:
        file_path = Path(filename)
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"   ✅ {filename}: {size:,} bytes")
        else:
            print(f"   ❌ {filename}: non trouvé")
    
    # Check database status
    try:
        with db_manager.get_session() as session:
            scan_reports_count = session.query(ScanReport).count()
            sync_logs_count = session.query(SyncLog).count()
            
            print(f"\n📊 Base de données:")
            print(f"   📄 Rapports de scan: {scan_reports_count:,}")
            print(f"   📝 Logs de synchronisation: {sync_logs_count:,}")
            
            # Show recent migration logs
            recent_migrations = session.query(SyncLog).filter(
                SyncLog.source == "migration"
            ).order_by(SyncLog.timestamp.desc()).limit(5).all()
            
            if recent_migrations:
                print(f"\n📝 Migrations récentes:")
                for log in recent_migrations:
                    status_icon = "✅" if log.status == "success" else "⚠️"
                    print(f"   {status_icon} {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}: {log.operation} ({log.records_processed} enregistrements)")
    
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de la base de données: {e}")


def main():
    """Main function with command line interface"""
    
    if len(sys.argv) < 2:
        print("Usage: python scripts/migrate_existing_data.py [migrate|status]")
        print("  migrate - Migrer les données JSON vers la base de données")
        print("  status  - Afficher le statut de la migration")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "migrate":
        success = migrate_existing_data()
        sys.exit(0 if success else 1)
    
    elif command == "status":
        show_migration_status()
        sys.exit(0)
    
    else:
        print(f"❌ Commande inconnue: {command}")
        print("Commandes disponibles: migrate, status")
        sys.exit(1)


if __name__ == "__main__":
    main()