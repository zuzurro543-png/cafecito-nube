"""Mini bus de eventos: permite que cada paso del pedido reaccione al anterior."""
from collections import defaultdict


class BusDeEventos:
    def __init__(self):
        self._manejadores = defaultdict(list)

    def on(self, evento):
        def registrar(funcion):
            self._manejadores[evento].append(funcion)
            return funcion
        return registrar

    def emit(self, evento, datos):
        for manejador in self._manejadores[evento]:
            manejador(datos)


bus = BusDeEventos()
