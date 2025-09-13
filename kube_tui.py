#!/usr/bin/env python3
"""
Kubernetes TUI - A modern terminal user interface for Kubernetes resource management
"""

import os
from typing import List, Dict, Any
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, ListView, ListItem, Label
from textual.binding import Binding
from kubernetes import client, config




class ResourceItem(ListItem):
    """Individual resource item in the sidebar"""
    
    def __init__(self, resource_name: str, resource_type: str, count: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.resource_name = resource_name
        self.resource_type = resource_type
        self.count = count
        
        # Add CSS class for header items
        if resource_type == "header":
            self.add_class("header-item")
    
    def compose(self) -> ComposeResult:
        if self.resource_type == "header":
            yield Label(f"{self.resource_name}")
        else:
            yield Label(f"📦 {self.resource_name}")


class NamespaceSelector(Static):
    """Namespace selector widget"""
    
    def __init__(self, **kwargs):
        super().__init__("namespace: default", **kwargs)
        self.selected_namespace = "default"
        self.namespaces = []
        self.can_focus = True
    
    def set_namespaces(self, namespaces):
        """Set the list of available namespaces"""
        self.namespaces = namespaces
    
    def set_selected_namespace(self, namespace):
        """Set the currently selected namespace"""
        self.selected_namespace = namespace
        if namespace:
            self.update(f"namespace: {namespace}")
        else:
            self.update("namespace: All")
        # Force refresh to ensure the display is updated
        self.refresh()
    
    def get_namespace_list(self):
        """Get formatted list of namespaces"""
        if not self.namespaces:
            return "No namespaces available"
        
        # Get terminal width for responsive layout
        terminal_width = self.app.size.width if hasattr(self.app, 'size') else 120
        name_width = min(30, max(15, terminal_width // 4))
        status_width = min(15, max(8, terminal_width // 10))
        age_width = 10
        
        details = "📁 Available Namespaces\n\n"
        details += f"{'NAME':<{name_width}} {'STATUS':<{status_width}} {'AGE':<{age_width}}\n"
        details += "-" * min(terminal_width - 10, 80) + "\n"
        
        for ns in self.namespaces:
            status = ns.status.phase if ns.status else "Unknown"
            age = self._get_age(ns.metadata.creation_timestamp)
            details += f"{ns.metadata.name:<{name_width}} {status:<{status_width}} {age:<{age_width}}\n"
        
        return details
    
    def _get_age(self, creation_timestamp):
        """Calculate age from creation timestamp"""
        if not creation_timestamp:
            return "Unknown"
        
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        created = creation_timestamp.replace(tzinfo=timezone.utc)
        age_delta = now - created
        
        days = age_delta.days
        hours, remainder = divmod(age_delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d{hours}h"
        elif hours > 0:
            return f"{hours}h{minutes}m"
        else:
            return f"{minutes}m"


class ResourceSidebar(ListView):
    """Sidebar showing available Kubernetes resources"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.resources: List[Dict[str, Any]] = []
    
    def add_resource(self, name: str, resource_type: str, count: int = 0) -> None:
        """Add a resource to the sidebar"""
        self.resources.append({"name": name, "type": resource_type, "count": count})
        self.append(ResourceItem(name, resource_type, count))
    
    def clear_resources(self) -> None:
        """Clear all resources from the sidebar"""
        self.resources.clear()
        self.clear()


class NamespaceItem(ListItem):
    """List item representing the namespace display/control at top of sidebar"""
    
    def __init__(self, namespace_text: str, **kwargs):
        super().__init__(**kwargs)
        self.namespace_text = namespace_text
        self.add_class("namespace-item")
    
    def compose(self) -> ComposeResult:
        yield Label(f"namespace: {self.namespace_text}")


class MainContent(Static):
    """Main content area showing resource details"""
    
    def __init__(self, **kwargs):
        super().__init__("Select a resource from the sidebar to view details", **kwargs)
        self.current_resource = None


class KubeTUI(App):
    """Main Kubernetes TUI Application"""
    
    CSS = """
    #app-layout {
        height: 1fr;
    }
    
    
    #namespace-selector:focus {
        background: $primary;
    }
    
    #main-layout {
        height: 1fr;
        layout: horizontal;
    }
    
    #left-panel {
        width: 30%;
        min-width: 20;
        max-width: 40;
        layout: vertical;
    }
    
    #sidebar {
        width: 100%;
        background: $surface;
        border: solid $primary;
        margin: 0;
        padding: 1;
    }
    
    
    #main-content {
        width: 70%;
        min-width: 40;
        background: $surface;
        border: solid $primary;
        margin: 1 1 1 0;
        padding: 1;
        overflow-x: auto;
    }
    
    .header-item {
        text-style: bold;
        background: $primary;
        color: $text;
        padding: 1;
        margin-bottom: 1;
        text-align: center;
    }
    .namespace-item {
        text-style: bold;
        background: transparent;
        color: $text;
        padding: 0 1;
        margin: 0 0 1 0;
        border: solid $primary;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
        Binding("up", "focus_namespace", "Focus Namespace"),
        Binding("down", "focus_sidebar", "Focus Sidebar"),
        Binding("enter", "select_namespace", "Select Namespace"),
    ]
    
    def __init__(self):
        super().__init__()
        self.k8s_client = None
        self.namespace_selector = None
        self.resource_sidebar = None
        self.main_content = None
        self.current_namespace = "default"
        self.current_resource = None
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        
        # Create namespace selector
        self.namespace_selector = NamespaceSelector(id="namespace-selector")
        # Initialize text explicitly so it renders immediately
        initial_ns_text = self.current_namespace if self.current_namespace else "All"
        try:
            self.namespace_selector.set_selected_namespace(initial_ns_text)
        except Exception as e:
            pass
        
        # Create main layout immediately
        self.resource_sidebar = ResourceSidebar(id="sidebar")
        self.main_content = MainContent(id="main-content")
        
        # Create the layout with namespace selector at the top
        yield Vertical(
            Horizontal(
                Vertical(
                    self.resource_sidebar,
                    id="left-panel"
                ),
                self.main_content,
                id="main-layout"
            ),
            id="app-layout"
        )
    
    def on_mount(self) -> None:
        """Called when the app is mounted"""
        
        # Set default namespace
        if self.namespace_selector:
            shown_ns = self.current_namespace if self.current_namespace else "All"
            self.namespace_selector.set_selected_namespace(shown_ns)
            # Make sure the namespace selector is visible
            self.namespace_selector.display = True
            self.namespace_selector.visible = True
            # Force refresh to ensure display is updated
            self.namespace_selector.refresh()
        
        # Try to load kube config and resources immediately
        try:
            config.load_kube_config()
            self.k8s_client = client.ApiClient()
            # Load namespaces after a short delay to ensure widgets are ready
            self.set_timer(0.1, self.load_namespaces)
            self.load_resources()
        except Exception:
            # If kube config fails, still show resources with 0 counts
            self.load_resources()
        
        # Focus the namespace selector first
        if self.namespace_selector:
            self.namespace_selector.focus()
    
    def load_namespaces(self) -> None:
        """Load available namespaces"""
        if not self.k8s_client or not self.namespace_selector:
            return
        
        try:
            v1 = client.CoreV1Api(self.k8s_client)
            namespaces = v1.list_namespace()
            self.namespace_selector.set_namespaces(namespaces.items)
        except Exception as e:
            # If namespace loading fails, continue without namespaces
            pass
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle resource selection"""
        # If the namespace line is selected, open the namespace chooser
        try:
            if isinstance(event.item, NamespaceItem):
                self.show_namespace_selection()
                return
        except Exception:
            pass
        if hasattr(event.item, 'resource_name') and hasattr(event.item, 'resource_type'):
            # Skip header items
            if event.item.resource_type == "header":
                return
            resource_name = event.item.resource_name
            self.show_resource_details(resource_name)
    
    
    def load_resources(self) -> None:
        """Load available Kubernetes resources"""
        # Clear existing resources and add header
        self.resource_sidebar.clear_resources()
        
        # Add namespace display item at the very top
        ns_text = self.current_namespace if self.current_namespace else "All"
        self.namespace_item = NamespaceItem(ns_text)
        self.resource_sidebar.append(self.namespace_item)
        
        # Add header after namespace
        self.resource_sidebar.add_resource("📋 Resources", "header", 0)
        
        common_resources = [
            ("pods", "Pod"), ("services", "Service"), ("deployments", "Deployment"),
            ("replicasets", "ReplicaSet"), ("statefulsets", "StatefulSet"), 
            ("daemonsets", "DaemonSet"), ("configmaps", "ConfigMap"), 
            ("secrets", "Secret"), ("nodes", "Node"), ("namespaces", "Namespace"),
            ("persistentvolumes", "PersistentVolume"), ("persistentvolumeclaims", "PersistentVolumeClaim"),
            ("ingresses", "Ingress"), ("networkpolicies", "NetworkPolicy"),
            ("jobs", "Job"), ("cronjobs", "CronJob"), ("horizontalpodautoscalers", "HorizontalPodAutoscaler"),
            ("roles", "Role"), ("rolebindings", "RoleBinding"), ("clusterroles", "ClusterRole"),
            ("clusterrolebindings", "ClusterRoleBinding"), ("storageclasses", "StorageClass"),
            ("endpoints", "Endpoints"), ("events", "Event"), ("serviceaccounts", "ServiceAccount"),
        ]
        
        # Get resource counts
        resource_counts = {}
        if self.k8s_client:
            try:
                v1 = client.CoreV1Api(self.k8s_client)
                apps_v1 = client.AppsV1Api(self.k8s_client)
                
                resource_counts["pods"] = len(v1.list_pod_for_all_namespaces().items)
                resource_counts["services"] = len(v1.list_service_for_all_namespaces().items)
                resource_counts["configmaps"] = len(v1.list_config_map_for_all_namespaces().items)
                resource_counts["secrets"] = len(v1.list_secret_for_all_namespaces().items)
                resource_counts["nodes"] = len(v1.list_node().items)
                resource_counts["namespaces"] = len(v1.list_namespace().items)
                resource_counts["deployments"] = len(apps_v1.list_deployment_for_all_namespaces().items)
                resource_counts["replicasets"] = len(apps_v1.list_replica_set_for_all_namespaces().items)
                resource_counts["statefulsets"] = len(apps_v1.list_stateful_set_for_all_namespaces().items)
                resource_counts["daemonsets"] = len(apps_v1.list_daemon_set_for_all_namespaces().items)
            except Exception as e:
                print(f"Warning: Could not get resource counts: {e}")
        
        # Add resources to sidebar
        for resource_name, resource_type in common_resources:
            count = resource_counts.get(resource_name, 0)
            self.resource_sidebar.add_resource(resource_name, resource_type, count)
        
        # Focus the sidebar
        self.resource_sidebar.focus()
    
    def show_resource_details(self, resource_name: str) -> None:
        """Show details for the selected resource"""
        if self.main_content:
            try:
                # Track current resource for resize handling
                self.current_resource = resource_name
                details = self.get_resource_details(resource_name)
                self.main_content.update(details)
            except Exception as e:
                error_msg = f"Error loading {resource_name} details: {str(e)}"
                self.main_content.update(error_msg)
    
    def get_resource_details(self, resource_name: str) -> str:
        """Get detailed information about a specific resource"""
        if not self.k8s_client:
            return "No Kubernetes client available"
        
        # Get terminal width for responsive layout
        terminal_width = self.size.width if hasattr(self, 'size') else 120
        name_width = min(30, max(15, terminal_width // 4))
        namespace_width = min(15, max(10, terminal_width // 8))
        status_width = min(15, max(8, terminal_width // 10))
        age_width = 10
        
        def format_row(name, namespace="", status="", age="", extra=""):
            """Format a row with responsive column widths"""
            if namespace:
                return f"{name:<{name_width}} {namespace:<{namespace_width}} {status:<{status_width}} {age:<{age_width}} {extra}"
            else:
                return f"{name:<{name_width}} {status:<{status_width}} {age:<{age_width}} {extra}"
        
        def format_header(name_col, namespace_col="", status_col="", age_col="", extra_col=""):
            """Format header row with responsive column widths"""
            if namespace_col:
                return f"{name_col:<{name_width}} {namespace_col:<{namespace_width}} {status_col:<{status_width}} {age_col:<{age_width}} {extra_col}"
            else:
                return f"{name_col:<{name_width}} {status_col:<{status_width}} {age_col:<{age_width}} {extra_col}"
        
        def get_separator():
            """Get separator line based on terminal width"""
            return "-" * min(terminal_width - 10, 80)
        
        try:
            v1 = client.CoreV1Api(self.k8s_client)
            apps_v1 = client.AppsV1Api(self.k8s_client)
            
            if resource_name == "pods":
                if self.current_namespace:
                    pods = v1.list_namespaced_pod(namespace=self.current_namespace)
                else:
                    pods = v1.list_pod_for_all_namespaces()
                details = f"📦 Pods ({len(pods.items)} total)" + (f" in {self.current_namespace}" if self.current_namespace else "") + "\n\n"
                if self.current_namespace:
                    details += format_header("NAME", "", "STATUS", "AGE") + "\n"
                else:
                    details += format_header("NAME", "NAMESPACE", "STATUS", "AGE") + "\n"
                details += get_separator() + "\n"
                for pod in pods.items[:10]:  # Show first 10 pods
                    status = pod.status.phase if pod.status else "Unknown"
                    age = self._get_age(pod.metadata.creation_timestamp)
                    # Show namespace column only when not filtering by namespace
                    if self.current_namespace:
                        details += format_row(pod.metadata.name, "", status, age) + "\n"
                    else:
                        details += format_row(pod.metadata.name, pod.metadata.namespace, status, age) + "\n"
                if len(pods.items) > 10:
                    details += f"... and {len(pods.items) - 10} more\n"
                    
            elif resource_name == "services":
                if self.current_namespace:
                    services = v1.list_namespaced_service(namespace=self.current_namespace)
                else:
                    services = v1.list_service_for_all_namespaces()
                details = f"🔗 Services ({len(services.items)} total)" + (f" in {self.current_namespace}" if self.current_namespace else "") + "\n\n"
                if self.current_namespace:
                    details += format_header("NAME", "", "TYPE", "AGE") + "\n"
                else:
                    details += format_header("NAME", "NAMESPACE", "TYPE", "AGE") + "\n"
                details += get_separator() + "\n"
                for svc in services.items[:10]:
                    age = self._get_age(svc.metadata.creation_timestamp)
                    if self.current_namespace:
                        details += format_row(svc.metadata.name, "", svc.spec.type, age) + "\n"
                    else:
                        details += format_row(svc.metadata.name, svc.metadata.namespace, svc.spec.type, age) + "\n"
                if len(services.items) > 10:
                    details += f"... and {len(services.items) - 10} more\n"
                    
            elif resource_name == "deployments":
                if self.current_namespace:
                    deployments = apps_v1.list_namespaced_deployment(namespace=self.current_namespace)
                else:
                    deployments = apps_v1.list_deployment_for_all_namespaces()
                details = f"🚀 Deployments ({len(deployments.items)} total)" + (f" in {self.current_namespace}" if self.current_namespace else "") + "\n\n"
                if self.current_namespace:
                    details += format_header("NAME", "", "READY", "AGE") + "\n"
                else:
                    details += format_header("NAME", "NAMESPACE", "READY", "AGE") + "\n"
                details += get_separator() + "\n"
                for dep in deployments.items[:10]:
                    replicas = dep.spec.replicas if dep.spec.replicas else 0
                    ready = dep.status.ready_replicas if dep.status.ready_replicas else 0
                    age = self._get_age(dep.metadata.creation_timestamp)
                    ready_str = f"{ready}/{replicas}"
                    if self.current_namespace:
                        details += format_row(dep.metadata.name, "", ready_str, age) + "\n"
                    else:
                        details += format_row(dep.metadata.name, dep.metadata.namespace, ready_str, age) + "\n"
                if len(deployments.items) > 10:
                    details += f"... and {len(deployments.items) - 10} more\n"
                    
            elif resource_name == "nodes":
                nodes = v1.list_node()
                details = f"🖥️  Nodes ({len(nodes.items)} total)\n\n"
                details += format_header("NAME", "", "STATUS", "AGE") + "\n"
                details += get_separator() + "\n"
                for node in nodes.items:
                    status = "Ready" if node.status.conditions and any(c.type == "Ready" and c.status == "True" for c in node.status.conditions) else "Not Ready"
                    age = self._get_age(node.metadata.creation_timestamp)
                    details += format_row(node.metadata.name, "", status, age) + "\n"
                    
            elif resource_name == "namespaces":
                namespaces = v1.list_namespace()
                details = f"📁 Namespaces ({len(namespaces.items)} total)\n\n"
                details += format_header("NAME", "", "STATUS", "AGE") + "\n"
                details += get_separator() + "\n"
                for ns in namespaces.items:
                    status = ns.status.phase if ns.status else "Unknown"
                    age = self._get_age(ns.metadata.creation_timestamp)
                    details += format_row(ns.metadata.name, "", status, age) + "\n"
                    
            elif resource_name == "configmaps":
                if self.current_namespace:
                    configmaps = v1.list_namespaced_config_map(namespace=self.current_namespace)
                else:
                    configmaps = v1.list_config_map_for_all_namespaces()
                details = f"⚙️  ConfigMaps ({len(configmaps.items)} total)" + (f" in {self.current_namespace}" if self.current_namespace else "") + "\n\n"
                if self.current_namespace:
                    details += format_header("NAME", "", "", "AGE") + "\n"
                else:
                    details += format_header("NAME", "NAMESPACE", "", "AGE") + "\n"
                details += get_separator() + "\n"
                for cm in configmaps.items[:10]:
                    age = self._get_age(cm.metadata.creation_timestamp)
                    if self.current_namespace:
                        details += format_row(cm.metadata.name, "", "", age) + "\n"
                    else:
                        details += format_row(cm.metadata.name, cm.metadata.namespace, "", age) + "\n"
                if len(configmaps.items) > 10:
                    details += f"... and {len(configmaps.items) - 10} more\n"
                    
            elif resource_name == "secrets":
                if self.current_namespace:
                    secrets = v1.list_namespaced_secret(namespace=self.current_namespace)
                else:
                    secrets = v1.list_secret_for_all_namespaces()
                details = f"🔐 Secrets ({len(secrets.items)} total)" + (f" in {self.current_namespace}" if self.current_namespace else "") + "\n\n"
                if self.current_namespace:
                    details += format_header("NAME", "", "TYPE", "AGE") + "\n"
                else:
                    details += format_header("NAME", "NAMESPACE", "TYPE", "AGE") + "\n"
                details += get_separator() + "\n"
                for secret in secrets.items[:10]:
                    secret_type = secret.type if secret.type else "Opaque"
                    age = self._get_age(secret.metadata.creation_timestamp)
                    if self.current_namespace:
                        details += format_row(secret.metadata.name, "", secret_type, age) + "\n"
                    else:
                        details += format_row(secret.metadata.name, secret.metadata.namespace, secret_type, age) + "\n"
                if len(secrets.items) > 10:
                    details += f"... and {len(secrets.items) - 10} more\n"
                    
            elif resource_name == "persistentvolumes":
                pvs = v1.list_persistent_volume()
                details = f"💾 Persistent Volumes ({len(pvs.items)} total)\n\n"
                details += format_header("NAME", "", "STATUS", "AGE") + "\n"
                details += get_separator() + "\n"
                for pv in pvs.items:
                    status = pv.status.phase if pv.status else "Unknown"
                    age = self._get_age(pv.metadata.creation_timestamp)
                    details += format_row(pv.metadata.name, "", status, age) + "\n"
                    
            elif resource_name == "persistentvolumeclaims":
                if self.current_namespace:
                    pvcs = v1.list_namespaced_persistent_volume_claim(namespace=self.current_namespace)
                else:
                    pvcs = v1.list_persistent_volume_claim_for_all_namespaces()
                details = f"💾 PVCs ({len(pvcs.items)} total)" + (f" in {self.current_namespace}" if self.current_namespace else "") + "\n\n"
                if self.current_namespace:
                    details += format_header("NAME", "", "STATUS", "AGE") + "\n"
                else:
                    details += format_header("NAME", "NAMESPACE", "STATUS", "AGE") + "\n"
                details += get_separator() + "\n"
                for pvc in pvcs.items[:10]:
                    status = pvc.status.phase if pvc.status else "Unknown"
                    age = self._get_age(pvc.metadata.creation_timestamp)
                    if self.current_namespace:
                        details += format_row(pvc.metadata.name, "", status, age) + "\n"
                    else:
                        details += format_row(pvc.metadata.name, pvc.metadata.namespace, status, age) + "\n"
                if len(pvcs.items) > 10:
                    details += f"... and {len(pvcs.items) - 10} more\n"
                    
            else:
                details = f"📋 {resource_name.title()}\n\nResource details not implemented yet.\n\nThis would show detailed information about {resource_name} resources."
            
            return details
            
        except Exception as e:
            return f"Error fetching {resource_name} details: {str(e)}"
    
    def _get_age(self, creation_timestamp) -> str:
        """Calculate age from creation timestamp"""
        if not creation_timestamp:
            return "Unknown"
        
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        created = creation_timestamp.replace(tzinfo=timezone.utc)
        age_delta = now - created
        
        days = age_delta.days
        hours, remainder = divmod(age_delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d{hours}h"
        elif hours > 0:
            return f"{hours}h{minutes}m"
        else:
            return f"{minutes}m"
    
    def on_resize(self, event) -> None:
        """Handle terminal resize"""
        # Refresh the current resource display with new column widths
        if hasattr(self, 'current_resource') and self.current_resource:
            self.show_resource_details(self.current_resource)
    
    def action_focus_namespace(self) -> None:
        """Focus the namespace selector"""
        if self.namespace_selector:
            self.namespace_selector.focus()
    
    def action_focus_sidebar(self) -> None:
        """Focus the resource sidebar"""
        if self.resource_sidebar:
            self.resource_sidebar.focus()
    
    def action_select_namespace(self) -> None:
        """Show namespace list when Enter is pressed on namespace selector"""
        if self.namespace_selector and self.namespace_selector.has_focus:
            # Show namespace selection interface
            self.show_namespace_selection()
    
    def show_namespace_selection(self) -> None:
        """Show namespace selection interface"""
        if not self.main_content:
            return
        
        # Get namespaces from the namespace selector or load them directly
        namespaces = []
        if self.namespace_selector and self.namespace_selector.namespaces:
            namespaces = self.namespace_selector.namespaces
        elif self.k8s_client:
            try:
                v1 = client.CoreV1Api(self.k8s_client)
                namespaces = v1.list_namespace().items
            except Exception as e:
                pass
        
        if not namespaces:
            self.main_content.update("No namespaces available")
            return
        
        # Create namespace selection interface
        details = "📁 Select Namespace\n\n"
        details += "Press number to select namespace:\n\n"
        details += "0. All namespaces (show all resources)\n"
        
        for i, ns in enumerate(namespaces, 1):
            status = ns.status.phase if ns.status else "Unknown"
            details += f"{i}. {ns.metadata.name} ({status})\n"
        
        details += "\nPress 'q' to go back to resource view"
        self.main_content.update(details)
        
        # Set up key handler for namespace selection
        self.namespace_selection_mode = True
    
    def on_key(self, event) -> None:
        """Handle key presses for navigation and namespace selection"""
        # If on first item (namespace line) and user presses Up again, open namespace selector
        if event.key == "up" and self.resource_sidebar and self.resource_sidebar.has_focus:
            try:
                current_index = self.resource_sidebar.index
                if current_index == 0:
                    self.show_namespace_selection()
                    return
            except Exception:
                pass
        
        # Handle namespace selection mode
        if hasattr(self, 'namespace_selection_mode') and self.namespace_selection_mode:
            if event.key == 'q':
                # Exit namespace selection mode
                self.namespace_selection_mode = False
                if self.current_resource:
                    self.show_resource_details(self.current_resource)
                else:
                    self.main_content.update("Select a resource from the sidebar to view details")
                return
            # Handle number keys for namespace selection
            if event.key.isdigit():
                try:
                    choice = int(event.key)
                    if choice == 0:
                        # Select all namespaces
                        self.select_namespace(None)
                    else:
                        # Get namespaces from the namespace selector or load them directly
                        namespaces = []
                        if self.namespace_selector and self.namespace_selector.namespaces:
                            namespaces = self.namespace_selector.namespaces
                        elif self.k8s_client:
                            try:
                                v1 = client.CoreV1Api(self.k8s_client)
                                namespaces = v1.list_namespace().items
                            except Exception:
                                pass
                        if 1 <= choice <= len(namespaces):
                            # Select specific namespace
                            selected_ns = namespaces[choice - 1]
                            self.select_namespace(selected_ns.metadata.name)
                    
                    self.namespace_selection_mode = False
                except (ValueError, IndexError):
                    pass
    
    def select_namespace(self, namespace_name: str) -> None:
        """Select a specific namespace and filter resources"""
        self.current_namespace = namespace_name
        if self.namespace_selector:
            selector_text = namespace_name if namespace_name else "All"
            self.namespace_selector.set_selected_namespace(selector_text)
            # Force refresh the namespace selector display
            self.namespace_selector.refresh()
        
        # Update the namespace display item in the sidebar
        try:
            if hasattr(self, 'namespace_item') and self.namespace_item is not None:
                ns_text = namespace_name if namespace_name else "All"
                self.namespace_item.namespace_text = ns_text
                self.namespace_item.refresh()
        except Exception as e:
            pass
        
        # Reload resources with namespace filter
        self.load_resources()
        
        # Focus back to sidebar
        if self.resource_sidebar:
            self.resource_sidebar.focus()
    
    def action_quit(self) -> None:
        """Quit the application"""
        self.exit()
    
    def action_inspect(self) -> None:
        """Inspect the current widget"""
        pass
    
    def action_debug_widgets(self) -> None:
        """Debug widgets manually"""
        pass
    
    def debug_widget_tree(self) -> None:
        """Debug the widget tree to see what's rendered"""
        pass


def main():
    """Main entry point"""
    app = KubeTUI()
    app.run()


if __name__ == "__main__":
    main()
