#!/usr/bin/env python3
"""
Qualys Automation - Version 0.5
CLI interface with scan type selection
"""
import sys
import argparse
import csv
import logging
from pathlib import Path
import time
from typing import List, Dict, Any, Optional

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.config import config
from src.core.exceptions import ConfigurationError, APIError
from src.api.qualys_client import QualysClient


def setup_logging():
    """Configure logging based on settings"""
    log_config = config.logging
    log_dir = Path(log_config.file).parent
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_config.level),
        format=log_config.format,
        handlers=[
            logging.FileHandler(log_config.file)
        ]
    )
    return logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Qualys Automation - Téléchargement de scans',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python main.py --scan-reseau scans.csv --csv    # Télécharge les scans réseau en CSV
  python main.py --scan-reseau scans.csv --pdf    # Télécharge les scans réseau en PDF
  python main.py --scan-agent                     # Télécharge les scans agent
  python main.py --scan-reseau scans.csv --pdf --output-folder ./output  # Avec dossier personnalisé
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--scan-reseau', '-sr',
        type=str,
        metavar='CSV_FILE',
        help='Télécharger les scans réseau (VM/PC) à partir d\'un fichier CSV'
    )
    group.add_argument(
        '--scan-agent', '-sa',
        action='store_true',
        help='Télécharger les scans agent'
    )
    group.add_argument(
        '--get30',
        action='store_true',
        help='Récupérer et afficher les 30 derniers scans'
    )

    parser.add_argument(
        '--output-folder', '-O',
        type=str,
        metavar='FOLDER',
        help='Dossier de sortie pour les fichiers téléchargés (optionnel)'
    )

    # Format options (required when --scan-reseau is used)
    parser.add_argument(
        '--csv',
        action='store_true',
        help='Télécharger les scans au format CSV (requis avec --scan-reseau)'
    )
    parser.add_argument(
        '--pdf',
        action='store_true',
        help='Télécharger les scans au format PDF (requis avec --scan-reseau)'
    )

    return parser.parse_args()


