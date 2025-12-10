import streamlit as st
import pandas as pd
import re
import base64
import os
from io import BytesIO
from PIL import Image as PILImage # Para manejar la relación de aspecto del logo
from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Consulta de Notas UNMRMA", page_icon="🎓", layout="centered")

# --- FUNCIÓN PARA IMAGEN DE FONDO ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

img_fondo_base64 = get_base64_of_bin_file("fondo.jpg")

# --- ESTILOS CSS BLINDADOS (ANTI-DARK MODE) ---
# Forzamos colores oscuros en los textos para que se vean bien sobre el fondo blanco
css_style = f"""
    <style>
    /* 1. Fondo de pantalla */
    .stApp {{
        background-image: url("data:image/jpg;base64,{img_fondo_base64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    /* 2. Contenedor Principal Blanco */
    .block-container {{
        background-color: rgba(255, 255, 255, 0.95); /* Más opaco para evitar problemas de contraste */
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        margin-top: 20px;
    }}

    /* 3. FORZAR TEXTO OSCURO (Ignorar Dark Mode del navegador) */
    html, body, [class*="css"] {{
        color: #2c3e50;
    }}
    .stMarkdown, .stText, h1, h2, h3, h4, p, li, label, div {{
        color: #222222 !important;
    }}
    
    /* Input de Texto */
    .stTextInput > div > div > input {{
        text-align: center;
        font-size: 1.3rem;
        font-weight: bold;
        color: #000000 !important;
        background-color: #ffffff !important;
        border: 2px solid #ddd;
    }}

    /* Botón Verde */
    div[data-testid="stFormSubmitButton"] > button {{
        background-color: #58b24c !important;
        color: white !important;
        border: none;
        font-weight: bold;
        transition: transform 0.2s;
    }}
    div[data-testid="stFormSubmitButton"] > button:hover {{
        transform: scale(1.03);
    }}

    /* Estilo de Tarjetas de Notas */
    .nota-card {{
        background-color: #f8f9fa;
        border-left: 5px solid #003366;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }}
    
    /* Ocultar elementos extra */
    #MainMenu, footer, header {{visibility: hidden;}}
    </style>
"""
st.markdown(css_style, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    try:
        if not os.path.exists("Notas.xlsx"):
            return None
        df = pd.read_excel("Notas.xlsx", sheet_name="Datos", dtype=str)
        df.columns = df.columns.str.strip()
        df = df.fillna("-")
        return df
    except Exception as e:
        return None

# --- GENERACIÓN PDF MEJORADA ---
def generar_pdf(alumno_data, info):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    # 1. LOGO Y ENCABEZADO CORREGIDOS
    try:
        logo_path = "logo.png"
        if os.path.exists(logo_path):
            # Usar Pillow para obtener dimensiones originales y evitar distorsión
            img_pil = PILImage.open(logo_path)
            orig_w, orig_h = img_pil.size
            aspect = orig_h / float(orig_w)
            
            # Definir ancho fijo (ej. 1.8 pulgadas) y calcular alto proporcional
            # new_w = 1.8 * inch
            # new_h = new_w * aspect
            
            logo = RLImage(logo_path)
            
            # Nombre Completo en 2 líneas
            txt_univ = """<font size=12><b>UNMRMA – CUR-Carazo</b></font>"""
            
            p_univ = Paragraph(txt_univ, ParagraphStyle('Titulo', parent=styles['Heading1'], alignment=TA_CENTER, leading=16))
            
            # Tabla de cabecera para alinear Logo e Institución
            data_header = [[logo, p_univ]]
            t_header = Table(data_header, colWidths=[2*inch, 4.5*inch])
            t_header.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            elements.append(t_header)
        else:
            elements.append(Paragraph("REPORTE DE NOTAS", styles['Heading1']))
    except Exception as e:
        elements.append(Paragraph(f"Error imagen: {e}", styles['Normal']))

    elements.append(Spacer(1, 15))
    elements.append(Paragraph("<b>ACTA DE CALIFICACIONES</b>", ParagraphStyle('Sub', parent=styles['Normal'], alignment=TA_CENTER, fontSize=14)))
    elements.append(Spacer(1, 20))
    
    # 2. DATOS DEL ESTUDIANTE (Con Año, Ciclo y Régimen)
    # Usamos una tabla invisible para alinear perfectamente los datos
    
    style_label = ParagraphStyle('L', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10)
    style_val = ParagraphStyle('V', parent=styles['Normal'], fontName='Helvetica', fontSize=10)
    
    # Fila 1: Nombre y Carnet
    row1 = [
        Paragraph("<b>ESTUDIANTE:</b>", style_label), Paragraph(info['nombre'], style_val),
        Paragraph("<b>CARNET:</b>", style_label), Paragraph(info['carnet'], style_val)
    ]
    # Fila 2: Carrera
    row2 = [Paragraph("<b>CARRERA:</b>", style_label), Paragraph(info['carrera'], style_val), "", ""]
    
    # Fila 3: Año, Ciclo, Regimen (Distribuidos)
    # Concatenamos etiquetas y valores para eficiencia en una sola linea visual o tabla
    row3 = [
        Paragraph("<b>AÑO:</b> " + info['anio'], style_val),
        Paragraph("<b>CICLO:</b> " + info['ciclo'], style_val),
        Paragraph("<b>RÉGIMEN:</b> " + info['regimen'], style_val),
        ""
    ]

    t_info = Table([row1, row2, row3], colWidths=[1.2*inch, 2.5*inch, 1.2*inch, 2*inch])
    t_info.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('SPAN', (1,1), (3,1)), # Carrera ocupa más espacio
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 20))
    
    # 3. TABLA DE NOTAS
    data = [['ASIGNATURA', 'DOCENTE', 'NOTA\nFINAL', 'NOTA\nESPECIAL', 'ESTADO']]
    
    for item in alumno_data:
        data.append([
            Paragraph(item['asignatura'], styles['Normal']), # Paragraph permite saltos de linea si es muy largo
            Paragraph(item['docente'], styles['Normal']),
            item['nota_final'],
            item['nota_especial'],
            item['estado']
        ])
        
    t_notas = Table(data, colWidths=[2.2*inch, 2.0*inch, 0.8*inch, 0.8*inch, 1.2*inch])
    t_notas.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,1), (-1,-1), 8),
    ]))
    elements.append(t_notas)
    
    # Pie
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("_______________________________", ParagraphStyle('Firma', alignment=TA_CENTER)))
    elements.append(Paragraph("Registro Académico", ParagraphStyle('FirmaT', alignment=TA_CENTER, fontSize=9)))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- INTERFAZ PRINCIPAL ---
