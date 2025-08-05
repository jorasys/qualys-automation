"""
Report service - handles report creation and management
Refactored from utils.py
"""
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..api.qualys_client import QualysClient
from ..core.config import config
from ..core.exceptions import ReportError, APIError
from ..core.database import db_manager
from ..models.scan_report import ScanReport
from ..models.sync_log import SyncLog


class ReportService:
    """Service for managing Qualys reports"""
    
    def __init__(self, qualys_client: QualysClient):
        self.qualys_client = qualys_client
        self.reports_config = config.reports
    
    def create_reports_from_selected_scans(self, selected_scans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create reports for selected scans with slot and rate limiting controls
        Refactored from utils.py
        """
        if not selected_scans:
            raise ReportError("No scans selected for report creation")
        
        print("\n" + "=" * 80)
        print("📊 CRÉATION DES RAPPORTS POUR LES SCANS SÉLECTIONNÉS")
        print("=" * 80)
        
        # Get scan-based templates from configuration
        scan_templates = config.get_scan_templates()
        
        created_reports = []
        total_reports = len(selected_scans) * len(scan_templates)
        current_report = 0
        
        # Display initial rate limit info
        rate_info = self.qualys_client.get_rate_limit_info()
        if rate_info['remaining'] is not None:
            print(f"📊 Requêtes API disponibles: {rate_info['remaining']}")
        
        with db_manager.get_session() as session:
            for scan in selected_scans:
                scan_id = scan['scan_id']
                scan_title = scan['title']
                scan_date = scan['formatted_date']
                
                print(f"\n🔄 Traitement du scan: [{scan_date}] {scan_title}")
                print(f"   ID: {scan_id}")
                print("-" * 60)
                
                scan_reports = {
                    'scan_info': scan,
                    'reports': []
                }
                
                for template in scan_templates:
                    current_report += 1
                    progress = f"({current_report}/{total_reports})"
                    
                    # CONTRÔLE 1: Vérifier les slots disponibles avant création
                    print(f"   🔍 Vérification des slots disponibles...")
                    if not self.qualys_client.wait_for_report_slots(required_slots=1, max_wait=300):
                        print(f"   ⚠️  Pas de slots disponibles, arrêt de la création de rapports")
                        break
                    
                    report_title = scan_title
                    
                    print(f"   📄 {progress} Création {template['description']}...")
                    
                    try:
                        report_id = self.qualys_client.create_report_scanbased(
                            scan_id=scan_id,
                            template_id=template['template_id'],
                            output_format=template['output_format'],
                            report_title=report_title
                        )
                        
                        if report_id:
                            # Save to database
                            scan_report = ScanReport(
                                qualys_report_id=report_id,
                                report_type=template['output_format'],
                                scan_date=datetime.strptime(scan['date'], "%Y-%m-%dT%H:%M:%SZ") if 'date' in scan else None,
                                status="created"
                            )
                            session.add(scan_report)
                            
                            report_info = {
                                'report_id': report_id,
                                'template_id': template['template_id'],
                                'output_format': template['output_format'],
                                'report_title': report_title,
                                'description': template['description'],
                                'status': 'created'
                            }
                            scan_reports['reports'].append(report_info)
                            print(f"   ✅ {template['description']} créé: {report_id}")
                            
                            # CONTRÔLE 2: Pause entre créations pour éviter la surcharge
                            if current_report < total_reports:
                                print(f"   ⏳ Pause de 2 secondes avant le prochain rapport...")
                                time.sleep(2)
                        else:
                            print(f"   ❌ Échec de création du {template['description']}")
                    
                    except Exception as e:
                        print(f"   ❌ Erreur lors de la création du {template['description']}: {e}")
                        # En cas d'erreur API, pause plus longue
                        if "rate" in str(e).lower() or "limit" in str(e).lower():
                            print(f"   ⏳ Pause de 60 secondes suite à une limitation API...")
                            time.sleep(60)
                
                if scan_reports['reports']:
                    created_reports.append(scan_reports)
            
            # Log the operation
            total_created = sum(len(scan_reports['reports']) for scan_reports in created_reports)
            sync_log = SyncLog(
                source="qualys",
                operation="create_scan_reports",
                timestamp=datetime.now(),
                status="success" if total_created > 0 else "warning",
                details=f"Created {total_created} reports from {len(selected_scans)} scans",
                records_processed=total_created
            )
            session.add(sync_log)
        
        # Summary
        total_created = sum(len(scan_reports['reports']) for scan_reports in created_reports)
        total_failed = total_reports - total_created
        
        print(f"\n📊 RÉSUMÉ DE CRÉATION:")
        print(f"   ✅ Rapports créés avec succès: {total_created}")
        if total_failed > 0:
            print(f"   ❌ Rapports en échec: {total_failed}")
        print(f"   📁 Scans traités: {len(created_reports)}/{len(selected_scans)}")
        
        return created_reports
    
    def create_reports_from_selected_templates(self, selected_templates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create reports for selected templates with slot and rate limiting controls
        Refactored from utils.py
        """
        if not selected_templates:
            raise ReportError("No templates selected for report creation")
        
        print("\n" + "=" * 80)
        print("📊 CRÉATION DES RAPPORTS POUR LES TEMPLATES SÉLECTIONNÉS")
        print("=" * 80)
        
        created_reports = []
        total_reports = len(selected_templates)
        current_report = 0
        
        # Display initial rate limit info
        rate_info = self.qualys_client.get_rate_limit_info()
        if rate_info['remaining'] is not None:
            print(f"📊 Requêtes API disponibles: {rate_info['remaining']}")
        
        with db_manager.get_session() as session:
            for template in selected_templates:
                template_id = template['template_id']
                template_title = template['name']
                template_date = datetime.today().strftime("%d/%m/%Y %H:%M")
                
                print(f"\n🔄 Traitement du template: [{template_date}] {template_title}")
                print(f"   ID: {template_id}")
                print("-" * 60)
                
                # CONTRÔLE 1: Vérifier les slots disponibles avant création
                print(f"   🔍 Vérification des slots disponibles...")
                if not self.qualys_client.wait_for_report_slots(required_slots=1, max_wait=300):
                    print(f"   ⚠️  Pas de slots disponibles, arrêt de la création de rapports")
                    break
                
                template_reports = {
                    'template_info': template,
                    'reports': []
                }
                
                current_report += 1
                progress = f"({current_report}/{total_reports})"
                
                report_title = template_title
                
                print(f"   📄 {progress} Création {report_title}...")
                
                try:
                    report_id = self.qualys_client.create_report_hostbased(
                        template_id=template_id,
                        output_format=template['output_format'],
                        report_title=report_title
                    )
                    
                    if report_id:
                        # Save to database
                        scan_report = ScanReport(
                            qualys_report_id=report_id,
                            report_type=template['output_format'],
                            scan_date=datetime.now(),
                            status="created"
                        )
                        session.add(scan_report)
                        
                        report_info = {
                            'report_id': report_id,
                            'template_id': template_id,
                            'output_format': template['output_format'],
                            'report_title': report_title,
                            'description': template['description'],
                            'status': 'created'
                        }
                        template_reports['reports'].append(report_info)
                        print(f"   ✅ {template_title} créé: {report_id}")
                        
                        # CONTRÔLE 2: Pause entre créations pour éviter la surcharge
                        if current_report < total_reports:
                            print(f"   ⏳ Pause de 2 secondes avant le prochain rapport...")
                            time.sleep(2)
                    else:
                        print(f"   ❌ Échec de création du {template['description']}")
                
                except Exception as e:
                    print(f"   ❌ Erreur lors de la création du {template['description']}: {e}")
                    # En cas d'erreur API, pause plus longue
                    if "rate" in str(e).lower() or "limit" in str(e).lower():
                        print(f"   ⏳ Pause de 60 secondes suite à une limitation API...")
                        time.sleep(60)
                
                if template_reports['reports']:
                    created_reports.append(template_reports)
            
            # Log the operation
            total_created = sum(len(template_reports['reports']) for template_reports in created_reports)
            sync_log = SyncLog(
                source="qualys",
                operation="create_template_reports",
                timestamp=datetime.now(),
                status="success" if total_created > 0 else "warning",
                details=f"Created {total_created} reports from {len(selected_templates)} templates",
                records_processed=total_created
            )
            session.add(sync_log)
        
        # Summary
        total_created = sum(len(template_reports['reports']) for template_reports in created_reports)
        total_failed = total_reports - total_created
        
        print(f"\n📊 RÉSUMÉ DE CRÉATION:")
        print(f"   ✅ Rapports créés avec succès: {total_created}")
        if total_failed > 0:
            print(f"   ❌ Rapports en échec: {total_failed}")
        print(f"   📁 Templates traités: {len(created_reports)}/{len(selected_templates)}")
        
        return created_reports
    
    def wait_until_ready_and_download(self, report_id: str, max_wait: int = 300, interval: int = 10) -> Optional[str]:
        """
        Wait for report to be ready and download it
        Refactored from utils.py
        """
        waited = 0
        
        with db_manager.get_session() as session:
            while waited < max_wait:
                try:
                    status = self.qualys_client.check_report_status(report_id)
                    
                    if status == "Finished":
                        print(f"📥 Rapport prêt. Téléchargement...")
                        filename = self.qualys_client.download_report(
                            report_id, 
                            download_path=self.reports_config.download_path
                        )
                        
                        if filename:
                            # Update database record
                            scan_report = session.query(ScanReport).filter(
                                ScanReport.qualys_report_id == report_id
                            ).first()
                            
                            if scan_report:
                                scan_report.file_path = filename
                                scan_report.status = "downloaded"
                        
                        return filename
                    
                    elif status in ["Error", "Cancelled"]:
                        print(f"❌ Rapport échoué ou annulé.")
                        
                        # Update database record
                        scan_report = session.query(ScanReport).filter(
                            ScanReport.qualys_report_id == report_id
                        ).first()
                        
                        if scan_report:
                            scan_report.status = "error"
                        
                        return None
                    
                    else:
                        print(f"⏳ En attente... Statut actuel: {status}. Nouvelle vérification dans {interval}s.")
                        time.sleep(interval)
                        waited += interval
                
                except Exception as e:
                    print(f"❌ Erreur lors de la vérification du statut: {e}")
                    time.sleep(interval)
                    waited += interval
        
        print("⚠️ Temps d'attente dépassé. Rapport non prêt.")
        return None
    
    def get_report_statistics(self) -> Dict[str, Any]:
        """Get report statistics from database"""
        with db_manager.get_session() as session:
            total_reports = session.query(ScanReport).count()
            
            status_stats = session.query(
                ScanReport.status,
                session.query(ScanReport).filter(ScanReport.status == ScanReport.status).count()
            ).group_by(ScanReport.status).all()
            
            type_stats = session.query(
                ScanReport.report_type,
                session.query(ScanReport).filter(ScanReport.report_type == ScanReport.report_type).count()
            ).group_by(ScanReport.report_type).all()
            
            return {
                'total': total_reports,
                'by_status': dict(status_stats),
                'by_type': dict(type_stats)
            }
    
    def create_reports_with_smart_batching(self, reports_to_create: List[Dict[str, Any]],
                                         batch_size: int = 4) -> List[Dict[str, Any]]:
        """
        Create reports with intelligent batching and slot management
        
        Args:
            reports_to_create: List of report configurations to create
            batch_size: Maximum number of reports to create in parallel
            
        Returns: List of created report information
        """
        if not reports_to_create:
            return []
        
        print(f"\n🔄 CRÉATION INTELLIGENTE DE {len(reports_to_create)} RAPPORTS")
        print(f"📊 Taille des lots: {batch_size} rapports maximum")
        print("=" * 60)
        
        created_reports = []
        total_batches = (len(reports_to_create) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(reports_to_create))
            batch = reports_to_create[start_idx:end_idx]
            
            print(f"\n📦 LOT {batch_num + 1}/{total_batches} ({len(batch)} rapports)")
            print("-" * 40)
            
            # Vérifier les slots disponibles pour ce lot
            required_slots = len(batch)
            print(f"🔍 Vérification de {required_slots} slot(s) disponible(s)...")
            
            if not self.qualys_client.wait_for_report_slots(required_slots=required_slots, max_wait=600):
                print(f"⚠️  Impossible d'obtenir {required_slots} slots, réduction de la taille du lot")
                # Réduire la taille du lot et réessayer
                for report_config in batch:
                    if self.qualys_client.wait_for_report_slots(required_slots=1, max_wait=300):
                        created_report = self._create_single_report(report_config)
                        if created_report:
                            created_reports.append(created_report)
                        time.sleep(3)  # Pause entre chaque rapport
                    else:
                        print(f"⚠️  Arrêt de la création, pas de slots disponibles")
                        break
            else:
                # Créer tous les rapports du lot
                for i, report_config in enumerate(batch):
                    print(f"   📄 Rapport {i+1}/{len(batch)}: {report_config.get('title', 'Sans titre')}")
                    
                    created_report = self._create_single_report(report_config)
                    if created_report:
                        created_reports.append(created_report)
                    
                    # Pause entre les rapports sauf pour le dernier
                    if i < len(batch) - 1:
                        time.sleep(2)
            
            # Pause entre les lots
            if batch_num < total_batches - 1:
                print(f"⏳ Pause de 5 secondes avant le prochain lot...")
                time.sleep(5)
        
        print(f"\n✅ Création terminée: {len(created_reports)}/{len(reports_to_create)} rapports créés")
        return created_reports
    
    def _create_single_report(self, report_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a single report from configuration
        
        Args:
            report_config: Report configuration dict
            
        Returns: Created report info or None if failed
        """
        try:
            if report_config.get('type') == 'scan_based':
                report_id = self.qualys_client.create_report_scanbased(
                    scan_id=report_config['scan_id'],
                    template_id=report_config['template_id'],
                    output_format=report_config['output_format'],
                    report_title=report_config['title']
                )
            else:  # host_based
                report_id = self.qualys_client.create_report_hostbased(
                    template_id=report_config['template_id'],
                    output_format=report_config['output_format'],
                    report_title=report_config['title']
                )
            
            if report_id:
                # Save to database
                with db_manager.get_session() as session:
                    scan_report = ScanReport(
                        qualys_report_id=report_id,
                        report_type=report_config['output_format'],
                        scan_date=datetime.now(),
                        status="created"
                    )
                    session.add(scan_report)
                
                return {
                    'report_id': report_id,
                    'title': report_config['title'],
                    'type': report_config.get('type', 'unknown'),
                    'status': 'created'
                }
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            if "rate" in str(e).lower() or "limit" in str(e).lower():
                print(f"   ⏳ Pause de 60 secondes suite à une limitation API...")
                time.sleep(60)
        
        return None
    
    def get_current_api_status(self) -> Dict[str, Any]:
        """Get current API status including rate limits and running reports"""
        try:
            rate_info = self.qualys_client.get_rate_limit_info()
            running_count = self.qualys_client.get_running_reports_count()
            running_reports = self.qualys_client.get_running_reports()
            
            return {
                'rate_limit': {
                    'remaining': rate_info['remaining'],
                    'reset': rate_info['reset'],
                    'last_request': rate_info['last_request']
                },
                'reports': {
                    'running_count': running_count,
                    'max_slots': self.qualys_client.max_running_reports,
                    'available_slots': self.qualys_client.max_running_reports - running_count,
                    'running_reports': running_reports[:5]  # First 5 for display
                }
            }
        except Exception as e:
            return {
                'error': str(e),
                'rate_limit': {'remaining': None},
                'reports': {'running_count': None, 'available_slots': None}
            }