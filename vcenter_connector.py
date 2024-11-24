from pyVim.connect import SmartConnect, Disconnect
import ssl

def connect_to_vcenter(host, user, password):
    context = ssl._create_unverified_context()  # Disable SSL for testing
    si = SmartConnect(host=host, user=user, pwd=password, sslContext=context)
    return si

def disconnect_vcenter(si):
    Disconnect(si)
