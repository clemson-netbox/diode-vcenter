from netboxlabs.diode.sdk import DiodeClient

def connect_to_diode(server, token):
    return DiodeClient(server=server, token=token)
