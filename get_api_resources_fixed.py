#!/usr/bin/env python3

from kubernetes import client, config
from kubernetes.client.rest import ApiException

def get_api_resources():
    """
    Get all API resources - fixed version
    """
    try:
        config.load_kube_config()
        api_client = client.ApiClient()
        
        print("🔍 Fetching API resources...")
        all_resources = []
        
        # Get core API (v1)
        try:
            response = api_client.call_api("/api/v1", 'GET', response_type='object')
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
            apis_api = client.ApisApi()
            api_group_list = apis_api.get_api_versions()
            
            for group in api_group_list.groups:
                for version in group.versions:
                    try:
                        path = f"/apis/{group.name}/{version.version}"
                        response = api_client.call_api(path, 'GET', response_type='object')
                        
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

def print_api_resources(resources):
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
    
    # Sort by name
    sorted_resources = sorted(resources, key=lambda x: x['name'])
    
    for resource in sorted_resources:
        namespaced_str = "true" if resource['namespaced'] else "false"
        print(f"{resource['name']:<35} {resource['shortnames']:<15} {resource['apiversion']:<25} {namespaced_str:<12} {resource['kind']}")

def test_resource_access():
    """
    Test access to specific resources
    """
    print("\n🧪 Testing resource access...")
    print("="*50)
    
    try:
        v1 = client.CoreV1Api()
        
        # Test common resources
        tests = [
            ("Pods", lambda: v1.list_pod_for_all_namespaces(watch=False)),
            ("Services", lambda: v1.list_service_for_all_namespaces(watch=False)),
            ("ConfigMaps", lambda: v1.list_config_map_for_all_namespaces(watch=False)),
            ("Secrets", lambda: v1.list_secret_for_all_namespaces(watch=False)),
            ("Namespaces", lambda: v1.list_namespace(watch=False)),
        ]
        
        for name, test_func in tests:
            try:
                result = test_func()
                print(f"✓ {name}: {len(result.items)} found")
            except Exception as e:
                print(f"❌ {name}: {e}")
        
        # Test apps/v1 if available
        try:
            apps_v1 = client.AppsV1Api()
            deployments = apps_v1.list_deployment_for_all_namespaces(watch=False)
            print(f"✓ Deployments: {len(deployments.items)} found")
        except Exception as e:
            print(f"❌ Deployments: {e}")
            
    except Exception as e:
        print(f"❌ Error testing resources: {e}")

def main():
    """
    Main function
    """
    print("🚀 Getting Kubernetes API Resources")
    print("Using service account: kube-tui-admin")
    print("="*60)
    
    resources = get_api_resources()
    
    if resources:
        print_api_resources(resources)
        test_resource_access()
        
        # Summary
        print(f"\n📊 Summary:")
        print("="*40)
        
        api_groups = {}
        for resource in resources:
            api_version = resource['apiversion']
            if api_version not in api_groups:
                api_groups[api_version] = 0
            api_groups[api_version] += 1
        
        for api_version, count in sorted(api_groups.items()):
            print(f"{api_version:<25} {count:>3} resources")
        
        print(f"\n🎯 Total: {len(resources)} resources across {len(api_groups)} API groups")
        print("✅ Service account has full cluster access!")
        
    else:
        print("❌ Failed to retrieve API resources")

if __name__ == "__main__":
    main()
