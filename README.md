# EmiSat Analytics 🛰️

EmiSat Analytics es una aplicación web interactiva construida con Streamlit que permite monitorear emisiones industriales mediante imágenes satelitales (Sentinel-5P vía Google Earth Engine). El sistema evalúa gases como Metano (CH4), Dióxido de Nitrógeno (NO2) y Dióxido de Azufre (SO2), calculando la exposición financiera de las empresas bajo las normativas del Mecanismo de Ajuste en Frontera por Carbono (CBAM) de la Unión Europea.

La aplicación cuenta con un sistema de autenticación de usuarios, una base de datos local SQLite para el guardado de la geometría de las plantas industriales y paneles de control gráficos interactivos (dashboards) para la comparativa de emisiones.

## 🚀 Características Principales

* **Monitor en Vivo y Mapeo:** Dibujo de polígonos sobre zonas industriales para el cálculo de emisiones en tiempo real usando imágenes satelitales.
* **Cálculo de Riesgo Financiero (CBAM):** Proyección del costo de certificados y posibles multas por discrepancias entre lo declarado por la empresa y lo detectado satelitalmente.
* **Gestión de Plantas:** Posibilidad de guardar y cargar instalaciones como "presets" en la base de datos.
* **Reporte Consolidado Global:** Vista general para analizar múltiples plantas de forma simultánea.

---

## 📋 Requisitos Previos

1.  **Python 3.8+** instalado en el sistema.
2.  Una **cuenta de Google Earth Engine (GEE)** activa.

---

## ⚙️ Instalación y Configuración

1.  **Clonar el repositorio:**
    Abre tu terminal y ejecuta el siguiente comando para descargar el proyecto:
    ```bash
    git clone [https://github.com/benjaamonti/EmiSat.git](https://github.com/benjaamonti/EmiSat.git)
    cd EmiSat
    ```

2.  **Crear un entorno virtual (Recomendado):**
    ```bash
    python -m venv venv
    
    # En Windows:
    venv\Scripts\activate
    
    # En macOS/Linux:
    source venv/bin/activate
    ```

3.  **Instalar las dependencias:**
    Ejecuta el siguiente comando para instalar las librerías necesarias:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Autenticación en Google Earth Engine:**
    Para que la API satelital funcione, debes autenticar tu cuenta de GEE. Abre una terminal y ejecuta:
    ```bash
    earthengine authenticate
    ```
    *(Nota: Si encuentras problemas de autenticación, puedes descomentar la línea `# ee.Authenticate()` en el archivo `app.py` durante la primera ejecución).*

---

## ▶️ Ejecución del Programa

Para iniciar la aplicación, ejecuta el siguiente comando en la terminal:

```bash
streamlit run app.py

---

## 🔐 Credenciales de Acceso

Al iniciar la aplicación por primera vez, la base de datos se inicializa automáticamente con usuarios de prueba. Puedes utilizar las siguientes credenciales según el rol que necesites probar:

| Usuario | Contraseña | Rol / Permisos |
| :--- | :--- | :--- |
| `admin` | `emisat2026` | **Administrador:** Acceso completo a todas las funciones y edición de parámetros avanzados de CBAM. |
| `usuario` | `usuario123` | **Usuario Regular:** Acceso al monitor en vivo, mapeo de polígonos y visualización de reportes consolidados. |
