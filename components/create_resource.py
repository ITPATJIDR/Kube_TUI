from textual.widget import Widget
from textual.app import ComposeResult, RenderResult
from textual.widgets import Static, TextArea, Button
from textual.containers import Container, Vertical, Horizontal
from textual.screen import ModalScreen
from kube_api import KubeAPI
import yaml
import os


class CreateResource(ModalScreen):
    """Modal screen for creating resources from templates"""
    
    BINDINGS = [
        ("escape", "close", "Close"),
        ("ctrl+a", "apply_resource", "Apply Resource"),
        ("ctrl+r", "reset_template", "Reset Template"),
    ]
    
    def __init__(self, resource_type: str, namespace: str = "default"):
        super().__init__()
        self.resource_type = resource_type
        self.namespace = namespace
        self.original_template = ""
        
    def compose(self) -> ComposeResult:
        with Container(classes="modal-container"):
            yield Static(f"Create {self.resource_type} Resource", 
                        classes="modal-title", id="create_title")
            with Vertical(classes="create_content"):
                yield Static("Edit the YAML template below. Click in the text area to edit, then press Ctrl+A to apply:", 
                           classes="create_instructions")
                yield TextArea("", id="yaml_editor", language="yaml")
                with Horizontal(classes="create_buttons"):
                    yield Button("Apply Resource", id="apply_btn", variant="primary")
                    yield Button("Reset Template", id="reset_btn", variant="default")
                    yield Button("Close", id="close_btn", variant="default")
        
    
    def on_mount(self) -> None:
        """Called when the modal is mounted"""
        self._load_template()
        self._update_title()
        # Don't auto-focus the text area, let user choose
    
    def action_close(self) -> None:
        """Close the modal"""
        self.dismiss()
    
    def action_apply_resource(self) -> None:
        """Apply the resource to Kubernetes"""
        self._apply_resource()
    
    def action_reset_template(self) -> None:
        """Reset template to original"""
        self._reset_template()
    
    def on_key(self, event) -> None:
        """Handle key events to ensure shortcuts work"""
        # If Ctrl+A is pressed, apply resource regardless of focus
        if event.key == "ctrl+a":
            event.prevent_default()
            self._apply_resource()
        # If Ctrl+R is pressed, reset template regardless of focus
        elif event.key == "ctrl+r":
            event.prevent_default()
            self._reset_template()
        # If Escape is pressed, close modal regardless of focus
        elif event.key == "escape":
            event.prevent_default()
            self.dismiss()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "apply_btn":
            self._apply_resource()
        elif event.button.id == "reset_btn":
            self._reset_template()
        elif event.button.id == "close_btn":
            self.dismiss()
    
    def on_click(self, event) -> None:
        """Handle clicks to focus text area when clicked"""
        if hasattr(event, 'target') and event.target.id == "yaml_editor":
            # Focus the text area when clicked
            text_area = self.query_one("#yaml_editor", TextArea)
            text_area.focus()
    
    def _update_title(self) -> None:
        """Update the title with resource type and namespace"""
        title_widget = self.query_one("#create_title", Static)
        title_widget.update(f"Create {self.resource_type} Resource (namespace: {self.namespace})")
    
    def _load_template(self) -> None:
        """Load template for the resource type"""
        try:
            text_area = self.query_one("#yaml_editor", TextArea)
            template_path = f"components/templates/{self.resource_type.lower()}.yaml"
            
            if os.path.exists(template_path):
                with open(template_path, 'r') as f:
                    template_content = f.read()
                
                # Update namespace in the template
                template_content = self._update_namespace_in_yaml(template_content, self.namespace)
                self.original_template = template_content
                text_area.text = template_content
            else:
                # Create a basic template if file doesn't exist
                basic_template = self._create_basic_template(self.resource_type)
                self.original_template = basic_template
                text_area.text = basic_template
                
        except Exception as e:
            self.notify(f"Error loading template: {str(e)}", title="Error")
    
    def _reset_template(self) -> None:
        """Reset template to original"""
        text_area = self.query_one("#yaml_editor", TextArea)
        text_area.text = self.original_template
        self.notify("Template reset to original", title="Info")
    
    def _apply_resource(self) -> None:
        """Apply the resource to Kubernetes"""
        try:
            text_area = self.query_one("#yaml_editor", TextArea)
            yaml_content = text_area.text
            
            if not yaml_content.strip():
                self.notify("Please enter YAML content", title="Error")
                return
            
            # Parse YAML to validate
            try:
                resource_data = yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                self.notify(f"Invalid YAML: {str(e)}", title="Error")
                return
            
            # Apply the resource
            kube_api = KubeAPI()
            result = self._apply_resource_to_k8s(kube_api, resource_data, self.namespace)
            
            if result:
                self.notify(f"Successfully created {self.resource_type} resource", title="Success")
                # Don't close the modal, keep it open for more resources
            else:
                self.notify(f"Failed to create {self.resource_type} resource", title="Error")
                
        except Exception as e:
            self.notify(f"Error applying resource: {str(e)}", title="Error")
    
    def _update_namespace_in_yaml(self, yaml_content: str, namespace: str) -> str:
        """Update the namespace in YAML content"""
        try:
            # Parse YAML
            data = yaml.safe_load(yaml_content)
            
            # Add or update namespace in metadata
            if 'metadata' not in data:
                data['metadata'] = {}
            
            data['metadata']['namespace'] = namespace
            
            # Convert back to YAML
            return yaml.dump(data, default_flow_style=False, sort_keys=False)
            
        except Exception:
            # If parsing fails, just return original content
            return yaml_content
    
    def _create_basic_template(self, resource_type: str) -> str:
        """Create a basic template for the resource type"""
        if resource_type.lower() == "pods":
            return f"""apiVersion: v1
kind: Pod
metadata:
  name: {resource_type.lower()}-example
  namespace: {self.namespace}
spec:
  containers:
  - name: {resource_type.lower()}-container
    image: nginx:latest
    ports:
    - containerPort: 80"""
        elif resource_type.lower() == "services":
            return f"""apiVersion: v1
kind: Service
metadata:
  name: {resource_type.lower()}-example
  namespace: {self.namespace}
spec:
  selector:
    app: {resource_type.lower()}-app
  ports:
  - protocol: TCP
    port: 80
    targetPort: 9376"""
        elif resource_type.lower() == "deployments":
            return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {resource_type.lower()}-example
  namespace: {self.namespace}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {resource_type.lower()}-app
  template:
    metadata:
      labels:
        app: {resource_type.lower()}-app
    spec:
      containers:
      - name: {resource_type.lower()}-container
        image: nginx:latest
        ports:
        - containerPort: 80"""
        else:
            return f"""apiVersion: v1
