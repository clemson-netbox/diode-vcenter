from pyVim.connect import SmartConnect, Disconnect
import ssl
import logging

# Set up logging for status messages
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def connect_to_vcenter(host, user, password):
    """
    Establish a connection to the vCenter server.
    :param host: vCenter hostname or IP
    :param user: vCenter username
    :param password: vCenter password
    :return: ServiceInstance object if connection is successful, None otherwise
    """
    logging.info(f"Attempting to connect to vCenter at {host}...")
    try:
        # Disable SSL verification for testing
        context = ssl._create_unverified_context()
        si = SmartConnect(host=host, user=user, pwd=password, sslContext=context)
        logging.info("Successfully connected to vCenter.")
        return si
    except Exception as e:
        logging.error(f"Failed to connect to vCenter: {e}")
        return None

def disconnect_vcenter(si):
    """
    Disconnect from the vCenter server.
    :param si: ServiceInstance object
    """
    if si:
        try:
            Disconnect(si)
            logging.info("Disconnected from vCenter.")
        except Exception as e:
            logging.error(f"Failed to disconnect from vCenter: {e}")
    else:
        logging.warning("No active vCenter session to disconnect.")
