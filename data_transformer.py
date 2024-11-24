from diode_sdk.models import Resource

def transform_and_push_clusters(diode_client, cluster_data):
    for cluster in cluster_data:
        resource = Resource(
            name=cluster["name"],
            resource_type="cluster",
            properties={"hosts": cluster["hosts"]}
        )
        diode_client.publish(resource)

def transform_and_push_vms(diode_client, vm_data):
    for vm in vm_data:
        resource = Resource(
            name=vm["name"],
            resource_type="virtual_machine",
            properties={
                "interfaces": vm["interfaces"],
                "disks": vm["disks"]
            }
        )
        diode_client.publish(resource)
