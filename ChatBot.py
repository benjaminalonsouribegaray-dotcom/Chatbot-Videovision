#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from fastapi import FastAPI
import pandas as pd
import re
from rapidfuzz import fuzz
import os

app = FastAPI()

# Cargar Excel (ruta relativa)
excel_path = os.path.join(os.path.dirname(__file__), "resultado_final.xlsx")
df = pd.read_excel(excel_path)
    
# Limpiar nombres de columnas
df.columns = df.columns.str.strip()

# Normalizar códigos (quitar ceros a la izquierda)
df["Codigo del Articulo"] = df["Codigo del Articulo"].astype(str).str.strip().str.lstrip("0")

# Reemplazar vacíos
df = df.fillna("")
df["Suma Bodegas"] = pd.to_numeric(df["Suma Bodegas"], errors="coerce").fillna(0).astype(int)


# 🔹 Función auxiliar para fuzzy search
def fuzzy_filter(df, columna, texto, umbral=70):
    coincidencias = []
    for _, row in df.iterrows():
        valor = str(row[columna])
        if fuzz.partial_ratio(texto.lower(), valor.lower()) >= umbral:
            coincidencias.append(row)
    return pd.DataFrame(coincidencias)


# 🔹 Menú inicial
@app.get("/menu")
def menu():
    return {
        "mensaje": "Bienvenido al sistema. ¿Quién eres?",
        "opciones": {
            "1": "Cliente",
            "2": "Vendedor"
        }
    }


# 🔹 Opciones de Cliente
@app.get("/menu/cliente/opcion/{opcion}")
def menu_cliente_opcion(opcion: int):
    opciones = {
        1: {"accion": "Consultar stock por código", "instruccion": "Usa /stock/?codigo=XXXX&rol=cliente"},
        2: {"accion": "Consultar stock por descripción", "instruccion": "Usa /stock/?descripcion=XXXX&rol=cliente"},
        3: {"accion": "Buscar productos por palabra clave en descripción", "instruccion": "Usa /buscar/descripcion/?texto=PALABRA&rol=cliente"},
        4: {"accion": "Buscar productos por categoría", "instruccion": "Usa /buscar/categoria/?nombre=PALABRA&rol=cliente"},
        5: {"accion": "Buscar productos por marca", "instruccion": "Usa /buscar/marca/?nombre=MARCA&rol=cliente"},
        6: {"accion": "Buscar productos por necesidad", "instruccion": "Usa /buscar/necesidad/?texto=FRASE&rol=cliente"}
    }
    return opciones.get(opcion, {"error": "Opción no válida", "volver": "/menu"})


# 🔹 Opciones de Vendedor
@app.get("/menu/vendedor/opcion/{opcion}")
def menu_vendedor_opcion(opcion: int):
    opciones = {
        1: {"accion": "Consultar stock por código", "instruccion": "Usa /stock/?codigo=XXXX&rol=vendedor"},
        2: {"accion": "Consultar stock por descripción", "instruccion": "Usa /stock/?descripcion=XXXX&rol=vendedor"},
        3: {"accion": "Buscar productos por palabra clave en descripción", "instruccion": "Usa /buscar/descripcion/?texto=PALABRA&rol=vendedor"},
        4: {"accion": "Buscar productos por categoría", "instruccion": "Usa /buscar/categoria/?nombre=PALABRA&rol=vendedor"},
        5: {"accion": "Buscar productos por marca", "instruccion": "Usa /buscar/marca/?nombre=MARCA&rol=vendedor"},
        6: {"accion": "Buscar productos por necesidad", "instruccion": "Usa /buscar/necesidad/?texto=FRASE&rol=vendedor"}
    }
    return opciones.get(opcion, {"error": "Opción no válida", "volver": "/menu"})


# 🔹 Consulta de stock
@app.get("/stock/")
def consultar_stock(codigo: str = None, descripcion: str = None, rol: str = "cliente"):
    if codigo:
        codigo = codigo.lstrip("0")
        fila = df[df["Codigo del Articulo"] == codigo]
    elif descripcion:
        fila = fuzzy_filter(df, "Descripcion", descripcion, umbral=70)
    else:
        return {"error": "Debes ingresar un código o una descripción"}

    if not fila.empty:
        resultados = []
        for _, row in fila.iterrows():
            stock_real = row["Suma Bodegas"]
            stock = "+10" if rol.lower() == "cliente" and stock_real > 10 else int(stock_real)
            resultados.append({
                "Codigo del Articulo": row["Codigo del Articulo"],
                "Descripcion": row["Descripcion"],
                "Fabricante": row["Fabricante"],
                "Categoria": row["Categoria"],
                "Stock": stock
            })
        return {"resultados": resultados}
    else:
        return {"error": "Artículo no encontrado"}