def parse_csv(filepath: str, logger: logging.Logger) -> List[Dict[str, str]]:
    """
    Parse un fichier CSV contenant les informations de scans.
    Supporte différents formats de colonnes.

    Args:
        filepath: Chemin vers le fichier CSV
        logger: Logger instance

    Returns:
        Liste de dictionnaires contenant les données avec 'id' et 'title'
    """
    data = []

    try:
        # Validate file exists
        if not Path(filepath).exists():
            logger.error(f"Le fichier '{filepath}' n'existe pas")
            print(f"❌ Erreur: Le fichier '{filepath}' n'existe pas", file=sys.stderr)
            sys.exit(1)

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if not lines:
            logger.error("Le fichier CSV est vide")
            print("❌ Erreur: Le fichier CSV est vide", file=sys.stderr)
            sys.exit(1)

        # Clean lines
        lines = [line.strip() for line in lines if line.strip()]

        if len(lines) < 2:
            logger.error("Le fichier CSV doit contenir au moins un en-tête et une ligne de données")
            print("❌ Erreur: Le fichier CSV doit contenir au moins un en-tête et une ligne de données", file=sys.stderr)
            sys.exit(1)

        # Detect format automatically
        header = lines[0].split(',')

        # Format 1: Standard columns 'id,title'
        if len(header) >= 2 and 'id' in [h.strip().lower() for h in header] and 'title' in [h.strip().lower() for h in header]:
            import io
            csv_content = '\n'.join(lines)
            reader = csv.DictReader(io.StringIO(csv_content))

            for row in reader:
                # Find actual columns (case insensitive)
                id_col = None
                title_col = None
                for col in reader.fieldnames:
                    if col.strip().lower() == 'id':
                        id_col = col
                    elif col.strip().lower() == 'title':
                        title_col = col

                if id_col and title_col:
                    data.append({
                        'id': row[id_col].strip(),
                        'title': row[title_col].strip()
                    })

        # Format 2: Simple list of scan IDs (one column)
        elif len(header) == 1 and header[0].strip():
            for line in lines[1:]:  # Skip header
                scan_id = line.strip()
                if scan_id:
                    # Extract numeric ID from 'scan/XXXXXXXXX.XXXXX' format
                    if '/' in scan_id:
                        parts = scan_id.split('/')
                        if len(parts) == 2:
                            scan_id = parts[1]

                    data.append({
                        'id': scan_id,
                        'title': f"Scan {scan_id}"
                    })

        # Format 3: Generic format with at least 2 columns
        elif len(header) >= 2:
            id_col = header[0].strip()
            title_col = header[1].strip()

            for line in lines[1:]:  # Skip header
                cols = line.split(',')
                if len(cols) >= 2:
                    data.append({
                        'id': cols[0].strip(),
                        'title': cols[1].strip()
                    })

        else:
            logger.error(f"Format CSV non reconnu. Première ligne: {lines[0]}")
            print("❌ Erreur: Format CSV non reconnu", file=sys.stderr)
            print(f"Première ligne: {lines[0]}", file=sys.stderr)
            print("Formats supportés:", file=sys.stderr)
            print("  - Colonnes 'id,title'", file=sys.stderr)
            print("  - Liste d'IDs de scan (une colonne)", file=sys.stderr)
            print("  - Format générique (au moins 2 colonnes)", file=sys.stderr)
            sys.exit(1)

        if not data:
            logger.error("Aucune donnée valide trouvée dans le fichier CSV")
            print("❌ Erreur: Aucune donnée valide trouvée dans le fichier CSV", file=sys.stderr)
            sys.exit(1)

        logger.info(f"CSV parsé avec succès: {len(data)} entrée(s)")
        return data

    except FileNotFoundError:
        logger.error(f"Le fichier '{filepath}' n'existe pas")
        print(f"❌ Erreur: Le fichier '{filepath}' n'existe pas", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du fichier: {e}")
        print(f"❌ Erreur lors de la lecture du fichier: {e}", file=sys.stderr)
        sys.exit(1)


def wait_for_reports_completion(qualys_client: QualysClient, report_ids: List[str], 
                                logger: logging.Logger, max_wait: int = 3600) -> List[str]:
    """
    Wait for all reports to complete with timeout and error handling.
    
    Args:
        qualys_client: QualysClient instance
        report_ids: List of report IDs to monitor
        logger: Logger instance
        max_wait: Maximum wait time in seconds (default: 1 hour)
    
    Returns:
        List of completed report IDs
    """
    reports_config = config.reports.creation_controls
    check_interval = reports_config["slot_check_interval"]
    
    reports_not_finished = set(report_ids)
    completed_reports = []
    failed_reports = []
    elapsed_time = 0
    
    logger.info(f"Attente de la complétion de {len(report_ids)} rapport(s)")
    
    while reports_not_finished and elapsed_time < max_wait:
        for report_id in list(reports_not_finished):
            try:
                status = qualys_client.check_report_status(report_id)
                
                if status == "Finished":
                    reports_not_finished.remove(report_id)
                    completed_reports.append(report_id)
                    logger.info(f"Rapport {report_id} terminé")
                    print(f"✅ Rapport {report_id} terminé")
                    
                elif status in ["Error", "Cancelled"]:
                    reports_not_finished.remove(report_id)
                    failed_reports.append(report_id)
                    logger.warning(f"Rapport {report_id} en erreur: {status}")
                    print(f"⚠️  Rapport {report_id} en erreur: {status}")
                    
            except Exception as e:
                logger.error(f"Erreur lors de la vérification du rapport {report_id}: {e}")
                print(f"⚠️  Erreur lors de la vérification du rapport {report_id}: {e}")
        
        if reports_not_finished:
            time.sleep(check_interval)
            elapsed_time += check_interval
            
            if elapsed_time % 120 == 0:  # Log every 2 minutes
                logger.info(f"En attente de {len(reports_not_finished)} rapport(s) - Temps écoulé: {elapsed_time}s")
    
    if reports_not_finished:
        logger.warning(f"Timeout atteint: {len(reports_not_finished)} rapport(s) non terminé(s)")
        print(f"⚠️  Timeout atteint: {len(reports_not_finished)} rapport(s) non terminé(s)")
    
    if failed_reports:
        logger.warning(f"{len(failed_reports)} rapport(s) en erreur")
    
    return completed_reports


def process_network_scans_csv(qualys_client: QualysClient, data: List[Dict[str, str]], 
                              output_folder: Optional[str], logger: logging.Logger) -> int:
    """
    Process network scans in CSV format.
    
    Returns:
        Number of successful downloads
    """
    logger.info(f"Traitement de {len(data)} scan(s) réseau au format CSV")
    print(f"📊 Traitement de {len(data)} scan(s) réseau au format CSV...")
    
    successful_downloads = 0

    for item in data:
        scan_ref = item['id']
        scan_title = item['title']

        print(f"📥 Téléchargement du scan: {scan_title} (ID: {scan_ref})")
        logger.info(f"Téléchargement du scan: {scan_title} (ID: {scan_ref})")

        try:
            filepath = qualys_client.get_scan(
                scan_ref=scan_ref,
                output_format='csv_extended',
                filename=f"{scan_title}.csv",
                download_path=output_folder
            )

            if filepath:
                print(f"✅ Fichier sauvegardé: {filepath}")
                logger.info(f"Fichier sauvegardé: {filepath}")
                successful_downloads += 1
            else:
                print(f"❌ Échec du téléchargement pour le scan {scan_ref}")
                logger.error(f"Échec du téléchargement pour le scan {scan_ref}")

        except Exception as e:
            print(f"❌ Erreur lors du téléchargement du scan {scan_ref}: {e}")
            logger.error(f"Erreur lors du téléchargement du scan {scan_ref}: {e}")

    print(f"\n📈 Résumé: {successful_downloads}/{len(data)} scan(s) téléchargé(s) avec succès")
    logger.info(f"Résumé CSV: {successful_downloads}/{len(data)} scan(s) téléchargé(s)")
    
    return successful_downloads


def process_network_scans_pdf(qualys_client: QualysClient, data: List[Dict[str, str]], 
                              output_folder: Optional[str], logger: logging.Logger) -> int:
    """
    Process network scans in PDF format with batching.
    
    Returns:
        Number of successful downloads
    """
    reports_config = config.reports.creation_controls
    batch_size = reports_config["batch_size"]
    pause_between_reports = reports_config["pause_between_reports"]
    
    template_id = config.get_scan_templates()[0]["template_id"]
    
    logger.info(f"Traitement de {len(data)} scan(s) réseau au format PDF (batch size: {batch_size})")
    print(f"📊 Traitement de {len(data)} scan(s) réseau au format PDF...")
    
    successful_downloads = 0
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(data) + batch_size - 1) // batch_size
        
        logger.info(f"Traitement du batch {batch_num}/{total_batches} ({len(batch)} scans)")
        print(f"\n📦 Batch {batch_num}/{total_batches} ({len(batch)} scans)")

        # Create reports for batch
        report_ids = []
        for item in batch:
            scan_ref = item['id']
            scan_title = item['title']
            
            try:
                print(f"📝 Création du rapport pour: {scan_title}")
                logger.info(f"Création du rapport pour: {scan_title} (ID: {scan_ref})")
                
                report_id = qualys_client.create_report_scanbased(
                    scan_ref, template_id, "pdf", scan_title
                )
                
                if report_id:
                    report_ids.append(report_id)
                    logger.info(f"Rapport créé: {report_id}")
                else:
                    logger.error(f"Échec de création du rapport pour {scan_ref}")
                    print(f"❌ Échec de création du rapport pour {scan_ref}")
                
                time.sleep(pause_between_reports)
                
            except Exception as e:
                logger.error(f"Erreur lors de la création du rapport pour {scan_ref}: {e}")
                print(f"❌ Erreur: {e}")

        if not report_ids:
            logger.warning(f"Aucun rapport créé pour le batch {batch_num}")
            continue

        # Wait for initial processing
        print(f"⏳ Attente du démarrage des rapports (30s)...")
        time.sleep(30)

        # Wait for completion
        completed_reports = wait_for_reports_completion(
            qualys_client, report_ids, logger,
            max_wait=reports_config["max_wait_for_slots"]
        )

        # Download completed reports
        for report_id in completed_reports:
            try:
                filepath = qualys_client.download_report(report_id, output_folder)
                if filepath:
                    print(f"✅ Rapport téléchargé: {filepath}")
                    logger.info(f"Rapport téléchargé: {filepath}")
                    successful_downloads += 1
            except Exception as e:
                logger.error(f"Erreur lors du téléchargement du rapport {report_id}: {e}")
                print(f"❌ Erreur lors du téléchargement: {e}")

    print(f"\n📈 Résumé: {successful_downloads}/{len(data)} rapport(s) téléchargé(s) avec succès")
    logger.info(f"Résumé PDF: {successful_downloads}/{len(data)} rapport(s) téléchargé(s)")
    
    return successful_downloads


