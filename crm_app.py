import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# ---------------- CONFIGURACIÓN INICIAL ----------------
st.set_page_config(page_title="CRM de Vendedores", layout="centered")
st.title("📋 CRM de Vendedores")

# ---------------- DETECCIÓN DE ARCHIVO ----------------
archivo = None
if os.path.exists("CLIENTES.xlsx"):
    archivo = "CLIENTES.xlsx"
elif os.path.exists("CLIENTES.xls"):
    archivo = "CLIENTES.xls"

# ---------------- FUNCIONES ----------------
def crear_link_whatsapp(numero, mensaje="Hola, gracias por su interés"):
    if pd.isna(numero):
        return None
    numero = str(numero).strip().replace(" ", "").replace("-", "").replace("+", "")
    if not numero.startswith("57"):
        numero = "57" + numero
    return f"https://wa.me/{numero}?text={mensaje.replace(' ', '%20')}"

# ---------------- CARGA DE DATOS ----------------
try:
    if not archivo:
        raise FileNotFoundError("No se encontró CLIENTES.xlsx ni CLIENTES.xls en la carpeta.")

    engine = 'openpyxl' if archivo.endswith('.xlsx') else 'xlrd'
    df = pd.read_excel(archivo, engine=engine)

    columnas_necesarias = ['VENDEDOR', 'NOMBRE TERCERO', 'TELEFONO', 'EMAIL', 'CIUDAD', 'DIRECCION']
    for col in columnas_necesarias:
        if col not in df.columns:
            df[col] = ""

    if 'fecha gestion' not in df.columns:
        df['fecha gestion'] = None
    if 'proxima gestion' not in df.columns:
        df['proxima gestion'] = None

    # ---------------- SELECCIÓN DE ROL ----------------
    st.sidebar.title("👥 Acceso")
    rol = st.sidebar.radio("¿Quién eres?", ["Vendedor", "Supervisor"])

    if rol == "Vendedor":
        usuario = st.sidebar.selectbox("Selecciona tu nombre", df['VENDEDOR'].dropna().unique())
        datos_visibles = df[df['VENDEDOR'] == usuario].copy()
    else:
        usuario = "Supervisor"
        datos_visibles = df.copy()

    # ---------------- ALERTAS PARA VENDEDORES ----------------
    if rol == "Vendedor":
        st.subheader("🚨 Clientes que requieren gestión")

        datos_visibles['fecha gestion'] = pd.to_datetime(datos_visibles['fecha gestion'], errors='coerce')
        hoy = datetime.now()
        limite = hoy - timedelta(days=30)

        sin_gestion = datos_visibles[datos_visibles['fecha gestion'].isna()]
        gestion_antigua = datos_visibles[datos_visibles['fecha gestion'] < limite]

        if not sin_gestion.empty:
            st.error(f"🟥 {len(sin_gestion)} cliente(s) sin gestión registrada:")
            for _, row in sin_gestion.iterrows():
                st.markdown(f"- {row['NOMBRE TERCERO']} ({row['CIUDAD']})")

        if not gestion_antigua.empty:
            st.warning(f"🟧 {len(gestion_antigua)} cliente(s) con gestión antigua (+30 días):")
            for _, row in gestion_antigua.iterrows():
                fecha = row['fecha gestion'].strftime('%Y-%m-%d')
                st.markdown(f"- {row['NOMBRE TERCERO']} — última gestión: {fecha}")

        if sin_gestion.empty and gestion_antigua.empty:
            st.success("✅ Todos los clientes tienen gestiones recientes.")

    # ---------------- INTERFAZ PARA SUPERVISOR ----------------
    if rol == "Supervisor":
        st.subheader("📊 Gestión completa de clientes")
        vendedor_filtro = st.selectbox("Filtrar por vendedor:", ["Todos"] + sorted(df['VENDEDOR'].dropna().unique()))
        if vendedor_filtro != "Todos":
            mostrar = df[df['VENDEDOR'] == vendedor_filtro]
        else:
            mostrar = df
        st.dataframe(mostrar[['VENDEDOR', 'NOMBRE TERCERO', 'CIUDAD', 'fecha gestion', 'proxima gestion']])

    # ---------------- DETALLE DE CLIENTE ----------------
    st.subheader("📁 Gestión individual")
    if not datos_visibles.empty:
        cliente = st.selectbox("Selecciona un cliente", datos_visibles['NOMBRE TERCERO'].unique())
        info = datos_visibles[datos_visibles['NOMBRE TERCERO'] == cliente].iloc[0]

        st.markdown(f"**📞 Teléfono:** {info['TELEFONO']}")
        st.markdown(f"**✉️ Email:** {info['EMAIL']}")
        st.markdown(f"**📍 Ciudad:** {info['CIUDAD']}")
        st.markdown(f"**🏠 Dirección:** {info['DIRECCION']}")

        wa_link = crear_link_whatsapp(info['TELEFONO'])
        if wa_link:
            st.markdown(f"[📲 Enviar WhatsApp]({wa_link})", unsafe_allow_html=True)

        # ----------- GESTIÓN -----------
        st.subheader("📝 Registrar nueva gestión")
        ultima_gestion = st.date_input("🗓️ Última gestión", value=datetime.now())
        proxima_gestion = st.date_input("📅 Próxima gestión", value=datetime.now() + timedelta(days=15))
        observaciones = st.text_area("🗒️ Observaciones (opcional, aún no se guarda)", "")

        if st.button("✅ Guardar gestión"):
            df.loc[df['NOMBRE TERCERO'] == cliente, 'fecha gestion'] = pd.to_datetime(ultima_gestion)
            df.loc[df['NOMBRE TERCERO'] == cliente, 'proxima gestion'] = pd.to_datetime(proxima_gestion)

            try:
                df.to_excel(archivo, index=False)
                st.success("✔️ Gestión registrada y guardada correctamente en Excel.")
            except PermissionError:
                st.error("❌ No se pudo guardar. Cierra el archivo Excel si está abierto.")
            except Exception as e:
                st.error(f"⚠️ Error al guardar: {e}")

except FileNotFoundError as fe:
    st.error(f"❌ {fe}")
except Exception as e:
    st.error(f"⚠️ Error inesperado: {e}")
