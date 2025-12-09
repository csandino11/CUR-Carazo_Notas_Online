import streamlit as st
import pandas as pd
import re

# Configuración de la página
st.set_page_config(page_title="Consulta de Notas", page_icon="🎓")

# Título y descripción
st.title("🎓 Consulta de Calificaciones")
st.markdown("Ingresa tu **Número de Carnet** o tu **Nombre Completo** para consultar tus resultados.")

# Cargar los datos (Ojo: Pandas es más rápido para lectura web que openpyxl puro)
# Usamos caché para no recargar el Excel con cada clic de cada alumno
@st.cache_data
def cargar_datos():
    try:
        # Asegúrate de que el nombre del archivo coincida exactamente con el que subas al repo
        df = pd.read_excel("Notas.xlsx", sheet_name="Datos", dtype=str)
        # Limpiar espacios en nombres de columnas por si acaso
        df.columns = df.columns.str.strip()
        # Rellenar NaN con cadenas vacías para evitar errores
        df = df.fillna("")
        return df
    except FileNotFoundError:
        return None

df = cargar_datos()

if df is None:
    st.error("Error: No se encuentra la base de datos de notas.")
    st.stop()

# --- INTERFAZ DE BÚSQUEDA ---
busqueda = st.text_input("Escribe aquí...", placeholder="Ej: 25-0022-02 o Juan Perez")
btn_buscar = st.button("Buscar 🔍")

# --- LÓGICA ---
if btn_buscar and busqueda:
    busqueda = busqueda.strip()
    
    # Determinar si es Carnet o Nombre
    # Regex simple: si tiene digitos y guiones es carnet, sino asumimos nombre
    es_carnet = bool(re.search(r'\d', busqueda)) and "-" in busqueda
    
    resultados = None
    
    if es_carnet:
        # Filtrar por Carnet (Búsqueda exacta o parcial)
        resultados = df[df['N° Carnet'].str.contains(busqueda, case=False, na=False)]
    else:
        # Filtrar por Nombre (Búsqueda flexible)
        resultados = df[df['Nombres y Apellidos'].str.contains(busqueda, case=False, na=False)]

    if resultados.empty:
        st.info("⚠️ Ningún registro encontrado. Verifique sus datos.")
    else:
        st.success(f"Se encontraron {len(resultados)} registros.")
        
        # Iterar sobre los resultados para mostrar las tarjetas
        for index, row in resultados.iterrows():
            
            # Lógica de Nota Especial
            nota_final_str = str(row['Nota Final']).strip()
            nota_especial_str = str(row['Nota de Especial']).strip()
            mostrar_especial = False
            
            # Intentar convertir nota a número para evaluar < 60
            try:
                nota_final_num = float(nota_final_str)
                if nota_final_num < 60 and nota_especial_str != "" and nota_final_str.upper() != "SD":
                    mostrar_especial = True
            except ValueError:
                # Si es "SD" o texto, no es menor a 60 numéricamente
                pass

            # Diseño de la "Tarjeta" de resultados
            with st.container():
                st.markdown("---")
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.subheader(row['Nombres y Apellidos'])
                    st.text(f"Carnet: {row['N° Carnet']}")
                    st.markdown(f"**Asignatura:** {row['Asignatura']}")
                    st.text(f"Docente: {row['Docente']}")
                
                with col2:
                    st.metric(label="Nota Final", value=nota_final_str)
                    if mostrar_especial:
                        st.metric(label="Nota Especial", value=nota_especial_str, delta_color="off")
                    elif nota_final_str.upper() == "SD":
                        st.warning("Sin Derecho")