def process_agent_scans(qualys_client: QualysClient, output_folder: Optional[str],
                        logger: logging.Logger) -> int:
    """
    Process agent-based scans.

    Returns:
        Number of successful downloads
    """
    reports_config = config.reports.creation_controls
    host_templates = config.get_host_templates()

    logger.info(f"Traitement de {len(host_templates)} rapport(s) agent")
    print(f"📊 Traitement de {len(host_templates)} rapport(s) agent...")

    report_ids = []

    # Create reports
    for template in host_templates:
        template_id = template["template_id"]
        template_name = template["name"]
        template_format = template["output_format"]
        report_title = f"{template_name}.{template_format}"

        try:
            print(f"📝 Création du rapport: {template_name}")
            logger.info(f"Création du rapport agent: {template_name}")

            report_id = qualys_client.create_report_hostbased(
                template_id, template_format, report_title
            )

            if report_id:
                report_ids.append(report_id)
                logger.info(f"Rapport créé: {report_id}")
            else:
                logger.error(f"Échec de création du rapport {template_name}")
                print(f"❌ Échec de création du rapport {template_name}")

        except Exception as e:
            logger.error(f"Erreur lors de la création du rapport {template_name}: {e}")
            print(f"❌ Erreur: {e}")

    if not report_ids:
        logger.warning("Aucun rapport agent créé")
        return 0

    # Wait for initial processing
    print(f"⏳ Attente du démarrage des rapports (30s)...")
    time.sleep(30)

    # Wait for completion
    completed_reports = wait_for_reports_completion(
        qualys_client, report_ids, logger,
        max_wait=reports_config["max_wait_for_slots"]
    )

    # Download completed reports
    successful_downloads = 0
    for report_id in completed_reports:
        try:
            filepath = qualys_client.download_report(report_id, output_folder)
            if filepath:
                print(f"✅ Rapport téléchargé: {filepath}")
                logger.info(f"Rapport téléchargé: {filepath}")
                successful_downloads += 1
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement du rapport {report_id}: {e}")
            print(f"❌ Erreur lors du téléchargement: {e}")

    print(f"\n📈 Résumé: {successful_downloads}/{len(report_ids)} rapport(s) téléchargé(s) avec succès")
    logger.info(f"Résumé agent: {successful_downloads}/{len(report_ids)} rapport(s) téléchargé(s)")

    return successful_downloads


