import sqlite3
import json

DB_NAME = "emisat.db"

def obtener_conexion():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Permite acceder a las columnas por nombre
    return conn

def inicializar_backend():
    """Crea las tablas si no existen e inserta datos iniciales de prueba."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    # 1. Crear tabla de usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        clave TEXT NOT NULL,
        rol TEXT NOT NULL
    )
    """)
    
    # 2. Crear tabla de plantas con geometría (almacenada como JSON texto)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plantas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        emision_declarada REAL NOT NULL,
        produccion_tons REAL NOT NULL,
        geometria TEXT NOT NULL  -- Aquí guardamos las coordenadas del polígono
    )
    """)
    
    # Insertar usuarios semilla si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios (usuario, clave, rol) VALUES (?, ?, ?)", ("admin", "emisat2026", "admin"))
        cursor.execute("INSERT INTO usuarios (usuario, clave, rol) VALUES (?, ?, ?)", ("usuario", "usuario123", "usuario"))
    
    # Insertar plantas preset si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM plantas")
    if cursor.fetchone()[0] == 0:
        # Polígono de ejemplo cercano a las coordenadas por defecto de tu mapa (Zona Houston/Baytown)
        coordenadas_ejemplo = [
            [-95.025, 29.725],
            [-94.995, 29.725],
            [-94.995, 29.745],
            [-95.025, 29.745],
            [-95.025, 29.725]
        ]
        # Estructura requerida por ee.Geometry.Polygon: lista de anillos de coordenadas
        geometria_json = json.dumps([coordenadas_ejemplo])
        
        cursor.execute("""
        INSERT INTO plantas (nombre, emision_declarada, produccion_tons, geometria)
        VALUES (?, ?, ?, ?)
        """, ("Complejo Industrial Completo (Preset)", 55000.0, 110000.0, geometria_json))
        
    conn.commit()
    conn.close()

def validar_usuario(usuario, clave):
    """Verifica credenciales y retorna el rol si es válido, o None."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT rol FROM usuarios WHERE usuario = ? AND clave = ?", (usuario, clave))
    res = cursor.fetchone()
    conn.close()
    return res["rol"] if res else None

def listar_plantas():
    """Retorna todas las plantas registradas."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, emision_declarada, produccion_tons, geometria FROM plantas")
    plantas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return plantas

def registrar_planta(nombre, emision, produccion, lista_coordenadas):
    """Guarda una nueva planta dibujada desde la interfaz."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    geometria_json = json.dumps(lista_coordenadas)
    cursor.execute("""
    INSERT INTO plantas (nombre, emision_declarada, produccion_tons, geometria)
    VALUES (?, ?, ?, ?)
    """, (nombre, emision, produccion, geometria_json))
    conn.commit()
    conn.close()