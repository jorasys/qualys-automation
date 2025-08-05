"""
Qualys API Client - Refactored version
Handles communication with Qualys API with rate limiting and report management
"""
import requests
import xml.etree.ElementTree as ET
import base64
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from ..core.config import APIConfig
from ..core.exceptions import APIError, AuthenticationError, ParsingError


class QualysClient:
    """Qualys API client with improved error handling, rate limiting and report management"""
    
    def __init__(self, api_config: APIConfig, reports_config=None):
        self.config = api_config
        self.base_url = f"https://{api_config.base_url}"
        
        # Rate limiting tracking
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
        self.last_request_time = None
        
        # Report management - use config value or default
        if reports_config:
            self.max_running_reports = reports_config.max_running_reports
        else:
            self.max_running_reports = 8
        
        # Initialize session
        self.session = requests.Session()
        
        # Configure proxy if enabled
        if api_config.proxy_url:
            self.session.proxies = {
                'http': api_config.proxy_url,
                'https': api_config.proxy_url
            }
        
        # Set up authentication
        credentials = f"{api_config.username}:{api_config.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        self.session.headers.update({
            'Authorization': f'Basic {encoded_credentials}',
            'X-Requested-With': 'QualysPostman'
        })
        
        # Configure timeout
        self.session.timeout = api_config.timeout
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling, retries and rate limiting"""
        url = f"{self.base_url}{endpoint}"
        
        # Check rate limiting before making request
        self._check_rate_limit()
        
        for attempt in range(self.config.max_retries + 1):
            try:
                self.last_request_time = datetime.now()
                response = self.session.request(method, url, **kwargs)
                
                # Update rate limiting info from headers
                self._update_rate_limit_info(response)
                
                # Check for authentication errors
                if response.status_code == 401:
                    raise AuthenticationError("Invalid credentials or session expired")
                
                # Check for rate limiting
                if response.status_code == 429:
                    print("⚠️  Rate limit atteint, attente avant nouvelle tentative...")
                    time.sleep(60)  # Wait 1 minute before retry
                    continue
                
                # Check for other HTTP errors
                response.raise_for_status()
                
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt == self.config.max_retries:
                    raise APIError(f"Request failed after {self.config.max_retries + 1} attempts: {e}")
                
                # Wait before retry (simple exponential backoff)
                time.sleep(2 ** attempt)
        
        raise APIError("Unexpected error in request handling")
    
    def _check_rate_limit(self):
        """Check if we're approaching rate limits and warn user"""
        if self.rate_limit_remaining is not None:
            if self.rate_limit_remaining < 10:
                print(f"⚠️  ATTENTION: Seulement {self.rate_limit_remaining} requêtes API restantes!")
                if self.rate_limit_remaining < 5:
                    print("🛑 Arrêt recommandé pour éviter le blocage API")
                    response = input("Continuer quand même? (oui/non): ").lower().strip()
                    if response not in ['oui', 'yes', 'y', 'o']:
                        raise APIError("Opération annulée pour préserver le quota API")
    
    def _update_rate_limit_info(self, response: requests.Response):
        """Update rate limiting information from response headers"""
        if 'X-RateLimit-Remaining' in response.headers:
            try:
                self.rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
                print(f"📊 Requêtes API restantes: {self.rate_limit_remaining}")
            except ValueError:
                pass
        
        if 'X-RateLimit-Reset' in response.headers:
            try:
                self.rate_limit_reset = int(response.headers['X-RateLimit-Reset'])
            except ValueError:
                pass
    
    def _parse_xml_response(self, response: requests.Response) -> ET.Element:
        """Parse XML response with error handling"""
        try:
            return ET.fromstring(response.content)
        except ET.ParseError as e:
            raise ParsingError(f"Failed to parse XML response: {e}")
    
    def get_last_30_scans(self) -> Dict[str, Dict[str, str]]:
        """
        Get last 30 scans from Qualys
        Returns: Dict with scan title as key, and dict of {date: scan_id} as value
        """
        try:
            response = self._make_request('GET', '/api/2.0/fo/scan/', params={'action': 'list'})
            root = self._parse_xml_response(response)
            
            scan_list = root.find('.//SCAN_LIST')
            if scan_list is None:
                return {}
            
            scans = scan_list.findall('SCAN')
            if not scans:
                return {}
            
            scan_results = {}
            for scan in scans:
                title_elem = scan.find('TITLE')
                date_elem = scan.find('LAUNCH_DATETIME')
                ref_elem = scan.find('REF')
                
                if title_elem is None or date_elem is None or ref_elem is None:
                    continue
                
                title = title_elem.text
                date = date_elem.text
                scan_id = ref_elem.text
                
                if title in scan_results:
                    scan_results[title][date] = scan_id
                else:
                    scan_results[title] = {date: scan_id}
            
            return scan_results
            
        except Exception as e:
            if isinstance(e, (APIError, AuthenticationError, ParsingError)):
                raise
            raise APIError(f"Failed to get scans: {e}")
    
    def create_report_scanbased(self, scan_id: str, template_id: str, 
                               output_format: str, report_title: str) -> Optional[str]:
        """
        Create a scan-based report
        Returns: Report ID if successful, None otherwise
        """
        data = {
            'action': 'launch',
            'report_type': 'Scan',
            'template_id': template_id,
            'output_format': output_format,
            'report_refs': scan_id,
            'report_title': report_title
        }
        
        try:
            response = self._make_request('POST', '/api/2.0/fo/report/', data=data)
            root = self._parse_xml_response(response)
            
            return self._extract_report_id(root)
            
        except Exception as e:
            if isinstance(e, (APIError, AuthenticationError, ParsingError)):
                raise
            raise APIError(f"Failed to create scan-based report: {e}")
    
    def create_report_hostbased(self, template_id: str, output_format: str, 
                               report_title: str) -> Optional[str]:
        """
        Create a host-based report
        Returns: Report ID if successful, None otherwise
        """
        data = {
            'action': 'launch',
            'template_id': template_id,
            'output_format': output_format,
            'report_title': report_title
        }
        
        try:
            response = self._make_request('POST', '/api/2.0/fo/report/', data=data)
            root = self._parse_xml_response(response)
            
            return self._extract_report_id(root)
            
        except Exception as e:
            if isinstance(e, (APIError, AuthenticationError, ParsingError)):
                raise
            raise APIError(f"Failed to create host-based report: {e}")
    
    def _extract_report_id(self, root: ET.Element) -> Optional[str]:
        """Extract report ID from XML response"""
        item_list = root.find('.//ITEM_LIST')
        if item_list is None:
            return None
        
        items = item_list.findall('ITEM')
        if not items:
            # Check if ITEM_LIST itself contains the data
            items = [item_list] if item_list.find('KEY') is not None else []
        
        if not items:
            return None
        
        report_ids = []
        for item in items:
            key_elem = item.find('KEY')
            value_elem = item.find('VALUE')
            
            if key_elem is None or value_elem is None:
                continue
            
            value = value_elem.text
            if value:
                report_ids.append(value)
        
        return report_ids[-1] if report_ids else None
    
    def check_report_status(self, report_id: str) -> Optional[str]:
        """
        Check report status
        Returns: Status string or None if error
        """
        data = {'action': 'list', 'id': report_id}
        
        try:
            response = self._make_request('POST', '/api/2.0/fo/report/', data=data)
            root = self._parse_xml_response(response)
            
            report_elem = root.find('.//REPORT')
            if report_elem is None:
                return None
            
            status_elem = report_elem.find('./STATUS/STATE')
            return status_elem.text if status_elem is not None else None
            
        except Exception as e:
            if isinstance(e, (APIError, AuthenticationError, ParsingError)):
                raise
            raise APIError(f"Failed to check report status: {e}")
    
    def download_report(self, report_id: str, download_path: Optional[str] = None) -> Optional[str]:
        """
        Download a report and save it to the specified path
        Returns: Full file path if successful, None otherwise
        """
        try:
            # First, get report information
            info_data = {'action': 'list', 'id': report_id}
            info_response = self._make_request('POST', '/api/2.0/fo/report/', data=info_data)
            info_root = self._parse_xml_response(info_response)
            
            report_elem = info_root.find('.//REPORT')
            if report_elem is None:
                raise APIError(f"Report {report_id} not found")
            
            # Extract report metadata
            title = report_elem.findtext('TITLE', default=f"report_{report_id}").strip()
            output_format = report_elem.findtext('OUTPUT_FORMAT', default='bin').lower()
            
            # Generate safe filename
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(" ", "_")
            filename = f"{safe_title}.{output_format}"
            
            # Determine download directory
            if download_path:
                download_dir = Path(download_path)
            else:
                download_dir = Path.home() / "Downloads"
            
            download_dir.mkdir(exist_ok=True)
            filepath = download_dir / filename
            
            # Download the report
            fetch_data = {'action': 'fetch', 'id': report_id}
            fetch_response = self._make_request('POST', '/api/2.0/fo/report/', 
                                              data=fetch_data, stream=True)
            
            # Save to file
            with open(filepath, 'wb') as f:
                for chunk in fetch_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return str(filepath)
            
        except Exception as e:
            if isinstance(e, (APIError, AuthenticationError, ParsingError)):
                raise
            raise APIError(f"Failed to download report: {e}")
    
    def get_report_info(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a report
        Returns: Report information dict or None if error
        """
        data = {'action': 'list', 'id': report_id}
        
        try:
            response = self._make_request('POST', '/api/2.0/fo/report/', data=data)
            root = self._parse_xml_response(response)
            
            report_elem = root.find('.//REPORT')
            if report_elem is None:
                return None
            
            # Extract report information
            info = {}
            for child in report_elem:
                if child.tag == 'STATUS':
                    status_elem = child.find('STATE')
                    info['status'] = status_elem.text if status_elem is not None else None
                else:
                    info[child.tag.lower()] = child.text
            
            return info
            
        except Exception as e:
            if isinstance(e, (APIError, AuthenticationError, ParsingError)):
                raise
            raise APIError(f"Failed to get report info: {e}")
    
    def get_running_reports_count(self) -> int:
        """
        Get count of currently running reports
        Returns: Number of reports in 'Running' status
        """
        try:
            response = self._make_request('POST', '/api/2.0/fo/report/', data={'action': 'list'})
            root = self._parse_xml_response(response)
            
            reports = root.findall('.//REPORT')
            running_count = 0
            
            for report in reports:
                status_elem = report.find('./STATUS/STATE')
                if status_elem is not None and status_elem.text == 'Running':
                    running_count += 1
            
            return running_count
            
        except Exception as e:
            if isinstance(e, (APIError, AuthenticationError, ParsingError)):
                raise
            raise APIError(f"Failed to get running reports count: {e}")
    
    def get_running_reports(self) -> List[Dict[str, Any]]:
        """
        Get list of currently running reports with details
        Returns: List of running report information
        """
        try:
            response = self._make_request('POST', '/api/2.0/fo/report/', data={'action': 'list'})
            root = self._parse_xml_response(response)
            
            reports = root.findall('.//REPORT')
            running_reports = []
            
            for report in reports:
                status_elem = report.find('./STATUS/STATE')
                if status_elem is not None and status_elem.text == 'Running':
                    report_info = {
                        'id': report.findtext('ID'),
                        'title': report.findtext('TITLE'),
                        'status': status_elem.text,
                        'launch_date': report.findtext('LAUNCH_DATETIME'),
                        'type': report.findtext('TYPE')
                    }
                    running_reports.append(report_info)
            
            return running_reports
            
        except Exception as e:
            if isinstance(e, (APIError, AuthenticationError, ParsingError)):
                raise
            raise APIError(f"Failed to get running reports: {e}")
    
    def wait_for_report_slots(self, required_slots: int = 1, max_wait: int = 1800, check_interval: int = 30) -> bool:
        """
        Wait until there are enough free report slots available
        
        Args:
            required_slots: Number of free slots needed
            max_wait: Maximum wait time in seconds (default 30 minutes)
            check_interval: Check interval in seconds
            
        Returns: True if slots are available, False if timeout
        """
        waited = 0
        
        while waited < max_wait:
            try:
                running_count = self.get_running_reports_count()
                available_slots = self.max_running_reports - running_count
                
                print(f"📊 Rapports en cours: {running_count}/{self.max_running_reports} (slots libres: {available_slots})")
                
                if available_slots >= required_slots:
                    return True
                
                if waited == 0:
                    print(f"⏳ Attente de {required_slots} slot(s) libre(s)...")
                    if running_count > 0:
                        running_reports = self.get_running_reports()
                        print("📋 Rapports en cours d'exécution:")
                        for report in running_reports[:5]:  # Show first 5
                            print(f"   - {report['title']} (ID: {report['id']})")
                        if len(running_reports) > 5:
                            print(f"   ... et {len(running_reports) - 5} autres")
                
                print(f"⏳ Nouvelle vérification dans {check_interval}s...")
                time.sleep(check_interval)
                waited += check_interval
                
            except Exception as e:
                print(f"❌ Erreur lors de la vérification des slots: {e}")
                time.sleep(check_interval)
                waited += check_interval
        
        print(f"⚠️  Timeout atteint ({max_wait}s). Slots toujours non disponibles.")
        return False
    
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get current rate limit information"""
        return {
            'remaining': self.rate_limit_remaining,
            'reset': self.rate_limit_reset,
            'last_request': self.last_request_time
        }