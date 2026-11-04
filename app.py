"""
Backend de la cafetería (solo librería estándar de Python, no requiere instalar nada).

Flujo orientado a eventos:
  POST /api/pedido  ->  evento "pedido_creado"
                    ->  se genera el recibo  ->  evento "recibo_generado"
                    ->  se elige un producto agotado al azar y se guarda la notificación
  GET  /api/notificacion/<folio>  ->  el frontend la consulta después de mostrar el recibo

Ejecutar:  python app.py   (puerto 8000)
"""
import json
import random
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from events import bus
from menu import PRODUCTOS, POR_ID

PUERTO = 8000
PEDIDOS = {}
NOTIFICACIONES = {}
_contador = {"n": 0}


# ---------------- Manejadores de eventos ----------------
@bus.on("pedido_creado")
def generar_recibo(pedido):
    lineas, total = [], 0
    for item in pedido["items"]:
        producto = POR_ID[item["id"]]
        importe = producto["precio"] * item["cantidad"]
        total += importe
        lineas.append({
            "nombre": producto["nombre"],
            "cantidad": item["cantidad"],
            "precio": producto["precio"],
            "importe": importe,
        })
    recibo = {
        "folio": pedido["folio"],
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "lineas": lineas,
        "total": total,
        "moneda": "MXN",
    }
    PEDIDOS[pedido["folio"]] = recibo
    bus.emit("recibo_generado", recibo)


@bus.on("recibo_generado")
def avisar_producto_agotado(recibo):
    producto = random.choice(PRODUCTOS)
    NOTIFICACIONES[recibo["folio"]] = {
        "producto_id": producto["id"],
        "titulo": "Producto agotado",
        "mensaje": f"Se acabó «{producto['nombre']}» por falta de ingredientes.",
    }


# ---------------- Servidor HTTP ----------------
def validar_items(cuerpo):
    items = cuerpo.get("items") if isinstance(cuerpo, dict) else None
    if not isinstance(items, list) or not items or len(items) > 30:
        return None
    limpios = []
    for it in items:
        try:
            pid, cant = it["id"], int(it["cantidad"])
        except (KeyError, TypeError, ValueError):
            return None
        if pid not in POR_ID or not 1 <= cant <= 20:
            return None
        limpios.append({"id": pid, "cantidad": cant})
    return limpios


class Manejador(BaseHTTPRequestHandler):
    def _cabeceras_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _responder(self, codigo, datos):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self._cabeceras_cors()
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cabeceras_cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/menu":
            return self._responder(200, {"moneda": "MXN", "productos": PRODUCTOS})
        if self.path.startswith("/api/notificacion/"):
            folio = self.path.rsplit("/", 1)[-1]
            if folio in NOTIFICACIONES:
                return self._responder(200, NOTIFICACIONES[folio])
            return self._responder(404, {"error": "No hay notificación para ese folio"})
        self._responder(404, {"error": "Ruta no encontrada"})

    def do_POST(self):
        if self.path != "/api/pedido":
            return self._responder(404, {"error": "Ruta no encontrada"})
        try:
            largo = int(self.headers.get("Content-Length", 0))
            cuerpo = json.loads(self.rfile.read(largo) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return self._responder(400, {"error": "JSON inválido"})
        items = validar_items(cuerpo)
        if items is None:
            return self._responder(400, {"error": "Pedido inválido"})
        _contador["n"] += 1
        folio = f"CN-{_contador['n']:04d}"
        bus.emit("pedido_creado", {"folio": folio, "items": items})
        self._responder(201, {"recibo": PEDIDOS[folio]})


if __name__ == "__main__":
    servidor = ThreadingHTTPServer(("0.0.0.0", PUERTO), Manejador)
    print(f"☕ Backend listo en http://localhost:{PUERTO}")
    servidor.serve_forever()
