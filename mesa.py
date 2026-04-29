import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import os

# --- RUTAS PARA LA NUBE ---
LOGO_PATH = "logo besco 2026.jpeg"

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BESCO | Reportes Técnicos", layout="wide")

# --- ESTILOS CSS BESCO ---
st.markdown("""
    <style>
    .stApp { color: #262730 !important; }
    .stButton > button { color: white !important; background-color: #E21836 !important; }
    h1, h2, h3 { color: #1E3A5F !important; }
    div[data-testid="stExpander"] div[role="button"] p { font-weight: bold !important; color: #1E3A5F !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CLASE PDF CORREGIDA ---
class BESCO_PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.section_count = 1

    def header(self):
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, x=10, y=8, h=25)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(30, 58, 95)
        self.set_xy(100, 15)
        self.cell(0, 10, 'REPORTE DE SERVICIO TÉCNICO', 0, 1, 'R')
        self.set_font('Arial', '', 9)
        self.set_x(100)
        self.cell(0, 5, f"Emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, 'R')
        self.ln(12)

    def add_custom_section(self, title):
        self.set_fill_color(30, 58, 95)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, f"{self.section_count}. {title.upper()}", 0, 1, 'L', fill=True)
        self.section_count += 1
        self.ln(2)
        self.set_text_color(0, 0, 0)

    # AQUÍ ESTÁ LA SOLUCIÓN AL ERROR DE LAS FOTOS
    def photo_grid(self, title, photos):
        if photos:
            self.add_custom_section(title)
            y_start = self.get_y()
            for i, foto in enumerate(photos):
                img = Image.open(foto).convert("RGB")
                # Nombre único para evitar que se repitan
                id_foto = title.replace(" ", "_")
                temp_p = f"temp_{id_foto}_{i}.jpg"
                img.save(temp_p)
                
                col = i % 2
                row = i // 2
                self.image(temp_p, x=10 + (col * 95), y=y_start + (row * 70), w=90, h=65)
                if col == 1 or i == len(photos)-1:
                    self.set_y(y_start + ((row + 1) * 70) + 5)
            self.ln(5)

# --- INTERFAZ ---
st.title("📑 Sistema de Evidencia Técnica BESCO")

# 1. IDENTIFICACIÓN
st.subheader("1. Identificación del Servicio")
col_cl1, col_cl2, col_cl3 = st.columns([2, 1, 1])
cliente = col_cl1.text_input("Cliente")
folio = col_cl2.text_input("Folio / OT")
estado_op = col_cl3.slider("Estado de Operación (1-10)", 1, 10, 5)

c1, c2, c3, c4 = st.columns(4)
tecnico = c1.text_input("Técnico Asignado")
supervisor = c2.text_input("Supervisor")
tipo_serv = c3.selectbox("Servicio", ["Preventivo", "Correctivo", "Emergencia"])
referencia = c4.selectbox("Referencia", ["Con Ticket", "Sin Ticket"])
st.markdown("---")

# 2. ESPECIALIDAD
st.subheader("2. Especialidad y Mediciones Críticas")
esp = st.selectbox("Categoría de Equipo", ["Ninguna", "Aire Acondicionado", "Tableros Eléctricos", "Hidroneumático", "Plantas de Emergencia", "Transformadores"])

if esp != "Ninguna":
    with st.expander("❓ AYUDA TÉCNICA (Puntos Clave)"):
        st.info("💡 Revise los parámetros de acuerdo al manual del equipo. Valores fuera de rango deben justificarse en los comentarios.")

mediciones = {}
if esp == "Aire Acondicionado":
    cols = st.columns(4)
    mediciones['P. Succión'] = cols[0].text_input("Succión (PSI)")
    mediciones['P. Descarga'] = cols[1].text_input("Descarga (PSI)")
    mediciones['T. Salida'] = cols[2].text_input("Salida (°C)")
    mediciones['Amp. Comp.'] = cols[3].text_input("Amperaje (A)")
elif esp == "Tableros Eléctricos":
    cols = st.columns(3)
    mediciones['V L1-L2'] = cols[0].text_input("V L1-L2")
    mediciones['Amp A'] = cols[1].text_input("Amp A")
    mediciones['Amp B'] = cols[2].text_input("Amp B")
elif esp == "Hidroneumático":
    cols = st.columns(3)
    mediciones['Arranque'] = cols[0].text_input("Arranque (PSI)")
    mediciones['Paro'] = cols[1].text_input("Paro (PSI)")
    mediciones['Amp. Bomba'] = cols[2].text_input("Amperaje (A)")
elif esp == "Plantas de Emergencia":
    cols = st.columns(3)
    mediciones['Frecuencia'] = cols[0].text_input("Freq (Hz)")
    mediciones['Voltaje Bat.'] = cols[1].text_input("V Batería")
    mediciones['Pres. Aceite'] = cols[2].text_input("Aceite (PSI)")

st.markdown("---")

# 3. DATOS EQUIPO
st.subheader("3. Datos del Equipo")
c_eq1, c_eq2, c_eq3 = st.columns(3)
tag = c_eq1.text_input("TAG")
marca = c_eq2.text_input("Marca/Modelo")
capacidad = c_eq3.text_input("Capacidad")

# 4. COMENTARIOS
st.subheader("4. Comentarios y Observaciones")
comentarios = st.text_area("Describa hallazgos o justificación técnica")

# 5. EVIDENCIA
st.subheader("5. Evidencia Fotográfica")
f_antes = st.file_uploader("Fotos ANTES", accept_multiple_files=True)
f_despues = st.file_uploader("Fotos DESPUÉS", accept_multiple_files=True)

# 6. MATERIALES
st.subheader("6. Materiales")
df_mat = st.data_editor(pd.DataFrame(columns=["Cantidad", "Descripción"]), num_rows="dynamic")

# BOTÓN FINAL (Adaptado para descargar en celular)
if st.button("🚀 Generar Reporte Final", type="primary"):
    pdf = BESCO_PDF()
    pdf.add_page()
    
    # PDF Sección 1
    pdf.add_custom_section("Información General")
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 7, f"Cliente: {cliente} | Folio: {folio}", 0, 1)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 7, f"ESTADO DE OPERACIÓN DEL EQUIPO: {estado_op}/10", 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 7, f"Servicio: {tipo_serv} ({referencia}) | Técnico: {tecnico}", 0, 1)
    pdf.ln(5)

    # Mediciones
    valid_meds = {k: v for k, v in mediciones.items() if v}
    if valid_meds:
        pdf.add_custom_section(f"Mediciones Técnicas: {esp}")
        for k, v in valid_meds.items():
            pdf.cell(60, 7, f"{k}:", 1); pdf.cell(130, 7, f"{v}", 1, 1)
        pdf.ln(5)

    # Datos Equipo
    if tag or marca:
        pdf.add_custom_section("Datos del Equipo")
        pdf.cell(0, 7, f"TAG: {tag} | Modelo: {marca} | Capacidad: {capacidad}", 0, 1); pdf.ln(5)

    # Comentarios
    if comentarios:
        pdf.add_custom_section("Comentarios")
        pdf.multi_cell(0, 7, comentarios, 1); pdf.ln(5)

    # Imágenes
    if f_antes: pdf.photo_grid("Evidencia Fotográfica (Antes)", f_antes)
    if f_despues: 
        if pdf.get_y() > 180: pdf.add_page()
        pdf.photo_grid("Evidencia Fotográfica (Después)", f_despues)

    # Materiales
    df_c = df_mat.dropna(subset=["Descripción"])
    if not df_c.empty:
        pdf.add_custom_section("Materiales Utilizados")
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(30, 7, "CANT.", 1, 0, 'C')
        pdf.cell(160, 7, "DESCRIPCIÓN", 1, 1, 'C')
        pdf.set_font('Arial', '', 9)
        for _, row in df_c.iterrows():
            pdf.cell(30, 7, str(row["Cantidad"]), 1); pdf.cell(160, 7, str(row["Descripción"]), 1, 1)

    # Preparar descarga para la Nube
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    nombre_pdf = f"Reporte_BESCO_{folio}.pdf"
    
    st.success(f"✅ ¡Reporte Listo!")
    st.download_button(
        label="📥 Descargar PDF a mi Celular",
        data=pdf_bytes,
        file_name=nombre_pdf,
        mime="application/pdf"
    )
