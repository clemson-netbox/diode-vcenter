from diode_sdk import DiodeClient

def connect_to_diode():
    from config import DIODE_SERVER, DIODE_TOKEN
    return DiodeClient(server=DIODE_SERVER, token=DIODE_TOKEN)
