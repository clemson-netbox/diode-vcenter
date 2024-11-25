import re
from netboxlabs.diode.sdk.ingester import Device, VirtualMachine, Cluster, Interface, VMInterface, VirtualDisk, IPAddress, Entity


def prepare_cluster_data(data):
    """
    Transforms cluster and host data into Diode-compatible entities.
    """
    entities = []

    for cluster in data:
        
        cluster_entity = Cluster(
            name=cluster['name'],
            group=cluster['group'],
            type="VMWare",
            site=cluster['site'],
            status='active',
            tags=["Diode-vCenter-Agent"],

        )
        entities.append(Entity(cluster=cluster_entity))
                    
        for host in cluster["hosts"]:
           
            # Create Device entity for each host
            device_data = Device(
                name=host["name"],
                site=cluster["site"],
                device_type=host["model"],
                manufacturer=host["vendor"],
                serial=host["serial_number"],
                role="Hypervisor Host",  # Replace with specific role if applicable
                status="active",
                tags=["Diode-vCenter-Agent"],

                #interfaces=interfaces,  # Host NICs as interfaces
            )
            entities.append(Entity(device=device_data))
            
            for nic in host["nics"]:
                interface_data = Interface(
                    name=nic["name"], 
                    device=host["name"],  
                    mac_address=nic["mac"],
                    type=nic["type"],
                    tags=["Diode-vCenter-Agent"],

                )       
                entities.append(Entity(interface=interface_data))
                for ip in nic['ip_addresses']:
                    ip_data = IPAddress(
                        address=ip,
                        interface=interface_data,
                        description=f"{nic['name']} {nic['dvs_name']} {nic['portgroup_name']}",
                        tags=["Diode-vCenter-Agent"],

                    )
                    entities.append(Entity(ip_address=ip_data))
           

    return entities

def prepare_vm_data(vm_data):
    """
    Transforms VM data into Diode-compatible VirtualMachine entities.
    """
    entities = []

    for vm in vm_data:

        # Create VirtualMachine entity for each VM
        virtual_machine = VirtualMachine(
            name=vm["name"],
            cluster=vm["cluster"],
            device=vm['device'],
            platform=vm['platform'],
            vcpus=vm['vcpus'],
            memory=vm['memory'],
            site=vm["site"],
            role=vm['role'],
            status=vm['status'],
            tags=["Diode-vCenter-Agent"],
        )
        entities.append(Entity(virtual_machine=virtual_machine))
        
        for nic in vm["interfaces"]:
            interface_data = Interface(
                name=nic["name"], 
                virtual_machine=vm["name"],  
                mac_address=nic["mac"],
                enabled=nic["enabled"],
                tags=["Diode-vCenter-Agent"],

            ) 
            entities.append(Entity(vminterface=interface_data))
            if nic['ipv6_address']:
                ip_data = IPAddress(
                    address=nic['ipv4_address'],
                    description=f"{vm['name']} {nic['name']}",
                    status='active'
                )
                entities.append(Entity(ip_address=ip_data))
            if nic['ipv6_address']:
                ip_data = IPAddress(
                    address=nic['ipv6_address'],
                    description=f"{vm['name']} {nic['name']}",
                    status='active'
                )
                entities.append(Entity(ip_address=ip_data))
            for disk in vm["disks"]:
                disk = VirtualDisk(
                    name=disk['label'],
                    virtual_machine=vm['name'],
                    capacity=disk['capacity'],
                    description=f"{disk['datastore']} {disk['vmdk']} {disk['tick_thin']} {disk['disk_type']}",
                    tags=["Diode-vCenter-Agent"],
                )
                entities.append(Entity(vmirtual_disk=disk))

    return entities
