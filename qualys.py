import requests
import xml.etree.ElementTree as ET
import base64
import os

downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")

class QualysAPI:
    def __init__(self, base_url, username, password, proxy_url="http://127.0.0.1:3128"):
        self.base_url = f"https://{base_url}"
        self.username = username
        self.password = password
        self.session = requests.Session()
        if proxy_url:
            self.session.proxies = {'http': proxy_url, 'https': proxy_url}
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.session.headers.update({
            'Authorization': f'Basic {encoded_credentials}',
            'X-Requested-With': 'QualysPostman'
        })

    def get_last_30_scans(self):
        url = f"{self.base_url}/api/2.0/fo/scan/"
        params = {'action': 'list'}
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            root = ET.fromstring(response.content)
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
        except Exception:
            return {}

    def create_report_scanbased(self, scan_id, template_id, output_format, report_title):
        url = f"{self.base_url}/api/2.0/fo/report/"
        data = {
            'action': 'launch',
            'report_type': 'Scan',
            'template_id': template_id,
            'output_format': output_format,
            'report_refs': scan_id,
            'report_title': report_title
        }
        try:
            response = self.session.post(url, data=data)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            item_list = root.find('.//ITEM_LIST')
            if item_list is None:
                return None
            items = item_list.findall('ITEM')
            if not items:
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
                report_ids.append(value)
            if report_ids:
                return report_ids[-1]
            else:
                return None
        except Exception:
            return None

    def create_report_hostbased(self, template_id, output_format, report_title):
        url = f"{self.base_url}/api/2.0/fo/report/"
        data = {
            'action': 'launch',
            'template_id': template_id,
            'output_format': output_format,
            'report_title': report_title
        }
        try:
            response = self.session.post(url, data=data)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            item_list = root.find('.//ITEM_LIST')
            if item_list is None:
                return None
            items = item_list.findall('ITEM')
            if not items:
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
                report_ids.append(value)
            if report_ids:
                return report_ids[-1]
            else:
                return None
        except Exception:
            return None

    def check_report_status(self, report_id):
        url = f"{self.base_url}/api/2.0/fo/report/"
        data = {'action': 'list', 'id': report_id}
        try:
            response = self.session.post(url, data=data)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            report_elem = root.find('.//REPORT')
            if report_elem is None:
                return None
            status_elem = report_elem.find('./STATUS/STATE')
            if status_elem is not None:
                return status_elem.text
            else:
                return None
        except Exception:
            return None

    def download_report(self, report_id):
        """
        Télécharge un rapport Qualys et le sauvegarde dans le dossier Downloads.
        """
        url = f"{self.base_url}/api/2.0/fo/report/"
        data = {
            'action': 'fetch',
            'id': report_id
        }

        try:
            info_data = {'action': 'list', 'id': report_id}
            info_response = self.session.post(url, data=info_data)
            info_response.raise_for_status()
            root = ET.fromstring(info_response.content)
            report_elem = root.find('.//REPORT')
            if report_elem is None:
                return None

            title = report_elem.findtext('TITLE', default=f"report_{report_id}").strip()
            output_format = report_elem.findtext('OUTPUT_FORMAT', default='bin').lower()
            safe_title = title.replace(" ", "_")
            filename = f"{safe_title}.{output_format}"

            # Chemin complet vers le dossier Downloads
            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            os.makedirs(downloads_dir, exist_ok=True)
            filepath = os.path.join(downloads_dir, filename)

            fetch_response = self.session.post(url, data=data, stream=True)
            fetch_response.raise_for_status()

            with open(filepath, 'wb') as f:
                for chunk in fetch_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            return filepath

        except requests.exceptions.RequestException as e:
            return None
        except ET.ParseError as e:
            return None