# 🔹 Buscar por categoría
@app.get("/buscar/categoria/")
def buscar_por_categoria(nombre: str, rol: str = "cliente"):
    resultados = fuzzy_filter(df, "Categoria", nombre, umbral=70)
    if resultados.empty:
        return {"error": f"No se encontraron productos en la categoría '{nombre}'", "volver": "/menu"}

    productos = []
    for _, row in resultados.iterrows():
        stock_real = row["Suma Bodegas"]
        stock = "+10" if rol.lower() == "cliente" and stock_real > 10 else int(stock_real)
        productos.append({
            "Codigo del Articulo": row["Codigo del Articulo"],
            "Descripcion": row["Descripcion"],
            "Fabricante": row["Fabricante"],
            "Categoria": row["Categoria"],
            "Stock": stock
        })
    return {"productos": productos, "volver": "/menu"}


# 🔹 Buscar por marca
@app.get("/buscar/marca/")
def buscar_por_marca(nombre: str, rol: str = "cliente"):
    resultados = fuzzy_filter(df, "Fabricante", nombre, umbral=70)
    if resultados.empty:
        return {"error": f"No se encontraron productos de la marca '{nombre}'", "volver": "/menu"}

    productos = []
    for _, row in resultados.iterrows():
        stock_real = row["Suma Bodegas"]
        stock = "+10" if rol.lower() == "cliente" and stock_real > 10 else int(stock_real)
        productos.append({
            "Codigo del Articulo": row["Codigo del Articulo"],
            "Descripcion": row["Descripcion"],
            "Fabricante": row["Fabricante"],
            "Categoria": row["Categoria"],
            "Stock": stock
        })
    return {"productos": productos, "volver": "/menu"}


# 🔹 Buscar por descripción
@app.get("/buscar/descripcion/")
def buscar_por_descripcion(texto: str, rol: str = "cliente"):
    resultados = fuzzy_filter(df, "Descripcion", texto, umbral=70)
    if resultados.empty:
        return {"error": f"No se encontraron productos que coincidan con '{texto}'", "volver": "/menu"}

    productos = []
    for _, row in resultados.iterrows():
        stock_real = row["Suma Bodegas"]
        stock = "+10" if rol.lower() == "cliente" and stock_real > 10 else int(stock_real)
        productos.append({
            "Codigo del Articulo": row["Codigo del Articulo"],
            "Descripcion": row["Descripcion"],
            "Fabricante": row["Fabricante"],
            "Categoria": row["Categoria"],
            "Stock": stock
        })
    return {"productos": productos, "volver": "/menu"}


# 🔹 Buscar por necesidad (palabras + números con lógica ≥ + fuzzy)
@app.get("/buscar/necesidad/")
def buscar_por_necesidad(texto: str, rol: str = "cliente"):
    texto = texto.lower()
    palabras = [p for p in texto.split() if not re.search(r"\d", p)]
    numeros = re.findall(r"(\d+)\s*([a-zA-Z]*)", texto)

    resultados = df.copy()

    # Filtrar por palabras clave con fuzzy
    for palabra in palabras:
        resultados = fuzzy_filter(resultados, "Descripcion", palabra, umbral=70)

    # Filtrar por números (≥ solicitado)
    if numeros:
        filtrados = []
        for _, row in resultados.iterrows():
            desc_text = row["Descripcion"].lower()
            desc_numeros = re.findall(r"(\d+)\s*([a-zA-Z]*)", desc_text)

            for num, unidad in numeros:
                num = int(num)
                for d, u in desc_numeros:
                    d = int(d)
                    if (not unidad or unidad.lower() == u.lower()) and d >= num:
                        filtrados.append(row)
                        break
        resultados = pd.DataFrame(filtrados)

    if resultados.empty:
        return {"error": "No se encontraron productos que coincidan con la necesidad", "volver": "/menu"}

    productos = []
    for _, row in resultados.iterrows():
        stock_real = row["Suma Bodegas"]
        stock = "+10" if rol.lower() == "cliente" and stock_real > 10 else int(stock_real)
        productos.append({
            "Codigo del Articulo": row["Codigo del Articulo"],
            "Descripcion": row["Descripcion"],
            "Fabricante": row["Fabricante"],
            "Categoria": row["Categoria"],
            "Stock": stock
        })
    return {"productos": productos, "volver": "/menu"}
           

