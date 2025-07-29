from datetime import datetime
from typing import Dict, List, Any, Callable

class Menu:
    def __init__(self, data: Dict[str, Any], menu_type: str = "scans", title: str = None, item_formatter: Callable = None):
        self.data = data
        self.menu_type = menu_type
        self.title = title or self._get_default_title()
        self.item_formatter = item_formatter or self._get_default_formatter()
        self.options = []
        self._prepare_options()

    def _get_default_title(self) -> str:
        titles = {
            "scans": "SÉLECTION DES SCANS À TRAITER",
            "templates": "SÉLECTION DES TEMPLATES DE RAPPORTS",
            "reports": "SÉLECTION DES RAPPORTS"
        }
        return titles.get(self.menu_type, "SÉLECTION D'ÉLÉMENTS")

    def _get_default_formatter(self) -> Callable:
        formatters = {
            "scans": self._format_scan_item,
            "templates": self._format_template_item,
            "reports": self._format_report_item
        }
        return formatters.get(self.menu_type, self._format_generic_item)

    def _format_scan_item(self, title: str, date: str, item_id: str) -> Dict[str, Any]:
        try:
            formatted_date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").strftime("%d/%m/%Y %H:%M")
        except:
            formatted_date = date
        return {
            'title': title,
            'date': date,
            'formatted_date': formatted_date,
            'scan_id': item_id,
            'id': item_id,
            'display_name': f"[{formatted_date}] {title} (ID: {item_id})",
            'description': f"Scan {title} du {formatted_date}"
        }

    def _format_template_item(self, name: str, template_id: str, output_format: str) -> Dict[str, Any]:
        return {
            'name': name,
            'template_id': template_id,
            'output_format': output_format,
            'id': template_id,
            'display_name': f"{name} ({output_format.upper()})",
            'description': f"Template {name} - Format: {output_format.upper()}"
        }

    def _format_report_item(self, title: str, report_id: str, status: str) -> Dict[str, Any]:
        return {
            'title': title,
            'report_id': report_id,
            'status': status,
            'id': report_id,
            'display_name': f"{title} - {status} (ID: {report_id})",
            'description': f"Rapport {title} - Statut: {status}"
        }

    def _format_generic_item(self, key: str, value: Any, extra: str = "") -> Dict[str, Any]:
        return {
            'key': key,
            'value': value,
            'id': str(value),
            'display_name': f"{key}: {value}",
            'description': f"{key} - {value}"
        }

    def _prepare_options(self):
        self.options = []
        if self.menu_type == "scans":
            for title, dates in self.data.items():
                for date, scan_id in dates.items():
                    option = self.item_formatter(title, date, scan_id)
                    self.options.append(option)
        elif self.menu_type == "templates":
            if isinstance(self.data, list):
                for template in self.data:
                    option = {
                        'name': template.get('name', ''),
                        'template_id': template.get('template_id', ''),
                        'output_format': template.get('output_format', ''),
                        'id': template.get('template_id', ''),
                        'display_name': template.get('description', ''),
                        'description': template.get('description', '')
                    }
                    self.options.append(option)
            else:
                for key, value in self.data.items():
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            option = self.item_formatter(key, sub_key, str(sub_value))
                            self.options.append(option)
        else:
            for key, value in self.data.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        option = self.item_formatter(key, sub_key, str(sub_value))
                        self.options.append(option)
                else:
                    option = self.item_formatter(key, str(value), "")
                    self.options.append(option)

    def display_checkbox_menu(self, use_inquirer: bool = None) -> List[Dict[str, Any]]:
        if not self.options:
            print("❌ Aucun élément disponible pour la sélection")
            return []
        if use_inquirer is None:
            try:
                import inquirer
                use_inquirer = True
            except ImportError:
                use_inquirer = False
        if use_inquirer:
            return self._display_inquirer_menu()
        else:
            return self._display_text_menu()

    def _display_inquirer_menu(self) -> List[Dict[str, Any]]:
        try:
            import inquirer
            choices = [option['display_name'] for option in self.options]
            questions = [
                inquirer.Checkbox(
                    'selected_items',
                    message=f"Sélectionnez les éléments à traiter",
                    choices=choices,
                    default=[]
                )
            ]
            answers = inquirer.prompt(questions)
            if not answers or not answers['selected_items']:
                return []
            selected_display_names = set(answers['selected_items'])
            selected_items = [
                option for option in self.options 
                if option['display_name'] in selected_display_names
            ]
            return selected_items
        except Exception:
            return self._display_text_menu()

    def _display_text_menu(self) -> List[Dict[str, Any]]:
        for i, option in enumerate(self.options, 1):
            print(f"  {i:2d}. {option['display_name']}")
        while True:
            try:
                user_input = input(f"\nSélectionner les éléments: ").strip().lower()
                if user_input in ['quit', 'q']:
                    return []
                if user_input in ['all', 'tout']:
                    return self.options.copy()
                selected_indices = set()
                parts = user_input.split(',')
                for part in parts:
                    part = part.strip()
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        selected_indices.update(range(start, end + 1))
                    else:
                        selected_indices.add(int(part))
                valid_indices = [i for i in selected_indices if 1 <= i <= len(self.options)]
                if not valid_indices:
                    continue
                selected_items = [self.options[i-1] for i in valid_indices]
                return selected_items
            except Exception:
                continue

def create_scan_menu(scan_results: Dict[str, Dict[str, str]]) -> Menu:
    return Menu(scan_results, "scans", "SÉLECTION DES SCANS À TRAITER")

def create_template_menu(templates: List[Dict[str, Any]]) -> Menu:
    return Menu(templates, "templates", "SÉLECTION DES TEMPLATES DE RAPPORTS")