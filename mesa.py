import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import os
import smtplib
from email.message import EmailMessage
import io
import uuid
from pypdf import PdfWriter

# --- RUTAS PARA EL LOGOTIPO BESCO (MEJORADO PARA LA NUBE) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_LOGO_PATH = r"C:\Users\GerardoMendez\OneDrive - Grupo Besco\Escritorio\MisProyectos\logo.png"
CLOUD_LOGO_PATH = os.path.join(BASE_DIR, "logo.png")
CLOUD_LOGO_JPG = os.path.join(BASE_DIR, "logo.jpg")
CLOUD_LOGO_BESCO = os.path.join(BASE_DIR, "logo besco 2026.jpeg")

if os.path.exists(LOCAL_LOGO_PATH):
    LOGO_PATH = LOCAL_LOGO_PATH
elif os.path.exists(CLOUD_LOGO_PATH):
    LOGO_PATH = CLOUD_LOGO_PATH
elif os.path.exists(CLOUD_LOGO_JPG):
    LOGO_PATH = CLOUD_LOGO_JPG
elif os.path.exists(CLOUD_LOGO_BESCO):
    LOGO_PATH = CLOUD_LOGO_BESCO
else:
    LOGO_PATH = None

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BESCO | Evidencia Técnica", layout="wide")

st.markdown("""
    <style>
    .stApp { color: #262730 !important; }
    .stButton > button { color: white !important; background-color: #E21836 !important; }
    h1, h2, h3 { color: #1E3A5F !important; }
    div[data-testid="stExpander"] div[role="button"] p { font-weight: bold !important; color: #1E3A5F !important; }
    </style>
    """, unsafe_allow_html=True)

class BESCO_PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.section_count = 1
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if LOGO_PATH and os.path.exists(LOGO_PATH):
            try:
                img_logo = Image.open(LOGO_PATH).convert("RGB")
                temp_logo = "temp_logo_principal.jpg"
                img_logo.save(temp_logo, format="JPEG")
                
                orig_w, orig_h = img_logo.size
                final_h = 25
                escala = final_h / orig_h
                final_w = orig_w * escala
                
                self.image(temp_logo, x=10, y=8, w=final_w, h=final_h)
            except Exception:
                self.set_font('Arial', 'I', 8)
                self.set_xy(10, 10)
                self.cell(0, 10, f"(Error al procesar logo)")
                
        self.set_font('Arial', 'B', 12)
        self.set_text_color(30, 58, 95)
        self.set_xy(100, 15)
        self.cell(0, 10, 'REPORTE DE SERVICIO TÉCNICO - BESCO', 0, 1, 'R')
        self.set_font('Arial', '', 9)
        self.set_x(100)
        self.cell(0, 5, f"Emisión del Reporte: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, 'R')
        self.ln(12)

    def add_custom_section(self, title):
        if self.get_y() > 250:
            self.add_page()
        self.set_fill_color(30, 58, 95)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, f"{self.section_count}. {title.upper()}", 0, 1, 'L', fill=True)
        self.section_count += 1
        self.ln(2)
        self.set_text_color(0, 0, 0)

    def photo_grid(self, title, photos, eq_index=0, prefix="img"):
        if not photos: return
        
        if self.get_y() > 240:
            self.add_page()
            
        self.add_custom_section(title)
        ancho_foto, alto_foto, espacio_v = 90, 65, 72
        
        for i, foto in enumerate(photos):
            foto.seek(0)
            img = Image.open(foto).convert("RGB")
            temp_p = f"temp_{prefix}_{uuid.uuid4().hex}.jpg"
            img.save(temp_p, format="JPEG")
            
            col = i % 2
            
            if col == 0 and (self.get_y() + alto_foto > 265):
                self.add_page()
                self.set_font('Arial', 'I', 9)
                self.set_text_color(100, 100, 100)
                self.cell(0, 6, f"(Continuación) {title}", 0, 1, 'L')
                self.set_text_color(0, 0, 0)
                self.ln(2)
                
            y_act = self.get_y()
            self.image(temp_p, x=10 + (col * 95), y=y_act, w=ancho_foto, h=alto_foto)
            
            if col == 1 or i == len(photos) - 1:
                self.set_y(y_act + espacio_v)
        self.ln(2)

    def folio_grid(self, title, photo_files):
        if not photo_files: return
        for i, foto in enumerate(photo_files[:4]):
            self.add_page()
            self.add_custom_section(f"{title} - Evidencia {i+1}")
            foto.seek(0)
            img = Image.open(foto).convert("RGB")
            temp_folio = f"temp_folio_{uuid.uuid4().hex}.jpg"
            img.save(temp_folio, format="JPEG")
            
            avail_w, avail_h = 190, 240
            img_w, img_h = img.size
            escala = min(avail_w/img_w, avail_h/img_h)
            final_w, final_h = img_w * escala, img_h * escala
            self.image(temp_folio, x=10 + (190 - final_w) / 2, y=self.get_y() + 5, w=final_w, h=final_h)

