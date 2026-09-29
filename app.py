import streamlit as st
import os
import csv
from pathlib import Path

# =====================================================
# FILTER LOGIC
# =====================================================

def filter_glossary_names(input_file_path: Path, output_file_path: Path):
    match_count = 0
    try:
        with open(input_file_path, mode='r', encoding='utf-8', newline='') as infile, \
             open(output_file_path, mode='w', encoding='utf-8', newline='') as outfile:
            
            reader = csv.reader(infile)
            writer = csv.writer(outfile)
            
            # Read and write header (Chinese, Russian, Notes, Type)
            try:
                header = next(reader)
                writer.writerow(header)
            except StopIteration:
                return 0, "Файл пуст."
            
            # Type column index is 3 (4th column)
            type_index = 3 
            
            for row in reader:
                if row and len(row) > type_index:
                    if row[type_index].strip().lower() == 'имя':
                        writer.writerow(row)
                        match_count += 1
                        
        return match_count, None
    except Exception as e:
        return 0, str(e)

# =====================================================
# STREAMLIT UI
# =====================================================

st.title("🏷️ Glossary Character Name Filter")
st.write("Upload your `glossary.csv` file to filter and extract **only character names** (`имя`) into a separate CSV file.")

uploaded_file = st.file_uploader("Upload glossary.csv", type=["csv"])

if uploaded_file:
    input_dir = Path("input")
    input_dir.mkdir(exist_ok=True)
    
    input_path = input_dir / "glossary.csv"
    output_path = Path("glossary_names_only.csv")
    
    # Save uploaded file locally
    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    st.success("Файл успешно загружен!")

    if st.button("Отфильтровать имена"):
        match_count, error = filter_glossary_names(input_path, output_path)
        
        if error:
            st.error(f"Произошла ошибка при обработке файла: {error}")
        else:
            st.success(f"Успех! Найдено и перенесено строк с именами: {match_count}")
            
            with open(output_path, "rb") as fp:
                st.download_button(
                    label="📦 Скачать отфильтрованный глоссарий (glossary_names_only.csv)",
                    data=fp,
                    file_name="glossary_names_only.csv",
                    mime="text/csv"
                )
