#!/usr/bin/env python3
"""
Kubernetes TUI - A modern terminal user interface for Kubernetes resource management
"""

import os
from textual.app import App, ComposeResult
from textual.containers import Horizontal
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
    
    def compose(self) -> ComposeResult:
        # yield Label(f"📦 {self.resource_name} - {self.resource_type} ({self.count})")
        yield Label(f"📦 {self.resource_name}")


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


class MainContent(Static):
    """Main content area showing resource details"""
    
    def __init__(self, **kwargs):
        super().__init__("Select a resource from the sidebar to view details", **kwargs)
        self.current_resource = None


class KubeTUI(App):
    """Main Kubernetes TUI Application"""
    
    CSS = """
    #sidebar {
        width: 30%;
        background: $surface;
        border: solid $primary;
        margin: 1;
        padding: 1;
    }
    
    #main-content {
        width: 70%;
        background: $surface;
        border: solid $primary;
        margin: 1;
        padding: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
    ]
    
    def __init__(self):
        super().__init__()
        self.k8s_client = None
        self.resource_sidebar = None
        self.main_content = None
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        
        # Create main layout immediately
        self.resource_sidebar = ResourceSidebar(id="sidebar")
        self.main_content = MainContent(id="main-content")
        
        yield Horizontal(
            self.resource_sidebar,
            self.main_content,
            id="main-layout"
        )
    
    def on_mount(self) -> None:
        """Called when the app is mounted"""
        # Try to load kube config and resources immediately
        try:
            config.load_kube_config()
            self.k8s_client = client.ApiClient()
            self.load_resources()
        except Exception as e:
            # If kube config fails, still show resources with 0 counts
            self.load_resources()
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle resource selection"""
        if hasattr(event.item, 'resource_name'):
            resource_name = event.item.resource_name
            self.show_resource_details(resource_name)
    
    
    def load_resources(self) -> None:
        """Load available Kubernetes resources"""
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
                details = self.get_resource_details(resource_name)
                self.main_content.update(details)
            except Exception as e:
                error_msg = f"Error loading {resource_name} details: {str(e)}"
                self.main_content.update(error_msg)
    
    def get_resource_details(self, resource_name: str) -> str:
        """Get detailed information about a specific resource"""
        if not self.k8s_client:
            return "No Kubernetes client available"
        
        try:
            v1 = client.CoreV1Api(self.k8s_client)
            apps_v1 = client.AppsV1Api(self.k8s_client)
            
            if resource_name == "pods":
                pods = v1.list_pod_for_all_namespaces()
                details = f"📦 Pods ({len(pods.items)} total)\n\n"
                for pod in pods.items[:10]:  # Show first 10 pods
                    status = pod.status.phase if pod.status else "Unknown"
                    details += f"• {pod.metadata.name} ({pod.metadata.namespace}) - {status}\n"
                if len(pods.items) > 10:
                    details += f"... and {len(pods.items) - 10} more\n"
                    
            elif resource_name == "services":
                services = v1.list_service_for_all_namespaces()
                details = f"🔗 Services ({len(services.items)} total)\n\n"
                for svc in services.items[:10]:
                    details += f"• {svc.metadata.name} ({svc.metadata.namespace}) - {svc.spec.type}\n"
                if len(services.items) > 10:
                    details += f"... and {len(services.items) - 10} more\n"
                    
            elif resource_name == "deployments":
                deployments = apps_v1.list_deployment_for_all_namespaces()
                details = f"🚀 Deployments ({len(deployments.items)} total)\n\n"
                for dep in deployments.items[:10]:
                    replicas = dep.spec.replicas if dep.spec.replicas else 0
                    ready = dep.status.ready_replicas if dep.status.ready_replicas else 0
                    details += f"• {dep.metadata.name} ({dep.metadata.namespace}) - {ready}/{replicas} ready\n"
                if len(deployments.items) > 10:
                    details += f"... and {len(deployments.items) - 10} more\n"
                    
            elif resource_name == "nodes":
                nodes = v1.list_node()
                details = f"🖥️  Nodes ({len(nodes.items)} total)\n\n"
                for node in nodes.items:
                    status = "Ready" if node.status.conditions and any(c.type == "Ready" and c.status == "True" for c in node.status.conditions) else "Not Ready"
                    details += f"• {node.metadata.name} - {status}\n"
                    
            elif resource_name == "namespaces":
                namespaces = v1.list_namespace()
                details = f"📁 Namespaces ({len(namespaces.items)} total)\n\n"
                for ns in namespaces.items:
                    status = ns.status.phase if ns.status else "Unknown"
                    details += f"• {ns.metadata.name} - {status}\n"
                    
            else:
                details = f"📋 {resource_name.title()}\n\nResource details not implemented yet.\n\nThis would show detailed information about {resource_name} resources."
            
            return details
            
        except Exception as e:
            return f"Error fetching {resource_name} details: {str(e)}"
    
    def action_quit(self) -> None:
        """Quit the application"""
        self.exit()


def main():
    """Main entry point"""
    app = KubeTUI()
    app.run()


if __name__ == "__main__":
    main()
