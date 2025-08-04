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
            session.execute("SELECT 1")
            print("   ✅ Connexion à la base de données OK")
        
        # Initialize Qualys client
        print("🔗 Initialisation du client Qualys...")
        qualys_client = QualysClient(api_config)
        
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
        
        # Step 4: Report creation
        created_reports = []
        
        if selected_scans:
            print("\n📊 ÉTAPE 4A: Création des rapports basés sur les scans")
            print("-" * 50)
            
            try:
                scan_reports = report_service.create_reports_from_selected_scans(selected_scans)
                created_reports.extend(scan_reports)
            except Exception as e:
                print(f"❌ Erreur lors de la création des rapports de scans: {e}")
        
        if selected_templates:
            print("\n📊 ÉTAPE 4B: Création des rapports basés sur les templates")
            print("-" * 50)
            
            try:
                template_reports = report_service.create_reports_from_selected_templates(selected_templates)
                created_reports.extend(template_reports)
            except Exception as e:
                print(f"❌ Erreur lors de la création des rapports de templates: {e}")
        
        # Step 5: Download reports
        if created_reports:
            print("\n📥 ÉTAPE 5: Téléchargement automatique des rapports")
            print("-" * 50)
            
            downloaded_count = 0
            failed_count = 0
            
            for report_group in created_reports:
                reports = report_group['reports']
                for report in reports:
                    report_id = report['report_id']
                    description = report.get('description', report.get('report_title', ''))
                    
                    print(f"\n🔎 Surveillance du rapport {report_id} ({description})...")
                    
                    try:
                        filename = report_service.wait_until_ready_and_download(report_id)
                        if filename:
                            print(f"✅ Rapport téléchargé: {filename}")
                            downloaded_count += 1
                        else:
                            print(f"❌ Rapport {report_id} non téléchargé")
                            failed_count += 1
                    except Exception as e:
                        print(f"❌ Erreur lors du téléchargement du rapport {report_id}: {e}")
                        failed_count += 1
            
            # Final summary
            print(f"\n📊 RÉSUMÉ FINAL:")
            print(f"   ✅ Rapports téléchargés: {downloaded_count}")
            if failed_count > 0:
                print(f"   ❌ Rapports en échec: {failed_count}")
            print(f"   📁 Total traité: {downloaded_count + failed_count}")
        
        else:
            print("\n⚠️  Aucun rapport à télécharger")
        
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