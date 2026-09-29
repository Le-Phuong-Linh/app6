import streamlit as st
import os
import csv
from pathlib import Path
from google import genai

# =====================================================
# PALLADIUS SYSTEM PROMPT
# =====================================================

SYSTEM_PROMPT = """You are an expert in Chinese-to-Russian transliteration, specifically the Palladius system (палладиевская система).

Your single task is to review the Russian transliteration of a Chinese name and correct it strictly according to the official Palladius rules.

CRITICAL RULES FOR PALLADIUS SYLLABLES:
- 'ch' becomes 'ч' (e.g., chen -> чэнь, chang -> чан).
- 'j' becomes 'цз' (e.g., jing -> цзин, jia -> цзя).
- 'q' becomes 'ци' (e.g., qing -> цин, qian -> цянь).
- 'x' becomes 'си' (e.g., xun -> сюнь, xiang -> сян).
- 'zh' becomes 'чж' (e.g., zhen -> чжэнь, zhang -> чжан).
- 'z' becomes 'цз' (e.g., zi -> цзы).

CRITICAL FINALS (A / AN / ANG / EN / ENG / IN / ING):
- -an becomes -ань (e.g., lian -> лянь, tian -> тянь, pan -> пань)
- -ang becomes -ан (e.g., liang -> лян, chang -> чан, wang -> ван)
- -en becomes -энь (e.g., chen -> чэнь, ren -> жэнь)
- -eng becomes -эн (e.g., cheng -> чэн, meng -> мэн)
- -in becomes -инь (e.g., jin -> цзинь, lin -> линь)
- -ing becomes -ин (e.g., jing -> цзин, ling -> лин)

Input format you will receive:
Chinese: [Иероглифы]
Current Russian: [Текущий перевод]

You must output ONLY the corrected Russian name. 
Do NOT include any explanations, punctuation, markdown formatting, or the original Chinese. Just the corrected Russian text.
If the current Russian is already 100% correct according to Palladius, output it exactly as it is.

Example 1:
Input:
Chinese: 陆景
Current Russian: Лу Цзин
Output: Лу Цзин

Example 2:
Input:
Chinese: 孟蓝之
Current Russian: Мэн Ланжи
Output: Мэн Ланьчжи
"""

# =====================================================
# CORRECTION FUNCTION
# =====================================================

def fix_name_with_gemini(client, model_name, chinese_text, current_russian):
    prompt_content = f"{SYSTEM_PROMPT}\n\nInput:\nChinese: {chinese_text}\nCurrent Russian: {current_russian}"
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt_content
        )
        if response and response.text:
            return response.text.strip().replace("*", "").replace('"', '')
    except Exception as e:
        st.error(f"Ошибка Gemini для имени '{chinese_text}': {e}")
    return current_russian

def process_glossary_file(input_file_path, output_file_path, api_key, model_name, status_container):
    if not api_key:
        status_container.error("Пожалуйста, введите ваш Gemini API Key!")
        return False

    try:
        # Инициализация клиента по обычному API-ключу
        client = genai.Client(api_key=api_key)
    except Exception as e:
        status_container.error(f"Не удалось инициализировать Google GenAI клиент: {e}")
        return False

    if not os.path.exists(input_file_path):
        status_container.error(f"Файл '{input_file_path}' не найден.")
        return False

    rows_to_write = []
    headers = []

    with open(input_file_path, mode='r', encoding='utf-8', newline='') as infile:
        reader = csv.DictReader(infile)
        headers = reader.fieldnames
        
        required = {"Chinese", "Russian", "Type"}
        if not required.issubset(headers):
            status_container.error("Ошибка: glossary.csv должен содержать поля: Chinese, Russian, Type")
            return False
            
        all_rows = list(reader)

    total_rows = len(all_rows)
    progress_bar = st.progress(0)
    changed_count = 0

    for index, row in enumerate(all_rows, start=1):
        zh = row["Chinese"].strip()
        ru = row["Russian"].strip()
        row_type = row.get("Type", "").strip().lower()

        if row_type == "имя" and zh and ru:
            status_container.text(f"[{index}/{total_rows}] Проверка имени: {ru}...")
            corrected_ru = fix_name_with_gemini(client, model_name, zh, ru)
            
            if corrected_ru != ru:
                row["Russian"] = corrected_ru
                changed_count += 1
        
        rows_to_write.append(row)
        progress_bar.progress(index / total_rows)

    with open(output_file_path, mode='w', encoding='utf-8', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_to_write)

    status_container.success(f"Готово! Обработано строк: {total_rows}. Исправлено имен по системе Палладия: {changed_count}.")
    return True

# =====================================================
# STREAMLIT UI
# =====================================================

st.title("🇨🇳🇷🇺 Palladius Glossary Name Corrector")
st.write("Upload your `glossary.csv`, enter your Gemini API Key, and let Gemini review and correct character names strictly according to the official Palladius rules.")

# Поле для ввода API ключа
api_key_input = st.text_input("Gemini API Key", type="password", placeholder="AIzaSy...")
model_input = st.text_input("Gemini Model Name", value="gemini-3-flash-preview")

uploaded_file = st.file_uploader("Upload glossary.csv", type=["csv"])

if uploaded_file:
    os.makedirs("input", exist_ok=True)
    input_path = os.path.join("input", "glossary.csv")
    
    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    st.success("Файл glossary.csv успешно загружен!")

if st.button("Запустить исправление по Палладию"):
    input_path = os.path.join("input", "glossary.csv")
    output_path = os.path.join("input", "glossary_fixed.csv")
    
    if not os.path.exists(input_path):
        st.error("Пожалуйста, сначала загрузите файл glossary.csv.")
    else:
        status_box = st.empty()
        success = process_glossary_file(input_path, output_path, api_key_input, model_input, status_box)
        
        if success and os.path.exists(output_path):
            with open(output_path, "rb") as fp:
                st.download_button(
                    label="📦 Скачать исправленный глоссарий (glossary_fixed.csv)",
                    data=fp,
                    file_name="glossary_fixed.csv",
                    mime="text/csv"
                )
