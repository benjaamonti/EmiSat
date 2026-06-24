import streamlit as st
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
import ee
import math
import datetime
import plotly.graph_objects as go
import json
from database import inicializar_backend, validar_usuario, listar_plantas, registrar_planta

# ─────────────────────────────────────────
# INICIALIZACIÓN
# ─────────────────────────────────────────
# Inicializar la base de datos SQLite antes de arrancar la app
inicializar_backend()

if 'ee_initialized' not in st.session_state:
    try:
        ee.Authenticate()
        ee.Initialize(project='emisat')
        st.session_state['ee_initialized'] = True
    except Exception as e:
        st.error(f"Error de conexión con Google Earth Engine: {e}")
        st.stop()

st.set_page_config(page_title="EmiSat Analytics", layout="wide", page_icon="🛰️")

# Inicializar variable de sesión para el login
if 'logeado' not in st.session_state:
    st.session_state['logeado'] = False
    st.session_state['rol'] = None

# ─────────────────────────────────────────
# PANTALLA DE LOGIN
# ─────────────────────────────────────────
if not st.session_state['logeado']:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        logo_col1, logo_col2, logo_col3 = st.columns([1, 1.5, 1])
        with logo_col2:
            st.image("Emisat_logo.png", use_container_width=True)

        st.markdown("<h1 style='text-align: center;'> Iniciar Sesión</h1>", unsafe_allow_html=True)

        usuario = st.text_input("Usuario")
        clave = st.text_input("Contraseña", type="password")

        st.write("")
        if st.button("Entrar", use_container_width=True):
            rol_detectado = validar_usuario(usuario, clave)
            if rol_detectado:
                st.session_state['logeado'] = True
                st.session_state['rol'] = rol_detectado
                st.rerun()
            else:
                st.error("Credenciales incorrectas. Verifique usuario o contraseña.")

