import streamlit as st
import pandas as pd
import re
import base64
import os
from io import BytesIO
from PIL import Image as PILImage 
from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="UNMRMA - Notas", page_icon="🎓", layout="centered")

# --- FUNCIONES DE UTILIDAD ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

img_fondo_base64 = get_base64_of_bin_file("fondo.jpg")
logo_base64 = get_base64_of_bin_file("logo.png")

# --- CSS: DISEÑO "MOBILE FIRST" ELEGANTE ---
css_style = f"""
    <style>
    /* 1. FONDO Y CONTENEDOR */
    .stApp {{
        background-image: url("data:image/jpg;base64,{img_fondo_base64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .block-container {{
        background-color: rgba(255, 255, 255, 0.96);
        border-radius: 0px 0px 20px 20px; /* Bordes redondeados solo abajo */
        padding: 1rem 1rem 3rem 1rem; /* Padding reducido para movil */
        max-width: 800px;
        margin-top: -60px; /* Subir todo para aprovechar pantalla movil */
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }}

    /* 2. TIPOGRAFÍA Y ENCABEZADOS */
    html, body, [class*="css"] {{
        font-family: 'Roboto', 'Segoe UI', sans-serif;
        color: #222;
    }}
    .header-container {{
        text-align: center;
        margin-bottom: 20px;
        padding-top: 20px;
    }}
    .univ-title {{
        color: #003366;
        font-size: 1.6rem; /* Grande y legible */
        font-weight: 800;
        margin-top: 10px;
        line-height: 1.2;
        letter-spacing: -0.5px;
    }}

    /* 3. INPUT DE CARNET (GRANDE PARA DEDOS) */
    .stTextInput > div > div > input {{
        text-align: center;
        font-size: 1.4rem;
        padding: 15px;
        border: 2px solid #ccc;
        border-radius: 12px;
        color: #333 !important;
        background-color: #fff !important;
    }}
    .stTextInput > div > div > input:focus {{
        border-color: #58b24c;
    }}

    /* 4. BOTONES VERDES UNIFICADOS (#58b24c) */
    /* Afecta tanto al botón de Buscar como al de Descargar */
    div.stButton > button {{
        background-color: #58b24c !important;
        color: white !important;
        border: none;
        font-weight: 700;
        font-size: 1.1rem;
        padding: 0.8rem 1rem;
        border-radius: 12px;
        width: 100%;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.2s;
    }}
    div.stButton > button:active {{
        transform: scale(0.98);
        background-color: #46963b !important;
    }}
    /* Hover effect */
    div.stButton > button:hover {{
        background-color: #46963b !important;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }}

    /* 5. TARJETA DE ESTUDIANTE (INFO PERSONAL) */
    .student-info-card {{
        background: #f0f4f8;
        border-left: 5px solid #003366;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
    }}
    .student-name {{
        color: #003366;
        font-size: 1.3rem;
        font-weight: 700;
        margin: 0 0 5px 0;
    }}
    .student-meta {{
        font-size: 0.9rem;
        color: #555;
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }}
    .meta-badge {{
        background: #fff;
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid #ddd;
    }}

    /* 6. TARJETAS DE ASIGNATURAS (DISEÑO MÓVIL) */
    /* Esto reemplaza a la tabla. Cada materia es un bloque. */
    .subject-card {{
        background-color: white;
        border: 1px solid #eee;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: transform 0.2s;
    }}
    .subject-left {{
        flex: 1;
        padding-right: 10px;
    }}
    .subject-title {{
        font-weight: 700;
        color: #333;
        font-size: 1rem;
        margin-bottom: 4px;
    }}
    .subject-docente {{
        font-size: 0.8rem;
        color: #777;
    }}
    .subject-right {{
        text-align: right;
        min-width: 80px;
    }}
    .grade-display {{
        font-size: 1.4rem;
        font-weight: 800;
        display: block;
    }}
    .status-badge {{
        font-size: 0.7rem;
        padding: 3px 8px;
        border-radius: 10px;
        font-weight: bold;
        text-transform: uppercase;
        display: inline-block;
        margin-top: 4px;
    }}
    .nota-esp {{
        font-size: 0.75rem;
        color: #d9534f;
        font-weight: bold;
        display: block;
        margin-top: 2px;
    }}

    /* Ocultar elementos nativos */
    #MainMenu, footer, header {{visibility: hidden;}}
    .stDeployButton {{display:none;}}
    </style>
"""
st.markdown(css_style, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    if not os.path.exists("Notas.xlsx"): return None
    try:
        df = pd.read_excel("Notas.xlsx", sheet_name="Datos", dtype=str)
        df.columns = df.columns.str.strip()
        return df.fillna("-")
    except:
        return None

# --- GENERACIÓN PDF (Lógica mantenida, visualización backend) ---
def generar_pdf(alumno_data, info):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, topMargin=40, bottomMargin=40)
    elements = []
    styles = getSampleStyleSheet()
    
    try:
        logo_path = "logo.png"
        if os.path.exists(logo_path):
            img_pil = PILImage.open(logo_path)
            orig_w, orig_h = img_pil.size
            aspect = orig_h / float(orig_w)
            pdf_w = 1.8 * inch
            pdf_h = pdf_w * aspect
            logo = RLImage(logo_path, width=pdf_w, height=pdf_h)
            
            txt_univ = """<font size=12><b>UNIVERSIDAD NACIONAL MULTIDISCIPLINARIA<br/>RICARDO MORALES AVILÉS</b></font>"""
            p_univ = Paragraph(txt_univ, ParagraphStyle('T', parent=styles['Heading1'], alignment=TA_CENTER, leading=16, textColor=colors.black))
            
            t_header = Table([[logo, p_univ]], colWidths=[2*inch, 4.5*inch])
            t_header.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
            elements.append(t_header)
    except:
        pass

    elements.append(Spacer(1, 15))
    elements.append(Paragraph("<b>ACTA DE CALIFICACIONES</b>", ParagraphStyle('S', alignment=TA_CENTER, fontSize=14)))
    elements.append(Spacer(1, 25))
    
    # Datos Estudiante en PDF
    estilo_b = ParagraphStyle('B', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10)
    estilo_n = ParagraphStyle('N', parent=styles['Normal'], fontName='Helvetica', fontSize=10)
    
    data_info = [
        [Paragraph("ESTUDIANTE:", estilo_b), Paragraph(info['nombre'], estilo_n), Paragraph("CARNET:", estilo_b), Paragraph(info['carnet'], estilo_n)],
        [Paragraph("CARRERA:", estilo_b), Paragraph(info['carrera'], estilo_n), "", ""],
        [Paragraph("AÑO:", estilo_b), Paragraph(info['anio'], estilo_n), Paragraph("CICLO:", estilo_b), Paragraph(f"{info['ciclo']} - {info['regimen']}", estilo_n)]
    ]
    t_info = Table(data_info, colWidths=[1.1*inch, 2.9*inch, 1.2*inch, 1.5*inch])
    t_info.setStyle(TableStyle([('SPAN', (1,1), (3,1)), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
    elements.append(t_info)
    elements.append(Spacer(1, 20))
    
    # Tabla Notas en PDF
    data_notas = [['ASIGNATURA', 'DOCENTE', 'NOTA', 'N. ESP.', 'ESTADO']]
    for item in alumno_data:
        data_notas.append([
            Paragraph(item['asignatura'], ParagraphStyle('Cell', fontSize=9)),
            Paragraph(item['docente'], ParagraphStyle('Cell', fontSize=9)),
            item['nota_final'], item['nota_especial'], item['estado']
        ])
    
    t_notas = Table(data_notas, colWidths=[2.3*inch, 2.0*inch, 0.7*inch, 0.7*inch, 1.0*inch])
    t_notas.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (1,0), (-1,-1), [colors.whitesmoke, colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    elements.append(t_notas)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- INTERFAZ DE USUARIO ---
def main():
    
    # 1. ENCABEZADO HTML (SOLUCIÓN LOGO GRANDE Y TÍTULO UNMRMA)
    # Ajustamos max-width de la imagen para que se vea grande en movil pero no gigante en PC
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" style="width: 100%; max-width: 250px; height: auto;">' if logo_base64 else ""
    
    st.markdown(f"""
        <div class="header-container">
            {logo_html}
            <h1 class="univ-title">UNMRMA – CUR-Carazo</h1>
        </div>
    """, unsafe_allow_html=True)

    # 2. CARGA DE DATOS
    df = cargar_datos()
    if df is None:
        st.error("⚠️ Error: No se encuentra 'Notas.xlsx'.")
        st.stop()

    # 3. INPUT Y BOTÓN (SIN st.form PARA EVITAR ERRORES)
    # Usamos session_state para controlar si se ha pulsado buscar
    if 'searched' not in st.session_state:
        st.session_state.searched = False
    if 'carnet_busqueda' not in st.session_state:
        st.session_state.carnet_busqueda = ""

    carnet_input = st.text_input("Ingrese su Nº de Carnet", placeholder="XX-XXXX-XX", label_visibility="collapsed")
    
    # Botón verde (estilizado por CSS)
    if st.button("CONSULTAR AHORA"):
        st.session_state.searched = True
        st.session_state.carnet_busqueda = carnet_input

    # 4. LÓGICA DE BÚSQUEDA Y VISUALIZACIÓN
    if st.session_state.searched:
        carnet = st.session_state.carnet_busqueda.strip()
        
        # Validación
        if not re.match(r"^\d{2}-\d{4}-\d{2}$", carnet):
            st.warning("⚠️ Formato incorrecto. Ejemplo: 25-0022-02")
        else:
            res = df[df['N° Carnet'] == carnet]
            
            if res.empty:
                st.error("❌ No se encontraron registros con ese carnet.")
            else:
                p = res.iloc[0]
                
                # DATOS PERSONALES (Diseño Limpio)
                st.markdown(f"""
                <div class="student-info-card">
                    <div class="student-name">{p['Nombres y Apellidos']}</div>
                    <div class="student-meta">
                        <span class="meta-badge">🆔 {p['N° Carnet']}</span>
                        <span class="meta-badge">📚 {p['Carrera']}</span>
                        <span class="meta-badge">📅 {p['Año']} | {p['Ciclo']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # TARJETAS DE ASIGNATURAS (LOOP VISUAL)
                datos_pdf = []
                
                for _, row in res.iterrows():
                    # Lógica de colores y estados
                    nf, ne = str(row['Nota Final']).strip(), str(row['Nota de Especial']).strip()
                    estado_texto, color_nota, color_badge, bg_badge = "APROBADO", "#2e7d32", "#155724", "#d4edda"
                    mostrar_ne_html = ""
                    
                    es_sd = (nf.upper() == "SD")
                    
                    try:
                        val = float(nf)
                        if val < 60:
                            estado_texto, color_nota, color_badge, bg_badge = "REPROBADO", "#c62828", "#721c24", "#f8d7da"
                            if ne and ne != "-" and not es_sd:
                                mostrar_ne_html = f'<span class="nota-esp">Nota Esp: {ne}</span>'
                    except:
                        if es_sd:
                            estado_texto, color_nota, color_badge, bg_badge = "SIN DERECHO", "#c62828", "#721c24", "#f8d7da"

                    # HTML DE LA TARJETA (CARD)
                    # Esto reemplaza a la tabla fea. Se ve genial en movil.
                    st.markdown(f"""
                    <div class="subject-card">
                        <div class="subject-left">
                            <div class="subject-title">{row['Asignatura']}</div>
                            <div class="subject-docente">👨‍🏫 {row['Docente']}</div>
                        </div>
                        <div class="subject-right">
                            <span class="grade-display" style="color: {color_nota}">{nf}</span>
                            <span class="status-badge" style="background-color: {bg_badge}; color: {color_badge}">{estado_texto}</span>
                            {mostrar_ne_html}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    datos_pdf.append({
                        'asignatura': row['Asignatura'], 'docente': row['Docente'], 
                        'nota_final': nf, 'nota_especial': ne if mostrar_ne_html else "-", 
                        'estado': estado_texto.title()
                    })

                # BOTÓN PDF (Mismo estilo verde que el de consultar)
                st.write("") # Espaciador
                pdf_bytes = generar_pdf(datos_pdf, {
                    'nombre': p['Nombres y Apellidos'], 'carnet': p['N° Carnet'], 
                    'carrera': p['Carrera'], 'anio': p['Año'], 'ciclo': p['Ciclo'], 
                    'regimen': p['Regimen']
                })
                
                st.download_button(
                    label="📥 DESCARGAR REPORTE PDF",
                    data=pdf_bytes,
                    file_name=f"Notas_{p['N° Carnet']}.pdf",
                    mime="application/pdf"
                )

if __name__ == "__main__":
    main()
