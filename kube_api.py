#!/usr/bin/env python3

from kubernetes import client, config
from kubernetes.client.rest import ApiException

class KubeAPI:
    """
    Kubernetes API wrapper class for kube-tui
    """
    
    def __init__(self):
        """Initialize the KubeAPI client"""
        try:
            config.load_kube_config()
            self.api_client = client.ApiClient()
            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.apis_api = client.ApisApi()
            print("✅ KubeAPI initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize KubeAPI: {e}")
            raise e
    
    def get_api_resources(self):
        """
        Get all API resources - fixed version
        """
        try:
            print("🔍 Fetching API resources...")
            all_resources = []
            
            # Get core API (v1)
            try:
                response = self.api_client.call_api("/api/v1", 'GET', response_type='object')
                if response and len(response) > 0:
                    api_resources = response[0]  # This is a dict
                    if 'resources' in api_resources:
                        for resource in api_resources['resources']:
                            if 'name' in resource and '/' not in resource['name']:
                                name = resource['name']
                                short_names = resource.get('shortNames', [])
                                short_names_str = ','.join(short_names) if short_names else ''
                                namespaced = resource.get('namespaced', False)
                                kind = resource.get('kind', '')
                                
                                all_resources.append({
                                    'name': name,
                                    'shortnames': short_names_str,
                                    'apiversion': 'v1',
                                    'namespaced': namespaced,
                                    'kind': kind
                                })
                print(f"✓ Core API (v1): {len([r for r in all_resources if r['apiversion'] == 'v1'])} resources")
            except Exception as e:
                print(f"❌ Core API: {e}")
            
            # Get other API groups
            try:
                api_group_list = self.apis_api.get_api_versions()
                
                for group in api_group_list.groups:
                    for version in group.versions:
                        try:
                            path = f"/apis/{group.name}/{version.version}"
                            response = self.api_client.call_api(path, 'GET', response_type='object')
                            
                            if response and len(response) > 0:
                                api_resources = response[0]  # This is a dict
                                if 'resources' in api_resources:
                                    for resource in api_resources['resources']:
                                        if 'name' in resource and '/' not in resource['name']:
                                            name = resource['name']
                                            short_names = resource.get('shortNames', [])
                                            short_names_str = ','.join(short_names) if short_names else ''
                                            api_version = f"{group.name}/{version.version}"
                                            namespaced = resource.get('namespaced', False)
                                            kind = resource.get('kind', '')
                                            
                                            all_resources.append({
                                                'name': name,
                                                'shortnames': short_names_str,
                                                'apiversion': api_version,
                                                'namespaced': namespaced,
                                                'kind': kind
                                            })
                        except Exception as e:
                            print(f"⚠ Error with {group.name}/{version.version}: {e}")
                            continue
                
                print(f"✓ Other API groups: {len(api_group_list.groups)} groups processed")
                
            except Exception as e:
                print(f"❌ API Groups: {e}")
            
            return all_resources
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return []
    
    def get_namespaces(self):
        """
        Get all namespaces
        """
        try:
            namespaces = self.v1.list_namespace(watch=False)
            return [ns.metadata.name for ns in namespaces.items]
        except Exception as e:
            print(f"❌ Error getting namespaces: {e}")
            return []
    
    def get_pods(self, namespace=None):
        """
        Get pods from a specific namespace or all namespaces
        """
        try:
            if namespace:
                pods = self.v1.list_namespaced_pod(namespace=namespace, watch=False)
            else:
                pods = self.v1.list_pod_for_all_namespaces(watch=False)
            return pods.items
        except Exception as e:
            print(f"❌ Error getting pods: {e}")
            return []
    
    def get_services(self, namespace=None):
        """
        Get services from a specific namespace or all namespaces
        """
        try:
            if namespace:
                services = self.v1.list_namespaced_service(namespace=namespace, watch=False)
            else:
                services = self.v1.list_service_for_all_namespaces(watch=False)
            return services.items
        except Exception as e:
            print(f"❌ Error getting services: {e}")
            return []
    
    def get_deployments(self, namespace=None):
        """
        Get deployments from a specific namespace or all namespaces
        """
        try:
            if namespace:
                deployments = self.apps_v1.list_namespaced_deployment(namespace=namespace, watch=False)
            else:
                deployments = self.apps_v1.list_deployment_for_all_namespaces(watch=False)
            return deployments.items
        except Exception as e:
            print(f"❌ Error getting deployments: {e}")
            return []

    def get_configmaps(self, namespace=None):
        """
        Get configmaps from a specific namespace or all namespaces
        """
        try:
            if namespace:
                configmaps = self.v1.list_namespaced_config_map(namespace=namespace, watch=False)
            else:
                configmaps = self.v1.list_config_map_for_all_namespaces(watch=False)
            return configmaps.items
        except Exception as e:
            print(f"❌ Error getting configmaps: {e}")
            return []

    def get_secrets(self, namespace=None):
        """
        Get secrets from a specific namespace or all namespaces
        """
        try:
            if namespace:
                secrets = self.v1.list_namespaced_secret(namespace=namespace, watch=False)
            else:
                secrets = self.v1.list_secret_for_all_namespaces(watch=False)
            return secrets.items
        except Exception as e:
            print(f"❌ Error getting secrets: {e}")
            return []
    
    def test_connection(self):
        """
        Test the connection to the Kubernetes cluster
        """
        try:
            namespaces = self.v1.list_namespace(watch=False)
            pods = self.v1.list_pod_for_all_namespaces(watch=False)
            
            print("🧪 Testing connection...")
            print(f"✓ Namespaces: {len(namespaces.items)} found")
            print(f"✓ Pods: {len(pods.items)} found")
            
            return True
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    def print_api_resources(self, resources):
        """
        Print resources in kubectl format
        """
        if not resources:
            print("❌ No resources found")
            return
        
        print(f"\n📋 Found {len(resources)} API resources:")
        print("="*100)
        print(f"{'NAME':<35} {'SHORTNAMES':<15} {'APIVERSION':<25} {'NAMESPACED':<12} {'KIND'}")
        print("-" * 100)
        
        sorted_resources = sorted(resources, key=lambda x: x['name'])
        
        for resource in sorted_resources:
            namespaced_str = "true" if resource['namespaced'] else "false"
            print(f"{resource['name']:<35} {resource['shortnames']:<15} {resource['apiversion']:<25} {namespaced_str:<12} {resource['kind']}")
    
    def get_resource_summary(self, resources):
        """
        Get summary of API resources by group
        """
        if not resources:
            return {}
        
        api_groups = {}
        for resource in resources:
            api_version = resource['apiversion']
            if api_version not in api_groups:
                api_groups[api_version] = 0
            api_groups[api_version] += 1
        
        return api_groups

def main():
    """
    Test the KubeAPI class
    """
    print("🚀 Testing KubeAPI Class")
    print("="*60)
    
    try:
        kube_api = KubeAPI()
        
        if not kube_api.test_connection():
            return
        
        resources = kube_api.get_api_resources()
        
        if resources:
            kube_api.print_api_resources(resources)
            
            summary = kube_api.get_resource_summary(resources)
            print(f"\n📊 Summary:")
            print("="*40)
            
            for api_version, count in sorted(summary.items()):
                print(f"{api_version:<25} {count:>3} resources")
            
            print(f"\n🎯 Total: {len(resources)} resources across {len(summary)} API groups")
            print("✅ KubeAPI working perfectly!")
            
        else:
            print("❌ Failed to retrieve API resources")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
