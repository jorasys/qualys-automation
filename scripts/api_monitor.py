#!/usr/bin/env python3
"""
API Monitor - Monitor Qualys API status, rate limits and running reports
"""
import sys
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import config
from src.api.qualys_client import QualysClient
from src.services.report_service import ReportService


def display_api_status():
    """Display current API status"""
    
    print("📊 STATUT DE L'API QUALYS")
    print("=" * 50)
    
    try:
        # Initialize client
        api_config = config.api
        qualys_client = QualysClient(api_config)
        report_service = ReportService(qualys_client)
        
        # Get API status
        status = report_service.get_current_api_status()
        
        # Display rate limiting info
        print("🚦 LIMITATION DE TAUX:")
        rate_limit = status.get('rate_limit', {})
        if rate_limit.get('remaining') is not None:
            remaining = rate_limit['remaining']
            print(f"   Requêtes restantes: {remaining}")
            
            if remaining < 50:
                print("   ⚠️  ATTENTION: Quota API faible!")
            elif remaining < 10:
                print("   🛑 CRITIQUE: Quota API très faible!")
            else:
                print("   ✅ Quota API OK")
        else:
            print("   ❓ Information non disponible (première requête)")
        
        if rate_limit.get('last_request'):
            print(f"   Dernière requête: {rate_limit['last_request']}")
        
        # Display running reports info
        print(f"\n📋 RAPPORTS EN COURS:")
        reports_info = status.get('reports', {})
        running_count = reports_info.get('running_count')
        max_slots = reports_info.get('max_slots', 8)
        available_slots = reports_info.get('available_slots')
        
        if running_count is not None:
            print(f"   Rapports en cours: {running_count}/{max_slots}")
            print(f"   Slots disponibles: {available_slots}")
            
            if available_slots == 0:
                print("   🛑 AUCUN SLOT DISPONIBLE")
            elif available_slots <= 2:
                print("   ⚠️  Peu de slots disponibles")
            else:
                print("   ✅ Slots disponibles OK")
            
            # Show running reports
            running_reports = reports_info.get('running_reports', [])
            if running_reports:
                print(f"\n   📄 Rapports en cours d'exécution:")
                for report in running_reports:
                    title = report.get('title', 'Sans titre')[:50]
                    report_id = report.get('id', 'N/A')
                    print(f"      - {title} (ID: {report_id})")
            else:
                print("   📄 Aucun rapport en cours")
        else:
            print("   ❓ Information non disponible")
        
        # Recommendations
        print(f"\n💡 RECOMMANDATIONS:")
        
        if rate_limit.get('remaining', 100) < 20:
            print("   🛑 Évitez de créer de nouveaux rapports")
            print("   ⏳ Attendez la réinitialisation du quota")
        elif available_slots is not None and available_slots <= 1:
            print("   ⏳ Attendez qu'un rapport se termine avant d'en créer de nouveaux")
        else:
            print("   ✅ Vous pouvez créer de nouveaux rapports")
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération du statut: {e}")


def wait_for_slots(required_slots: int = 1):
    """Wait for available report slots"""
    
    print(f"⏳ ATTENTE DE {required_slots} SLOT(S) DISPONIBLE(S)")
    print("=" * 50)
    
    try:
        api_config = config.api
        qualys_client = QualysClient(api_config)
        
        success = qualys_client.wait_for_report_slots(
            required_slots=required_slots,
            max_wait=1800,  # 30 minutes
            check_interval=60  # Check every minute
        )
        
        if success:
            print(f"✅ {required_slots} slot(s) disponible(s)!")
        else:
            print(f"⚠️  Timeout: slots toujours non disponibles")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")


def test_api_connection():
    """Test API connection and basic functionality"""
    
    print("🔗 TEST DE CONNEXION API")
    print("=" * 50)
    
    try:
        api_config = config.api
        print(f"🌐 Serveur: {api_config.base_url}")
        print(f"👤 Utilisateur: {api_config.username}")
        print(f"🔒 Proxy: {'Activé' if api_config.proxy_url else 'Désactivé'}")
        
        qualys_client = QualysClient(api_config)
        
        print(f"\n🧪 Test de récupération des scans...")
        scans = qualys_client.get_last_30_scans()
        
        if scans:
            print(f"✅ Connexion réussie - {len(scans)} scan(s) trouvé(s)")
            
            # Show first few scans
            count = 0
            for title, dates in scans.items():
                if count >= 3:  # Show only first 3
                    break
                print(f"   📄 {title} ({len(dates)} date(s))")
                count += 1
            
            if len(scans) > 3:
                print(f"   ... et {len(scans) - 3} autres")
        else:
            print("⚠️  Connexion réussie mais aucun scan trouvé")
        
        # Test report status check
        print(f"\n🧪 Test de vérification des rapports en cours...")
        running_count = qualys_client.get_running_reports_count()
        print(f"✅ {running_count} rapport(s) en cours d'exécution")
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print(f"💡 Vérifiez vos credentials et la connectivité réseau")


def main():
    """Main function with command line interface"""
    
    if len(sys.argv) < 2:
        print("Usage: python scripts/api_monitor.py [status|wait|test] [options]")
        print("  status           - Afficher le statut actuel de l'API")
        print("  wait [slots]     - Attendre que des slots soient disponibles")
        print("  test             - Tester la connexion API")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "status":
        display_api_status()
    
    elif command == "wait":
        slots = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        wait_for_slots(slots)
    
    elif command == "test":
        test_api_connection()
    
    else:
        print(f"❌ Commande inconnue: {command}")
        print("Commandes disponibles: status, wait, test")
        sys.exit(1)


if __name__ == "__main__":
    main()