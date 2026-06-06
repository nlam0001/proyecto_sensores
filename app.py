import streamlit as st
import mysql.connector
import pandas as pd
import numpy as np

# Configuración del Dashboard estilo Grafana
st.set_page_config(page_title="AWARE Multi-Sensor Dashboard", layout="wide", initial_sidebar_state="expanded")

# Estilo personalizado para emular un entorno oscuro/profesional
st.markdown("""
    <style>
    .block-container {padding-top: 1.5rem;}
    h1 {color: #ff4b4b; font-weight: 700;}
    h3 {color: #fafafa; font-size: 1.1rem; margin-top: 1rem;}
    </style>
""", unsafe_allow_html=True)

# Configuración de la conexión
def obtener_conexion():
    return mysql.connector.connect(
        host="localhost",
        user="nlam",                    # usuario con permiso SELECT
        password="proyfinal01",         # contraseña de MySQL
        database="proyecto_sensores"   # nombre de la base de datos
    )

# Función de carga optimizada (Limita las lecturas masivas para mejorar rendimiento)
def cargar_tabla(nombre_tabla, con, limite=None):
    try:
        if limite and nombre_tabla not in ["aware_device", "sensor_accelerometer", "sensor_gyroscope", "sensor_magnetometer"]:
            query = f"SELECT * FROM {nombre_tabla} ORDER BY timestamp DESC LIMIT {limite}"
        else:
            query = f"SELECT * FROM {nombre_tabla}"
            
        df = pd.read_sql(query, con)
        
        if 'timestamp' in df.columns:
            df['Fecha/Hora'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.sort_values(by='Fecha/Hora')
        return df
    except:
        return pd.DataFrame()

# --- EXTRACCIÓN DE DATOS ---
try:
    conexion = obtener_conexion()
    
    # Cantidad máxima de puntos a pintar por sensor para evitar lentitud
    MAX_PUNTOS = 500
    
    # Carga de datos de telemetría y estado
    df_dev = cargar_tabla("aware_device", conexion)
    df_bat = cargar_tabla("battery", conexion, limite=MAX_PUNTOS)
    df_tz  = cargar_tabla("timezone", conexion)
    df_acc = cargar_tabla("accelerometer", conexion, limite=MAX_PUNTOS)
    df_blu = cargar_tabla("bluetooth", conexion, limite=10)
    df_gyr = cargar_tabla("gyroscope", conexion, limite=MAX_PUNTOS)
    df_lig = cargar_tabla("light", conexion, limite=MAX_PUNTOS)
    df_lin = cargar_tabla("linear_accelerometer", conexion, limite=MAX_PUNTOS) 
    df_loc = cargar_tabla("locations", conexion, limite=MAX_PUNTOS)
    df_mag = cargar_tabla("magnetometer", conexion, limite=MAX_PUNTOS)
    df_prx = cargar_tabla("proximity", conexion, limite=MAX_PUNTOS)
    df_rot = cargar_tabla("rotation", conexion, limite=MAX_PUNTOS)

    # Tablas de especificaciones de hardware
    df_s_acc = cargar_tabla("sensor_accelerometer", conexion)
    df_s_gyr = cargar_tabla("sensor_gyroscope", conexion)
    df_s_mag = cargar_tabla("sensor_magnetometer", conexion)

    conexion.close()

    # --- BARRA LATERAL: INFORMACIÓN DEL DISPOSITIVO ---
    if not df_dev.empty:
        st.sidebar.header("📱 Dispositivo Vinculado")
        ultimo_dev = df_dev.iloc[-1]
        st.sidebar.markdown(f"**Marca:** {str(ultimo_dev.get('brand', 'Desconocido')).upper()}")
        st.sidebar.markdown(f"**Modelo:** {ultimo_dev.get('model', 'Desconocido')}")
        st.sidebar.markdown(f"**Fabricante:** {ultimo_dev.get('manufacturer', 'Desconocido')}")
        st.sidebar.markdown(f"**Versión Android (SDK):** {ultimo_dev.get('sdk', 'Desconocido')}")
        st.sidebar.caption(f"Device ID: {ultimo_dev.get('device_id', '')}")
    else:
        st.sidebar.info("Esperando sincronización de 'aware_device'...")

    st.title("📊 AWARE Multi-Sensor Analytics")
    st.caption("Monitoreo interactivo de telemetría móvil")

    # --- DISEÑO EN PESTAÑAS ---
    tab_mov, tab_amb, tab_est, tab_geo = st.tabs([
        "🏃 Movimiento y Dinámica", 
        "🌿 Sensores Ambientales", 
        "🔋 Estado del Dispositivo", 
        "📍 Geolocalización"
    ])

    # ================= PESTAÑA 1: MOVIMIENTO Y DINÁMICA =================
    with tab_mov:
        col1, col2 = st.columns(2)
        
        with col1:
            with st.container(border=True):
                st.subheader("Acelerómetro Convencional")
                if not df_acc.empty:
                    df_acc = df_acc.rename(columns={'double_values_0': 'X', 'double_values_1': 'Y', 'double_values_2': 'Z'})
                    st.line_chart(df_acc.set_index('Fecha/Hora')[['X', 'Y', 'Z']])
                else:
                    st.info("Esperando datos de 'accelerometer'...")

            with st.container(border=True):
                st.subheader("Giroscopio (Rotación Angular)")
                if not df_gyr.empty:
                    df_gyr = df_gyr.rename(columns={'double_values_0': 'Pitch', 'double_values_1': 'Roll', 'double_values_2': 'Yaw'})
                    st.line_chart(df_gyr.set_index('Fecha/Hora')[['Pitch', 'Roll', 'Yaw']])
                else:
                    st.info("Esperando datos de 'gyroscope'...")

        with col2:
            with st.container(border=True):
                st.subheader("Acelerómetro Lineal (Sin Gravedad)")
                if not df_lin.empty:
                    if 'double_linear_acceleration_x' in df_lin.columns:
                        df_lin = df_lin.rename(columns={
                            'double_linear_acceleration_x': 'X', 
                            'double_linear_acceleration_y': 'Y', 
                            'double_linear_acceleration_z': 'Z'
                        })
                    else:
                        df_lin = df_lin.rename(columns={'double_values_0': 'X', 'double_values_1': 'Y', 'double_values_2': 'Z'})
                    st.line_chart(df_lin.set_index('Fecha/Hora')[['X', 'Y', 'Z']])
                else:
                    st.info("Esperando datos de 'linear_accelerometer'...")

            with st.container(border=True):
                st.subheader("Sensor de Rotación (Vectores)")
                if not df_rot.empty:
                    columnas_rot = [c for c in ['double_values_0', 'double_values_1', 'double_values_2'] if c in df_rot.columns]
                    st.line_chart(df_rot.set_index('Fecha/Hora')[columnas_rot])
                else:
                    st.info("Esperando datos de 'rotation'...")

    # ================= PESTAÑA 2: SENSORES AMBIENTALES =================
    with tab_amb:
        col_amb1, col_amb2 = st.columns(2)
        
        with col_amb1:
            with st.container(border=True):
                st.subheader("Luminosidad (Light)")
                if not df_lig.empty and 'double_light_lux' in df_lig.columns:
                    st.metric("Última lectura de luz", f"{df_lig['double_light_lux'].iloc[-1]} Lux")
                    st.area_chart(df_lig.set_index('Fecha/Hora')['double_light_lux'], color="#ffaa00")
                else:
                    st.info("Esperando datos de 'light'...")

        with col_amb2:
            with st.container(border=True):
                st.subheader("Proximidad")
                if not df_prx.empty and 'double_values_0' in df_prx.columns:
                    estado_prx = "Cerca 🔴" if df_prx['double_values_0'].iloc[-1] == 0 else "Lejos 🟢"
                    st.metric("Estado de Proximidad", estado_prx)
                    st.bar_chart(df_prx.set_index('Fecha/Hora')['double_values_0'])
                else:
                    st.info("Esperando datos de 'proximity'...")

        with st.container(border=True):
            st.subheader("Magnetómetro (Campo Magnético Microteslas)")
            if not df_mag.empty:
                df_mag = df_mag.rename(columns={'double_values_0': 'Mag X', 'double_values_1': 'Mag Y', 'double_values_2': 'Mag Z'})
                st.line_chart(df_mag.set_index('Fecha/Hora')[['Mag X', 'Mag Y', 'Mag Z']])
            else:
                st.info("Esperando datos de 'magnetometer'...")

    # ================= PESTAÑA 3: ESTADO DEL DISPOSITIVO =================
    with tab_est:
        col_b1, col_b2 = st.columns([1, 2])
        
        with col_b1:
            with st.container(border=True):
                st.subheader("Nivel de Batería")
                if not df_bat.empty and 'battery_level' in df_bat.columns:
                    actual_bat = df_bat['battery_level'].iloc[-1]
                    st.metric("Carga Actual", f"{actual_bat}%")
                    st.progress(int(actual_bat) / 100)
                else:
                    st.info("Esperando datos de 'battery'...")
            
            with st.container(border=True):
                st.subheader("Zona Horaria")
                if not df_tz.empty and 'timezone' in df_tz.columns:
                    st.info(f"Zona horaria activa: {df_tz['timezone'].iloc[-1]}")
                else:
                    st.info("Esperando datos de 'timezone'...")

        with col_b2:
            with st.container(border=True):
                st.subheader("Dispositivos Bluetooth Detectados")
                if not df_blu.empty:
                    st.dataframe(df_blu.tail(10), use_container_width=True)
                else:
                    st.info("Esperando detecciones de 'bluetooth'...")

        # Módulo de metadatos de hardware de las tablas de sensores
        with st.container(border=True):
            st.subheader("🛠️ Especificaciones de Hardware del Dispositivo")
            col_s1, col_s2, col_s3 = st.columns(3)
            
            with col_s1:
                st.markdown("**Acelerómetro:**")
                if not df_s_acc.empty:
                    nombre = str(df_s_acc['sensor_name'].iloc[-1])
                    proveedor = str(df_s_acc['sensor_vendor'].iloc[-1])
                    rango = df_s_acc['double_sensor_maximum_range'].iloc[-1]
                    resolucion = df_s_acc['double_sensor_resolution'].iloc[-1]
                    st.text(f"Modelo: {nombre}\nFabricante: {proveedor}\nRango Máx: {rango}\nResolución: {resolucion}")
                else:
                    st.caption("No registrado o tabla vacía.")
                    
            with col_s2:
                st.markdown("**Giroscopio:**")
                if not df_s_gyr.empty:
                    nombre = str(df_s_gyr['sensor_name'].iloc[-1])
                    proveedor = str(df_s_gyr['sensor_vendor'].iloc[-1])
                    rango = df_s_gyr['double_sensor_maximum_range'].iloc[-1]
                    st.text(f"Modelo: {nombre}\nFabricante: {proveedor}\nRango Máx: {rango}")
                else:
                    st.caption("No registrado o tabla vacía.")
                    
            with col_s3:
                st.markdown("**Magnetómetro:**")
                if not df_s_mag.empty:
                    nombre = str(df_s_mag['sensor_name'].iloc[-1])
                    proveedor = str(df_s_mag['sensor_vendor'].iloc[-1])
                    rango = df_s_mag['double_sensor_maximum_range'].iloc[-1]
                    st.text(f"Modelo: {nombre}\nFabricante: {proveedor}\nRango Máx: {rango}")
                else:
                    st.caption("No registrado o tabla vacía.")

    # ================= PESTAÑA 4: GEOLOCALIZACIÓN =================
    with tab_geo:
        if not df_loc.empty:
            if 'double_latitude' in df_loc.columns and 'double_longitude' in df_loc.columns:
                df_mapa = df_loc[['double_latitude', 'double_longitude']].dropna()
                df_mapa.columns = ['lat', 'lon']
                
                st.subheader("Mapa de Posicionamiento Global (GPS & Network)")
                st.map(df_mapa)
                st.write(f"Total de coordenadas registradas: {len(df_mapa)}")
            else:
                st.warning("Estructura de coordenadas no compatible.")
        else:
            st.info("Esperando datos de localización en la tabla 'locations'...")

except Exception as e:
    st.error(f"Error general en la interfaz: {e}")