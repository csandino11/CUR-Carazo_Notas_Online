import streamlit as st
import pandas as pd
import re
from io import BytesIO
from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Consulta de Notas UNM", page_icon="🎓", layout="centered")

# --- ESTILOS CSS PERSONALIZADOS ---
# Aquí definimos el fondo azul (#149ed5) y el estilo de la tabla
st.markdown("""
    <style>
    /* Fondo General de la App */
    .stApp {
        background-color: #149ed5;
    }
    
    /* Contenedor blanco para el contenido principal para dar contraste */
    .main-container {
        background-color: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Estilo de los inputs y botones */
    .stTextInput > div > div > input {
        text-align: center;
        font-size: 1.2rem;
        letter-spacing: 2px;
    }
    
    /* Estilo para la Tabla de Resultados (HTML) */
    .styled-table {
        border-collapse: collapse;
        margin: 25px 0;
        font-size: 0.9em;
        font-family: sans-serif;
        min-width: 100%;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
        background-color: white;
        border-radius: 8px; 
        overflow: hidden;
    }
    .styled-table thead tr {
        background-color: #003366; /* Azul oscuro institucional */
        color: #ffffff;
        text-align: left;
    }
    .styled-table th, .styled-table td {
        padding: 12px 15px;
    }
    .styled-table tbody tr {
        border-bottom: 1px solid #dddddd;
    }
    .styled-table tbody tr:nth-of-type(even) {
        background-color: #f3f3f3;
    }
    .styled-table tbody tr:last-of-type {
        border-bottom: 2px solid #009879;
    }
    .styled-table tbody tr.active-row {
        font-weight: bold;
        color: #009879;
    }
    
    /* Ajustes de textos generales */
    h1, h2, h3, p, label {
        color: #000000 !important; /* Forzar texto negro para contraste */
    }
    
    /* Ocultar elementos propios de Streamlit que ensucian la vista */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE CARGA Y PDF ---

@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel("Notas.xlsx", sheet_name="Datos", dtype=str)
        df.columns = df.columns.str.strip()
        df = df.fillna("")
        return df
    except FileNotFoundError:
        return None

def generar_pdf(alumno_data, info_estudiante):
    """Genera un PDF en memoria usando ReportLab"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    elements = []
    
    styles = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle('Titulo', parent=styles['Heading1'], alignment=1, fontSize=16, spaceAfter=20)
    estilo_normal = styles['Normal']
    
    # 1. Encabezado con Logo (si existe)
    try:
        # Ajusta width y height según tu logo real
        logo = Image('logo.png', width=1.5*inch, height=1.5*inch) 
        # Título de la Universidad
        titulo = Paragraph("<b>UNIVERSIDAD NACIONAL<br/>ACTA DE CALIFICACIONES</b>", estilo_titulo)
        
        # Tabla invisible para alinear logo y título
        data_header = [[logo, titulo]]
        t_header = Table(data_header, colWidths=[2*inch, 4*inch])
        t_header.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(t_header)
    except:
        # Si no hay logo, solo pone el texto
        elements.append(Paragraph("<b>REPORTE DE NOTAS</b>", estilo_titulo))

    elements.append(Spacer(1, 20))
    
    # 2. Información del Estudiante
    info_text = f"""
    <b>Estudiante:</b> {info_estudiante['nombre']}<br/>
    <b>Carnet:</b> {info_estudiante['carnet']}<br/>
    <b>Carrera:</b> {info_estudiante['carrera']}<br/>
    <b>Año/Ciclo:</b> {info_estudiante['anio']} - {info_estudiante['ciclo']}
    """
    elements.append(Paragraph(info_text, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # 3. Tabla de Notas
    # Encabezados
    data = [['Asignatura', 'Docente', 'Nota Final', 'Nota Especial', 'Estado']]
    
    # Rellenar filas
    for item in alumno_data:
        data.append([
            item['asignatura'],
            item['docente'],
            item['nota_final'],
            item['nota_especial'],
            item['estado']
        ])
        
    # Crear Tabla ReportLab
    t = Table(data, colWidths=[2.5*inch, 2*inch, 0.8*inch, 0.8*inch, 1*inch])
    
    # Estilo de la tabla PDF
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")), # Encabezado azul
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    
    elements.append(t)
    
    # Pie de página
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("<i>Este documento es un reporte generado automáticamente.</i>", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- LÓGICA PRINCIPAL ---

def main():
    # Contenedor blanco simulado
    with st.container():
        # Layout de encabezado: Logo a la izquierda, Título al centro/derecha
        col1, col2 = st.columns([1, 4])
        with col1:
            try:
                st.image("logo.png", width=100)
            except:
                st.write("🏛️") # Placeholder si no encuentra la imagen
        with col2:
            st.title("Sistema de Consulta de Notas")
            st.markdown("**Centro Universitario Regional Carazo**")

        st.markdown("---")
        
        # Cargar datos
        df = cargar_datos()
        if df is None:
            st.error("⚠️ No se encontró la base de datos de notas. Contacte al administrador.")
            st.stop()
            
        # Formulario de búsqueda
        st.subheader("Ingrese sus credenciales:")
        
        col_search, col_btn = st.columns([3, 1])
        with col_search:
            carnet_input = st.text_input(
                "N° de Carnet", 
                placeholder="Ej: 25-0022-02", 
                help="Formato requerido: XX-XXXX-XX"
            )
        with col_btn:
            st.write("") # Espacio para alinear
            st.write("") 
            buscar = st.button("CONSULTAR NOTAS", type="primary")

        # Validación y Búsqueda
        if buscar:
            carnet_limpio = carnet_input.strip()
            # Regex: 2 dígitos, guion, 4 dígitos, guion, 2 dígitos
            patron_carnet = r"^\d{2}-\d{4}-\d{2}$"
            
            if not re.match(patron_carnet, carnet_limpio):
                st.warning("⚠️ Formato incorrecto. Por favor use el formato: XX-XXXX-XX (incluyendo guiones).")
            else:
                # Filtrar DataFrame
                resultados = df[df['N° Carnet'] == carnet_limpio]
                
                if resultados.empty:
                    st.error("❌ No se encontraron registros con ese número de carnet.")
                else:
                    # Extraer datos generales del primer registro (asumiendo que nombre y carrera no cambian)
                    primer_reg = resultados.iloc[0]
                    nombre_estudiante = primer_reg['Nombres y Apellidos']
                    carrera = primer_reg['Carrera']
                    anio = primer_reg['Año']
                    ciclo = primer_reg['Ciclo']
                    
                    # Mostrar Tarjeta de Información
                    st.markdown(f"""
                    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #003366;">
                        <h3 style="margin:0; color:#003366;">{nombre_estudiante}</h3>
                        <p style="margin:0;"><b>Carnet:</b> {carnet_limpio} | <b>Carrera:</b> {carrera}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Procesar datos para la tabla y PDF
                    datos_procesados = []
                    html_rows = ""
                    
                    for _, row in resultados.iterrows():
                        asignatura = row['Asignatura']
                        docente = row['Docente']
                        nota_final = str(row['Nota Final']).strip()
                        nota_especial = str(row['Nota de Especial']).strip()
                        
                        # Lógica de visualización
                        mostrar_especial = "-"
                        estado = "Aprobado"
                        
                        try:
                            nf_val = float(nota_final)
                            if nf_val < 60:
                                estado = "Reprobado"
                                if nota_especial and nota_final.upper() != "SD":
                                    mostrar_especial = nota_especial
                        except:
                            if nota_final.upper() == "SD":
                                estado = "Sin Derecho"
                            else:
                                estado = "-"

                        # Construir fila HTML
                        html_rows += f"""
                        <tr>
                            <td>{asignatura}</td>
                            <td>{docente}</td>
                            <td><b>{nota_final}</b></td>
                            <td>{mostrar_especial}</td>
                            <td>{estado}</td>
                        </tr>
                        """
                        
                        # Guardar para PDF
                        datos_procesados.append({
                            'asignatura': asignatura,
                            'docente': docente,
                            'nota_final': nota_final,
                            'nota_especial': mostrar_especial,
                            'estado': estado
                        })

                    # Renderizar Tabla HTML Elegante
                    tabla_html = f"""
                    <table class="styled-table">
                        <thead>
                            <tr>
                                <th>Asignatura</th>
                                <th>Docente</th>
                                <th>Nota Final</th>
                                <th>Nota Especial</th>
                                <th>Estado</th>
                            </tr>
                        </thead>
                        <tbody>
                            {html_rows}
                        </tbody>
                    </table>
                    """
                    st.markdown(tabla_html, unsafe_allow_html=True)
                    
                    # Generar y ofrecer PDF
                    st.markdown("### 📄 Descargar Resultados")
                    
                    info_estudiante = {
                        'nombre': nombre_estudiante,
                        'carnet': carnet_limpio,
                        'carrera': carrera,
                        'anio': anio,
                        'ciclo': ciclo
                    }
                    
                    pdf_bytes = generar_pdf(datos_procesados, info_estudiante)
                    
                    st.download_button(
                        label="⬇️ Descargar Esquela de Notas (PDF)",
                        data=pdf_bytes,
                        file_name=f"Notas_{carnet_limpio}.pdf",
                        mime="application/pdf"
                    )

if __name__ == "__main__":
    main()
