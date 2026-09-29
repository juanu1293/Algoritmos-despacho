"""Algoritmos de despacho de CPU: FCFS, SJF, Prioridad y Round Robin.

Cada proceso es un dict: {"pid": str, "llegada": int, "rafaga": int, "prioridad": int}
Convención de prioridad: número MENOR = prioridad MÁS ALTA.
Todas las funciones devuelven (linea_tiempo, metricas).
"""


def _agregar(linea, pid, ini, fin):
    """Agrega un segmento y lo fusiona con el anterior si es el mismo proceso."""
    if linea and linea[-1]["pid"] == pid and linea[-1]["fin"] == ini:
        linea[-1]["fin"] = fin
    else:
        linea.append({"pid": pid, "inicio": ini, "fin": fin})


def _metricas(procesos, linea):
    fin, primera = {}, {}
    for seg in linea:
        if seg["pid"] is None:
            continue
        primera.setdefault(seg["pid"], seg["inicio"])
        fin[seg["pid"]] = seg["fin"]
    filas = []
    for p in procesos:
        ct = fin[p["pid"]]
        tat = ct - p["llegada"]
        filas.append({
            **p,
            "finalizacion": ct,
            "retorno": tat,
            "espera": tat - p["rafaga"],
            "respuesta": primera[p["pid"]] - p["llegada"],
        })
    n = len(filas)
    prom = lambda k: round(sum(f[k] for f in filas) / n, 2)
    return {
        "procesos": filas,
        "prom_espera": prom("espera"),
        "prom_retorno": prom("retorno"),
        "prom_respuesta": prom("respuesta"),
    }


def _no_expulsivo(procesos, clave):
    """Planificador sin expulsión: elige entre los listos usando `clave`."""
    pend = sorted(procesos, key=lambda p: p["llegada"])
    t, linea = 0, []
    while pend:
        listos = [p for p in pend if p["llegada"] <= t]
        if not listos:
            sig = min(p["llegada"] for p in pend)
            _agregar(linea, None, t, sig)
            t = sig
            continue
        p = min(listos, key=lambda x: (clave(x), x["llegada"]))
        _agregar(linea, p["pid"], t, t + p["rafaga"])
        t += p["rafaga"]
        pend.remove(p)
    return linea


def _expulsivo(procesos, clave):
    """Versión con expulsión (SRTF / prioridad expulsiva), unidad por unidad."""
    resta = {p["pid"]: p["rafaga"] for p in procesos}
    t, linea = 0, []
    while any(resta.values()):
        listos = [p for p in procesos if p["llegada"] <= t and resta[p["pid"]] > 0]
        if not listos:
            sig = min(p["llegada"] for p in procesos if resta[p["pid"]] > 0)
            _agregar(linea, None, t, sig)
            t = sig
            continue
        p = min(listos, key=lambda x: (clave(x, resta), x["llegada"]))
        _agregar(linea, p["pid"], t, t + 1)
        resta[p["pid"]] -= 1
        t += 1
    return linea


def fcfs(procesos):
    return _no_expulsivo(procesos, lambda p: p["llegada"])


def sjf(procesos, expulsivo=False):
    if expulsivo:
        return _expulsivo(procesos, lambda p, r: r[p["pid"]])
    return _no_expulsivo(procesos, lambda p: p["rafaga"])


def prioridad(procesos, expulsivo=False):
    if expulsivo:
        return _expulsivo(procesos, lambda p, r: p["prioridad"])
    return _no_expulsivo(procesos, lambda p: p["prioridad"])


def round_robin(procesos, quantum):
    resta = {p["pid"]: p["rafaga"] for p in procesos}
    pend = sorted(procesos, key=lambda p: p["llegada"])
    cola, linea, t, i = [], [], 0, 0

    def admitir(hasta):
        nonlocal i
        while i < len(pend) and pend[i]["llegada"] <= hasta:
            cola.append(pend[i])
            i += 1

    admitir(t)
    while cola or i < len(pend):
        if not cola:
            sig = pend[i]["llegada"]
            _agregar(linea, None, t, sig)
            t = sig
            admitir(t)
            continue
        p = cola.pop(0)
        uso = min(quantum, resta[p["pid"]])
        _agregar(linea, p["pid"], t, t + uso)
        t += uso
        resta[p["pid"]] -= uso
        admitir(t)       
        if resta[p["pid"]] > 0:
            cola.append(p)   
    return linea


def simular(algoritmo, procesos, quantum=2, expulsivo=False):
    if algoritmo == "fcfs":
        linea = fcfs(procesos)
    elif algoritmo == "sjf":
        linea = sjf(procesos)
    elif algoritmo == "prioridad":
        linea = prioridad(procesos, expulsivo=True)
    elif algoritmo == "rr":
        linea = round_robin(procesos, quantum)
    else:
        raise ValueError("Algoritmo desconocido")
    return linea, _metricas(procesos, linea)