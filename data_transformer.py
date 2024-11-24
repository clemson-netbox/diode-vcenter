import re
from netboxlabs.diode.sdk.ingester import (
    Device,
    VirtualMachine,
 )

# Utility function to apply regex transformations
def apply_regex_replacements(value, replacements):
    for pattern, replacement in replacements:
        if re.match(pattern, value, flags=re.IGNORECASE):
            return re.sub(pattern, replacement, value, flags=re.IGNORECASE)
    return value

# Regex transformation rules for site
SITE_REPLACEMENTS = [
    (r"(?i)^CU-.+", "Clemson Information Technology Center"),
    (r"(?i)^CUDR-.+|^DR-.+", "University of California San Diego"),
    (r"(?i)^Poole-.+", "Poole Agricultural Center"),
    (r"(?i)^Proto-.+", "Clemson Information Technology Center"),
]

def get_site_name(cluster_name):
    return apply_regex_replacements(cluster_name, SITE_REPLACEMENTS)

def get_group_name(cluster_parent_name):
    return cluster_parent_name  # Direct mapping for now, adjust as needed

def transform_and_push_clusters(diode_client, cluster_data):
    for cluster in cluster_data:
        site_name = get_site_name(cluster["name"])  # Determine site from cluster name
        group_name = get_group_name(cluster["parent_name"])  # Determine group from parent name
        
        # Transform and push each host in the cluster
        for host in cluster["hosts"]:
            device = Device(
                name=host["name"],
                site=site_name,  # Use site name determined above
                cluster_group=group_name,  # Use group name determined above
                role="host",  # Replace with appropriate role
                manufacturer="VMware",  # Assuming VMware hosts
                model="ESXi",  # Replace with appropriate model info
                custom_fields={
                    "cpus": host["cpus"],
                    "memory": host["memory"],
                }
            )
            diode_client.publish(device)

def transform_and_push_vms(diode_client, vm_data):
    for vm in vm_data:
        virtual_machine = VirtualMachine(
            name=vm["name"],
            cluster=vm["cluster"],  # Use cluster name directly from VM data
            site=vm.get("site"),  # Optionally include site if applicable
            role="application-server",  # Replace with appropriate VM role
            custom_fields={
                "interfaces": vm["interfaces"],  # List of NICs
                "disks": vm["disks"],  # List of disks
            }
        )
        diode_client.publish(virtual_machine)