def process_get_last_30_scans(qualys_client: QualysClient, output_folder: Optional[str],
                              logger: logging.Logger) -> None:
    """
    Get and display the last 30 scans, save to file.
    """
    from datetime import datetime

    logger.info("Récupération des 30 derniers scans")
    print("📊 Récupération des 30 derniers scans...")

    try:
        scans = qualys_client.get_last_30_scans()

        if not scans:
            print("❌ Aucun scan trouvé")
            logger.warning("Aucun scan trouvé")
            return

        # Display results
        print(f"\n📋 Trouvé {len(scans)} scan(s) :")
        print("-" * 100)
        print(f"{'Titre':<50} {'Date':<16} {'Type':<8} {'ID'}")
        print("-" * 100)

        for scan in scans:
            title = scan.get('title', 'N/A')[:48]  # Truncate long titles
            date = scan.get('formatted_date', scan.get('date', 'N/A'))
            scan_type = scan.get('type', 'N/A')
            scan_id = scan.get('scan_id', 'N/A')
            print(f"{title:<50} {date:<16} {scan_type:<8} {scan_id}")

        print("-" * 100)

        # Save to CSV file
        output_dir = Path(output_folder) if output_folder else Path.home() / "Downloads"
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"last_30_scans_{timestamp}.csv"
        filepath = output_dir / filename

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'title'])

            for scan in scans:
                scan_id = scan.get('scan_id', '')
                original_title = scan.get('title', '')
                date_str = scan.get('date', '')

                # Extract YYYYMMDD from date
                try:
                    if date_str:
                        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        yyyymmdd = date_obj.strftime('%Y%m%d')
                    else:
                        yyyymmdd = '00000000'
                except ValueError:
                    yyyymmdd = '00000000'

                # Reformat title
                clean_title = original_title.replace("#", "IVS-")
                reformatted_title = f"{clean_title}-{yyyymmdd}"

                writer.writerow([scan_id, reformatted_title])

        print(f"✅ Fichier sauvegardé: {filepath}")
        logger.info(f"Fichier sauvegardé: {filepath}")

    except Exception as e:
        print(f"❌ Erreur lors de la récupération des scans: {e}")
        logger.error(f"Erreur lors de la récupération des scans: {e}")