def enviar_correo(pdf_bytes, cliente, folio, sucursal, oficina, nombre_archivo, correos_extra, fecha_ejec, lista_destinatarios):
    try:
        if "EMAIL_SENDER" not in st.secrets or "EMAIL_PASSWORD" not in st.secrets:
            st.error("❌ Error de configuración: No se encontraron las claves 'EMAIL_SENDER' o 'EMAIL_PASSWORD' en los Secrets de Streamlit.")
            return False

        remitente = st.secrets["EMAIL_SENDER"]
        password = st.secrets["EMAIL_PASSWORD"]
        destinatarios = list(set(lista_destinatarios + ([c.strip() for c in correos_extra.split(",")] if correos_extra else [])))

        msg = EmailMessage()
        msg['Subject'] = f"Reporte Fotográfico BESCO: {cliente} | TK: {folio} | Of: {oficina}"
        msg['From'] = remitente
        msg['To'] = ", ".join(destinatarios) 
        msg.set_content(f"Se ha generado un nuevo reporte desde el Sistema de Evidencia Técnica BESCO.\n\nFecha Ejecución: {fecha_ejec}\nOficina: {oficina}\nCliente: {cliente}\nFolio: {folio}\nSucursal: {sucursal}")
        msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename=nombre_archivo)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(remitente, password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"❌ Error de conexión SMTP: {e}")
        return False

# --- INTERFAZ ---
if LOGO_PATH is None:
    st.warning("⚠️ Advertencia: No se encontró el archivo del logotipo en GitHub. El PDF se generará sin logotipo.")

st.title("📑 Sistema de Evidencia Técnica BESCO")

st.subheader("1. Identificación General del Servicio")
c_g1, c_g2, c_g3 = st.columns([2, 1, 1.5])
cliente = c_g1.text_input("Cliente")
folio = c_g2.text_input("Folio / OT / TK", max_chars=20)
fecha_ejecucion = c_g3.date_input("Fecha de Ejecución", datetime.now())

col_loc1, col_loc2 = st.columns(2)
sucursal = col_loc1.text_input("Sucursal / Inmueble")

lista_oficinas = [
    "Acapulco", "Toluca", "Pachuca", "Michoacán", "Zonas/ CDMX", "CDMX", 
    "Ben & Company", "BX+", "Emerson", "Odoo", "Tampico"
]
oficina = col_loc2.selectbox("Oficina Responsable", lista_oficinas)

c_t1, c_t2, c_t3, c_t4 = st.columns(4)
tecnico = c_t1.text_input("Técnico Asignado")
supervisor = c_t2.text_input("Supervisor")
tipo_serv = c_t3.selectbox("Servicio", ["Preventivo", "Correctivo", "Emergencia"])
referencia = c_t4.selectbox("Referencia", ["Con Ticket", "Sin Ticket"])

st.markdown("---")