kind: {resource_type}
metadata:
  name: {resource_type.lower()}-example
  namespace: {self.namespace}
spec:
  # Add your specification here"""
    
    def _apply_resource_to_k8s(self, kube_api: KubeAPI, resource_data: dict, namespace: str) -> bool:
        """Apply resource to Kubernetes cluster"""
        try:
            # Get the resource type and API version
            kind = resource_data.get('kind', '').lower()
            api_version = resource_data.get('apiVersion', 'v1')
            
            # Determine the appropriate API client
            if api_version == 'v1':
                if kind == 'pod':
                    result = kube_api.v1.create_namespaced_pod(
                        namespace=namespace,
                        body=resource_data
                    )
                elif kind == 'service':
                    result = kube_api.v1.create_namespaced_service(
                        namespace=namespace,
                        body=resource_data
                    )
                elif kind == 'configmap':
                    result = kube_api.v1.create_namespaced_config_map(
                        namespace=namespace,
                        body=resource_data
                    )
                elif kind == 'secret':
                    result = kube_api.v1.create_namespaced_secret(
                        namespace=namespace,
                        body=resource_data
                    )
                else:
                    self.notify(f"Unsupported resource type: {kind}", title="Error")
                    return False
            elif api_version.startswith('apps/v1'):
                if kind == 'deployment':
                    result = kube_api.apps_v1.create_namespaced_deployment(
                        namespace=namespace,
                        body=resource_data
                    )
                elif kind == 'replicaset':
                    result = kube_api.apps_v1.create_namespaced_replica_set(
                        namespace=namespace,
                        body=resource_data
                    )
                else:
                    self.notify(f"Unsupported resource type: {kind}", title="Error")
                    return False
            else:
                self.notify(f"Unsupported API version: {api_version}", title="Error")
                return False
            
            return result is not None
            
        except Exception as e:
            self.notify(f"Kubernetes API error: {str(e)}", title="Error")
            return False
