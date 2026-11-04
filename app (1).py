"""
Frontend del kiosko (interfaz de escritorio hecha con Tkinter, sin HTML).
Habla con el backend por HTTP (ver cliente.py). Ejecutar:  python frontend\\app.py
"""
import tkinter as tk
from tkinter import messagebox

import cliente
from dibujos import dibujar

LECHE, FRESA, FRESA_FUERTE = "#fff4ee", "#ff8fb0", "#ec5d8a"
CAFE, MENTA, MANTEQUILLA, PAPEL = "#5b3a3a", "#bfeacc", "#ffe9a8", "#fffdf9"
FUENTE = "Comic Sans MS"
COLUMNAS, TAM_DIBUJO = 4, 140


def pesos(n):
    return f"${n:,.2f}"


def boton(padre, texto, comando, fondo=FRESA, **extra):
    return tk.Button(padre, text=texto, command=comando, bg=fondo, fg=CAFE, activebackground=fondo,
                     activeforeground=CAFE, relief="flat", cursor="hand2", font=(FUENTE, 11, "bold"),
                     highlightthickness=3, highlightbackground=CAFE, bd=0, **extra)


class Kiosko:
    def __init__(self, raiz):
        self.raiz = raiz
        raiz.title("Cafecito Nube - Kiosko")
        raiz.geometry("1200x780")
        raiz.minsize(940, 600)
        raiz.configure(bg=LECHE)
        self.productos, self.carrito, self.controles = [], {}, {}
        tk.Label(raiz, text="  ☕ Cafecito Nube  ", font=(FUENTE, 26, "bold"), bg=MANTEQUILLA, fg=CAFE,
                 highlightthickness=3, highlightbackground=CAFE).pack(pady=(16, 4))
        tk.Label(raiz, text="Toca lo que se te antoje y paga aquí mismito", font=(FUENTE, 12),
                 bg=LECHE, fg=CAFE).pack(pady=(0, 10))
        cuerpo = tk.Frame(raiz, bg=LECHE)
        cuerpo.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self._crear_menu(cuerpo)
        self._crear_carrito(cuerpo)
        raiz.after(100, self.cargar_menu)

    # ---------- menú ----------
    def _crear_menu(self, padre):
        marco = tk.Frame(padre, bg=LECHE)
        marco.pack(side="left", fill="both", expand=True)
        self.lienzo = tk.Canvas(marco, bg=LECHE, highlightthickness=0)
        barra = tk.Scrollbar(marco, orient="vertical", command=self.lienzo.yview)
        self.lienzo.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y")
        self.lienzo.pack(side="left", fill="both", expand=True)
        self.menu = tk.Frame(self.lienzo, bg=LECHE)
        self.lienzo.create_window((0, 0), window=self.menu, anchor="nw")
        self.menu.bind("<Configure>", lambda e: self.lienzo.configure(scrollregion=self.lienzo.bbox("all")))
        self.raiz.bind_all("<MouseWheel>", lambda e: self.lienzo.yview_scroll(int(-e.delta / 120), "units"))

    def cargar_menu(self):
        for hijo in self.menu.winfo_children():
            hijo.destroy()
        try:
            self.productos = cliente.obtener_menu()
        except cliente.ErrorCliente:
            tk.Label(self.menu, text="No pude conectar con el backend.\nInícialo con:  python backend\\app.py",
                     font=(FUENTE, 13), bg=LECHE, fg=CAFE, justify="left").pack(padx=20, pady=20)
            boton(self.menu, "Reintentar", self.cargar_menu, MENTA, padx=16, pady=6).pack()
            return
        fila = 0
        for titulo, categoria in (("Cafés", "cafe"), ("Postres", "postre")):
            tk.Label(self.menu, text=titulo, font=(FUENTE, 20, "bold"), bg=LECHE, fg=CAFE).grid(
                row=fila, column=0, columnspan=COLUMNAS, sticky="w", padx=8, pady=(10, 6))
            fila += 1
            for i, p in enumerate([q for q in self.productos if q["categoria"] == categoria]):
                self._tarjeta(p).grid(row=fila + i // COLUMNAS, column=i % COLUMNAS, padx=8, pady=8, sticky="n")
            fila += (len([q for q in self.productos if q["categoria"] == categoria]) + COLUMNAS - 1) // COLUMNAS

    def _tarjeta(self, p):
        t = tk.Frame(self.menu, bg=PAPEL, highlightthickness=3, highlightbackground=CAFE, padx=8, pady=8)
        arte = tk.Canvas(t, width=TAM_DIBUJO, height=TAM_DIBUJO, bg=PAPEL, highlightthickness=0)
        arte.pack()
        dibujar(arte, p["id"], TAM_DIBUJO)
        tk.Label(t, text=p["nombre"], font=(FUENTE, 11, "bold"), bg=PAPEL, fg=CAFE, wraplength=150,
                 height=2).pack(pady=(4, 0))
        tk.Label(t, text=pesos(p["precio"]), font=(FUENTE, 13, "bold"), bg=PAPEL, fg=FRESA_FUERTE).pack()
        fila = tk.Frame(t, bg=PAPEL)
        fila.pack(pady=(6, 0), fill="x")
        menos = boton(fila, "−", lambda i=p["id"]: self.cambiar(i, -1), "#ffffff", width=2)
        cantidad = tk.Label(fila, text="0", font=(FUENTE, 12, "bold"), bg=PAPEL, fg=CAFE, width=3)
        mas = boton(fila, "Agregar", lambda i=p["id"]: self.cambiar(i, 1), MENTA, pady=3)
        menos.grid(row=0, column=0)
        cantidad.grid(row=0, column=1)
        mas.grid(row=0, column=2, sticky="ew")
        fila.columnconfigure(2, weight=1)
        menos.grid_remove()
        cantidad.grid_remove()
        self.controles[p["id"]] = (menos, cantidad)
        return t

    # ---------- carrito ----------
    def _crear_carrito(self, padre):
        marco = tk.Frame(padre, bg=PAPEL, highlightthickness=3, highlightbackground=CAFE, padx=16, pady=14, width=320)
        marco.pack(side="right", fill="y", padx=(16, 0))
        marco.pack_propagate(False)
        tk.Label(marco, text="Tu pedido", font=(FUENTE, 18, "bold"), bg=PAPEL, fg=CAFE).pack(anchor="w")
        self.lista = tk.Frame(marco, bg=PAPEL)
        self.lista.pack(fill="x", pady=8)
        pie = tk.Frame(marco, bg=PAPEL)
        pie.pack(side="bottom", fill="x")
        fila = tk.Frame(pie, bg=PAPEL)
        fila.pack(fill="x", pady=8)
        tk.Label(fila, text="Total", font=(FUENTE, 15), bg=PAPEL, fg=CAFE).pack(side="left")
        self.total = tk.Label(fila, text=pesos(0), font=(FUENTE, 20, "bold"), bg=PAPEL, fg=CAFE)
        self.total.pack(side="right")
        self.pagar_btn = boton(pie, "Pagar", self.pagar, FRESA, pady=8, state="disabled")
        self.pagar_btn.pack(fill="x")

    def cambiar(self, id_, delta):
        nueva = max(0, min(20, self.carrito.get(id_, 0) + delta))
        if nueva:
            self.carrito[id_] = nueva
        else:
            self.carrito.pop(id_, None)
        self.actualizar()

    def actualizar(self):
        for hijo in self.lista.winfo_children():
            hijo.destroy()
        total = 0
        for p in self.productos:
            c = self.carrito.get(p["id"], 0)
            menos, cantidad = self.controles[p["id"]]
            if c:
                cantidad.config(text=str(c))
                menos.grid()
                cantidad.grid()
                total += c * p["precio"]
                f = tk.Frame(self.lista, bg=PAPEL)
                f.pack(fill="x", pady=2)
                tk.Label(f, text=f"{c} × {p['nombre']}", font=(FUENTE, 10), bg=PAPEL, fg=CAFE, wraplength=190,
                         justify="left").pack(side="left")
                tk.Label(f, text=pesos(c * p["precio"]), font=(FUENTE, 10, "bold"), bg=PAPEL,
                         fg=CAFE).pack(side="right")
            else:
                menos.grid_remove()
                cantidad.grid_remove()
        if not self.carrito:
            tk.Label(self.lista, text="Aún no has elegido nada.\n¡Anímate a pedir algo rico!", font=(FUENTE, 10),
                     bg=PAPEL, fg="#8c7270", justify="left").pack(anchor="w")
        self.total.config(text=pesos(total))
        self.pagar_btn.config(state="normal" if self.carrito else "disabled")

    # ---------- pago, recibo y notificación ----------
    def pagar(self):
        items = [{"id": i, "cantidad": c} for i, c in self.carrito.items()]
        try:
            recibo = cliente.enviar_pedido(items)
        except cliente.ErrorCliente:
            messagebox.showerror("No se pudo cobrar", "Revisa que el backend esté encendido e inténtalo de nuevo.")
            return
        self.carrito.clear()
        self.actualizar()
        self.mostrar_recibo(recibo)
        self.raiz.after(2500, lambda: self.pedir_notificacion(recibo["folio"]))

    def mostrar_recibo(self, r):
        ventana = tk.Toplevel(self.raiz, bg=PAPEL, highlightthickness=3, highlightbackground=CAFE)
        ventana.title("Tu recibo")
        ventana.transient(self.raiz)
        ancho = 38
        raya = "- " * (ancho // 2)
        lineas = ["CAFECITO NUBE".center(ancho), f"Folio {r['folio']}  {r['fecha']}".center(ancho), raya]
        for l in r["lineas"]:
            izq, der = f"{l['cantidad']}x {l['nombre']}", pesos(l["importe"])
            lineas.append(izq[: ancho - len(der) - 1].ljust(ancho - len(der)) + der)
            lineas.append(f"   {pesos(l['precio'])} c/u")
        lineas += [raya, "TOTAL".ljust(ancho - len(pesos(r["total"]))) + pesos(r["total"]), raya,
                   "¡Gracias por tu visita!".center(ancho)]
        tk.Label(ventana, text="\n".join(lineas), font=("Courier New", 11), bg=PAPEL, fg=CAFE, justify="left",
                 padx=20, pady=18).pack()
        boton(ventana, "Hacer otro pedido", ventana.destroy, MENTA, pady=6).pack(fill="x", padx=20, pady=(0, 18))
        ventana.update_idletasks()
        x = self.raiz.winfo_x() + (self.raiz.winfo_width() - ventana.winfo_width()) // 2
        y = self.raiz.winfo_y() + max(20, (self.raiz.winfo_height() - ventana.winfo_height()) // 2)
        ventana.geometry(f"+{x}+{y}")

    def pedir_notificacion(self, folio):
        aviso = cliente.obtener_notificacion(folio)
        if aviso:
            self.mostrar_aviso(aviso["titulo"], aviso["mensaje"])

    def mostrar_aviso(self, titulo, mensaje):
        v = tk.Toplevel(self.raiz, bg=MANTEQUILLA, highlightthickness=3, highlightbackground=CAFE)
        v.overrideredirect(True)
        v.attributes("-topmost", True)
        tk.Label(v, text=f"★ {titulo}", font=(FUENTE, 13, "bold"), bg=MANTEQUILLA, fg=CAFE).pack(
            anchor="w", padx=16, pady=(14, 2))
        tk.Label(v, text=mensaje, font=(FUENTE, 11), bg=MANTEQUILLA, fg=CAFE, wraplength=300,
                 justify="left").pack(anchor="w", padx=16)
        boton(v, "Entendido", v.destroy, FRESA, padx=14, pady=3).pack(anchor="e", padx=16, pady=12)
        v.update_idletasks()
        x = self.raiz.winfo_x() + self.raiz.winfo_width() - v.winfo_width() - 24
        y = self.raiz.winfo_y() + self.raiz.winfo_height() - v.winfo_height() - 48
        v.geometry(f"+{x}+{y}")
        self.raiz.bell()


if __name__ == "__main__":
    raiz = tk.Tk()
    Kiosko(raiz)
    raiz.mainloop()