st.subheader("2. Evidencia Documental (Reporte Físico)")
st.info("📌 Puede subir hasta 4 fotos (JPG/PNG) y/o archivos PDF del reporte firmado.")
archivos_folio = st.file_uploader("Subir Folio BESCO", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

st.markdown("---")

st.subheader("3. Equipos a Reportar")
num_equipos = st.number_input("¿Cuántos equipos se atendieron?", min_value=1, max_value=20, value=1)

leyendas_default = {
    "Conservación": "SE REALIZA REAPRIETE DE TORNILLERIA Y LUBRICACIÓN DE CHAPAS, BISAGRAS, SE HACE REVISIÓN DE ESTADO DE PINTURA, PISOS EXTINTORES Y MOBILIARIO.",
    "Hidrosanitario": "SE REALIZA REVISIÓN DE CESPOL, MEZCLADORA, MANGUERAS, LLAVES, WC, DESPACHADORES, EXTRACTORES Y CONEXIONES, SE DEJA FUNCIONANDO CORRECTAMENTE.",
    "Tableros Eléctricos": "SE REALIZA LIMPIEZA, REAPRIETE DE TORNILLERIA, TOMA DE AMPERAJES Y VOLTAJES, SE DEJA FUNCIONANDO CORRECTAMENTE.",
    "Iluminación": "SE REALIZA REVISIÓN GENERAL DE LÁMPARAS, SE CAMBIAN LAMPARAS FUNDIDAS, SE DEJA FUNCIONANDO CORRECTAMENTE.",
    "Aire Acondicionado": "SE REALIZA LIMPIEZA GENERAL DE SERPENTINES, TOMADO PRESIÓN DE REFRIGERANTE, VOLTAJES, AMPERAJES, REAPRIRTE DE CONEXIONES, LIMPIEZA DE FILTROS, SE DEJA FUNCIONANDO CORRECTAMENTE."
}

equipos_data = []
for i in range(num_equipos):
    with st.expander(f"CONFIGURACIÓN EQUIPO {i+1}", expanded=True):
        
        cols_cat = st.columns(2)
        categorias_opciones = ["Ninguna", "Aire Acondicionado", "Tableros Eléctricos", "Hidroneumático", "Conservación", "Hidrosanitario", "Iluminación", "Otros"]
        esp = cols_cat[0].selectbox("Categoría", categorias_opciones, key=f"esp_{i}")
        estatus = cols_cat[1].selectbox("Estatus Final", ["Operando correctamente", "Operando con observaciones", "No queda operando"], key=f"est_{i}")
        
        meds, otros = {}, ""
        
        if esp == "Aire Acondicionado":
            cols = st.columns(4)
            meds['Succión'] = cols[0].text_input("Succión", key=f"s_{i}")
            meds['Descarga'] = cols[1].text_input("Descarga", key=f"d_{i}")
            meds['Salida'] = cols[2].text_input("Salida", key=f"t_{i}")
            meds['Amperaje'] = cols[3].text_input("Amp", key=f"a_{i}")
        elif esp == "Otros":
            otros = st.text_area("Detalles/Mediciones:", key=f"o_{i}")
            
        ca1, ca2, ca3 = st.columns(3)
        tag = ca1.text_input("TAG", key=f"tg_{i}")
        marca = ca2.text_input("Marca", key=f"mr_{i}")
        cap = ca3.text_input("Capacidad", key=f"cp_{i}")
        
        texto_defecto = leyendas_default.get(esp, "")
        actividades = st.text_area("Actividades Realizadas", value=texto_defecto, height=80, key=f"act_{i}_{esp}")
        
        com = st.text_area("Comentarios Extras", key=f"com_{i}")
        
        fa = st.file_uploader("Fotos ANTES", accept_multiple_files=True, key=f"fa_{i}")
        fd = st.file_uploader("Fotos DESPUÉS", accept_multiple_files=True, key=f"fd_{i}")
        
        equipos_data.append({
            "numero": i+1, "esp": esp, "estatus": estatus, "actividades": actividades, 
            "meds": meds, "otros": otros, "tag": tag, "marca": marca, "cap": cap, 
            "com": com, "fa": fa, "fd": fd
        })

st.subheader("4. Materiales Utilizados")
df_mat = st.data_editor(pd.DataFrame(columns=["Cantidad", "Descripción"]), num_rows="dynamic")

st.markdown("---")
st.subheader("5. Envío de Reporte")

mapeo_correos = {
    "Acapulco": ["itzallana.vazquez@besco.mx", "gerardo.fuentes@besco.mx"],
    "Toluca": ["policarpo.rosaliano@besco.mx", "monica.iniestra@besco.mx"],
    "Pachuca": ["german.constantino@besco.mx"],
    "Michoacán": ["cristobal.rodriguez@besco.mx", "ximena.acosta@besco.mx", "javier.zamano@besco.mx"],
    "Zonas/ CDMX": ["german.constantino@besco.mx", "andres.mayagoitia@besco.mx", "brenda.cervantes@besco.mx"],
    "CDMX": ["gerardo.mendez@besco.mx", "alejandro.ramirez@besco.mx"],
    "Ben & Company": ["gerardo.mendez@besco.mx", "alejandro.ramirez@besco.mx"],
    "BX+": ["gerardo.mendez@besco.mx", "alejandro.ramirez@besco.mx", "patricia.cortes@besco.mx"],
    "Emerson": ["gerardo.mendez@besco.mx", "alejandro.ramirez@besco.mx", "patricia.cortes@besco.mx"],
    "Odoo": ["gerardo.mendez@besco.mx", "alejandro.ramirez@besco.mx", "dorian.rodriguez@besco.mx"],
    "Tampico": ["ingrid.lucio@besco.mx", "joel.perez@besco.mx", "gerardo.mendez@besco.mx"]
}

dest_oficina = mapeo_correos.get(oficina, ["gerardo.mendez@besco.mx"])
if "gerardo.mendez@besco.mx" not in dest_oficina: 
    dest_oficina.append("gerardo.mendez@besco.mx")

st.info(f"📧 Destinatarios automáticos: {', '.join(dest_oficina)}")
correos_extra = st.text_input("Correos adicionales (separados por coma)")

if st.button("🚀 Generar y Enviar Reporte Final", type="primary"):
    with st.spinner("Construyendo documento PDF y procesando imágenes..."):
        pdf = BESCO_PDF()
        pdf.add_page()
        
        pdf.add_custom_section("Información General")
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 7, f"Cliente: {cliente} | Folio: {folio}", 0, 1)
        f_ejec_str = fecha_ejecucion.strftime('%d/%m/%Y')
        pdf.cell(0, 7, f"Fecha de Ejecución: {f_ejec_str} | Oficina: {oficina}", 0, 1)
        if sucursal: pdf.cell(0, 7, f"Sucursal: {sucursal}", 0, 1)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 7, f"Técnico: {tecnico} | Supervisor: {supervisor}", 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 7, f"Servicio: {tipo_serv} ({referencia})", 0, 1); pdf.ln(5)

        for eq in equipos_data:
            if pdf.get_y() > 240: pdf.add_page()
            pdf.add_custom_section(f"EQUIPO {eq['numero']}: {eq['esp']}")
            
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 7, f"Estatus Final: {eq['estatus']}", 0, 1)
            pdf.set_font('Arial', '', 10)
            
            valid_meds = {k: v for k, v in eq['meds'].items() if v}
            for k, v in valid_meds.items(): 
                pdf.cell(60, 6, f"{k}:", 1)
                pdf.cell(130, 6, f"{v}", 1, 1)
            if eq['otros']: 
                pdf.multi_cell(0, 6, f"Detalles: {eq['otros']}", 1)
                
            if eq['tag'] or eq['marca'] or eq['cap']: 
                pdf.set_font('Arial', 'B', 9)
                pdf.cell(0, 7, f"TAG: {eq['tag']} | Marca: {eq['marca']} | Cap: {eq['cap']}", 0, 1)
                pdf.set_font('Arial', '', 10)
            
            if eq['actividades']:
                pdf.multi_cell(0, 6, f"Actividades Realizadas:\n{eq['actividades']}", 1)
            if eq['com']: 
                pdf.multi_cell(0, 6, f"Comentarios Extras:\n{eq['com']}", 1)
                
            pdf.photo_grid(f"Antes (Eq. {eq['numero']})", eq['fa'], eq['numero'], "antes")
            pdf.photo_grid(f"Después (Eq. {eq['numero']})", eq['fd'], eq['numero'], "despues")
            pdf.ln(5)

        df_c = df_mat.dropna(subset=["Descripción"])
        if not df_c.empty:
            if pdf.get_y() > 220: pdf.add_page()
            pdf.add_custom_section("Materiales Utilizados")
            pdf.set_font('Arial', 'B', 9); pdf.cell(30, 7, "CANT.", 1, 0, 'C'); pdf.cell(160, 7, "DESCRIPCIÓN", 1, 1, 'C'); pdf.set_font('Arial', '', 9)
            for _, row in df_c.iterrows(): pdf.cell(30, 7, str(row["Cantidad"]), 1); pdf.cell(160, 7, str(row["Descripción"]), 1, 1)

        fotos_folio = [f for f in archivos_folio if f and "image" in f.type]
        if fotos_folio: 
            pdf.folio_grid("FOLIO BESCO", fotos_folio)

        pdf_bytes = pdf.output(dest='S').encode('latin-1')

        pdfs_folio = [f for f in archivos_folio if f and f.type == "application/pdf"]
        if pdfs_folio:
            merger = PdfWriter()
            merger.append(io.BytesIO(pdf_bytes))
            for p in pdfs_folio: 
                p.seek(0) 
                merger.append(p)
            out = io.BytesIO()
            merger.write(out)
            pdf_bytes = out.getvalue()

        nom_archivo = f"Reporte_BESCO_{cliente}_{folio}.pdf".replace(" ", "_")
        
        correo_enviado = enviar_correo(pdf_bytes, cliente, folio, sucursal, oficina, nom_archivo, correos_extra, f_ejec_str, dest_oficina)
        
        if correo_enviado:
            st.success("✅ Reporte enviado exitosamente y listo para descargar.")
        else:
            st.warning("⚠️ El PDF se generó correctamente, pero hubo un problema de envío. Descárgalo aquí abajo:")
        
    st.download_button("📥 Descargar PDF", data=pdf_bytes, file_name=nom_archivo, mime="application/pdf")