def main():
    """Main entry point for Qualys Automation v0.5"""
    
    # Setup logging first
    logger = setup_logging()
    logger.info("=" * 50)
    logger.info("Qualys Automation v0.5 - Démarrage")
    logger.info("=" * 50)

    # Parse arguments
    args = parse_arguments()

    # Validate format options for --scan-reseau
    if args.scan_reseau and not (args.csv or args.pdf):
        logger.error("Format non spécifié pour --scan-reseau")
        print("❌ Erreur: Spécifiez --csv ou --pdf avec --scan-reseau")
        return 1

    # Determine scan type
    if args.scan_reseau:
        scan_type = 'network'
        scan_type_display = 'réseau'
        csv_file = args.scan_reseau
    elif args.scan_agent:
        scan_type = 'agent'
        scan_type_display = 'agent'
    elif args.get30:
        scan_type = 'get30'
        scan_type_display = 'get30'
    else:
        logger.error("Type de scan non spécifié")
        print("❌ Erreur: Spécifiez --scan-reseau, --scan-agent ou --get30")
        return 1

    print("🚀 Qualys Automation - Version 0.5")
    print("=" * 50)
    print(f"Mode: Scans {scan_type_display}")
    print()

    try:
        # Initialize configuration
        print("⚙️  Chargement de la configuration...")
        logger.info("Chargement de la configuration")
        
        api_config = config.api
        print(f"   API: {api_config.base_url}")
        print(f"   Proxy: {'Activé' if api_config.proxy_url else 'Désactivé'}")
        logger.info(f"API: {api_config.base_url}, Proxy: {bool(api_config.proxy_url)}")

        # Initialize Qualys client
        print("🔗 Initialisation du client Qualys...")
        logger.info("Initialisation du client Qualys")
        qualys_client = QualysClient(api_config, config.reports)

        # Check API connection
        print("🔗 Vérification de la connexion API...")
        logger.info("Vérification de la connexion API")
        
        try:
            response = qualys_client._make_request('POST', '/msp/user_list.php')
            if response.status_code == 200:
                print("✅ Connexion API réussie")
                logger.info("Connexion API réussie")
            else:
                logger.warning(f"Connexion API: Code de retour {response.status_code}")
                print(f"⚠️  Connexion API: Code de retour {response.status_code}")
                raise APIError(f"API connection failed with status code {response.status_code}")
        except APIError:
            raise
        except Exception as e:
            logger.error(f"Échec de la vérification de connexion API: {e}")
            print(f"❌ Échec de la vérification de connexion API: {e}")
            raise APIError(f"API connection check failed: {e}")

        # Process based on scan type
        if args.scan_reseau:
            data = parse_csv(args.scan_reseau, logger)

            if args.csv:
                process_network_scans_csv(qualys_client, data, args.output_folder, logger)
            elif args.pdf:
                process_network_scans_pdf(qualys_client, data, args.output_folder, logger)

        elif args.scan_agent:
            process_agent_scans(qualys_client, args.output_folder, logger)

        elif args.get30:
            process_get_last_30_scans(qualys_client, args.output_folder, logger)

        logger.info("Traitement terminé avec succès")
        return 0

    except ConfigurationError as e:
        logger.error(f"Erreur de configuration: {e}")
        print(f"❌ Erreur de configuration: {e}")
        print("💡 Vérifiez vos fichiers de configuration et variables d'environnement")
        return 1

    except APIError as e:
        logger.error(f"Erreur API Qualys: {e}")
        print(f"❌ Erreur API Qualys: {e}")
        print("💡 Vérifiez vos credentials et la connectivité réseau")
        return 1

    except KeyboardInterrupt:
        logger.warning("Script interrompu par l'utilisateur")
        print("\n⚠️  Script interrompu par l'utilisateur")
        return 1

    except Exception as e:
        logger.exception(f"Erreur inattendue: {e}")
        print(f"❌ Erreur inattendue: {e}")
        print("💡 Consultez les logs pour plus de détails")
        return 1


if __name__ == "__main__":
    sys.exit(main())