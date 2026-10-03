import streamlit as st
import gspread
import pandas as pd
import datetime

# --- НАСТРОЙКА ИНТЕРФЕЙСА ДЛЯ СМАРТФОНОВ ---
st.set_page_config(page_title="Псы на мясе: Склад", page_icon="🥩", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div.stButton > button:first-child { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; font-size: 16px; }
    .stSelectbox, .stNumberInput { font-size: 16px !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🥩 Псы на мясе: Склад")

# --- ПОДКЛЮЧЕНИЕ К GOOGLE ТАБЛИЦЕ ---
try:
    # Подключаемся напрямую через сохраненный в репозитории файл key.json
    client = gspread.service_account(filename="key.json")

    sheet = client.open_by_key("1tUSQUfy61KASOwuMDeCixWWt6y68XondNohNitiW7cM")
    sheet_prihod = sheet.worksheet("Приход")
    sheet_prodazha = sheet.worksheet("Продажа")
except Exception as e:
    st.error(f"Ошибка подключения к Google Таблице: {e}")
    st.stop()

# --- ЗАГРУЗКА ДАННЫХ ИЗ ТАБЛИЦЫ ---
data_prihod = sheet_prihod.get_all_records()
df_prihod = pd.DataFrame(data_prihod)

tab1, tab2, tab3 = st.tabs(["🛍️ Оформить Продажу", "📥 Принять Приход", "📊 Текущий Склад"])

# --- ВКЛАДКА 1: ПРОДАЖА ---
with tab1:
    st.subheader("Оформление продажи у прилавка")
    with st.form("sale_form", clear_on_submit=True):
        product_sale = st.selectbox("Выберите товар:", df_prihod["Название"].tolist())
        weight_sale = st.number_input("Продано вес (кг):", min_value=0.0, step=0.1, format="%.3f")
        
        # Получаем строку для выбранного товара
        matched_rows = df_prihod[df_prihod["Название"] == product_sale]
        if not matched_rows.empty:
            price = float(matched_rows.iloc[0]["Цена за кг"])
            current_stock = float(matched_rows.iloc[0]["Остаток (кг)"])
        else:
            price = 0.0
            current_stock = 0.0
        
        total_sum = weight_sale * price
        st.info(f"Цена за кг: {price} руб.  |  💵 К ОПЛАТЕ: {total_sum:.2f} руб.")
        
        submitted_sale = st.form_submit_button("💰 ОФОРМИТЬ ПРОДАЖУ")
        
        if submitted_sale:
            if weight_sale <= 0:
                st.warning("Введите корректный вес мяса!")
            elif current_stock < weight_sale:
                st.error(f"Недостаточно товара! Осталось всего: {current_stock} кг")
            else:
                today = datetime.date.today().strftime("%d.%m.%Y")
                sheet_prodazha.append_row([today, product_sale, weight_sale, price, total_sum])
                
                row_idx = int(matched_rows.index[0]) + 2
                new_stock = current_stock - weight_sale
                sheet_prihod.update_cell(row_idx, 2, new_stock)
                
                st.success(f"Продано {weight_sale} кг '{product_sale}'. Остатки обновлены!")
                st.rerun()

# --- ВКЛАДКА 2: ПРИХОД ---
with tab2:
    st.subheader("Поступление новой партии товара")
    with st.form("prihod_form", clear_on_submit=True):
        product_prihod = st.selectbox("Выберите товар для пополнения:", df_prihod["Название"].tolist())
        weight_prihod = st.number_input("Принято вес (кг):", min_value=0.0, step=0.1, format="%.3f")
        
        submitted_prihod = st.form_submit_button("📥 ЗАФИКСИРОВАТЬ ПРИХОД")
        
        if submitted_prihod:
            if weight_prihod <= 0:
                st.warning("Введите корректный вес!")
            else:
                matched_rows = df_prihod[df_prihod["Название"] == product_prihod]
                if not matched_rows.empty:
                    current_stock = float(matched_rows.iloc[0]["Остаток (кг)"])
                    row_idx = int(matched_rows.index[0]) + 2
                    
                    new_stock = current_stock + weight_prihod
                    sheet_prihod.update_cell(row_idx, 2, new_stock)
                    st.success(f"Остаток товара успешно увеличен на {weight_prihod} кг!")
                    st.rerun()
                else:
                    st.error("Товар не найден в таблице.")

# --- ВКЛАДКА 3: ТЕКУЩИЙ СКЛАД ---
with tab3:
    st.subheader("Актуальные остатки и розничные цены")
    st.dataframe(df_prihod[["Название", "Остаток (кг)", "Цена за кг"]], hide_index=True, use_container_width=True)
