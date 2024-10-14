from flask import Flask, render_template, request, jsonify
import mysql.connector
from multiprocessing import Pool
import random

app = Flask(__name__)

# Conectar a la base de datos
def conectar_bd():
    return mysql.connector.connect(
        host='localhost',
        user='root',  
        password='',  
        database='suma_paralela'
    )

# Función para obtener números de la base de datos
def obtener_numeros():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM numeros")
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return [valor[0] for valor in resultados]

# Función para sumar parcialmente
def suma_parcial(numeros):
    return sum(numeros)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Obtener el número del formulario
        numero = request.form.get('numero')
        
        if numero:  # Si hay un número, se agrega a la base de datos
            # Conectar a la base de datos y agregar el número
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO numeros (valor) VALUES (%s)", (numero,))
            conn.commit()
            cursor.close()
            conn.close()

        # Obtener los números actualizados y calcular la suma
        numeros = obtener_numeros()

        # Dividir los números en partes para la suma paralela
        num_partes = 4  # Número de partes para dividir
        partes = [numeros[i::num_partes] for i in range(num_partes)]
        
        # Crear un pool de procesos para realizar la suma en paralelo
        with Pool(processes=num_partes) as pool:
            resultados = pool.map(suma_parcial, partes)

        # Sumar los resultados parciales
        suma_total = sum(resultados)

        # Crear la respuesta JSON
        numeros_html = generar_tabla_html(numeros)
        return jsonify(numeros_html=numeros_html, suma_total=suma_total)

    # Al cargar la página, se muestra una tabla vacía
    numeros_html = generar_tabla_html([])  # Tabla vacía
    suma_total = 0

    return render_template('index.html', numeros_html=numeros_html, suma_total=suma_total)

@app.route('/generar/<int:cantidad>', methods=['POST'])
def generar_datos(cantidad):
    conn = conectar_bd()
    cursor = conn.cursor()
    
    # Generar números desde 1 hasta 'cantidad' y agregarlos a la base de datos
    for numero in range(1, cantidad + 1):
        cursor.execute("INSERT INTO numeros (valor) VALUES (%s)", (numero,))
    
    conn.commit()
    cursor.close()
    conn.close()

    # Obtener los números actualizados y calcular la suma
    numeros = obtener_numeros()

    # Dividir los números en partes para la suma paralela
    num_partes = 4  # Número de partes para dividir
    partes = [numeros[i::num_partes] for i in range(num_partes)]
    
    # Crear un pool de procesos para realizar la suma en paralelo
    with Pool(processes=num_partes) as pool:
        resultados = pool.map(suma_parcial, partes)

    # Sumar los resultados parciales
    suma_total = sum(resultados)

    # Crear la respuesta JSON
    numeros_html = generar_tabla_html(numeros)
    return jsonify(numeros_html=numeros_html, suma_total=suma_total)

@app.route('/borrar', methods=['POST'])
def borrar_datos():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM numeros")  # Borrar todos los datos
    conn.commit()
    cursor.close()
    conn.close()

    # Retornar una respuesta JSON vacía
    return jsonify(numeros_html="", suma_total=0)

def generar_tabla_html(numeros):
    n = int(len(numeros) ** 0.5) + 1  # Calcular el tamaño de la tabla
    numeros_html = "<table><thead><tr>"
    # Generar cabeceras (opcional, puede ser solo un índice)
    for i in range(n):
        numeros_html += f"<th>{i + 1}</th>"
    numeros_html += "</tr></thead><tbody>"

    for i in range(n):
        numeros_html += "<tr>"
        for j in range(n):
            index = i * n + j
            if index < len(numeros):
                numeros_html += f"<td>{numeros[index]}</td>"
            else:
                numeros_html += "<td></td>"  # Espacio vacío
        numeros_html += "</tr>"
    
    numeros_html += "</tbody></table>"
    return numeros_html

if __name__ == '__main__':
    app.run(debug=True)
