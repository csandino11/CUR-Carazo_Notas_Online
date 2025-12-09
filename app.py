import streamlit as st
import pandas as pd
import re
import base64
import os
from io import BytesIO
from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Consulta de Notas UNM", page_icon="🎓", layout="centered")

# --- FUNCIÓN PARA IMAGEN DE FONDO ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

# Cargar imagen de fondo (Asegúrate de tener 'fondo.jpg' en la carpeta)
img_fondo_base64 = get_base64_of_bin_file("fondo.jpg")

# --- ESTILOS CSS ---
css_style = f"""
    <style>
    /* 1. Fondo de pantalla con imagen */
    .stApp {{
        background-image: url("data:image/jpg;base64,{img_fondo_base64}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}

    /* 2. Contenedor principal blanco semi-transparente para legibilidad */
    .block-container {{
        background-color: rgba(255, 255, 255, 0.92);
        padding: 3rem;
        border-radius: 15px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        backdrop-filter: blur(4px);
        margin-top: 20px;
    }}

    /* 3. Input de texto centrado y grande */
    .stTextInput > div > div > input {{
        text-align: center;
        font-size: 1.4rem;
        letter-spacing: 3px;
        color: #333;
        font-weight: bold;
    }}

    /* 4. BOTÓN VERDE (#58b24c) */
    div[data-testid="stFormSubmitButton"] > button {{
        background-color: #58b24c !important;
        color: white !important;
        border: none;
        width: 100%;
        font-size: 1.2rem;
        padding: 0.5rem;
        border-radius: 8px;
        transition: all 0.3s ease;
    }}
    div[data-testid="stFormSubmitButton"] > button:hover {{
        background-color: #46963b !important;
        transform: scale(1.02);
    }}

    /* 5. Tabla Elegante */
    .styled-table {{
        border-collapse: collapse;
        margin: 25px 0;
        font-size: 0.95em;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        min-width: 100%;
        border-radius: 8px 8px 0 0;
        overflow: hidden;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
    }}
    .styled-table thead tr {{
        background-color: #003366;
        color: #ffffff;
        text-align: left;
    }}
    .styled-table th, .styled-table td {{
        padding: 12px 15px;
    }}
    .styled-table tbody tr {{
        border-bottom: 1px solid #dddddd;
        color: #333;
    }}
    .styled-table tbody tr:nth-of-type(even) {{
        background-color: #f3f3f3;
    }}
    .styled-table tbody tr:last-of-type {{
        border-bottom: 2px solid #58b24c;
    }}
    
    /* Textos */
    h1, h2, h3, p, span, div {{
        color: #2c3e50;
    }}
    
    /* Ocultar elementos de Streamlit */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
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
        df = df.fillna("-") # Rellenar vacíos con guion para evitar errores
        return df
    except Exception as e:
        st.error(f"Error leyendo la base de datos: {e}")
        return None

# --- GENERACIÓN PDF ---
def generar_pdf(alumno_data, info_estudiante):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, topMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    # 1. Encabezado
    try:
        if os.path.exists("logo.png"):
            logo = Image('logo.png', width=1.2*inch, height=1.2*inch)
            titulo_texto = "<b>UNIVERSIDAD NACIONAL<br/>ACTA DE CALIFICACIONES</b>"
            titulo = Paragraph(titulo_texto, styles['Heading1'])
            t_header = Table([[logo, titulo]], colWidths=[1.5*inch, 4.5*inch])
            t_header.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
            elements.append(t_header)
        else:
            elements.append(Paragraph("<b>REPORTE DE NOTAS</b>", styles['Heading1']))
    except:
        elements.append(Paragraph("REPORTE DE NOTAS", styles['Heading1']))

    elements.append(Spacer(1, 20))
    
    # 2. Datos Estudiante
    estilo_datos = ParagraphStyle('Datos', parent=styles['Normal'], fontSize=11, leading=14)
    info_text = f"""
    <b>ESTUDIANTE:</b> {info_estudiante['nombre']}<br/>
    <b>CARNET:</b> {info_estudiante['carnet']}<br/>
    <b>CARRERA:</b> {info_estudiante['carrera']}<br/>
    <b>PERIODO:</b> {info_estudiante['anio']} - {info_estudiante['ciclo']}
    """
    elements.append(Paragraph(info_text, estilo_datos))
    elements.append(Spacer(1, 20))
    
    # 3. Tabla
    data = [['ASIGNATURA', 'DOCENTE', 'NOTA FINAL', 'N. ESPECIAL', 'ESTADO']]
    for item in alumno_data:
        data.append([item['asignatura'], item['docente'], item['nota_final'], item['nota_especial'], item['estado']])
        
    t = Table(data, colWidths=[2.5*inch, 2.0*inch, 0.9*inch, 0.9*inch, 1*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 1, colors.grey),
        ('FONTSIZE', (0,1), (-1,-1), 8),
    ]))
    elements.append(t)
    
    # Pie
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("Documento generado automáticamente por el Sistema de Consultas.", styles['Italic']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- INTERFAZ PRINCIPAL ---
def main():
    # Encabezado con columnas ajustadas para logo grande
    col_logo, col_titulo = st.columns([1, 2])
    
    with col_logo:
        # Logo más grande y centrado
        if os.path.exists("logo.png"):
            st.image("logo.png", width=180) 
        else:
            st.warning("Falta logo.png")
            
    with col_titulo:
        # Espaciado vertical para centrar el texto con el logo
        st.write("") 
        st.markdown("<h1 style='text-align: left; color: #003366; margin-bottom: 0;'>Consulta de Notas</h1>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: left; color: #555; margin-top: 0;'>Centro Universitario Regional Carazo</h4>", unsafe_allow_html=True)

    st.markdown("---")

    df = cargar_datos()
    if df is None:
        st.error("No se encontró 'Notas.xlsx'. Por favor verifica el archivo.")
        st.stop()

    # FORMULARIO DE BÚSQUEDA (Permite usar ENTER)
    with st.form(key="search_form"):
        st.markdown("### 🔍 Ingrese sus credenciales")
        carnet_input = st.text_input(
            "Número de Carnet", 
            placeholder="XX-XXXX-XX",
            help="Escriba su carnet completo con guiones."
        )
        
        # Botón de envío (Verde gracias al CSS)
        submit_button = st.form_submit_button(label="CONSULTAR NOTAS")

    # Lógica de búsqueda
    if submit_button:
        carnet_limpio = carnet_input.strip()
        patron_carnet = r"^\d{2}-\d{4}-\d{2}$"
        
        if not re.match(patron_carnet, carnet_limpio):
            st.warning("⚠️ Formato inválido. Asegúrese de escribir el carnet correctamente: XX-XXXX-XX")
        else:
            resultados = df[df['N° Carnet'] == carnet_limpio]
            
            if resultados.empty:
                st.error(f"❌ No se encontraron registros para el carnet: {carnet_limpio}")
            else:
                try:
                    primer = resultados.iloc[0]
                    # Tarjeta de Info Estudiante
                    st.markdown(f"""
                    <div style="background-color: white; border-left: 6px solid #58b24c; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px;">
                        <h2 style="color: #003366; margin:0;">{primer['Nombres y Apellidos']}</h2>
                        <hr style="margin: 10px 0;">
                        <div style="display: flex; justify-content: space-between; font-size: 1.1em;">
                            <span>🎓 <b>Carnet:</b> {primer['N° Carnet']}</span>
                            <span>📚 <b>Carrera:</b> {primer['Carrera']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Preparar tabla
                    filas_html = ""
                    datos_pdf = []
                    
                    for _, row in resultados.iterrows():
                        asignatura = str(row['Asignatura'])
                        docente = str(row['Docente'])
                        nf = str(row['Nota Final']).strip()
                        ne = str(row['Nota de Especial']).strip()
                        
                        estado = "Aprobado"
                        mostrar_ne = "-"
                        clase_estado = "color: #333;" # Color normal

                        # Lógica Notas
                        es_sd = (nf.upper() == "SD")
                        try:
                            val_nf = float(nf)
                            if val_nf < 60:
                                estado = "Reprobado"
                                clase_estado = "color: #d9534f; font-weight: bold;" # Rojo
                                if ne and ne != "-" and not es_sd:
                                    mostrar_ne = ne
                        except:
                            if es_sd:
                                estado = "Sin Derecho"
                                clase_estado = "color: #d9534f; font-weight: bold;"
                            else:
                                estado = "-"

                        filas_html += f"""
                        <tr>
                            <td>{asignatura}</td>
                            <td>{docente}</td>
                            <td style="font-weight: bold; text-align: center;">{nf}</td>
                            <td style="text-align: center;">{mostrar_ne}</td>
                            <td style="{clase_estado}">{estado}</td>
                        </tr>
                        """
                        datos_pdf.append({
                            'asignatura': asignatura, 'docente': docente,
                            'nota_final': nf, 'nota_especial': mostrar_ne, 'estado': estado
                        })
                    
                    # Pintar Tabla
                    tabla_html = f"""
                    <table class="styled-table">
                        <thead>
                            <tr>
                                <th>Asignatura</th>
                                <th>Docente</th>
                                <th style="text-align: center;">Nota Final</th>
                                <th style="text-align: center;">Nota Esp.</th>
                                <th>Estado</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filas_html}
                        </tbody>
                    </table>
                    """
                    st.markdown(tabla_html, unsafe_allow_html=True)
                    
                    # Botón PDF
                    st.markdown("<br>", unsafe_allow_html=True)
                    col_izq, col_der = st.columns([3, 2])
                    with col_der:
                        pdf_data = generar_pdf(datos_pdf, {
                            'nombre': primer['Nombres y Apellidos'],
                            'carnet': primer['N° Carnet'],
                            'carrera': primer['Carrera'],
                            'anio': primer['Año'],
                            'ciclo': primer['Ciclo']
                        })
                        st.download_button(
                            label="⬇️ DESCARGAR REPORTE (PDF)",
                            data=pdf_data,
                            file_name=f"Notas_{primer['N° Carnet']}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

                except Exception as e:
                    st.error(f"Ocurrió un error al procesar los datos: {e}")

if __name__ == "__main__":
    main()
