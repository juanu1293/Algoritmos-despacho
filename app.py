from flask import Flask, jsonify, render_template, request

from algoritmos import simular

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/simular")
def api_simular():
    datos = request.get_json(silent=True) or {}
    try:
        procesos = [
            {
                "pid": str(p["pid"]).strip(),
                "llegada": int(p["llegada"]),
                "rafaga": int(p["rafaga"]),
                "prioridad": int(p.get("prioridad", 0)),
            }
            for p in datos.get("procesos", [])
        ]
        quantum = int(datos.get("quantum", 2))
    except (KeyError, ValueError, TypeError):
        return jsonify(error="Revisa que todos los campos sean números enteros."), 400

    if not procesos:
        return jsonify(error="Agrega al menos un proceso."), 400
    if len({p["pid"] for p in procesos}) != len(procesos) or "" in {p["pid"] for p in procesos}:
        return jsonify(error="Cada proceso necesita un nombre único."), 400
    if any(p["rafaga"] < 1 or p["llegada"] < 0 for p in procesos):
        return jsonify(error="La ráfaga debe ser ≥ 1 y la llegada ≥ 0."), 400
    if quantum < 1:
        return jsonify(error="El quantum debe ser ≥ 1."), 400

    try:
        linea, metricas = simular(
            datos.get("algoritmo", "fcfs"), procesos, quantum, bool(datos.get("expulsivo"))
        )
    except ValueError as e:
        return jsonify(error=str(e)), 400
    return jsonify(linea=linea, metricas=metricas)


if __name__ == "__main__":
    app.run(debug=True)
