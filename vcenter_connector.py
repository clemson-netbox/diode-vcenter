from pyVim.connect import SmartConnect, Disconnect
import ssl

def connect_to_vcenter():
    from config import VCENTER_HOST, VCENTER_USER, VCENTER_PASSWORD
    context = ssl._create_unverified_context()  # Disable SSL for testing (not recommended in production)
    si = SmartConnect(host=VCENTER_HOST, user=VCENTER_USER, pwd=VCENTER_PASSWORD, sslContext=context)
    return si

def disconnect_vcenter(si):
    Disconnect(si)
