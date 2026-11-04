
import json
import urllib.error
import urllib.request

API = "http://127.0.0.1:8000"


class ErrorCliente(Exception):
    


def _pedir(ruta, datos=None):
    cuerpo = None if datos is None else json.dumps(datos).encode("utf-8")
    peticion = urllib.request.Request(
        API + ruta,
        data=cuerpo,
        headers={"Content-Type": "application/json"},
        method="GET" if datos is None else "POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=5) as respuesta:
            return json.loads(respuesta.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError) as error:
        raise ErrorCliente(str(error)) from error


def obtener_menu():
    return _pedir("/api/menu")["productos"]


def enviar_pedido(items):
    """items: lista de {"id": ..., "cantidad": ...}. Devuelve el recibo."""
    return _pedir("/api/pedido", {"items": items})["recibo"]


def obtener_notificacion(folio):
    try:
        return _pedir(f"/api/notificacion/{folio}")
    except ErrorCliente:
        return None
