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

# --- CSS: DISEÑO FINAL ---
css_style = f"""
    <style>
    /* 1. FONDO MOSAICO */
    .stApp {{
        background-image: url("data:image/jpg;base64,{img_fondo_base64}");
        background-attachment: fixed;
        background-repeat: repeat;
        background-size: auto;
    }}
    
    /* 2. CONTENEDOR */
    .block-container {{
        background-color: rgba(255, 255, 255, 0.88);
        border-radius: 0px 0px 20px 20px;
        padding: 1rem 1rem 3rem 1rem;
        max-width: 800px;
        margin-top: -60px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        backdrop-filter: blur(5px);
    }}

    /* 3. TIPOGRAFÍA */
    html, body, [class*="css"] {{
        font-family: 'Roboto', 'Segoe UI', sans-serif;
        color: #222;
    }}
    .header-container {{
        text-align: center;
        margin-bottom: 25px;
        padding-top: 15px;
    }}
    .header-subtitle {{
        color: #555 !important;
        font-size: 1.1rem;
        font-weight: 500;
        margin-bottom: 5px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .univ-title {{
        color: #003366 !important;
        font-size: 1.5rem;
        font-weight: 800;
        margin-top: 5px;
        line-height: 1.2;
    }}

    /* 4. INPUT Y BOTONES */
    .stTextInput > div > div > input {{
        text-align: center;
        font-size: 1.4rem;
        padding: 12px;
        border: 2px solid #ccc;
        border-radius: 12px;
        color: #000 !important;
        background-color: #fff !important;
    }}
    .stTextInput > div > div > input:focus {{
        border-color: #58b24c;
        box-shadow: 0 0 0 2px rgba(88, 178, 76, 0.2);
    }}

    div.stButton > button, div.stDownloadButton > button {{
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
        margin-bottom: 10px;
    }}
    div.stButton > button:active, div.stDownloadButton > button:active {{
        transform: scale(0.98);
        background-color: #46963b !important;
    }}
    div.stButton > button:hover, div.stDownloadButton > button:hover {{
        background-color: #46963b !important;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }}

    /* 5. TARJETAS */
    .student-info-card {{
        background: #ffffff;
        border-left: 5px solid #003366;
        padding: 15px 20px;
        border-radius: 8px;
        margin-bottom: 25px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }}
    .student-name {{
        color: #003366 !important;
        font-size: 1.4rem;
        font-weight: 700;
        margin: 0 0 10px 0;
    }}
    .student-meta {{
        font-size: 0.95rem;
        color: #444 !important;
        line-height: 1.6;
        border-top: 1px solid #eee;
        padding-top: 10px;
    }}
    
    /* Tarjeta de Asignatura (Estructura Fija) */
    .subject-card {{
        background-color: white;
        border: 1px solid #f0f0f0;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .subject-left {{ flex: 1; padding-right: 15px; }}
    .subject-title {{ font-weight: 700; color: #222 !important; font-size: 1rem; display: block; }}
    .subject-docente {{ font-size: 0.85rem; color: #666 !important; display: block; }}
    
    .subject-right {{ 
        text-align: right; 
        min-width: 90px; 
        display: flex; 
        flex-direction: column; 
        align-items: flex-end; 
    }}
    .grade-display {{ font-size: 1.5rem; font-weight: 800; display: block; }}
    .status-badge {{ 
        font-size: 0.75rem; 
        padding: 4px 10px; 
        border-radius: 12px; 
        font-weight: bold; 
        text-transform: uppercase; 
        display: inline-block; 
        margin-top: 5px; 
    }}

    .selection-title {{
        text-align: center;
        color: #003366;
        margin-bottom: 20px;
        font-weight: bold;
    }}

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

# --- GENERACIÓN PDF ---
def generar_pdf(alumno_data, info):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, topMargin=40, bottomMargin=40)
    elements = []
    styles = getSampleStyleSheet()
    
    # ENCABEZADO
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
    
    # INFO ESTUDIANTE
    estilo_b = ParagraphStyle('B', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10)
    estilo_n = ParagraphStyle('N', parent=styles['Normal'], fontName='Helvetica', fontSize=10)
    
    data_info = [
        [Paragraph("ESTUDIANTE", estilo_b), Paragraph(info['nombre'], estilo_n), Paragraph("CARNET", estilo_b), Paragraph(info['carnet'], estilo_n)],
        [Paragraph("CARRERA", estilo_b), Paragraph(info['carrera'], estilo_n), "", ""],
        [Paragraph("AÑO", estilo_b), Paragraph(info['anio'], estilo_n), Paragraph("CICLO", estilo_b), Paragraph(f"{info['ciclo']} - {info['regimen']}", estilo_n)]
    ]
    t_info = Table(data_info, colWidths=[1.1*inch, 2.9*inch, 1.2*inch, 1.5*inch])
    t_info.setStyle(TableStyle([('SPAN', (1,1), (3,1)), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
    elements.append(t_info)
    elements.append(Spacer(1, 20))
    
    # TABLA DE NOTAS
    # Corrección de "Aprobado con Especial" en Estado
    data_notas = [['ASIGNATURA', 'DOCENTE', 'NOTA', 'N. ESP.', 'ESTADO']]
    for item in alumno_data:
        data_notas.append([
            Paragraph(item['asignatura'], ParagraphStyle('Cell', fontSize=9)),
            Paragraph(item['docente'], ParagraphStyle('Cell', fontSize=9)),
            item['nota_final'], item['nota_especial'], item['estado']
        ])
    
    t_notas = Table(data_notas, colWidths=[2.3*inch, 2.0*inch, 0.7*inch, 0.7*inch, 1.0*inch])
    t_notas.setStyle(TableStyle([
        # ENCABEZADO AZUL SOLIDO (Col 0 a Col final de la Fila 0)
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        # FILAS ALTERNAS (Empieza Fila 1)
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    elements.append(t_notas)
    
    elements.append(Spacer(1, 60))
    elements.append(Paragraph("___________________________________", ParagraphStyle('FirmaLine', alignment=TA_CENTER)))
    elements.append(Paragraph("Registro Académico", ParagraphStyle('FirmaText', alignment=TA_CENTER, fontSize=10, fontName='Helvetica-Bold')))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- INTERFAZ DE USUARIO ---
def main():
    
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" style="width: 100%; max-width: 250px; height: auto;">' if logo_base64 else ""
    
    st.markdown(f"""
        <div class="header-container">
            {logo_html}
            <div class="header-subtitle">Consulta de Calificaciones</div>
            <h1 class="univ-title">UNMRMA – CUR-Carazo</h1>
        </div>
    """, unsafe_allow_html=True)

    df = cargar_datos()
    if df is None:
        st.error("⚠️ Error: No se encuentra 'Notas.xlsx'.")
        st.stop()

    if 'searched' not in st.session_state:
        st.session_state.searched = False
    if 'carnet_busqueda' not in st.session_state:
        st.session_state.carnet_busqueda = ""
    if 'selected_student_name' not in st.session_state:
        st.session_state.selected_student_name = None

    carnet_input = st.text_input("Ingrese su Nº de Carnet", placeholder="XX-XXXX-XX", label_visibility="collapsed")
    
    if st.button("CONSULTAR AHORA"):
        st.session_state.searched = True
        st.session_state.carnet_busqueda = carnet_input
        st.session_state.selected_student_name = None 

    if st.session_state.searched:
        carnet = st.session_state.carnet_busqueda.strip()
        
        if not re.match(r"^\d{2}-\d{4}-\d{2}$", carnet):
            st.warning("⚠️ Formato incorrecto. Ejemplo: 25-0022-02")
        else:
            res_raw = df[df['N° Carnet'] == carnet]
            
            if res_raw.empty:
                st.error("❌ No se encontraron registros con ese carnet.")
            else:
                nombres_unicos = res_raw['Nombres y Apellidos'].unique()
                nombre_seleccionado = None
                
                # CASO A: Solo 1 estudiante
                if len(nombres_unicos) == 1:
                    nombre_seleccionado = nombres_unicos[0]
                # CASO B: Múltiples (Duplicados)
                else:
                    if st.session_state.selected_student_name:
                        nombre_seleccionado = st.session_state.selected_student_name
                    else:
                        st.markdown('<h3 class="selection-title">¿Quién eres?</h3>', unsafe_allow_html=True)
                        st.info("Carnet asociado a varios estudiantes. Selecciona tu nombre:")
                        for nombre in nombres_unicos:
                            if st.button(f"👤 {nombre}", key=nombre):
                                st.session_state.selected_student_name = nombre
                                st.rerun()
                        st.stop()

                res = res_raw[res_raw['Nombres y Apellidos'] == nombre_seleccionado]
                p = res.iloc[0]
                
                st.markdown(f"""
                <div class="student-info-card">
                    <div class="student-name">{p['Nombres y Apellidos']}</div>
                    <div class="student-meta">
                        <b>Carnet:</b> {p['N° Carnet']} &nbsp;|&nbsp; <b>Carrera:</b> {p['Carrera']}<br>
                        Año: {p['Año']} &nbsp;|&nbsp; Régimen: {p['Regimen']} &nbsp;|&nbsp; Ciclo: {p['Ciclo']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                datos_pdf = []
                
                for _, row in res.iterrows():
                    nf = str(row['Nota Final']).strip()
                    ne_raw = str(row['Nota de Especial']).strip()
                    ne = ne_raw if ne_raw and ne_raw.lower() != "nan" and ne_raw != "-" else ""
                    
                    # --- LÓGICA DE 3 ESTADOS (COLORES) ---
                    # 1. Aprobado (Verde)
                    # 2. Reprobado (Rojo)
                    # 3. Especial (Azul)
                    
                    estado_app = "APROBADO"
                    estado_pdf = "Aprobado"
                    
                    # Colores por defecto (Aprobado/Verde)
                    color_nota = "#2e7d32" 
                    bg_badge = "#d4edda"
                    color_badge = "#155724"
                    
                    es_sd = (nf.upper() == "SD" or nf.upper() == "NSP")
                    
                    try:
                        val_nf = float(nf)
                        if val_nf < 60:
                            # Evaluamos si califica como Especial (tiene nota numérica en NE)
                            es_especial = (ne and re.match(r"^\d+(\.\d+)?$", ne))
                            
                            if es_especial:
                                # ESTADO: ESPECIAL (AZUL)
                                estado_app = "ESPECIAL"
                                estado_pdf = "Aprobado con Especial"
                                color_nota = "#0056b3" # Azul fuerte
                                bg_badge = "#cce5ff"   # Azul claro fondo
                                color_badge = "#004085" # Azul texto
                            else:
                                # ESTADO: REPROBADO (ROJO)
                                estado_app = "REPROBADO"
                                estado_pdf = "Reprobado"
                                color_nota = "#c62828" 
                                bg_badge = "#f8d7da"
                                color_badge = "#721c24"
                    except:
                        # Si es SD, NSP o texto no numérico
                        estado_app = nf.upper() if len(nf) < 12 else "REPROBADO"
                        estado_pdf = "Reprobado" # En PDF suele ponerse Sin Derecho o Reprobado
                        if es_sd:
                             estado_pdf = "Sin Derecho"
                        
                        color_nota = "#c62828"
                        bg_badge = "#f8d7da"
                        color_badge = "#721c24"

                    # TARJETA HTML (ESTRUCTURA FIJA = 0 ERRORES)
                    st.markdown(f"""
                    <div class="subject-card">
                        <div class="subject-left">
                            <span class="subject-title">{row['Asignatura']}</span>
                            <span class="subject-docente">{row['Docente']}</span>
                        </div>
                        <div class="subject-right">
                            <span class="grade-display" style="color: {color_nota}">{nf}</span>
                            <span class="status-badge" style="background-color: {bg_badge}; color: {color_badge}">{estado_app}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    datos_pdf.append({
                        'asignatura': row['Asignatura'], 'docente': row['Docente'], 
                        'nota_final': nf, 'nota_especial': ne if ne else "-", 
                        'estado': estado_pdf
                    })

                st.write("") 
                pdf_bytes = generar_pdf(datos_pdf, {
                    'nombre': p['Nombres y Apellidos'], 'carnet': p['N° Carnet'], 
                    'carrera': p['Carrera'], 'anio': p['Año'], 'ciclo': p['Ciclo'], 
                    'regimen': p['Regimen']
                })
                
                st.download_button(
                    label="DESCARGAR REPORTE PDF",
                    data=pdf_bytes,
                    file_name=f"Notas_{p['N° Carnet']}.pdf",
                    mime="application/pdf"
                )

if __name__ == "__main__":
    main()
