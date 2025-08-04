import json
import re
from datetime import datetime
import time

# Interface avec cases à cocher
try:
    import inquirer
    INQUIRER_AVAILABLE = True
except ImportError:
    INQUIRER_AVAILABLE = False
    print("⚠️  Pour une interface avec cases à cocher, installez: pip install inquirer")
    print("   En attendant, utilisation de l'interface texte classique")

def display_scans_checkbox_menu(scan_results):
    """
    Affiche un menu avec cases à cocher pour sélectionner les scans
    Utilise inquirer si disponible, sinon interface texte classique
    """
    if not scan_results:
        print("❌ Aucun scan disponible pour la sélection")
        return []
    
    # Créer une liste plate de tous les scans
    scan_options = []
    for title, dates in scan_results.items():
        for date, scan_id in dates.items():
            # Formatage de la date pour l'affichage
            try:
                formatted_date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").strftime("%d/%m/%Y %H:%M")
            except:
                formatted_date = date
            
            scan_options.append({
                'title': title,
                'date': date,
                'formatted_date': formatted_date,
                'scan_id': scan_id,
                'display_name': f"[{formatted_date}] {title} (ID: {scan_id})"
            })
    
    if INQUIRER_AVAILABLE:
        return display_inquirer_checkbox_menu(scan_options)
    else:
        return display_text_menu(scan_options)

def display_inquirer_checkbox_menu(scan_options):
    """
    Interface avec cases à cocher utilisant inquirer
    """
    print("\n" + "=" * 80)
    print("📋 SÉLECTION DES SCANS À TRAITER (Cases à cocher)")
    print("=" * 80)
    print("💡 Utilisez les flèches ↑↓ pour naviguer, ESPACE pour cocher/décocher, ENTRÉE pour valider")
    print("-" * 80)
    
    try:
        # Création des choix pour inquirer
        choices = [scan['display_name'] for scan in scan_options]
        
        questions = [
            inquirer.Checkbox(
                'selected_scans',
                message="Sélectionnez les scans à traiter",
                choices=choices,
                default=[]
            )
        ]
        
        answers = inquirer.prompt(questions)
        
        if not answers or not answers['selected_scans']:
            print("❌ Aucun scan sélectionné")
            return []
        
        # Retrouver les scans correspondants
        selected_display_names = set(answers['selected_scans'])
        selected_scans = [
            scan for scan in scan_options 
            if scan['display_name'] in selected_display_names
        ]
        
        print(f"\n✅ {len(selected_scans)} scan(s) sélectionné(s)")
        return selected_scans
        
    except KeyboardInterrupt:
        print("\n❌ Sélection interrompue")
        return []
    except Exception as e:
        print(f"❌ Erreur avec l'interface graphique: {e}")
        print("🔄 Basculement vers l'interface texte...")
        return display_text_menu(scan_options)

def display_text_menu(scan_options):
    """
    Interface texte classique (fallback)
    """
    print("\n" + "=" * 60)
    print("📋 SÉLECTION DES SCANS À TRAITER")
    print("=" * 60)
    
    # Afficher la liste numérotée
    for i, scan in enumerate(scan_options, 1):
        print(f"  {i:2d}. [{scan['formatted_date']}] {scan['title']}")
        print(f"      ID: {scan['scan_id']}")
    
    print("\n" + "-" * 60)
    print("💡 Options de sélection:")
    print("   • Numéros individuels: 1,3,5")
    print("   • Plages: 1-5")
    print("   • Combinaison: 1,3-7,10")
    print("   • Tout sélectionner: 'all' ou 'tout'")
    print("   • Annuler: 'quit' ou 'q'")
    print("-" * 60)
    
    while True:
        try:
            user_input = input("\n🎯 Sélectionner les scans: ").strip().lower()
            
            if user_input in ['quit', 'q']:
                print("❌ Sélection annulée")
                return []
            
            if user_input in ['all', 'tout']:
                selected_scans = scan_options.copy()
                print(f"✅ Tous les scans sélectionnés ({len(selected_scans)} scans)")
                break
            
            # Parse de la sélection
            selected_indices = set();
            parts = user_input.split(',')
            
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # Gestion des plages (ex: 1-5)
                    start, end = map(int, part.split('-'))
                    selected_indices.update(range(start, end + 1))
                else:
                    # Numéro individuel
                    selected_indices.add(int(part))
            
            # Validation des indices
            valid_indices = [i for i in selected_indices if 1 <= i <= len(scan_options)]
            if not valid_indices:
                print("❌ Aucun numéro valide sélectionné")
                continue
            
            selected_scans = [scan_options[i-1] for i in valid_indices]
            print(f"✅ {len(selected_scans)} scan(s) sélectionné(s)")
            break;
            
        except ValueError:
            print("❌ Format invalide. Utilisez des numéros, plages (1-5) ou 'all'")
        except KeyboardInterrupt:
            print("\n❌ Sélection interrompue")
            return []
    
    return selected_scans

