"""
Qualys API Client - Refactored version
Handles communication with Qualys API
"""
import requests
import xml.etree.ElementTree as ET
import base64
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..core.config import APIConfig
from ..core.exceptions import APIError, AuthenticationError, ParsingError


class QualysClient:
    """Qualys API client with improved error handling and configuration"""
    
    def __init__(self, api_config: APIConfig):
        self.config = api_config
        self.base_url = f"https://{api_config.base_url}"
        
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
        """Make HTTP request with error handling and retries"""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.config.max_retries + 1):
            try:
                response = self.session.request(method, url, **kwargs)
                
                # Check for authentication errors
                if response.status_code == 401:
                    raise AuthenticationError("Invalid credentials or session expired")
                
                # Check for other HTTP errors
                response.raise_for_status()
                
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt == self.config.max_retries:
                    raise APIError(f"Request failed after {self.config.max_retries + 1} attempts: {e}")
                
                # Wait before retry (simple exponential backoff)
                import time
                time.sleep(2 ** attempt)
        
        raise APIError("Unexpected error in request handling")
    
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