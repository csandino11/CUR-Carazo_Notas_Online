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
st.set_page_config(page_title="Consulta de Notas UNMRMA", page_icon="🎓", layout="centered")

# --- FUNCIONES DE UTILIDAD PARA IMÁGENES ---

def get_base64_of_bin_file(bin_file):
    """Convierte un archivo binario (imagen) a base64 para usar en CSS/HTML"""
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

# Cargar imágenes
img_fondo_base64 = get_base64_of_bin_file("fondo.jpg")
logo_base64 = get_base64_of_bin_file("logo.png")

# --- ESTILOS CSS PROFESIONALES ---
css_style = f"""
    <style>
    /* 1. IMAGEN DE FONDO */
    .stApp {{
        background-image: url("data:image/jpg;base64,{img_fondo_base64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    /* 2. CONTENEDOR PRINCIPAL (Efecto Cristal/Glassmorphism limpio) */
    .block-container {{
        background-color: rgba(255, 255, 255, 0.97);
        border-radius: 20px;
        padding: 3rem 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        max-width: 800px;
    }}

    /* 3. TIPOGRAFÍA Y COLORES */
    html, body, [class*="css"] {{
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        color: #1a1a1a;
    }}
    
    /* Títulos centrados y elegantes */
    .main-header {{
        text-align: center;
        margin-bottom: 30px;
    }}
    .univ-title {{
        color: #003366;
        font-size: 1.5rem;
        font-weight: 800;
        margin: 10px 0 5px 0;
        line-height: 1.3;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .univ-subtitle {{
        color: #555;
        font-size: 1.1rem;
        font-weight: 500;
        margin: 0;
    }}

    /* 4. INPUT DE CARNET */
    .stTextInput > div > div > input {{
        text-align: center;
        font-size: 1.5rem;
        padding: 12px;
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        transition: border-color 0.3s;
        background-color: #fff !important;
        color: #333 !important;
    }}
    .stTextInput > div > div > input:focus {{
        border-color: #58b24c;
        box-shadow: 0 0 0 3px rgba(88, 178, 76, 0.2);
    }}

    /* 5. BOTÓN CONSULTAR */
    div[data-testid="stFormSubmitButton"] > button {{
        background-color: #58b24c !important;
        color: white !important;
        border: none;
        font-weight: 700;
        font-size: 1.1rem;
        padding: 0.8rem 2rem;
        border-radius: 12px;
        width: 100%;
        margin-top: 10px;
        box-shadow: 0 4px 6px rgba(88, 178, 76, 0.3);
        transition: all 0.2s ease;
    }}
    div[data-testid="stFormSubmitButton"] > button:hover {{
        background-color: #46963b !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(88, 178, 76, 0.4);
    }}

    /* 6. TARJETA DE ESTUDIANTE */
    .student-card {{
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border-left: 6px solid #003366;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 30px;
    }}
    .student-name {{
        color: #003366;
        margin: 0 0 15px 0;
        font-size: 1.6rem;
        font-weight: 700;
    }}

    /* 7. RESULTADOS (FILAS) */
    .result-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px 10px;
        border-bottom: 1px solid #eee;
        transition: background-color 0.2s;
    }}
    .result-row:hover {{
        background-color: #f9fbfd;
    }}
    
    /* Ocultar elementos de Streamlit */
    #MainMenu, footer, header {{visibility: hidden;}}
    .stDeployButton {{display:none;}}
    </style>
"""
st.markdown(css_style, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    if not os.path.exists("Notas.xlsx"): return None
    df = pd.read_excel("Notas.xlsx", sheet_name="Datos", dtype=str)
    df.columns = df.columns.str.strip()
    return df.fillna("-")

# --- GENERACIÓN PDF (Backend) ---
def generar_pdf(alumno_data, info):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, topMargin=40, bottomMargin=40)
    elements = []
    styles = getSampleStyleSheet()
    
    # ENCABEZADO PDF
    try:
        logo_path = "logo.png"
        if os.path.exists(logo_path):
            img_pil = PILImage.open(logo_path)
            # Calcular aspecto exacto
            orig_w, orig_h = img_pil.size
            aspect = orig_h / float(orig_w)
            
            # Ancho del logo en PDF
            pdf_logo_w = 1.6 * inch
            pdf_logo_h = pdf_logo_w * aspect
            
            logo = RLImage(logo_path, width=pdf_logo_w, height=pdf_logo_h)
            
            # Texto Encabezado
            txt_univ = """<font size=12><b>UNIVERSIDAD NACIONAL MULTIDISCIPLINARIA<br/>RICARDO MORALES AVILÉS</b></font>"""
            p_univ = Paragraph(txt_univ, ParagraphStyle('T', parent=styles['Heading1'], alignment=TA_CENTER, leading=16, textColor=colors.black))
            
            data_header = [[logo, p_univ]]
            t_header = Table(data_header, colWidths=[2*inch, 4.5*inch])
            t_header.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
            elements.append(t_header)
    except:
        elements.append(Paragraph("REPORTE DE NOTAS", styles['Heading1']))

    elements.append(Spacer(1, 15))
    elements.append(Paragraph("<b>ACTA DE CALIFICACIONES</b>", ParagraphStyle('S', alignment=TA_CENTER, fontSize=14)))
    elements.append(Spacer(1, 25))
    
    # DATOS ESTUDIANTE
    estilo_negrita = ParagraphStyle('B', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10)
    estilo_normal = ParagraphStyle('N', parent=styles['Normal'], fontName='Helvetica', fontSize=10)
    
    data_info = [
        [Paragraph("ESTUDIANTE:", estilo_negrita), Paragraph(info['nombre'], estilo_normal), Paragraph("CARNET:", estilo_negrita), Paragraph(info['carnet'], estilo_normal)],
        [Paragraph("CARRERA:", estilo_negrita), Paragraph(info['carrera'], estilo_normal), "", ""],
        [Paragraph("AÑO:", estilo_negrita), Paragraph(info['anio'], estilo_normal), Paragraph("CICLO/RÉGIMEN:", estilo_negrita), Paragraph(f"{info['ciclo']} - {info['regimen']}", estilo_normal)]
    ]
    t_info = Table(data_info, colWidths=[1.1*inch, 2.9*inch, 1.2*inch, 1.5*inch])
    t_info.setStyle(TableStyle([('SPAN', (1,1), (3,1)), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
    elements.append(t_info)
    elements.append(Spacer(1, 20))
    
    # TABLA NOTAS
    data_notas = [['ASIGNATURA', 'DOCENTE', 'NOTA', 'N. ESP.', 'ESTADO']]
    for item in alumno_data:
        data_notas.append([
            Paragraph(item['asignatura'], ParagraphStyle('Cell', fontSize=9, leading=10)),
            Paragraph(item['docente'], ParagraphStyle('Cell', fontSize=9, leading=10)),
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
    
    # PIE
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("_"*30, ParagraphStyle('C', alignment=TA_CENTER)))
    elements.append(Paragraph("Registro Académico", ParagraphStyle('C', alignment=TA_CENTER, fontSize=9)))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- INTERFAZ DE USUARIO ---
def main():
    
    # 1. ENCABEZADO HTML CENTRADO (Solución a la alineación y calidad de imagen)
    # Usamos HTML directo para un control perfecto
    if logo_base64:
        st.markdown(f"""
            <div class="main-header">
                <img src="data:image/png;base64,{logo_base64}" style="width: 160px; height: auto; margin-bottom: 15px;">
                <h1 class="univ-title">UNIVERSIDAD NACIONAL MULTIDISCIPLINARIA<br>RICARDO MORALES AVILÉS</h1>
                <h3 class="univ-subtitle">SISTEMA DE CONSULTA DE CALIFICACIONES</h3>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.error("⚠️ Faltan archivos: Asegúrate de subir 'logo.png' y 'fondo.jpg'.")

    # 2. CARGA
    df = cargar_datos()
    if df is None:
        st.warning("Esperando base de datos...")
        st.stop()

    # 3. FORMULARIO
    st.write("") # Espaciador
    with st.form(key="search_form"):
        carnet_input = st.text_input("Ingrese su Nº de Carnet", placeholder="XX-XXXX-XX")
        submit_button = st.form_submit_button(label="CONSULTAR NOTAS")

    # 4. LÓGICA
    if submit_button:
        carnet = carnet_input.strip()
        if not re.match(r"^\d{2}-\d{4}-\d{2}$", carnet):
            st.warning("⚠️ Formato incorrecto. Use el formato: XX-XXXX-XX")
        else:
            res = df[df['N° Carnet'] == carnet]
            if res.empty:
                st.error("❌ No se encontraron registros.")
            else:
                p = res.iloc[0]
                
                # TARJETA DATOS (HTML + CSS)
                st.markdown(f"""
                <div class="student-card">
                    <h2 class="student-name">{p['Nombres y Apellidos']}</h2>
                    <div style="display: flex; flex-wrap: wrap; gap: 20px; font-size: 1rem; color: #444;">
                        <div><b>🆔 Carnet:</b> {p['N° Carnet']}</div>
                        <div><b>📚 Carrera:</b> {p['Carrera']}</div>
                    </div>
                    <hr style="margin: 15px 0; border: 0; border-top: 1px solid #ddd;">
                    <div style="display: flex; flex-wrap: wrap; gap: 15px; font-size: 0.9rem; color: #666;">
                        <span style="background: #eef2f5; padding: 5px 10px; border-radius: 5px;">📅 Año: <b>{p['Año']}</b></span>
                        <span style="background: #eef2f5; padding: 5px 10px; border-radius: 5px;">🔄 Ciclo: <b>{p['Ciclo']}</b></span>
                        <span style="background: #eef2f5; padding: 5px 10px; border-radius: 5px;">📋 Régimen: <b>{p['Regimen']}</b></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # RESULTADOS
                datos_pdf = []
                
                # Encabezados visuales
                st.markdown("""
                <div style="display: grid; grid-template-columns: 3fr 2fr 1fr 1fr 1fr; font-weight: bold; color: #003366; padding: 0 10px 10px 10px; border-bottom: 2px solid #003366; font-size: 0.9rem;">
                    <div>ASIGNATURA</div><div>DOCENTE</div><div style="text-align:center">NOTA</div><div style="text-align:center">N.ESP</div><div style="text-align:center">ESTADO</div>
                </div>
                """, unsafe_allow_html=True)

                for _, row in res.iterrows():
                    nf, ne = str(row['Nota Final']).strip(), str(row['Nota de Especial']).strip()
                    estado, color, bg = "Aprobado", "#155724", "#d4edda"
                    mostrar_ne = "-"
                    
                    es_sd = (nf.upper() == "SD")
                    try:
                        val = float(nf)
                        if val < 60:
                            estado, color, bg = "Reprobado", "#721c24", "#f8d7da"
                            if ne and ne != "-" and not es_sd: mostrar_ne = ne
                    except:
                        if es_sd: estado, color, bg = "Sin Derecho", "#721c24", "#f8d7da"

                    # Fila HTML Limpia
                    st.markdown(f"""
                    <div class="result-row" style="display: grid; grid-template-columns: 3fr 2fr 1fr 1fr 1fr; font-size: 0.9rem;">
                        <div style="font-weight: 500;">{row['Asignatura']}</div>
                        <div style="color: #666; font-size: 0.85rem;">{row['Docente']}</div>
                        <div style="text-align:center; font-weight:bold; color: #333;">{nf}</div>
                        <div style="text-align:center; color: #666;">{mostrar_ne}</div>
                        <div style="text-align:center;"><span style="background-color:{bg}; color:{color}; padding: 3px 8px; border-radius: 10px; font-size: 0.75rem; font-weight: bold;">{estado}</span></div>
                    </div>
                    """, unsafe_allow_html=True)

                    datos_pdf.append({'asignatura': row['Asignatura'], 'docente': row['Docente'], 'nota_final': nf, 'nota_especial': mostrar_ne, 'estado': estado})

                # PDF
                st.write("")
                pdf = generar_pdf(datos_pdf, {'nombre': p['Nombres y Apellidos'], 'carnet': p['N° Carnet'], 'carrera': p['Carrera'], 'anio': p['Año'], 'ciclo': p['Ciclo'], 'regimen': p['Regimen']})
                
                col_btn, _ = st.columns([1, 2])
                with col_btn:
                    st.download_button("📄 DESCARGAR REPORTE (PDF)", data=pdf, file_name=f"Notas_{p['N° Carnet']}.pdf", mime="application/pdf", type="secondary")

if __name__ == "__main__":
    main()