def save_selected_scans(selected_scans):
    """
    Sauvegarde les scans sélectionnés dans un fichier JSON
    """
    if not selected_scans:
        return False
    
    # Préparer les données pour la sauvegarde
    selected_data = {
        'selected_scans': selected_scans,
        'selection_timestamp': datetime.now().isoformat(),
        'total_selected': len(selected_scans)
    }
    
    with open('selected_scans.json', 'w', encoding='utf-8') as f:
        json.dump(selected_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Sélection sauvegardée dans 'selected_scans.json'")
    return True

def create_reports_from_selected_scans(api, selected_scans):
    """
    Crée des rapports PDF et CSV pour tous les scans sélectionnés
    """
    from config import REPORT_CONFIGS
    if not selected_scans:
        print("❌ Aucun scan sélectionné pour la création de rapports")
        return []
    
    print("\n" + "=" * 80)
    print("📊 CRÉATION DES RAPPORTS POUR LES SCANS SÉLECTIONNÉS")
    print("=" * 80)
    
    report_configs = REPORT_CONFIGS
    created_reports = []
    total_reports = len(selected_scans) * len(report_configs)
    current_report = 0

    created_reports = []
    for scan in selected_scans:
        scan_id = scan['scan_id']
        scan_title = scan['title']
        scan_date = scan['formatted_date']
        print(f"\n🔄 Traitement du scan: [{scan_date}] {scan_title}")
        print(f"   ID: {scan_id}")
        scan_reports = {
            'scan_info': scan,
            'reports': []
        }
        # Découper les configs en lots de 8
        configs = list(report_configs)
        for i in range(0, len(configs), MAX_REPORTS):
            batch = configs[i:i+MAX_REPORTS]
            batch_results = []
            for config in batch:
                report_title = scan_title
                print(f"   📄 Création {config['description']}...")
                report_id = api.create_report_scanbased(
                    scan_id=scan_id,
                    template_id=config['template_id'],
                    output_format=config['output_format'],
                    report_title=report_title
                )
                if report_id:
                    print(f"   ✅ {config['description']} créé: {report_id}")
                    batch_results.append({
                        'report_id': report_id,
                        'template_id': config['template_id'],
                        'output_format': config['output_format'],
                        'report_title': scan_title,
                        'description': config['description'],
                        'status': 'created'
                    })
                else:
                    print(f"   ❌ Échec de création du {config['description']}")
            # Attendre la fin des rapports du lot
            wait_for_reports_to_finish(api, [r['report_id'] for r in batch_results])
            scan_reports['reports'].extend(batch_results)
        if scan_reports['reports']:
            created_reports.append(scan_reports)

    # Résumé de création
    total_created = sum(len(scan_reports['reports']) for scan_reports in created_reports)
    total_failed = total_reports - total_created

    print(f"\n📊 RÉSUMÉ DE CRÉATION:")
    print(f"   ✅ Rapports créés avec succès: {total_created}")
    if total_failed > 0:
        print(f"   ❌ Rapports en échec: {total_failed}")
    print(f"   📁 Scans traités: {len(created_reports)}/{len(selected_scans)}")

    return created_reports

def create_reports_from_selected_templates(api, selected_templates):
    """
    Crée des rapports PDF et CSV pour tous les templates sélectionnés
    """
    if not selected_templates:
        print("❌ Aucun scan sélectionné pour la création de rapports")
        return []
    
    print("\n" + "=" * 80)
    print("📊 CRÉATION DES RAPPORTS POUR LES TEMPLATES SÉLECTIONNÉS")
    print("=" * 80)
    
    
    created_reports = []
    total_reports = len(selected_templates)

    # Préparer la liste de jobs (un par template)
    jobs = []
    for template in selected_templates:
        jobs.append(template)

    def create_job(template):
        template_id = template['template_id']
        template_title = template['name']
        template_date = datetime.today().strftime("%d/%m/%Y %H:%M")
        progress = f"({jobs.index(template)+1}/{len(jobs)})"
        report_title = template_title
        print(f"\n🔄 Traitement du template: [{template_date}] {template_title}")
        print(f"   ID: {template_id}")
        print(f"   📄 {progress} Création {report_title}...")
        report_id = api.create_report_hostbased(
            template_id=template_id,
            output_format=template['output_format'],
            report_title=report_title
        )
        if report_id:
            print(f"   ✅ {template_title} créé: {report_id}")
        else:
            print(f"   ❌ Échec de création du {template['description']}")
        return {
            'template': template,
            'report_id': report_id
        }

    # Utilise la logique de lot
    batch = []
    batch_results = []
    for template in jobs:
        result = create_job(template)
        if result['report_id']:
            batch.append(result)
        if len(batch) == MAX_REPORTS:
            wait_for_reports_to_finish(api, [r['report_id'] for r in batch])
            batch_results.extend(batch)
            batch = []
    if batch:
        wait_for_reports_to_finish(api, [r['report_id'] for r in batch])
        batch_results.extend(batch)

    # Regroupe les résultats
    for result in batch_results:
        template = result['template']
        report_id = result['report_id']
        if not report_id:
            continue
        template_reports = {
            'template_info': template,
            'reports': [{
                'report_id': report_id,
                'template_id': template['template_id'],
                'output_format': template['output_format'],
                'report_title': template['name'],
                'description': template['description'],
                'status': 'created'
            }]
        }
        created_reports.append(template_reports)

    # Résumé de création
    total_created = sum(len(template_reports['reports']) for template_reports in created_reports)
    total_failed = total_reports - total_created

    print(f"\n📊 RÉSUMÉ DE CRÉATION:")
    print(f"   ✅ Rapports créés avec succès: {total_created}")
    if total_failed > 0:
        print(f"   ❌ Rapports en échec: {total_failed}")
    print(f"   📁 Scans traités: {len(created_reports)}/{len(selected_templates)}")

    return created_reports

def remplacer_date_par_aujourdhui(texte):
    # Motif regex pour une date au format yyyymmdd
    motif = r'\b\d{8}\b'

    # Date du jour au format yyyymmdd
    date_aujourdhui = datetime.today().strftime('%Y%m%d')

    # Remplacement
    texte_modifie = re.sub(motif, date_aujourdhui, texte)

    return texte_modifie

import time

def wait_until_ready_and_download(api, report_id, max_wait=300, interval=30):
    """
    Attend que le rapport soit prêt (Finished), puis le télécharge automatiquement.
    
    Args:
        api: instance de QualysAPI
        report_id: ID du rapport à surveiller
        max_wait: temps max d'attente en secondes (par défaut 5 minutes)
        interval: intervalle de vérification en secondes
    """
    waited = 0
    interval = 30
    while waited < max_wait:
        status = api.check_report_status(report_id)
        if status == "Finished":
            print(f"📥 Rapport prêt. Téléchargement...")
            filename = api.download_report(report_id)
            return filename
        elif status in ["Error", "Cancelled"]:
            print(f"❌ Rapport échoué ou annulé.")
            return None
        else:
            print(f"⏳ En attente... Statut actuel: {status}. Nouvelle vérification dans {interval}s.")
            time.sleep(interval)
            waited += interval

    print("⚠️ Temps d'attente dépassé. Rapport non prêt.")
    return None

def wait_for_reports_to_finish(api, report_ids, interval=30):
    """
    Attend que tous les rapports du lot soient terminés avant de continuer.
    """
    import time
    finished = set()
    while len(finished) < len(report_ids):
        for report_id in report_ids:
            if report_id in finished:
                continue
            status = api.check_report_status(report_id)
            if status == "Finished":
                finished.add(report_id)
            elif status in ["Error", "Cancelled"]:
                finished.add(report_id)
        if len(finished) < len(report_ids):
            print(f"⏳ Attente des rapports en cours... ({len(finished)}/{len(report_ids)} terminés)")
            time.sleep(interval)

MAX_REPORTS = 8

def create_reports_with_limit(api, items, create_func):
    """
    Crée les rapports par lots de MAX_REPORTS, en attendant que chaque lot soit terminé.
    """
    all_reports = []
    batch = []
    for item in items:
        report_id = create_func(item)
        if report_id:
            batch.append(report_id)
        if len(batch) == MAX_REPORTS:
            wait_for_reports_to_finish(api, batch, interval=30)
            all_reports.extend(batch)
            batch = []
    if batch:
        wait_for_reports_to_finish(api, batch, interval=30)
        all_reports.extend(batch)
    return all_reports