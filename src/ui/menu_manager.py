"""
Menu manager - refactored from menu.py
Handles interactive menus with improved functionality
"""
from datetime import datetime
from typing import Dict, List, Any, Callable, Optional

try:
    import inquirer
    INQUIRER_AVAILABLE = True
except ImportError:
    INQUIRER_AVAILABLE = False


class MenuManager:
    """Enhanced menu manager with multiple display options"""
    
    def __init__(self, data: Any, menu_type: str = "generic", title: Optional[str] = None, 
                 item_formatter: Optional[Callable] = None):
        self.data = data
        self.menu_type = menu_type
        self.title = title or self._get_default_title()
        self.item_formatter = item_formatter or self._get_default_formatter()
        self.options = []
        self._prepare_options()
    
    def _get_default_title(self) -> str:
        """Get default title based on menu type"""
        titles = {
            "scans": "SÉLECTION DES SCANS À TRAITER",
            "templates": "SÉLECTION DES TEMPLATES DE RAPPORTS",
            "reports": "SÉLECTION DES RAPPORTS",
            "vulnerabilities": "SÉLECTION DES VULNÉRABILITÉS"
        }
        return titles.get(self.menu_type, "SÉLECTION D'ÉLÉMENTS")
    
    def _get_default_formatter(self) -> Callable:
        """Get default formatter based on menu type"""
        formatters = {
            "scans": self._format_scan_item,
            "templates": self._format_template_item,
            "reports": self._format_report_item,
            "vulnerabilities": self._format_vulnerability_item
        }
        return formatters.get(self.menu_type, self._format_generic_item)
    
    def _format_scan_item(self, title: str, date: str, item_id: str) -> Dict[str, Any]:
        """Format scan item for display"""
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
    
    def _format_template_item(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """Format template item for display"""
        return {
            'name': template.get('name', ''),
            'template_id': template.get('template_id', ''),
            'output_format': template.get('output_format', ''),
            'id': template.get('template_id', ''),
            'display_name': template.get('description', ''),
            'description': template.get('description', '')
        }
    
    def _format_report_item(self, title: str, report_id: str, status: str) -> Dict[str, Any]:
        """Format report item for display"""
        return {
            'title': title,
            'report_id': report_id,
            'status': status,
            'id': report_id,
            'display_name': f"{title} - {status} (ID: {report_id})",
            'description': f"Rapport {title} - Statut: {status}"
        }
    
    def _format_vulnerability_item(self, vuln: Dict[str, Any]) -> Dict[str, Any]:
        """Format vulnerability item for display"""
        return {
            'qid': vuln.get('qid', ''),
            'title': vuln.get('title', ''),
            'severity': vuln.get('severity', ''),
            'id': vuln.get('qid', ''),
            'display_name': f"[{vuln.get('severity', 'Unknown')}] {vuln.get('title', 'Unknown')} (QID: {vuln.get('qid', 'Unknown')})",
            'description': f"Vulnérabilité {vuln.get('title', 'Unknown')} - Sévérité: {vuln.get('severity', 'Unknown')}"
        }
    
    def _format_generic_item(self, key: str, value: Any, extra: str = "") -> Dict[str, Any]:
        """Format generic item for display"""
        return {
            'key': key,
            'value': value,
            'id': str(value),
            'display_name': f"{key}: {value}",
            'description': f"{key} - {value}"
        }
    
    def _prepare_options(self):
        """Prepare options based on data type and menu type"""
        self.options = []
        
        if self.menu_type == "scans":
            for title, dates in self.data.items():
                for date, scan_id in dates.items():
                    option = self.item_formatter(title, date, scan_id)
                    self.options.append(option)
        
        elif self.menu_type == "templates":
            if isinstance(self.data, list):
                for template in self.data:
                    option = self._format_template_item(template)
                    self.options.append(option)
        
        elif self.menu_type == "vulnerabilities":
            if isinstance(self.data, list):
                for vuln in self.data:
                    option = self._format_vulnerability_item(vuln)
                    self.options.append(option)
        
        else:
            # Generic handling
            if isinstance(self.data, dict):
                for key, value in self.data.items():
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            option = self.item_formatter(key, sub_key, str(sub_value))
                            self.options.append(option)
                    else:
                        option = self.item_formatter(key, str(value), "")
                        self.options.append(option)
            elif isinstance(self.data, list):
                for i, item in enumerate(self.data):
                    option = self.item_formatter(f"Item {i+1}", str(item), "")
                    self.options.append(option)
    
    def display_checkbox_menu(self, use_inquirer: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Display checkbox menu with fallback options"""
        if not self.options:
            print("❌ Aucun élément disponible pour la sélection")
            return []
        
        if use_inquirer is None:
            use_inquirer = INQUIRER_AVAILABLE
        
        if use_inquirer and INQUIRER_AVAILABLE:
            return self._display_inquirer_menu()
        else:
            return self._display_text_menu()
    
    def _display_inquirer_menu(self) -> List[Dict[str, Any]]:
        """Display interactive checkbox menu using inquirer"""
        try:
            print("\n" + "=" * 80)
            print(f"📋 {self.title}")
            print("=" * 80)
            print("💡 Utilisez les flèches ↑↓ pour naviguer, ESPACE pour cocher/décocher, ENTRÉE pour valider")
            print("-" * 80)
            
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
                print("❌ Aucun élément sélectionné")
                return []
            
            # Map back to original options
            selected_display_names = set(answers['selected_items'])
            selected_items = [
                option for option in self.options 
                if option['display_name'] in selected_display_names
            ]
            
            print(f"\n✅ {len(selected_items)} élément(s) sélectionné(s)")
            return selected_items
            
        except KeyboardInterrupt:
            print("\n❌ Sélection interrompue")
            return []
        except Exception as e:
            print(f"❌ Erreur avec l'interface graphique: {e}")
            print("🔄 Basculement vers l'interface texte...")
            return self._display_text_menu()
    
    def _display_text_menu(self) -> List[Dict[str, Any]]:
        """Display text-based menu (fallback)"""
        print("\n" + "=" * 80)
        print(f"📋 {self.title}")
        print("=" * 80)
        
        # Display numbered list
        for i, option in enumerate(self.options, 1):
            print(f"  {i:2d}. {option['display_name']}")
        
        print("\n" + "-" * 80)
        print("💡 Options de sélection:")
        print("   • Numéros individuels: 1,3,5")
        print("   • Plages: 1-5")
        print("   • Combinaison: 1,3-7,10")
        print("   • Tout sélectionner: 'all' ou 'tout'")
        print("   • Annuler: 'quit' ou 'q'")
        print("-" * 80)
        
        while True:
            try:
                user_input = input(f"\n🎯 Sélectionner les éléments: ").strip().lower()
                
                if user_input in ['quit', 'q']:
                    print("❌ Sélection annulée")
                    return []
                
                if user_input in ['all', 'tout']:
                    selected_items = self.options.copy()
                    print(f"✅ Tous les éléments sélectionnés ({len(selected_items)} éléments)")
                    return selected_items
                
                # Parse selection
                selected_indices = set()
                parts = user_input.split(',')
                
                for part in parts:
                    part = part.strip()
                    if '-' in part:
                        # Handle ranges (e.g., 1-5)
                        start, end = map(int, part.split('-'))
                        selected_indices.update(range(start, end + 1))
                    else:
                        # Individual number
                        selected_indices.add(int(part))
                
                # Validate indices
                valid_indices = [i for i in selected_indices if 1 <= i <= len(self.options)]
                if not valid_indices:
                    print("❌ Aucun numéro valide sélectionné")
                    continue
                
                selected_items = [self.options[i-1] for i in valid_indices]
                print(f"✅ {len(selected_items)} élément(s) sélectionné(s)")
                return selected_items
                
            except ValueError:
                print("❌ Format invalide. Utilisez des numéros, plages (1-5) ou 'all'")
            except KeyboardInterrupt:
                print("\n❌ Sélection interrompue")
                return []
    
    def get_summary(self) -> str:
        """Get menu summary"""
        return f"{self.menu_type.title()} Menu: {len(self.options)} options available"


def create_scan_menu(scan_results: Dict[str, Dict[str, str]]) -> MenuManager:
    """Create a scan selection menu"""
    return MenuManager(scan_results, "scans", "SÉLECTION DES SCANS À TRAITER")


def create_template_menu(templates: List[Dict[str, Any]]) -> MenuManager:
    """Create a template selection menu"""
    return MenuManager(templates, "templates", "SÉLECTION DES TEMPLATES DE RAPPORTS")


def create_vulnerability_menu(vulnerabilities: List[Dict[str, Any]]) -> MenuManager:
    """Create a vulnerability selection menu"""
    return MenuManager(vulnerabilities, "vulnerabilities", "SÉLECTION DES VULNÉRABILITÉS")