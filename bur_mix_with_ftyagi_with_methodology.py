
import streamlit as st
import math
import pandas as pd
from io import BytesIO

# Настройки страницы
st.set_page_config(page_title="Калькулятор расхода бентонита и полимера по СП 341.1325800.2017", page_icon="🧮")
st.title("Калькулятор расхода бентонита и полимера по СП 341.1325800.2017")

# Таблица 8.3: соответствие диаметра трубы и бурового канала
def get_bur_diameter_from_table(pipe_diameter_mm):
    bur_diameter_table = [
        (0, 160, 240),
        (161, 225, 300),
        (226, 315, 400),
        (316, 400, 500),
        (401, 500, 600),
        (501, 630, 700),
        (631, 710, 800),
        (711, 800, 900),
        (801, 900, 1000),
        (901, 1000, 1100),
        (1001, 1200, 1300),
        (1201, 1400, 1500),
        (1401, 1600, 1700),
        (1601, 1800, 1900),
        (1801, 2000, 2100)
    ]
    for d_min, d_max, bur_d in bur_diameter_table:
        if d_min <= pipe_diameter_mm <= d_max:
            return bur_d / 1000
    return pipe_diameter_mm * 1.3 / 1000

# Типовые коэффициенты запаса по группам буримости
group_reserve_coefficients = {
    "I": 1.5,
    "II": 1.5,
    "III": 1.5,
    "IV": 2.0,
    "V": 2.0,
    "VI": 2.5,
    "VII": 2.5,
    "VIII": 2.5
}

# Типы грунтов и нормы
soil_data = {
    "Супесь": ("I", 1.0, 40, 0.3),
    "Песок": ("II", 1.0, 45, 0.4),
    "Суглинок": ("III", 1.2, 50, 0.5),
    "Глина": ("IV", 1.2, 70, 0.6),
    "Песок средней плотности": ("V", 1.3, 80, 0.8),
    "Глина тугопластичная": ("VI", 1.4, 90, 1.0),
    "Мергель": ("VII", 1.5, 100, 1.2),
    "Скала": ("VIII", 1.5, 110, 1.5)
}

# Таблица А.3 (встроенная, примерная)
table_a3_values = {
    240: {60: 70, 100: 90, 120: 100, 150: 110},
    300: {60: 90, 100: 110, 120: 120, 150: 140},
    400: {60: 120, 100: 140, 120: 160, 150: 180},
    500: {60: 140, 100: 160, 120: 180, 150: 200},
    600: {60: 160, 100: 180, 120: 200, 150: 220},
    700: {60: 180, 100: 200, 120: 230, 150: 250},
    800: {60: 200, 100: 230, 120: 260, 150: 280},
    900: {60: 220, 100: 260, 120: 290, 150: 310},
    1000: {60: 240, 100: 280, 120: 310, 150: 340}
}

def get_ftab(d_bur_mm, length_m):
    diam_key = min(table_a3_values.keys(), key=lambda k: abs(k - d_bur_mm))
    length_key = min(table_a3_values[diam_key].keys(), key=lambda k: abs(k - length_m))
    return table_a3_values[diam_key][length_key]

# Кол-во участков
num_sections = st.number_input("Количество участков", min_value=1, max_value=20, value=1, step=1)

section_results = []

for i in range(num_sections):
    st.subheader(f"Участок {i+1}")
    diameter = st.number_input(f"Диаметр трубы (мм) — Участок {i+1}", min_value=50, max_value=2000, value=200, step=10, key=f"diameter_{i}")
    length = st.number_input(f"Протяженность (м) — Участок {i+1}", min_value=1, max_value=10000, value=100, step=1, key=f"length_{i}")
    soil_type = st.selectbox(f"Тип грунта — Участок {i+1}", list(soil_data.keys()), key=f"soil_{i}")

    group, f, bentonite_norm, polymer_norm = soil_data[soil_type]
    delta_L = length * 0.1
    D_bur = get_bur_diameter_from_table(diameter)
    volume = math.pi * (D_bur ** 2) / 4 * (length + delta_L) * f
    bentonite_total = volume * bentonite_norm
    polymer_total = volume * polymer_norm
    bentonite_per_m = bentonite_total / length
    polymer_per_m = polymer_total / length

    D_bur_mm = int(D_bur * 1000)
    F_tab = get_ftab(D_bur_mm, length)
    reserve_k = group_reserve_coefficients[group]
    F_total = F_tab * reserve_k

    section_results.append({
        "Участок": f"{i+1}",
        "Диаметр трубы (мм)": diameter,
        "Длина (м)": length,
        "Тип грунта": soil_type,
        "Группа": group,
        "Коэф. F": f,
        "D бур. (мм)": D_bur_mm,
        "Объем (м³)": round(volume, 2),
        "Бентонит (всего, кг)": round(bentonite_total, 1),
        "Бентонит (кг/м)": round(bentonite_per_m, 2),
        "Полимер (всего, кг)": round(polymer_total, 1),
        "Полимер (кг/м)": round(polymer_per_m, 2),
        "F табл. (кН)": F_tab,
        "Коэф. запаса": reserve_k,
        "F итог. (кН)": round(F_total, 1)
    })


def append_methodology_sheet(writer):
    methodology_rows = [
        ["Методика расчёта расхода бурового раствора и силы тяги (по СП 341.1325800.2017)"],
        [""],
        ["1. Вводные параметры:"],
        ["   - Диаметр трубопровода (dн), мм"],
        ["   - Длина перехода, м"],
        ["   - Тип грунта (по классификации Приложения Л)"],
        [""],
        ["2. Определение группы грунта по таблице соответствия."],
        ["3. Определение диаметра бурового канала (Dбур): по таблице 8.3 СП."],
        ["4. Расчёт объёма и расхода раствора по грунту и диаметру канала."],
        ["5. Расчёт F табличная по таблицам А.2 и А.3, и умножение на коэффициент запаса."],
        [""],
        ["F_итого = Fтаб × коэффициент запаса"],
    ]
    workbook = writer.book
    worksheet = workbook.add_worksheet("Методика расчета")
    for row_idx, row in enumerate(methodology_rows):
        worksheet.write_row(row_idx, 0, row)

if st.button("Рассчитать все участки"):
    st.subheader("Сводная таблица расчёта")
    df = pd.DataFrame(section_results)
    st.dataframe(df)

    output_xlsx = BytesIO()
    with pd.ExcelWriter(output_xlsx, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Расчет')
        append_methodology_sheet(writer)
    st.download_button("📥 Скачать Excel", data=output_xlsx.getvalue(), file_name="bur_mix_with_ftyagi.xlsx")
