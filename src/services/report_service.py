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
        Create reports for selected scans using the new smart batching architecture
        """
        if not selected_scans:
            raise ReportError("No scans selected for report creation")
        
        print("\n" + "=" * 80)
        print("📊 CRÉATION DES RAPPORTS POUR LES SCANS SÉLECTIONNÉS")
        print("=" * 80)
        
        # Get scan-based templates from configuration
        scan_templates = config.get_scan_templates()
        
        # Build list of all report configurations to create
        reports_to_create = []
        for scan in selected_scans:
            scan_id = scan['scan_id']
            scan_title = scan['title']
            scan_date = scan.get('date')
            
            for template in scan_templates:
                report_config = {
                    'type': 'scan_based',
                    'scan_id': scan_id,
                    'template_id': template['template_id'],
                    'output_format': template['output_format'],
                    'title': scan_title,
                    'description': template['description'],
                    'scan_info': scan,
                    'template_info': template,
                    'scan_date': datetime.strptime(scan_date, "%Y-%m-%dT%H:%M:%SZ") if scan_date else None
                }
                reports_to_create.append(report_config)
        
        print(f"📋 Total de {len(reports_to_create)} rapports à créer")
        print(f"   📊 {len(selected_scans)} scans × {len(scan_templates)} templates")
        
        # Display initial rate limit info
        rate_info = self.qualys_client.get_rate_limit_info()
        if rate_info['remaining'] is not None:
            print(f"📊 Requêtes API disponibles: {rate_info['remaining']}")
        
        # Use the new smart batching system
        processed_reports = self.create_reports_with_smart_batching_v2(reports_to_create)
        
        # Log the operation
        successful_reports = [r for r in processed_reports if r['status'] == 'downloaded']
        with db_manager.get_session() as session:
            sync_log = SyncLog(
                source="qualys",
                operation="create_scan_reports_v2",
                timestamp=datetime.now(),
                status="success" if successful_reports else "warning",
                details=f"Processed {len(processed_reports)} reports from {len(selected_scans)} scans using smart batching",
                records_processed=len(successful_reports)
            )
            session.add(sync_log)
        
        # Convert to legacy format for compatibility
        legacy_format = self._convert_to_legacy_format(processed_reports, selected_scans, 'scan')
        
        return legacy_format
    
    def create_reports_from_selected_templates(self, selected_templates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create reports for selected templates using the new smart batching architecture
        """
        if not selected_templates:
            raise ReportError("No templates selected for report creation")
        
        print("\n" + "=" * 80)
        print("📊 CRÉATION DES RAPPORTS POUR LES TEMPLATES SÉLECTIONNÉS")
        print("=" * 80)
        
        # Build list of all report configurations to create
        reports_to_create = []
        for template in selected_templates:
            template_id = template['template_id']
            template_title = template['name']
            
            report_config = {
                'type': 'host_based',
                'template_id': template_id,
                'output_format': template['output_format'],
                'title': template_title,
                'description': template['description'],
                'template_info': template
            }
            reports_to_create.append(report_config)
        
        print(f"📋 Total de {len(reports_to_create)} rapports à créer")
        
        # Display initial rate limit info
        rate_info = self.qualys_client.get_rate_limit_info()
        if rate_info['remaining'] is not None:
            print(f"📊 Requêtes API disponibles: {rate_info['remaining']}")
        
        # Use the new smart batching system
        processed_reports = self.create_reports_with_smart_batching_v2(reports_to_create)
        
        # Log the operation
        successful_reports = [r for r in processed_reports if r['status'] == 'downloaded']
        with db_manager.get_session() as session:
            sync_log = SyncLog(
                source="qualys",
                operation="create_template_reports_v2",
                timestamp=datetime.now(),
                status="success" if successful_reports else "warning",
                details=f"Processed {len(processed_reports)} reports from {len(selected_templates)} templates using smart batching",
                records_processed=len(successful_reports)
            )
            session.add(sync_log)
        
        # Convert to legacy format for compatibility
        legacy_format = self._convert_to_legacy_format(processed_reports, selected_templates, 'template')
        
        return legacy_format
    
    def _convert_to_legacy_format(self, processed_reports: List[Dict[str, Any]],
                                 source_items: List[Dict[str, Any]],
                                 source_type: str) -> List[Dict[str, Any]]:
        """
        Convert new format results to legacy format for backward compatibility
        
        Args:
            processed_reports: Reports processed by the new system
            source_items: Original scans or templates
            source_type: 'scan' or 'template'
            
        Returns: Legacy format results
        """
        legacy_results = []
        
        if source_type == 'scan':
            # Group by scan
            for scan in source_items:
                scan_id = scan['scan_id']
                scan_reports = {
                    'scan_info': scan,
                    'reports': []
                }
                
                # Find all reports for this scan
                for report in processed_reports:
                    if report['config'].get('scan_id') == scan_id:
                        legacy_report = {
                            'report_id': report['report_id'],
                            'template_id': report['config']['template_id'],
                            'output_format': report['config']['output_format'],
                            'report_title': report['config']['title'],
                            'description': report['config']['description'],
                            'status': report['status'],
                            'filename': report.get('filename')
                        }
                        scan_reports['reports'].append(legacy_report)
                
                if scan_reports['reports']:
                    legacy_results.append(scan_reports)
        
        else:  # template
            # Group by template
            for template in source_items:
                template_id = template['template_id']
                template_reports = {
                    'template_info': template,
                    'reports': []
                }
                
                # Find all reports for this template
                for report in processed_reports:
                    if report['config'].get('template_id') == template_id:
                        legacy_report = {
                            'report_id': report['report_id'],
                            'template_id': template_id,
                            'output_format': report['config']['output_format'],
                            'report_title': report['config']['title'],
                            'description': report['config']['description'],
                            'status': report['status'],
                            'filename': report.get('filename')
                        }
                        template_reports['reports'].append(legacy_report)
                
                if template_reports['reports']:
                    legacy_results.append(template_reports)
        
        return legacy_results
    
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
    
    def create_and_wait_reports_batch(self, reports_configs: List[Dict[str, Any]],
                                    max_batch_size: int = 8) -> List[Dict[str, Any]]:
        """
        Create a batch of reports and wait until all are completely generated
        
        Args:
            reports_configs: List of report configurations to create
            max_batch_size: Maximum number of reports to create in this batch
            
        Returns: List of successfully created and completed reports with download info
        """
        if not reports_configs:
            return []
        
        # Limit batch size to available slots and max_batch_size
        available_slots = self.qualys_client.max_running_reports - self.qualys_client.get_running_reports_count()
        actual_batch_size = min(len(reports_configs), max_batch_size, available_slots)
        
        if actual_batch_size <= 0:
            print("⚠️  Aucun slot disponible pour créer des rapports")
            return []
        
        batch = reports_configs[:actual_batch_size]
        print(f"\n📦 CRÉATION D'UN LOT DE {len(batch)} RAPPORTS")
        print("=" * 50)
        
        # Phase 1: Create all reports in the batch
        created_report_ids = []
        created_reports_info = []
        
        for i, report_config in enumerate(batch):
            print(f"📄 Création {i+1}/{len(batch)}: {report_config.get('title', 'Sans titre')}")
            
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
                    created_report_ids.append(report_id)
                    created_reports_info.append({
                        'report_id': report_id,
                        'config': report_config,
                        'status': 'created'
                    })
                    print(f"   ✅ Créé: {report_id}")
                    
                    # Save to database immediately
                    with db_manager.get_session() as session:
                        scan_report = ScanReport(
                            qualys_report_id=report_id,
                            report_type=report_config['output_format'],
                            scan_date=datetime.now(),
                            status="created"
                        )
                        session.add(scan_report)
                else:
                    print(f"   ❌ Échec de création")
                    
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
            
            # Small pause between creations
            if i < len(batch) - 1:
                time.sleep(2)
        
        if not created_report_ids:
            print("❌ Aucun rapport créé dans ce lot")
            return []
        
        print(f"\n🔄 SURVEILLANCE DE {len(created_report_ids)} RAPPORTS EN GÉNÉRATION")
        print("-" * 50)
        
        # Phase 2: Monitor all reports until completion
        completed_reports = self.monitor_reports_until_completion(
            created_report_ids,
            max_wait=3600  # 1 hour max wait
        )
        
        # Phase 3: Download completed reports immediately
        final_reports = []
        for report_info in created_reports_info:
            report_id = report_info['report_id']
            if report_id in completed_reports:
                print(f"\n📥 Téléchargement du rapport {report_id}...")
                try:
                    filename = self.qualys_client.download_report(
                        report_id,
                        download_path=self.reports_config.download_path
                    )
                    
                    if filename:
                        # Update database
                        with db_manager.get_session() as session:
                            scan_report = session.query(ScanReport).filter(
                                ScanReport.qualys_report_id == report_id
                            ).first()
                            
                            if scan_report:
                                scan_report.file_path = filename
                                scan_report.status = "downloaded"
                        
                        report_info.update({
                            'status': 'downloaded',
                            'filename': filename
                        })
                        final_reports.append(report_info)
                        print(f"   ✅ Téléchargé: {filename}")
                    else:
                        print(f"   ❌ Échec du téléchargement")
                        report_info['status'] = 'download_failed'
                        final_reports.append(report_info)
                        
                except Exception as e:
                    print(f"   ❌ Erreur de téléchargement: {e}")
                    report_info['status'] = 'download_error'
                    final_reports.append(report_info)
            else:
                print(f"⚠️  Rapport {report_id} non terminé dans les temps")
                report_info['status'] = 'timeout'
                final_reports.append(report_info)
        
        return final_reports
    
    def monitor_reports_until_completion(self, report_ids: List[str],
                                       max_wait: int = 3600,
                                       check_interval: int = 30) -> List[str]:
        """
        Monitor reports until they are all completed (Finished status)
        
        Args:
            report_ids: List of report IDs to monitor
            max_wait: Maximum wait time in seconds
            check_interval: Check interval in seconds
            
        Returns: List of report IDs that completed successfully
        """
        if not report_ids:
            return []
        
        completed_reports = []
        failed_reports = []
        waited = 0
        
        print(f"🔍 Surveillance de {len(report_ids)} rapports...")
        
        while waited < max_wait and len(completed_reports) + len(failed_reports) < len(report_ids):
            remaining_reports = [rid for rid in report_ids
                               if rid not in completed_reports and rid not in failed_reports]
            
            if not remaining_reports:
                break
            
            print(f"⏳ Vérification ({waited}s/{max_wait}s) - Restants: {len(remaining_reports)}")
            
            for report_id in remaining_reports:
                try:
                    status = self.qualys_client.check_report_status(report_id)
                    
                    if status == "Finished":
                        completed_reports.append(report_id)
                        print(f"   ✅ Rapport {report_id} terminé")
                    elif status in ["Error", "Cancelled"]:
                        failed_reports.append(report_id)
                        print(f"   ❌ Rapport {report_id} échoué: {status}")
                        
                        # Update database
                        with db_manager.get_session() as session:
                            scan_report = session.query(ScanReport).filter(
                                ScanReport.qualys_report_id == report_id
                            ).first()
                            
                            if scan_report:
                                scan_report.status = "error"
                    else:
                        # Still running or queued
                        pass
                        
                except Exception as e:
                    print(f"   ⚠️  Erreur lors de la vérification du rapport {report_id}: {e}")
            
            if len(completed_reports) + len(failed_reports) < len(report_ids):
                time.sleep(check_interval)
                waited += check_interval
        
        # Summary
        if completed_reports:
            print(f"✅ {len(completed_reports)} rapport(s) terminé(s) avec succès")
        if failed_reports:
            print(f"❌ {len(failed_reports)} rapport(s) échoué(s)")
        
        remaining = len(report_ids) - len(completed_reports) - len(failed_reports)
        if remaining > 0:
            print(f"⚠️  {remaining} rapport(s) non terminé(s) dans les temps")
        
        return completed_reports
    
    def create_reports_with_smart_batching_v2(self, reports_to_create: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create reports with intelligent batching and complete generation control
        
        Args:
            reports_to_create: List of report configurations to create
            
        Returns: List of all processed reports with their final status
        """
        if not reports_to_create:
            return []
        
        max_batch_size = self.reports_config.creation_controls.get('batch_size', 4)
        total_reports = len(reports_to_create)
        
        print(f"\n🚀 CRÉATION INTELLIGENTE DE {total_reports} RAPPORTS")
        print(f"📊 Traitement par lots de {max_batch_size} rapports maximum")
        print("=" * 60)
        
        all_processed_reports = []
        remaining_reports = reports_to_create.copy()
        batch_number = 1
        
        while remaining_reports:
            print(f"\n📦 LOT {batch_number}")
            print("-" * 30)
            
            # Process one batch
            batch_results = self.create_and_wait_reports_batch(
                remaining_reports,
                max_batch_size
            )
            
            # Add results to overall list
            all_processed_reports.extend(batch_results)
            
            # Remove processed reports from remaining list
            processed_count = len(batch_results)
            remaining_reports = remaining_reports[processed_count:]
            
            print(f"\n📊 LOT {batch_number} TERMINÉ:")
            print(f"   ✅ Traités: {processed_count}")
            print(f"   📋 Restants: {len(remaining_reports)}")
            
            batch_number += 1
            
            # Pause between batches if there are more to process
            if remaining_reports:
                pause_time = self.reports_config.creation_controls.get('pause_between_reports', 5)
                print(f"⏳ Pause de {pause_time}s avant le prochain lot...")
                time.sleep(pause_time)
        
        # Final summary
        successful = len([r for r in all_processed_reports if r['status'] == 'downloaded'])
        failed = len([r for r in all_processed_reports if r['status'] in ['error', 'timeout', 'download_failed']])
        
        print(f"\n🎉 TRAITEMENT TERMINÉ:")
        print(f"   ✅ Rapports téléchargés: {successful}")
        print(f"   ❌ Rapports échoués: {failed}")
        print(f"   📁 Total traité: {len(all_processed_reports)}")
        
        return all_processed_reports
    
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