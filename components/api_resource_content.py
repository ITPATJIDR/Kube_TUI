from textual.widget import Widget
from textual.app import ComposeResult, RenderResult
from textual.widgets import Static, DataTable
from kube_api import KubeAPI
from components.describe_modal import DescribeModal
from textual.timer import Timer


class ApiResourceContent(Widget):
    BINDINGS = [
        ("up", "cursor_up", "Up"),
        ("down", "cursor_down", "Down"),
        ("left", "cursor_left", "Left"),
        ("right", "cursor_right", "Right"),
        ("enter", "focus_table", "Focus Table"),
        ("escape", "unfocus_table", "Unfocus Table"),
        ("ctrl+d", "describe", "Describe"),
        ("w", "watch", "Watch"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.watch_enabled = False
        self.watch_timer = None
        self.current_resource = None

    def compose(self) -> ComposeResult:
        yield Static("API Resource Content", id="content_title")
        yield DataTable(id="resource_table")

    def on_mount(self) -> None:
        selected_resource = getattr(self.app, "selected_api_resource", None)
        current_namespace = self.app.current_namespace
        
        table = self.query_one("#resource_table", DataTable)
        table.can_focus = True
        
        if selected_resource:
            if str(selected_resource).startswith("Option('") and str(selected_resource).endswith("')"):
                selected_resource = str(selected_resource)[8:-2]  
            self._populate_output(selected_resource)
        else:
            print("no resource selected")
            table.clear()
            table.add_columns("STATUS")
            table.add_row("No resource selected")
        
        # Update title initially
        self._update_title()

    def on_unmount(self) -> None:
        """Clean up when widget is unmounted"""
        self._stop_watch()

    def on_focus(self) -> None:
        """Called when the widget gains focus"""
        self._update_title()

    def on_blur(self) -> None:
        """Called when the widget loses focus"""
        self._update_title()

    def _populate_output(self, resource_name: str):
        """Populate the DataTable with resource data"""
        try:
            # Stop watching if resource changed
            if self.watch_enabled and self.current_resource != resource_name:
                self._stop_watch()
                self._update_title()
            
            kube_api = KubeAPI()
            table = self.query_one("#resource_table", DataTable)
            
            table.clear()
            
            resource_data = self._get_resource_data(resource_name, kube_api)
            
            if resource_data:
                columns = self._analyze_resource_structure(resource_data[0] if resource_data else {})
                
                if columns:
                    column_names = [col[0] for col in columns]
                    table.add_columns(*column_names)
                    
                    for item in resource_data:
                        row_data = []
                        for col_name, col_path, width in columns:
                            value = self._extract_field_value(item, col_path)
                            row_data.append(str(value))
                        table.add_row(*row_data)
                else:
                    table.add_columns("NAME", "DETAILS")
                    table.add_row("No data", "No displayable columns found")
            else:
                current_namespace = getattr(self.app, 'current_namespace', 'default')
                table.add_columns("RESULT")
                table.add_row(f"No {resource_name} found in namespace {current_namespace}")
                
        except Exception as e:
            table = self.query_one("#resource_table", DataTable)
            table.clear()
            table.add_columns("ERROR")
            table.add_row(f"Error: {str(e)}")

    def action_cursor_up(self) -> None:
        """Move cursor up in the table"""
        table = self.query_one("#resource_table", DataTable)
        if table.cursor_row > 0:
            table.cursor_row -= 1

    def action_cursor_down(self) -> None:
        """Move cursor down in the table"""
        table = self.query_one("#resource_table", DataTable)
        if table.cursor_row < table.row_count - 1:
            table.cursor_row += 1

    def action_cursor_left(self) -> None:
        """Move cursor left in the table"""
        table = self.query_one("#resource_table", DataTable)
        if table.cursor_column > 0:
            table.cursor_column -= 1

    def action_cursor_right(self) -> None:
        """Move cursor right in the table"""
        table = self.query_one("#resource_table", DataTable)
        if table.cursor_column < table.column_count - 1:
            table.cursor_column += 1

    def action_focus_table(self) -> None:
        """Focus the DataTable when Enter is pressed"""
        table = self.query_one("#resource_table", DataTable)
        table.focus()
        self._update_title()

    def action_unfocus_table(self) -> None:
        """Unfocus the DataTable and return focus to the main content area when ESC is pressed"""
        table = self.query_one("#resource_table", DataTable)
        table.blur()
        if hasattr(self.app, "_apply_focus"):
            self.app._apply_focus("box_3")
        self._update_title()

    def action_describe(self) -> None:
        """Show describe modal for the selected resource"""
        table = self.query_one("#resource_table", DataTable)
        
        if table.row_count == 0:
            self.notify("No resources to describe", title="Error")
            return
        
        try:
            # Get the currently selected row
            selected_row = table.cursor_row
            if selected_row >= table.row_count:
                selected_row = 0
            
            # Get the resource name from the first column (NAME)
            resource_name = table.get_cell_at((selected_row, 0))
            
            # Get the selected API resource type
            selected_resource = getattr(self.app, "selected_api_resource", None)
            if not selected_resource:
                self.notify("No API resource selected", title="Error")
                return
                
            if str(selected_resource).startswith("Option('") and str(selected_resource).endswith("')"):
                selected_resource = str(selected_resource)[8:-2]
            selected_resource = selected_resource.split(' (')[0]
            
            # Get raw resource data
            describe_data = self._get_raw_resource_data(selected_resource, resource_name)
            
            # Show modal
            modal = DescribeModal(selected_resource, resource_name, describe_data)
            self.app.push_screen(modal)
            
        except Exception as e:
            self.notify(f"Error describing resource: {str(e)}", title="Error")

    def action_watch(self) -> None:
        """Toggle watch mode for the current resource"""
        selected_resource = getattr(self.app, "selected_api_resource", None)
        if not selected_resource:
            self.notify("No API resource selected", title="Error")
            return
        
        if str(selected_resource).startswith("Option('") and str(selected_resource).endswith("')"):
            selected_resource = str(selected_resource)[8:-2]
        selected_resource = selected_resource.split(' (')[0]
        
        if self.watch_enabled:
            # Stop watching
            self._stop_watch()
            self.notify("Watch stopped", title="Info")
        else:
            # Start watching
            self.current_resource = selected_resource
            self._start_watch()
            self.notify(f"Watching {selected_resource} (refresh every 1s)", title="Info")
        
        self._update_title()

    def _start_watch(self) -> None:
        """Start the watch timer"""
        self.watch_enabled = True
        # Refresh every 1 second (1000ms)
        self.watch_timer = self.set_timer(1.0, self._refresh_data)

    def _stop_watch(self) -> None:
        """Stop the watch timer"""
        self.watch_enabled = False
        if self.watch_timer:
            self.watch_timer.stop()
            self.watch_timer = None

    def _refresh_data(self) -> None:
        """Refresh the data when in watch mode"""
        if self.watch_enabled and self.current_resource:
            self._populate_output(self.current_resource)
            # Reschedule the timer for continuous watching
            self.watch_timer = self.set_timer(1.0, self._refresh_data)

    def _update_title(self) -> None:
        """Update the title based on current focus and selected resource"""
        selected_resource = getattr(self.app, "selected_api_resource", None)
        table = self.query_one("#resource_table", DataTable)
        title_widget = self.query_one("#content_title", Static)
        
        if selected_resource:
            if str(selected_resource).startswith("Option('") and str(selected_resource).endswith("')"):
                selected_resource = str(selected_resource)[8:-2]
            selected_resource = selected_resource.split(' (')[0]
            
            # Add watch status with red circle indicator
            if self.watch_enabled:
                watch_indicator = "🔴 "
                watch_status = " [WATCHING]"
            else:
                watch_indicator = "⚪ "
                watch_status = ""
            
            title_widget.update(f"{watch_indicator}Api Resource: {selected_resource}{watch_status}")
        else:
            if table.has_focus:
                title_widget.update("API Resource Content (FOCUSED)")
            else:
                title_widget.update("API Resource Content")

    def _get_resource_data(self, resource_name: str, kube_api: KubeAPI):
        """Get the actual resource data from Kubernetes using generic API calls"""
        try:
            current_namespace = getattr(self.app, 'current_namespace', 'default')
            
            api_resources = kube_api.get_api_resources()
            resource_info = None
            
            for resource in api_resources:
                if resource['name'] == resource_name:
                    resource_info = resource
                    break
            
            if not resource_info:
                return None
            
            api_version = resource_info['apiversion']
            kind = resource_info['kind']
            namespaced = resource_info['namespaced']
            
            if api_version == 'v1':
                if namespaced:
                    path = f"/api/v1/namespaces/{current_namespace}/{resource_name}"
                else:
                    path = f"/api/v1/{resource_name}"
            else:
                group = api_version.split('/')[0]
                version = api_version.split('/')[1]
                if namespaced:
                    path = f"/apis/{group}/{version}/namespaces/{current_namespace}/{resource_name}"
                else:
                    path = f"/apis/{group}/{version}/{resource_name}"
            
            print(f"🔍 Fetching {resource_name} from namespace: {current_namespace} (namespaced: {namespaced})")
            
            # Make the API call
            response = kube_api.api_client.call_api(path, 'GET', response_type='object')
            
            if response and len(response) > 0:
                return response[0].get('items', [])
            else:
                return []
                
        except Exception as e:
            print(f"Error getting {resource_name}: {e}")
            return None


    def _analyze_resource_structure(self, sample_resource):
        """Analyze a sample resource to determine the best columns to display"""
        columns = []
        
        if 'metadata' in sample_resource and 'name' in sample_resource['metadata']:
            columns.append(('NAME', 'metadata.name', 20))
        
        if 'status' in sample_resource:
            status_fields = sample_resource['status']
            
            if 'phase' in status_fields:
                columns.append(('STATUS', 'status.phase', 15))
            elif 'conditions' in status_fields and status_fields['conditions']:
                first_condition = status_fields['conditions'][0]
                if 'type' in first_condition:
                    columns.append(('STATUS', 'status.conditions[0].type', 15))
            
            if 'readyReplicas' in status_fields and 'replicas' in status_fields:
                columns.append(('READY', 'status.readyReplicas/status.replicas', 10))
            elif 'availableReplicas' in status_fields and 'replicas' in status_fields:
                columns.append(('AVAILABLE', 'status.availableReplicas/status.replicas', 12))
        
        if 'spec' in sample_resource:
            spec_fields = sample_resource['spec']
            
            if 'type' in spec_fields:
                columns.append(('TYPE', 'spec.type', 15))
            elif 'replicas' in spec_fields:
                columns.append(('REPLICAS', 'spec.replicas', 10))
            elif 'clusterIP' in spec_fields:
                columns.append(('CLUSTER-IP', 'spec.clusterIP', 15))
        
        if 'data' in sample_resource:
            columns.append(('DATA', 'data_count', 8))
        
        if 'metadata' in sample_resource and 'creationTimestamp' in sample_resource['metadata']:
            columns.append(('AGE', 'metadata.creationTimestamp', 10))
        
        if len(columns) <= 1:  
            if 'kind' in sample_resource:
                columns.append(('KIND', 'kind', 15))
            if 'apiVersion' in sample_resource:
                columns.append(('VERSION', 'apiVersion', 15))
        return columns

    def _extract_field_value(self, item, field_path):
        """Extract a value from a nested dictionary using dot notation"""
        try:
            if field_path == 'data_count':
                return len(item.get('data', {}))
            elif field_path == 'status.readyReplicas/status.replicas':
                ready = item.get('status', {}).get('readyReplicas', 0)
                total = item.get('status', {}).get('replicas', 0)
                return f"{ready}/{total}"
            elif field_path == 'status.availableReplicas/status.replicas':
                available = item.get('status', {}).get('availableReplicas', 0)
                total = item.get('status', {}).get('replicas', 0)
                return f"{available}/{total}"
            elif field_path == 'metadata.creationTimestamp':
                timestamp = item.get('metadata', {}).get('creationTimestamp')
                return self._calculate_age(timestamp) if timestamp else "Unknown"
            else:
                parts = field_path.split('.')
                value = item
                for part in parts:
                    if '[' in part and ']' in part:
                        key = part.split('[')[0]
                        index = int(part.split('[')[1].split(']')[0])
                        value = value.get(key, [])[index] if index < len(value.get(key, [])) else None
                    else:
                        value = value.get(part, {})
                    if value is None:
                        return "<none>"
                return value if value != {} else "<none>"
        except (KeyError, IndexError, TypeError, ValueError):
            return "<none>"

    def _calculate_age(self, creation_timestamp):
        """Calculate age from creation timestamp"""
        if not creation_timestamp:
            return "Unknown"
        
        try:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            
            if isinstance(creation_timestamp, str):
                created = datetime.fromisoformat(creation_timestamp.replace('Z', '+00:00'))
            else:
                created = creation_timestamp.replace(tzinfo=timezone.utc)
            
            age_delta = now - created
            
            days = age_delta.days
            hours, remainder = divmod(age_delta.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            if days > 0:
                return f"{days}d"
            elif hours > 0:
                return f"{hours}h"
            else:
                return f"{minutes}m"
        except (ValueError, TypeError, AttributeError):
            return "Unknown"

    def _get_raw_resource_data(self, resource_type: str, resource_name: str):
        """Get raw resource data for Pretty display"""
        try:
            kube_api = KubeAPI()
            current_namespace = getattr(self.app, 'current_namespace', 'default')
            
            # Get the resource data
            resource_data = self._get_resource_data(resource_type, kube_api)
            
            if not resource_data:
                return {"error": f"No {resource_type} found"}
            
            # Find the specific resource by name
            target_resource = None
            for resource in resource_data:
                if isinstance(resource, dict):
                    name = resource.get('metadata', {}).get('name', '')
                else:
                    name = getattr(resource.metadata, 'name', '') if hasattr(resource, 'metadata') else ''
                
                if name == resource_name:
                    target_resource = resource
                    break
            
            if not target_resource:
                return {"error": f"Resource {resource_name} not found in {resource_type}"}
            
            # Return raw dictionary data
            return target_resource
            
        except Exception as e:
            return {"error": f"Error getting resource data: {str(e)}"}

