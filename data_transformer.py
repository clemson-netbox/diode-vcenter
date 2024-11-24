from diode_sdk.models import VirtualMachine, Device

def transform_and_push_clusters(diode_client, cluster_data):
    for cluster in cluster_data:
        # Transform each host in the cluster into a Device
        for host in cluster["hosts"]:
            device = Device(
                name=host["name"],
                site="Default Site",  # Replace with the appropriate site name
                role="host",          # Replace with the appropriate role
                manufacturer="VMware",  # Assuming VMware hosts
                model="ESXi",          # Replace with appropriate model info
                custom_fields={
                    "cpus": host["cpus"],
                    "memory": host["memory"],
                }
            )
            diode_client.publish(device)

def transform_and_push_vms(diode_client, vm_data):
    for vm in vm_data:
        # Transform each VM into a VirtualMachine
        virtual_machine = VirtualMachine(
            name=vm["name"],
            cluster="Default Cluster",  # Replace with the appropriate cluster name
            role="application-server",  # Replace with the appropriate VM role
            custom_fields={
                "interfaces": vm["interfaces"],  # List of NICs
                "disks": vm["disks"],            # List of disks
            }
        )
        diode_client.publish(virtual_machine)