def main():
    # Encabezado (Logo Izq, Texto Der)
    col1, col2 = st.columns([1, 3])
    with col1:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=150)
        else:
            st.warning("⚠️ Cargar logo.png")
    
    with col2:
        st.markdown("""
        <div style="padding-top: 10px;">
            <h2 style="margin:0; color:#003366 !important;">Consulta de Calificaciones</h2>
            <h5 style="margin:0; color:#555 !important;">Universidad Nacional Multidisciplinaria</h5>
            <h5 style="margin:0; color:#555 !important;">Ricardo Morales Avilés</h5>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

    df = cargar_datos()
    if df is None:
        st.error("Error: No se encontró 'Notas.xlsx'.")
        st.stop()

    # Formulario
    with st.form(key="search_form"):
        st.markdown("##### 🔍 Ingrese número de carnet:")
        carnet_input = st.text_input("Carnet", placeholder="XX-XXXX-XX", label_visibility="collapsed")
        submit_button = st.form_submit_button(label="CONSULTAR AHORA")

    if submit_button:
        carnet = carnet_input.strip()
        if not re.match(r"^\d{2}-\d{4}-\d{2}$", carnet):
            st.warning("⚠️ Formato inválido. Use: XX-XXXX-XX")
        else:
            res = df[df['N° Carnet'] == carnet]
            if res.empty:
                st.error("❌ No encontrado.")
            else:
                p = res.iloc[0]
                
                # DATOS ESTUDIANTE
                st.markdown(f"""
                <div style="background-color: #e3f2fd; padding: 15px; border-radius: 10px; border: 1px solid #90caf9; margin-bottom: 20px;">
                    <h3 style="color: #003366 !important; margin:0;">{p['Nombres y Apellidos']}</h3>
                    <p style="margin:5px 0 0 0;"><b>Carnet:</b> {p['N° Carnet']} &nbsp;|&nbsp; <b>Carrera:</b> {p['Carrera']}</p>
                    <p style="margin:0; font-size: 0.9em; color: #666 !important;">
                        <b>Año:</b> {p['Año']} &nbsp;|&nbsp; <b>Ciclo:</b> {p['Ciclo']} &nbsp;|&nbsp; <b>Régimen:</b> {p['Regimen']}
                    </p>
                </div>
                """, unsafe_allow_html=True)

                # PREPARAR DATOS
                datos_pdf = []
                
                # ENCABEZADOS DE COLUMNAS (Visualización Pantalla)
                cols = st.columns([3, 2, 1, 1, 1])
                cols[0].markdown("**Asignatura**")
                cols[1].markdown("**Docente**")
                cols[2].markdown("**N. Final**")
                cols[3].markdown("**N. Esp.**")
                cols[4].markdown("**Estado**")
                st.markdown("<hr style='margin: 5px 0'>", unsafe_allow_html=True)

                for _, row in res.iterrows():
                    # Procesar valores
                    nf = str(row['Nota Final']).strip()
                    ne = str(row['Nota de Especial']).strip()
                    asig = row['Asignatura']
                    doc = row['Docente']
                    
                    estado = "Aprobado"
                    color_nota = "black"
                    bg_estado = "#d4edda" # Verde claro
                    txt_estado = "#155724" # Verde oscuro
                    mostrar_ne = "-"

                    es_sd = (nf.upper() == "SD")
                    
                    try:
                        val_nf = float(nf)
                        if val_nf < 60:
                            estado = "Reprobado"
                            color_nota = "#dc3545" # Rojo
                            bg_estado = "#f8d7da"
                            txt_estado = "#721c24"
                            if ne and ne != "-" and not es_sd:
                                mostrar_ne = ne
                    except:
                        if es_sd:
                            estado = "Sin Derecho"
                            color_nota = "#dc3545"
                            bg_estado = "#f8d7da"
                            txt_estado = "#721c24"

                    # VISUALIZACIÓN EN PANTALLA (SIN TABLA HTML)
                    c = st.columns([3, 2, 1, 1, 1])
                    c[0].write(asig)
                    c[1].write(doc)
                    c[2].markdown(f"<span style='color:{color_nota}; font-weight:bold'>{nf}</span>", unsafe_allow_html=True)
                    c[3].write(mostrar_ne)
                    c[4].markdown(f"<span style='background-color:{bg_estado}; color:{txt_estado}; padding: 2px 6px; border-radius:4px; font-size:0.8em'>{estado}</span>", unsafe_allow_html=True)
                    
                    st.markdown("<div style='border-bottom: 1px solid #eee; margin-bottom: 8px'></div>", unsafe_allow_html=True)

                    datos_pdf.append({
                        'asignatura': asig, 'docente': doc,
                        'nota_final': nf, 'nota_especial': mostrar_ne, 'estado': estado
                    })

                # BOTÓN PDF
                st.write("")
                pdf_data = generar_pdf(datos_pdf, {
                    'nombre': p['Nombres y Apellidos'],
                    'carnet': p['N° Carnet'],
                    'carrera': p['Carrera'],
                    'anio': p['Año'],
                    'ciclo': p['Ciclo'],
                    'regimen': p['Regimen']
                })
                
                st.download_button(
                    "⬇️ Descargar Reporte PDF",
                    data=pdf_data,
                    file_name=f"Notas_{p['N° Carnet']}.pdf",
                    mime="application/pdf",
                    type="primary"
                )

if __name__ == "__main__":
    main()

