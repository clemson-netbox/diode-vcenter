import re
from netboxlabs.diode.sdk.ingester import Device, VirtualMachine, Cluster, Interface, VMInterface, VirtualDisk, IPAddress, Entity

def prepare_data(client,data,vm_data,logging):
    """
    Transforms cluster and host data into Diode-compatible entities.
    """
    entities = []
    cluster_cache={}
    host_cache={}

    for cluster in data:
        
        cluster_entity = Cluster(
            name=cluster['name'],
            group=cluster['group'],
            type="VMWare",
            site=cluster['site'],
            status='active',
            tags=["Diode-vCenter-Agent",'Diode'],

        )
        cluster_cache[cluster['name']]=cluster_entity
        entities.append(Entity(cluster=cluster_entity))
                    
        for host in cluster["hosts"]:
           
            #TODO: link to cluster when diode is updated to support
            # Create Device entity for each host
            device_data = Device(
                name=host["name"],
                site=cluster["site"],
                device_type=host["model"],
                manufacturer=host["vendor"],
                serial=host["serial_number"],
                role="Hypervisor Host",  # Replace with specific role if applicable
                status="active",
                tags=["Diode-vCenter-Agent",'Diode'],

                #interfaces=interfaces,  # Host NICs as interfaces
            )
            host_cache[host['name']]=device_data

            #TODO: Create prefixes and VLANs for networks
            for nic in host["nics"]:
                interface_data = Interface(
                    name=nic["name"], 
                    device=device_data, 
                    description=f"{host['name']} {nic['name']} {nic['portgroup_name']}",
                    mac_address=nic["mac"],
                    type=nic["type"],
                    tags=["Diode-vCenter-Agent",'Diode'],

                )       
                entities.append(Entity(interface=interface_data))
                for ip in nic['ip_addresses']:
                    ip_data = IPAddress(
                        address=ip,
                        interface=interface_data,
                        description=f"{host['name']} {nic['name']} {nic['portgroup_name']}",
                        tags=["Diode-vCenter-Agent",'Diode'],

                    )
                    entities.append(Entity(ip_address=ip_data))
           
        logging.info("Ingesting Cluster/Host data into Diode...")
        logging.debug(f"Total entities being sent: {entities}")
        try:
            response = client.ingest(entities=entities)
            if response.errors:
                logging.error(f"Diode Ingestion Errors: {response.errors}")
            else:
                logging.info(f"Successfully ingested {len(entities)}.")
        except Exception as e:
            logging.error(f"Error during ingestion: {e}")
        entities=[]
                
                
    for vm in vm_data:
        
        try:
            # Create VirtualMachine entity for each VM
            virtual_machine = VirtualMachine(
                name=vm["name"],
                cluster=cluster_cache[vm["cluster"]],
                device=host_cache[vm["device"]],
                platform=vm["platform"],
                vcpus=vm["vcpus"],
                memory=vm["memory"],
                site=vm["site"],
                role=vm["role"],
                status=vm["status"],
                tags=["Diode-vCenter-Agent",'Diode'],
            )
            entities.append(Entity(virtual_machine=virtual_machine))
            
            for nic in vm["interfaces"]:
                try:
                    interface_data = VMInterface(
                        name=nic["name"],
                        description=f"{vm["name"]}: {nic["name"]}",                
                        virtual_machine=virtual_machine,
                        mac_address=nic["mac"],
                        enabled=nic["enabled"],
                        tags=["Diode-vCenter-Agent",'Diode'],
                    )
                    entities.append(Entity(vminterface=interface_data))
                    
                    #TODO: Create prefixes and VLANs for networks
                    #TODO: link to vm_interface when diode is updated to support
                    if nic.get("ipv4_address"):
                        ip_data = IPAddress(
                            address=nic["ipv4_address"]["address"],
                            description=f"{vm['name']} {nic['name']}",
                            status="active",
                            tags=["Diode-vCenter-Agent",'Diode'],
                        )
                        entities.append(Entity(ip_address=ip_data))
                        
                    #TODO: link to vm_interface when diode is updated to support
                    if nic.get("ipv6_address"):
                        ip_data = IPAddress(
                            address=nic["ipv6_address"]["address"],
                            description=f"{vm['name']} {nic['name']}",
                            status="active",
                            tags=["Diode-vCenter-Agent",'Diode'],

                        )
                        entities.append(Entity(ip_address=ip_data))
                except KeyError as e:
                    logging.error(f"Error processing NIC for VM {vm['name']}: Missing key {e}")
                    continue

            for disk in vm["disks"]:
                try:
                    disk_data = VirtualDisk(
                        name=disk["name"],
                        virtual_machine=virtual_machine,
                        size=disk["capacity"],
                        description=f"{disk.get('datastore', 'Unknown')} "
                                    f"{disk.get('vmdk', 'Unknown')} "
                                    f"{disk.get('thin_thick', 'Unknown')} "
                                    f"{disk.get('disk_type', 'Unknown')}",
                        tags=["Diode-vCenter-Agent",'Diode'],
                    )
                    entities.append(Entity(virtual_disk=disk_data))
                except KeyError as e:
                    logging.error(f"Error processing disk for VM {vm['name']}: Missing key {e}")
                    continue
        except KeyError as e:
            logging.error(f"Error processing VM: Missing key {e}")
            continue
        
        # Ingest data into Diode
        if len(entities) > 10000:
            logging.info(f"Ingesting {len(entities)} entity batch device data into Diode...")
            response = client.ingest(entities=entities)# + interface_entities)
            if response.errors:
                logging.error(f"Errors during ingestion: {response.errors}")
            else:
                logging.info("Data ingested successfully into Diode.")
            entities = []

    return entities
