import json
from datetime import datetime
from qualys import QualysAPI
from menu import create_scan_menu, create_template_menu
from utils import save_selected_scans, wait_until_ready_and_download, create_reports_from_selected_scans, create_reports_from_selected_templates


def main():
    # Configuration depuis votre environnement Postman
    BASE_URL = "qualysapi.qualys.eu"
    USERNAME = "wha-ep2"  # Remplacez par votre nom d'utilisateur
    PASSWORD = "c4XFr:wH5tHB!!"  # Remplacez par votre mot de passe
    PROXY_URL = "http://127.0.0.1:3128"  # Proxy configuré
    
    print("🚀 Démarrage du script Qualys - Étapes 1 & 2")
    print("=" * 50)
    
    # Initialisation de l'API avec le proxy
    api = QualysAPI(BASE_URL, USERNAME, PASSWORD, PROXY_URL)
    
    # Étape 1: Récupération des scans (équivalent à votre requête 01)
    scan_results = api.get_last_30_scans()
    
    if not scan_results:
        print("❌ Aucun résultat obtenu. Vérifiez vos credentials et la connectivité.")
        return
    
    # Sauvegarde des résultats bruts
    with open('scan_results.json', 'w', encoding='utf-8') as f:
        json.dump(scan_results, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Résultats bruts sauvegardés dans 'scan_results.json'")

    # print("=== EXEMPLE 1: Menu de scans ===")
    scan_menu = create_scan_menu(scan_results)
    # print(f"Résumé: {scan_menu.get_summary()}")
    selected_scans = scan_menu.display_checkbox_menu()

    # Exemple 2: Menu de templates
    templates = [
        {
            'name': '#19-PCI-HostBased_Distribution_Report',
            'template_id': '92297434',
            'output_format': 'pdf',
            'description': 'PCI HostBased Distribution Report (PDF)'
        },
        {
            'name': '#19-PCI-HostBased_Distribution_Report',
            'template_id': '92297443',
            'output_format': 'csv',
            'description': 'PCI HostBased Distribution Report (CSV)'
        },
        {
            'name': '#20-PCI-HostBased_NoDistribution_Report',
            'template_id': '92297435',
            'output_format': 'pdf',
            'description': 'PCI HostBased NoDistribution Report (PDF)'
        },
        {
            'name': '#20-PCI-HostBased_NoDistribution_Report',
            'template_id': '92297457',
            'output_format': 'csv',
            'description': 'PCI HostBased NoDistribution Report (CSV)'
        }
    ]
    
    # print("\n=== EXEMPLE 2: Menu de templates ===")
    template_menu = create_template_menu(templates)
    # print(f"Résumé: {template_menu.get_summary()}")
    selected_templates = template_menu.display_checkbox_menu()
    
    # Étape 2: Sélection interactive des scans avec cases à cocher
    # selected_scans = display_scans_checkbox_menu(scan_results)
    created_reports = []

    if selected_scans:
        # Affichage du résumé de sélection
        print("\n📋 SCANS SÉLECTIONNÉS:")
        print("-" * 60)
        for scan in selected_scans:
            print(f"  ✓ [{scan['formatted_date']}] {scan['title']}")
            print(f"    ID: {scan['scan_id']}")
        
        save_selected_scans(selected_scans)
        print(f"\n🎯 Prêt pour l'étape 3: Génération des rapports pour {len(selected_scans)} scan(s)")
    else:
        print("\n❌ Aucun scan sélectionné. Script terminé.")

    created_scan_reports = create_reports_from_selected_scans(api, selected_scans)


    if created_scan_reports:
        # save_created_reports(created_reports)
        print(f"\n🎯 Prêt pour l'étape 4: Vérification du statut et téléchargement des rapports")
        
        # Affichage des IDs de rapports créés pour référence
        print(f"\n📋 RAPPORTS CRÉÉS (pour référence):")
        for scan_reports in created_scan_reports:
            scan_info = scan_reports['scan_info']
            print(f"  📁 [{scan_info['formatted_date']}] {scan_info['title']}:")
            for report in scan_reports['reports']:
                print(f"    - {report['description']}: {report['report_id']}")
        created_reports.extend(created_scan_reports)
    else:
        print("\n❌ Aucun rapport créé. Vérifiez les erreurs ci-dessus.")

    if selected_templates:
        # Affichage du résumé de sélection
        print("\n📋 TEMPLATES SÉLECTIONNÉS:")
        print("-" * 60)
        for template in selected_templates:
            print(f"  ✓ [{datetime.today().strftime("%d/%m/%Y %H:%M")}] {template['name']}")
            print(f"    ID: {template['template_id']}")
        
        # save_selected_templates(selected_templates)
        print(f"\n🎯 Prêt pour l'étape 3: Génération des rapports pour {len(selected_templates)} template(s)")
    else:
        print("\n❌ Aucun template sélectionné. Script terminé.")

    created_template_reports = create_reports_from_selected_templates(api, selected_templates)
    if created_template_reports:
        # save_created_reports(created_reports)
        print(f"\n🎯 Prêt pour l'étape 4: Vérification du statut et téléchargement des rapports")
        
        # Affichage des IDs de rapports créés pour référence
        print(f"\n📋 RAPPORTS CRÉÉS (pour référence):")
        for template_reports in created_template_reports:
            template_info = template_reports['template_info']
            # print(template_info)
            print(f"  📁 [{datetime.today().strftime("%d/%m/%Y %H:%M")}] {template_info['name']}:")
            for report in template_reports['reports']:
                print(f"    - {report['description']}: {report['report_id']}")
        created_reports.extend(created_template_reports)
    else:
        print("\n❌ Aucun rapport créé. Vérifiez les erreurs ci-dessus.")

    print("\n" + "=" * 80)
    print("📥 TÉLÉCHARGEMENT AUTOMATIQUE DES RAPPORTS PRÊTS")
    print("=" * 80)

    for report_group in created_reports:
        reports = report_group['reports']
        for report in reports:
            report_id = report['report_id']
            description = report.get('description', report.get('report_title', ''))
            print(f"\n🔎 Surveillance du rapport {report_id} ({description})...")
            filename = wait_until_ready_and_download(api, report_id)
            if filename:
                print(f"✅ Rapport téléchargé: {filename}")
            else:
                print(f"❌ Rapport {report_id} non téléchargé.")
    

if __name__ == "__main__":
    main()