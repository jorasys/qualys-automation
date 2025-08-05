#!/usr/bin/env python3
"""
Qualys Automation - Version 0.3
Refactored main entry point with new architecture
"""
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.config import config
from src.core.database import db_manager
from src.core.exceptions import ConfigurationError, APIError
from src.api.qualys_client import QualysClient
from src.services.report_service import ReportService
from src.ui.menu_manager import create_scan_menu, create_template_menu
from datetime import datetime
from sqlalchemy import text


def main():
    """Main entry point for Qualys Automation v0.3"""
    
    print("🚀 Qualys Automation - Version 0.3")
    print("=" * 50)
    
    try:
        # Initialize configuration
        print("⚙️  Chargement de la configuration...")
        api_config = config.api
        print(f"   API: {api_config.base_url}")
        print(f"   Proxy: {'Activé' if api_config.proxy_url else 'Désactivé'}")
        
        # Initialize database
        print("🗄️  Vérification de la base de données...")
        with db_manager.get_session() as session:
            # Test connection
            session.execute(text("SELECT 1"))
            print("   ✅ Connexion à la base de données OK")
        
        # Initialize Qualys client
        print("🔗 Initialisation du client Qualys...")
        reports_config = config.reports
        qualys_client = QualysClient(api_config, reports_config)

        # Initialize services
        report_service = ReportService(qualys_client)
        
        print("✅ Initialisation terminée\n")
        
        # Step 1: Get scans from Qualys
        print("📡 ÉTAPE 1: Récupération des scans")
        print("-" * 40)
        
        scan_results = qualys_client.get_last_30_scans()
        
        if not scan_results:
            print("❌ Aucun scan trouvé. Vérifiez vos credentials et la connectivité.")
            return 1
        
        print(f"✅ {len(scan_results)} scan(s) récupéré(s)")
        
        # Step 2: Scan selection
        print("\n📋 ÉTAPE 2: Sélection des scans")
        print("-" * 40)
        
        scan_menu = create_scan_menu(scan_results)
        selected_scans = scan_menu.display_checkbox_menu()
        
        if not selected_scans:
            print("❌ Aucun scan sélectionné.")
        else:
            print(f"✅ {len(selected_scans)} scan(s) sélectionné(s)")
        
        # Step 3: Template selection
        print("\n📋 ÉTAPE 3: Sélection des templates")
        print("-" * 40)
        
        host_templates = config.get_host_templates()
        template_menu = create_template_menu(host_templates)
        selected_templates = template_menu.display_checkbox_menu()
        
        if not selected_templates:
            print("❌ Aucun template sélectionné.")
        else:
            print(f"✅ {len(selected_templates)} template(s) sélectionné(s)")
        
        # Step 4: Report creation with integrated download
        all_processed_reports = []
        
        if selected_scans:
            print("\n📊 ÉTAPE 4A: Création et téléchargement des rapports basés sur les scans")
            print("-" * 60)
            
            try:
                scan_reports = report_service.create_reports_from_selected_scans(selected_scans)
                all_processed_reports.extend(scan_reports)
            except Exception as e:
                print(f"❌ Erreur lors de la création des rapports de scans: {e}")
        
        if selected_templates:
            print("\n📊 ÉTAPE 4B: Création et téléchargement des rapports basés sur les templates")
            print("-" * 60)
            
            try:
                template_reports = report_service.create_reports_from_selected_templates(selected_templates)
                all_processed_reports.extend(template_reports)
            except Exception as e:
                print(f"❌ Erreur lors de la création des rapports de templates: {e}")
        
        # Final summary (download is now integrated)
        if all_processed_reports:
            # Count successful downloads from all report groups
            downloaded_count = 0
            failed_count = 0
            
            for report_group in all_processed_reports:
                reports = report_group.get('reports', [])
                for report in reports:
                    if report.get('status') == 'downloaded':
                        downloaded_count += 1
                    else:
                        failed_count += 1
            
            print(f"\n🎉 RÉSUMÉ FINAL:")
            print(f"   ✅ Rapports téléchargés avec succès: {downloaded_count}")
            if failed_count > 0:
                print(f"   ❌ Rapports échoués ou non téléchargés: {failed_count}")
            print(f"   📁 Total traité: {downloaded_count + failed_count}")
            print(f"   📂 Fichiers sauvegardés dans: {reports_config.download_path}")
        
        else:
            print("\n⚠️  Aucun rapport créé")
        
        print(f"\n🎉 Script terminé avec succès!")
        return 0
        
    except ConfigurationError as e:
        print(f"❌ Erreur de configuration: {e}")
        print("💡 Vérifiez vos fichiers de configuration et variables d'environnement")
        return 1
    
    except APIError as e:
        print(f"❌ Erreur API Qualys: {e}")
        print("💡 Vérifiez vos credentials et la connectivité réseau")
        return 1
    
    except KeyboardInterrupt:
        print("\n⚠️  Script interrompu par l'utilisateur")
        return 1
    
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        print("💡 Consultez les logs pour plus de détails")
        return 1


if __name__ == "__main__":
    sys.exit(main())