# ─────────────────────────────────────────
# APLICACIÓN PRINCIPAL
# ─────────────────────────────────────────
else:
    # ─────────────────────────────────────────
    # PALETA EMISAT + ESTILOS DASHBOARD
    # ─────────────────────────────────────────
    COLOR_BG = "#EEF2EF"
    COLOR_CARD = "#FFFFFF"
    COLOR_PRIMARY = "#4F9D8F"
    COLOR_PRIMARY_DK = "#2F6B5E"
    COLOR_PRIMARY_LT = "#CFE3DC"
    COLOR_TEXT = "#1F2A28"
    COLOR_SUBTEXT = "#6B7B77"
    COLOR_WARN = "#E0A23B"
    COLOR_DANGER = "#D6604D"
    COLOR_OK = "#4F9D8F"

    DASHBOARD_CSS = f"""
    <style>
    .dash-section {{ margin-top: 4px; margin-bottom: 6px; }}
    .dash-section-title {{ font-size: 15px; font-weight: 700; color: {COLOR_TEXT}; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }}
    .dash-card {{ background: {COLOR_CARD}; border-radius: 14px; padding: 18px 20px; box-shadow: 0 2px 10px rgba(31, 42, 40, 0.06); border: 1px solid rgba(0,0,0,0.04); height: 100%; transition: transform 0.15s ease, box-shadow 0.15s ease; }}
    .dash-card:hover {{ transform: translateY(-2px); box-shadow: 0 6px 18px rgba(31, 42, 40, 0.10); }}
    .kpi-label {{ font-size: 12.5px; font-weight: 600; color: {COLOR_SUBTEXT}; text-transform: uppercase; letter-spacing: 0.03em; margin-bottom: 6px; }}
    .kpi-value {{ font-size: 26px; font-weight: 800; color: {COLOR_TEXT}; line-height: 1.15; }}
    .kpi-sub {{ font-size: 12px; color: {COLOR_SUBTEXT}; margin-top: 4px; }}
    .kpi-icon {{ font-size: 20px; margin-bottom: 6px; display: inline-block; }}
    .pill {{ display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 11.5px; font-weight: 700; margin-top: 8px; }}
    .pill-ok {{ background: rgba(79,157,143,0.15); color: {COLOR_PRIMARY_DK}; }}
    .pill-warn {{ background: rgba(224,162,59,0.15); color: #8a611f; }}
    .pill-danger {{ background: rgba(214,96,77,0.15); color: #93291c; }}
    .alert-card {{ background: linear-gradient(135deg, #FFF7F0 0%, #FDEFE9 100%); border-radius: 14px; padding: 18px 22px; border: 1px solid rgba(214,96,77,0.25); box-shadow: 0 2px 10px rgba(214,96,77,0.08); height: 100%; display: flex; flex-direction: column; justify-content: center; }}
    .alert-card.ok {{ background: linear-gradient(135deg, #F1FBF8 0%, #E8F6F1 100%); border: 1px solid rgba(79,157,143,0.25); box-shadow: 0 2px 10px rgba(79,157,143,0.08); }}
    .alert-icon {{ font-size: 30px; text-align: center; margin-bottom: 4px; }}
    .alert-title {{ text-align: center; font-size: 13px; font-weight: 700; color: {COLOR_SUBTEXT}; text-transform: uppercase; letter-spacing: 0.03em; }}
    .alert-value {{ text-align: center; font-size: 28px; font-weight: 800; color: {COLOR_DANGER}; margin: 4px 0 2px 0; }}
    .alert-value.ok-text {{ color: {COLOR_PRIMARY_DK}; }}
    .alert-caption {{ text-align: center; font-size: 12px; color: {COLOR_SUBTEXT}; }}
    </style>
    """

    # ─────────────────────────────────────────
    # CONSTANTES OFICIALES
    # ─────────────────────────────────────────
    GWP_CH4 = 28
    PRECIO_ETS = 75.36
    MULTA_POR_TON = 100.0
    FACTOR_FASE = 0.025
    CH4_FONDO_GLOBAL = 1930.0
    M_CH4 = 0.01604
    M_AIRE = 0.02896
    G = 9.80665

    # ─────────────────────────────────────────
    # SIDEBAR
    # ─────────────────────────────────────────
    side_col1, side_col2, side_col3 = st.sidebar.columns([1, 2, 1])
    with side_col2:
        st.image("Emisat_logo.png", use_container_width=True)

    st.sidebar.markdown("<br>", unsafe_allow_html=True)

    st.sidebar.markdown("""
    <style>
    div[data-testid="stSidebar"] .stButton > button { background-color: #D6604D; color: white; border: 1px solid #C45341; transition: all 0.2s ease-in-out; }
    div[data-testid="stSidebar"] .stButton > button:hover { background-color: #B24634; border-color: #B24634; color: white; transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state['logeado'] = False
        st.session_state['rol'] = None
        st.rerun()

    st.sidebar.title("⚙️ Configuración")

    if st.session_state.get('rol') == "admin":
        with st.sidebar.expander(" Parámetros Avanzados CBAM", expanded=False):
            GWP_CH4 = st.number_input("GWP CH4 (IPCC AR6)", value=28.0, step=1.0)
            PRECIO_ETS = st.number_input("Precio ETS (€/tCO₂e)", value=75.36, step=1.0)
            MULTA_POR_TON = st.number_input("Multa CBAM (€/t mal declarada)", value=100.0, step=10.0)
            FACTOR_FASE = st.number_input("Factor de fase CBAM (0 a 1)", value=0.025, step=0.005, format="%.3f")
        st.sidebar.divider()

    hoy = datetime.date.today()
    un_mes_atras = hoy - datetime.timedelta(days=30)

    with st.sidebar.expander("Período de análisis", expanded=True):
        f_inicio = st.date_input("Fecha inicio", un_mes_atras)
        f_fin = st.date_input("Fecha fin", hoy)
        if f_inicio >= f_fin:
            st.error("La fecha de inicio debe ser anterior a la de fin.")
            st.stop()

    st.sidebar.divider()

    # 1. PLANTA SELECCIONADA PRIMERO
    with st.sidebar.expander("Mis plantas", expanded=True):
        plantas_db = listar_plantas()
        nombres_plantas = [p["nombre"] for p in plantas_db]

        seleccion = st.selectbox("Seleccionar preset:", ["-- Dibujo Libre --"] + nombres_plantas)

        planta_seleccionada = None
        if seleccion != "-- Dibujo Libre --":
            planta_seleccionada = next(p for p in plantas_db if p["nombre"] == seleccion)
            st.success(f"Geometría cargada: {planta_seleccionada['nombre']}")

    st.sidebar.divider()

    # 2. DATOS QUE SE RELLENAN DINÁMICAMENTE (Y PERMITEN EDICIÓN)
    with st.sidebar.expander("Datos declarados por empresa", expanded=True):
        defecto_emision = float(planta_seleccionada["emision_declarada"]) if planta_seleccionada else 50000.0
        defecto_produccion = float(planta_seleccionada["produccion_tons"]) if planta_seleccionada else 100000.0

        emision_declarada = st.number_input(
            "Emisión declarada (tCO₂e/año)",
            min_value=0.0,
            value=defecto_emision,
            step=1000.0,
            help="Modificá este valor para simular nuevos escenarios."
        )
        produccion_tons = st.number_input(
            "Producción exportada a EU (ton/año)",
            min_value=0.0,
            value=defecto_produccion,
            step=1000.0
        )

    st.sidebar.divider()
    st.sidebar.info(" Dibujá un polígono sobre una planta industrial para analizar sus emisiones.")


    # ─────────────────────────────────────────
    # FUNCIONES GEE
    # ─────────────────────────────────────────
    @st.cache_data(ttl=3600)
    def obtener_capas(fecha_i, fecha_f):
        fi, ff = str(fecha_i), str(fecha_f)
        ch4_img = (ee.ImageCollection('COPERNICUS/S5P/OFFL/L3_CH4').select(
            'CH4_column_volume_mixing_ratio_dry_air').filterDate(fi, ff).mean())
        ch4_url = ch4_img.getMapId({'min': 1800, 'max': 1950,
                                    'palette': ['#313695', '#4575b4', '#74add1', '#ffffbf', '#fdae61', '#d73027',
                                                '#a50026']})['tile_fetcher'].url_format

        no2_img = (ee.ImageCollection('COPERNICUS/S5P/NRTI/L3_NO2').select(
            'tropospheric_NO2_column_number_density').filterDate(fi, ff).mean())
        no2_url = no2_img.getMapId(
            {'min': 0, 'max': 0.0002, 'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red']})[
            'tile_fetcher'].url_format

        so2_img = (ee.ImageCollection('COPERNICUS/S5P/NRTI/L3_SO2').select('SO2_column_number_density').filterDate(fi,
                                                                                                                   ff).mean())
        so2_url = \
        so2_img.getMapId({'min': 0, 'max': 0.001, 'palette': ['white', 'yellow', 'orange', 'red', 'darkred']})[
            'tile_fetcher'].url_format

        return ch4_url, no2_url, so2_url


    def calcular_variables_atmosfericas(img):
        u = img.select("u_component_of_wind_10m")
        v = img.select("v_component_of_wind_10m")
        p = img.select("surface_pressure")
        velocidad = (u.pow(2).add(v.pow(2))).sqrt().rename("wind_speed")
        return img.addBands([velocidad, p])


    # ─────────────────────────────────────────
    # TÍTULO Y PESTAÑAS
    # ─────────────────────────────────────────
    st.markdown(f"""
            <div style="text-align: center; margin-bottom: 20px; padding-top: 10px;">
                <h1 style="margin: 0; font-size: 48px; font-weight: 800; letter-spacing: 0.02em;">
                     <span style="color: #162C4F;">Emi</span><span style="color: #2D7C98;">Sat</span> <span style="color: {COLOR_TEXT};">Analytics</span>
                </h1>
                <p style="color: {COLOR_SUBTEXT}; margin: 10px 0 0 0; font-size: 18px; font-weight: 500;">
                    Monitor satelital de emisiones industriales — <b>{f_inicio}</b> al <b>{f_fin}</b>
                </p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown(
            """
            <style>
            [data-testid="stMetricValue"] > div { white-space: pre-wrap !important; font-size: 1.3rem !important; line-height: 1.2 !important; }
            </style>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    st.markdown(
        """
        <style>
        [data-testid="stMetricValue"] > div { white-space: pre-wrap !important; font-size: 1.3rem !important; line-height: 1.2 !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

    col_info1, col_info2, col_info3, col_info4 = st.columns(4)
    col_info1.metric("Fuentes Utilizadas", "Sentinel-5P (ESA),\nERA5 (ECMWF)")
    col_info2.metric("Cobertura", "Global diaria")
    col_info3.metric("Precio ETS Q1 2026", f"€{PRECIO_ETS}/tCO₂e")
    col_info4.metric("Factor de fase CBAM", f"{FACTOR_FASE * 100}%")

    st.divider()

    tab_mapa, tab_reportes = st.tabs(["Monitor en Vivo y Mapeo", "Gestión y Cálculos por Planta"])

    # =====================================================================================
    # PESTAÑA 1: MAPA
    # =====================================================================================
    with tab_mapa:
        with st.spinner(" Sincronizando con satélites Sentinel-5P..."):
            ch4_url, no2_url, so2_url = obtener_capas(f_inicio, f_fin)

        mapa_centro = [29.734, -95.006]
        mapa_zoom = 6
        mapa_key = "mapa_emisat_v4"
        poligono_geojson = None

        if planta_seleccionada is not None:
            try:
                coords_guardadas = json.loads(planta_seleccionada["geometria"])
                mapa_centro = [coords_guardadas[0][0][1], coords_guardadas[0][0][0]]
                mapa_zoom = 15
                mapa_key = f"mapa_{planta_seleccionada['nombre']}"

                poligono_geojson = {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": coords_guardadas}
                }
            except Exception as e:
                st.warning(f"⚠️ Error al leer la geometría: {e}")

        m = folium.Map(location=mapa_centro, zoom_start=mapa_zoom, tiles="CartoDB positron")

        folium.TileLayer(tiles=ch4_url, attr='Copernicus', name='🟠 CH4', overlay=True, show=True, opacity=0.6).add_to(m)
        folium.TileLayer(tiles=no2_url, attr='Copernicus', name='🔴 NO2', overlay=True, show=False, opacity=0.6).add_to(
            m)
        folium.TileLayer(tiles=so2_url, attr='Copernicus', name='🟡 SO2', overlay=True, show=False, opacity=0.6).add_to(
            m)
        folium.LayerControl(position='topright').add_to(m)

        Draw(draw_options={'polyline': False, 'rectangle': True, 'circle': False, 'polygon': True,
                           'marker': False}).add_to(m)

        if poligono_geojson:
            folium.GeoJson(
                poligono_geojson,
                name=planta_seleccionada["nombre"],
                style_function=lambda x: {'color': '#D6604D', 'fillColor': '#D6604D', 'weight': 2, 'fillOpacity': 0.4}
            ).add_to(m)

        datos_mapa = st_folium(m,width=1200,height=520,key=f"mapa_emisatv4{f_inicio}{f_fin}")

        tiene_preset = planta_seleccionada is not None
        tiene_dibujo = datos_mapa["last_active_drawing"] is not None

        if tiene_dibujo or tiene_preset:
            st.divider()
            st.subheader(" Análisis de zona seleccionada")

            with st.spinner(" Calculando emisiones reales desde el satélite..."):
                try:
                    if tiene_preset:
                        coords = json.loads(planta_seleccionada["geometria"])
                    else:
                        coords = datos_mapa["last_active_drawing"]["geometry"]["coordinates"]

                    poligono = ee.Geometry.Polygon(coords)
                    area_km2 = poligono.area().getInfo() / 1e6
                    fi, ff = str(f_inicio), str(f_fin)

                    val_ch4 = (ee.ImageCollection('COPERNICUS/S5P/OFFL/L3_CH4').select(
                        'CH4_column_volume_mixing_ratio_dry_air').filterDate(fi, ff).mean().reduceRegion(
                        ee.Reducer.mean(), poligono, 1113.2).get('CH4_column_volume_mixing_ratio_dry_air').getInfo())
                    val_no2 = (ee.ImageCollection('COPERNICUS/S5P/NRTI/L3_NO2').select(
                        'tropospheric_NO2_column_number_density').filterDate(fi, ff).mean().reduceRegion(
                        ee.Reducer.mean(), poligono, 1113.2).get('tropospheric_NO2_column_number_density').getInfo())
                    val_so2 = (
                        ee.ImageCollection('COPERNICUS/S5P/NRTI/L3_SO2').select('SO2_column_number_density').filterDate(
                            fi, ff).mean().reduceRegion(ee.Reducer.mean(), poligono, 1113.2).get(
                            'SO2_column_number_density').getInfo())

                    coleccion_era5 = (
                        ee.ImageCollection("ECMWF/ERA5/DAILY").filterDate(fi, ff).map(calcular_variables_atmosfericas))
                    stats = (
                        coleccion_era5.select(["wind_speed", "surface_pressure"]).mean().reduceRegion(ee.Reducer.mean(),
                                                                                                      poligono,
                                                                                                      27830).getInfo())

                    U = stats.get("wind_speed") if stats.get("wind_speed") is not None else 0.0
                    Ps = stats.get("surface_pressure") if stats.get("surface_pressure") is not None else 101325.0

                    L = math.sqrt(area_km2 * 1e6)
                    renovaciones_diarias = (86400 * U) / L if L > 0 and U > 0 else 6.0

                    exceso_ch4 = max(0, (val_ch4 or 0) - CH4_FONDO_GLOBAL)
                    factor_fisico_dinamico = (Ps / (G * M_AIRE)) * M_CH4 * 1e-9 * 1e3

                    masa_ch4_instant = exceso_ch4 * factor_fisico_dinamico * area_km2
                    ch4_anual_toneladas = masa_ch4_instant * renovaciones_diarias * 365
                    co2e_anual = ch4_anual_toneladas * GWP_CH4

                    if emision_declarada > 0:
                        indice = emision_declarada / co2e_anual if co2e_anual > 0 else 1.0
                    else:
                        indice = 1.0

                    diferencia_tco2e = max(0, co2e_anual - emision_declarada)

                    if indice >= 0.9:
                        estado_indice, pill_class, gauge_color = "Consistente", "pill-ok", COLOR_OK
                    elif indice >= 0.7:
                        estado_indice, pill_class, gauge_color = "Discrepancia leve", "pill-warn", COLOR_WARN
                    else:
                        estado_indice, pill_class, gauge_color = "Discrepancia grave", "pill-danger", COLOR_DANGER

                    costo_certificados_real = co2e_anual * FACTOR_FASE * PRECIO_ETS
                    costo_certificados_declarado = emision_declarada * FACTOR_FASE * PRECIO_ETS
                    multa_potencial = diferencia_tco2e * MULTA_POR_TON
                    exposicion_total = multa_potencial + (costo_certificados_real - costo_certificados_declarado)

                    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)

                    st.markdown(
                        '<div class="dash-section"><div class="dash-section-title"> Gases detectados por satélite</div></div>',
                        unsafe_allow_html=True)
                    g1, g2, g3, g4 = st.columns(4)
                    with g1:
                        val_txt = f"{val_ch4:.1f}" if val_ch4 else "—"
                        st.markdown(
                            f'<div class="dash-card"><div class="kpi-icon"></div><div class="kpi-label">CH4 — Metano</div><div class="kpi-value">{val_txt} <span style="font-size:14px;font-weight:600;">ppb</span></div><div class="kpi-sub">Indicador de fugas de gas</div></div>',
                            unsafe_allow_html=True)
                    with g2:
                        st.markdown(
                            f'<div class="dash-card"><div class="kpi-icon"></div><div class="kpi-label">CH4 exceso sobre fondo</div><div class="kpi-value">{exceso_ch4:.1f} <span style="font-size:14px;font-weight:600;">ppb</span></div><div class="kpi-sub">Exceso sobre 1930 ppb</div></div>',
                            unsafe_allow_html=True)
                    with g3:
                        val_txt = f"{val_no2:.6f}" if val_no2 else "—"
                        st.markdown(
                            f'<div class="dash-card"><div class="kpi-icon"></div><div class="kpi-label">NO2 — Act. industrial</div><div class="kpi-value" style="font-size:20px;">{val_txt} <span style="font-size:12px;font-weight:600;">mol/m²</span></div><div class="kpi-sub">Intensidad de combustión</div></div>',
                            unsafe_allow_html=True)
                    with g4:
                        val_txt = f"{val_so2:.6f}" if val_so2 else "—"
                        st.markdown(
                            f'<div class="dash-card"><div class="kpi-icon"></div><div class="kpi-label">SO2 — Refinación</div><div class="kpi-value" style="font-size:20px;">{val_txt} <span style="font-size:12px;font-weight:600;">mol/m²</span></div><div class="kpi-sub">Específico de refinerías</div></div>',
                            unsafe_allow_html=True)

                    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

                    st.markdown(
                        '<div class="dash-section"><div class="dash-section-title"> Conversión a CO₂e e índice de consistencia</div></div>',
                        unsafe_allow_html=True)
                    r2c1, r2c2, r2c3 = st.columns([1, 1, 1.3])
                    with r2c1:
                    # Usamos min-height para estirar la tarjeta y flexbox para centrar el contenido verticalmente
                        st.markdown(f"""
                        <div class="dash-card" style="min-height: 325px; display: flex; flex-direction: column; justify-content: center;">
                            <div>
                                <div class="kpi-icon"></div>
                                <div class="kpi-label">Área analizada</div>
                                <div class="kpi-value">{area_km2:.1f} <span style="font-size:14px;font-weight:600;">km²</span></div>
                            </div>
                            <div style="margin-top: 18px;">
                                <div class="kpi-sub">CO₂e satélite</div>
                                <div class="kpi-value" style="color:{COLOR_PRIMARY_DK};">{co2e_anual:,.0f} <span style="font-size:13px;">tCO₂e/año</span></div>
                            </div>
                            <div style="margin-top: 12px;">
                                <div class="kpi-sub">CO₂e declarado</div>
                                <div class="kpi-value" style="font-size:20px;color:{COLOR_SUBTEXT};">{emision_declarada:,.0f} <span style="font-size:13px;">tCO₂e/año</span></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with r2c2:
                        fig_gauge = go.Figure(go.Indicator(mode="gauge+number", value=min(indice, 1.5),
                                                           number={'suffix': "",
                                                                   'font': {'size': 34, 'color': COLOR_TEXT}},
                                                           domain={'x': [0, 1], 'y': [0, 1]}, gauge={
                                'axis': {'range': [0, 1.5], 'tickwidth': 1, 'tickcolor': COLOR_SUBTEXT},
                                'bar': {'color': gauge_color, 'thickness': 0.3}, 'bgcolor': "white", 'borderwidth': 0,
                                'steps': [{'range': [0, 0.7], 'color': '#FBE5E0'},
                                          {'range': [0.7, 0.9], 'color': '#FBF0DD'},
                                          {'range': [0.9, 1.5], 'color': '#E3F2EE'}],
                                'threshold': {'line': {'color': COLOR_TEXT, 'width': 2}, 'thickness': 0.75,
                                              'value': 0.9}}))
                        fig_gauge.update_layout(height=230, margin=dict(l=10, r=10, t=30, b=15),
                                                paper_bgcolor="rgba(0,0,0,0)",
                                                font={'color': COLOR_TEXT, 'family': "Arial"})
                        st.markdown(
                            f'<div class="dash-card" style="padding-bottom:6px;"><div class="kpi-label" style="text-align:center;">Índice de consistencia</div>',
                            unsafe_allow_html=True)
                        st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})
                        st.markdown(
                            f'<div style="text-align:center;margin-top:-10px;"><span class="pill {pill_class}">{estado_indice}</span></div></div>',
                            unsafe_allow_html=True)
                    with r2c3:
                        fig_bar = go.Figure()
                        fig_bar.add_trace(go.Bar(x=["Declarado", "Satélite"], y=[emision_declarada, co2e_anual],
                                                 marker_color=[COLOR_PRIMARY_LT, COLOR_PRIMARY],
                                                 text=[f"{emision_declarada:,.0f}", f"{co2e_anual:,.0f}"],
                                                 textposition="outside", width=[0.5, 0.5]))
                        fig_bar.update_layout(height=230, margin=dict(l=10, r=10, t=30, b=10),
                                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                              yaxis=dict(showgrid=True, gridcolor="#EEF2EF", title="tCO₂e/año"),
                                              xaxis=dict(showgrid=False),
                                              font={'color': COLOR_TEXT, 'family': "Arial", 'size': 12},
                                              showlegend=False)
                        st.markdown(
                            f'<div class="dash-card"><div class="kpi-label">Declarado vs. detectado por satélite</div>',
                            unsafe_allow_html=True)
                        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
                        st.markdown(
                            f'<div class="kpi-sub" style="text-align:center;">Diferencia: <b style="color:{COLOR_DANGER};">{diferencia_tco2e:,.0f} tCO₂e</b></div></div>',
                            unsafe_allow_html=True)

                    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

                    st.markdown(
                        f'<div class="dash-section"><div class="dash-section-title"> Exposición financiera CBAM</div></div>',
                        unsafe_allow_html=True)
                    st.caption(
                        f"Fórmula: tCO₂e × factor de fase ({FACTOR_FASE * 100}%) × precio ETS (€{PRECIO_ETS}) | Multa: €{MULTA_POR_TON}/tCO₂e mal declarada")
                    r3c1, r3c2, r3c3, r3c4 = st.columns(4)
                    with r3c1:
                        st.markdown(
                            f'<div class="dash-card"><div class="kpi-icon"></div><div class="kpi-label">Certificados (satélite)</div><div class="kpi-value" style="font-size:21px;">€{costo_certificados_real:,.0f}</div><div class="kpi-sub">Lo que debería pagar si declara bien</div></div>',
                            unsafe_allow_html=True)
                    with r3c2:
                        st.markdown(
                            f'<div class="dash-card"><div class="kpi-icon"></div><div class="kpi-label">Certificados (declarado)</div><div class="kpi-value" style="font-size:21px;">€{costo_certificados_declarado:,.0f}</div><div class="kpi-sub">Lo que planea pagar según su reporte</div></div>',
                            unsafe_allow_html=True)
                    with r3c3:
                        st.markdown(
                            f'<div class="dash-card"><div class="kpi-icon"></div><div class="kpi-label">Multa potencial</div><div class="kpi-value" style="font-size:21px;color:{COLOR_DANGER};">€{multa_potencial:,.0f}</div><div class="kpi-sub">Si el regulador usa estos datos</div></div>',
                            unsafe_allow_html=True)
                    with r3c4:
                        es_critico = exposicion_total > 0
                        alert_class = "alert-card" if es_critico else "alert-card ok"
                        st.markdown(
                            f'<div class="{alert_class}"><div class="alert-icon">{"⚠️" if es_critico else "✅"}</div><div class="alert-title">Exposición total</div><div class="{"alert-value" if es_critico else "alert-value ok-text"}">€{exposicion_total:,.0f}</div><div class="alert-caption">{"Riesgo financiero real" if es_critico else "Sin exposición adicional"}</div></div>',
                            unsafe_allow_html=True)

                    st.divider()
                    st.subheader("Proyección de Exposición según Calendario CBAM (2026-2034)")
                    años_proyeccion = ["2026", "2027", "2028", "2029", "2030", "2031", "2032", "2033", "2034"]
                    arreglo_fases = [0.025, 0.05, 0.10, 0.225, 0.485, 0.61, 0.735, 0.86, 1.0]

                    if st.button("Proyectar Exposición Futura", type="primary", use_container_width=True):
                        y_vals_exposicion = [
                            multa_potencial + ((co2e_anual * f * PRECIO_ETS) - (emision_declarada * f * PRECIO_ETS)) for
                            f in arreglo_fases]
                        fig_proy = go.Figure(
                            go.Scatter(x=años_proyeccion, y=y_vals_exposicion, mode='lines+markers+text',
                                       text=[f"{f * 100}%" for f in arreglo_fases], textposition="top left",
                                       line=dict(color=COLOR_DANGER, width=3), marker=dict(size=8, color=COLOR_DANGER)))
                        fig_proy.update_layout(title="Evolución de la Exposición Financiera (Cronograma EU CBAM)",
                                               xaxis_title="Año de aplicación", yaxis_title="Exposición Total (€)",
                                               paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                               yaxis=dict(showgrid=True, gridcolor="#EEF2EF"),
                                               font={'color': COLOR_TEXT, 'family': "Arial"})
                        st.plotly_chart(fig_proy, use_container_width=True)

                    if st.session_state.get('rol') == "admin" and tiene_dibujo and not tiene_preset:
                        st.divider()
                        with st.expander("Guardar este polígono como Preset"):
                            nuevo_nombre = st.text_input("Nombre de la nueva planta")
                            if st.button("Confirmar Registro en Backend"):
                                if nuevo_nombre:
                                    registrar_planta(nuevo_nombre, emision_declarada, produccion_tons, coords)
                                    st.success(f"Planta '{nuevo_nombre}' guardada con éxito.")
                                    st.rerun()
                                else:
                                    st.error("Por favor, ingrese un nombre válido.")
                except Exception as err:
                    st.error(f"Error en el cálculo: {err}")
                    st.info("Intentá dibujar un área más grande o verificá el rango de fechas.")

    # =====================================================================================
    # PESTAÑA 2: REPORTES GLOBALES
    # =====================================================================================
    with tab_reportes:
        st.subheader("Portafolio Global: Balance Consolidado de la Empresa")

        plantas_db = listar_plantas()
        nombres_validos = [p["nombre"] for p in plantas_db if p["nombre"] and p["nombre"] != "-- Dibujo Libre --"]

        if not nombres_validos:
            st.info(
                "Aún no hay plantas guardadas en el sistema. Dibujá un polígono en el mapa y guardalo para empezar.")
        else:
            plantas_elegidas = st.multiselect(
                "Seleccioná o quitá plantas del análisis consolidado:",
                options=nombres_validos,
                default=nombres_validos
            )

            if not plantas_elegidas:
                st.warning("Seleccioná al menos una planta para ver el reporte.")
            else:
                total_emision_decl = 0.0
                total_co2e_sat = 0.0
                total_multa = 0.0
                total_cert_sat = 0.0
                total_cert_decl = 0.0

                nombres_chart = []
                emisiones_decl_chart = []
                emisiones_sat_chart = []
                exposicion_chart = []

                with st.spinner(f"📡 Procesando {len(plantas_elegidas)} instalaciones con Google Earth Engine..."):
                    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)

                    for nombre in plantas_elegidas:
                        planta = next(p for p in plantas_db if p["nombre"] == nombre)

                        with st.expander(f"Ajustes: {nombre}", expanded=False):
                            col1, col2 = st.columns(2)
                            with col1:
                                prod_var = st.number_input("Producción (ton/año)",
                                                           value=float(planta["produccion_tons"]), key=f"p_{nombre}")
                            with col2:
                                emis_var = st.number_input("Emisión declarada",
                                                           value=float(planta["emision_declarada"]), key=f"e_{nombre}")

                        # Cálculo GEE real para la planta iterada
                        try:
                            coords_p = json.loads(planta["geometria"])
                            poligono_p = ee.Geometry.Polygon(coords_p)
                            area_p = poligono_p.area().getInfo() / 1e6

                            val_ch4_p = (ee.ImageCollection('COPERNICUS/S5P/OFFL/L3_CH4').select(
                                'CH4_column_volume_mixing_ratio_dry_air').filterDate(str(f_inicio),
                                                                                     str(f_fin)).mean().reduceRegion(
                                ee.Reducer.mean(), poligono_p, 1113.2).get(
                                'CH4_column_volume_mixing_ratio_dry_air').getInfo())

                            col_era5_p = (
                                ee.ImageCollection("ECMWF/ERA5/DAILY").filterDate(str(f_inicio), str(f_fin)).map(
                                    calcular_variables_atmosfericas))
                            stats_p = col_era5_p.select(["wind_speed", "surface_pressure"]).mean().reduceRegion(
                                ee.Reducer.mean(), poligono_p, 27830).getInfo()

                            u_p = stats_p.get("wind_speed") if stats_p.get("wind_speed") else 0.0
                            p_p = stats_p.get("surface_pressure") if stats_p.get("surface_pressure") else 101325.0

                            l_p = math.sqrt(area_p * 1e6)
                            ren_p = (86400 * u_p) / l_p if l_p > 0 and u_p > 0 else 6.0

                            exc_p = max(0, (val_ch4_p or 0) - CH4_FONDO_GLOBAL)
                            fac_p = (p_p / (G * M_AIRE)) * M_CH4 * 1e-9 * 1e3

                            co2e_anual_planta = (exc_p * fac_p * area_p) * ren_p * 365 * GWP_CH4
                        except:
                            co2e_anual_planta = 0.0  # Fallback si falla el satélite para esta planta

                        diferencia = max(0, co2e_anual_planta - emis_var)
                        multa_planta = diferencia * MULTA_POR_TON
                        cert_sat_planta = co2e_anual_planta * FACTOR_FASE * PRECIO_ETS
                        cert_decl_planta = emis_var * FACTOR_FASE * PRECIO_ETS
                        exposicion_planta = multa_planta + (cert_sat_planta - cert_decl_planta)

                        total_emision_decl += emis_var
                        total_co2e_sat += co2e_anual_planta
                        total_multa += multa_planta
                        total_cert_sat += cert_sat_planta
                        total_cert_decl += cert_decl_planta

                        nombres_chart.append(nombre)
                        emisiones_decl_chart.append(emis_var)
                        emisiones_sat_chart.append(co2e_anual_planta)
                        exposicion_chart.append(exposicion_planta)

                total_exposicion = total_multa + (total_cert_sat - total_cert_decl)

                st.divider()
                st.markdown(f"### Dashboard Consolidado ({len(plantas_elegidas)} plantas)")

                col_k1, col_k2, col_k3 = st.columns(3)
                with col_k1:
                    st.markdown(
                        f'<div class="dash-card"><div class="kpi-label">CO₂e Total Detectado (Satélite)</div><div class="kpi-value" style="color:{COLOR_PRIMARY_DK};">{total_co2e_sat:,.0f} <span style="font-size:13px;">tCO₂e</span></div></div>',
                        unsafe_allow_html=True)
                with col_k2:
                    st.markdown(
                        f'<div class="dash-card"><div class="kpi-label">CO₂e Total Declarado (Empresa)</div><div class="kpi-value" style="color:{COLOR_SUBTEXT};">{total_emision_decl:,.0f} <span style="font-size:13px;">tCO₂e</span></div></div>',
                        unsafe_allow_html=True)
                with col_k3:
                    es_critico = total_exposicion > 0
                    st.markdown(
                        f'<div class="{"alert-card" if es_critico else "alert-card ok"}"><div class="alert-title">Exposición Total Global</div><div class="alert-value">€{total_exposicion:,.0f}</div></div>',
                        unsafe_allow_html=True)

                st.markdown("<div style='height:25px'></div>", unsafe_allow_html=True)

                graf_col1, graf_col2 = st.columns([1.5, 1])

                with graf_col1:
                    fig_emisiones = go.Figure()
                    fig_emisiones.add_trace(go.Bar(x=nombres_chart, y=emisiones_decl_chart, name='Declarado',
                                                   marker_color=COLOR_PRIMARY_LT))
                    fig_emisiones.add_trace(
                        go.Bar(x=nombres_chart, y=emisiones_sat_chart, name='Detectado', marker_color=COLOR_PRIMARY))
                    fig_emisiones.update_layout(title='Comparativa de Emisiones', barmode='group',
                                                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig_emisiones, use_container_width=True, config={'displayModeBar': False})

                with graf_col2:
                    # 1. Filtramos los negativos (los pasamos a 0)
                    exposicion_pie_bruta = [max(0, val) for val in exposicion_chart]

                    # 2. NUEVO: Filtramos los que son exactamente 0 para que no amontonen texto arriba
                    nombres_pie = []
                    valores_pie = []
                    for nom, val in zip(nombres_chart, exposicion_pie_bruta):
                        if val > 0:
                            nombres_pie.append(nom)
                            valores_pie.append(val)

                    if sum(valores_pie) > 0:
                        fig_pie = go.Figure(data=[go.Pie(
                            labels=nombres_pie,
                            values=valores_pie,
                            hole=0.45,
                            textinfo='percent+label',
                            insidetextorientation='auto',
                            marker=dict(colors=[COLOR_DANGER, COLOR_WARN, COLOR_PRIMARY_DK, '#8c510a', '#dfc27d'])
                        )])

                        fig_pie.update_layout(
                            title=dict(text='Distribución de Exposición (€)', font=dict(size=15)),
                            height=400,  # Altura ajustada para que no pise los bordes
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            showlegend=False,
                            margin=dict(t=50, b=20, l=20, r=20)
                        )

                        # Agregamos padding al contenedor para darle más aire
                        st.markdown('<div class="dash-card" style="padding: 10px;">', unsafe_allow_html=True)
                        st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(
                            f'<div class="dash-card" style="display: flex; align-items: center; justify-content: center; text-align: center; height: 400px;"><h4 style="color:{COLOR_OK};">✅ Ninguna planta presenta riesgo financiero positivo.</h4></div>',
                            unsafe_allow_html=True)

    # ─────────────────────────────────────────
    # FOOTER
    # ─────────────────────────────────────────
    st.divider()
    st.caption(
        "EmiSat Analytics | Datos: Sentinel-5P (ESA/Copernicus) | Fórmula CBAM: Reglamento EU 2023/956 | GWP: IPCC AR6 | Precio ETS: EU CBAM Registry Q1 2026")
