import streamlit as st
import gspread
import pandas as pd
import datetime

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
    # Читаем доступы из сохраненных Secrets
    # --- ПОДКЛЮЧЕНИЕ К GOOGLE ТАБЛИЦЕ ---
try:
    client = gspread.service_account_from_dict(dict(st.secrets))
    
    # ОТКРЫВАЕМ ПО НАЗВАНИЮ ТАБЛИЦЫ
    sheet = client.open("Псы на мясе")
    sheet_prihod = sheet.worksheet("приход")
    sheet_prodazha = sheet.worksheet("продажа")
except Exception as e:
    st.error(f"Ошибка подключения к Google Таблице: {e}")
    st.stop()

    st.error(f"Ошибка подключения к Google Таблице: {e}")
    st.stop()

# --- ЗАГРУЗКА ДАННЫХ ИЗ ТАБЛИЦЫ ---
data_prihod = sheet_prihod.get_all_records()
df_prihod = pd.DataFrame(data_prihod)

tab1, tab2, tab3 = st.tabs(["🛍️ Оформить Продажу", "📥 Принять Приход", "📊 Текущий Склад"])

# --- ВКЛАДКА 1: ПРОДАЖА ---
with tab1:
    st.subheader("Оформление продажи у прилавка")
    if df_prihod.empty:
        st.info("На складе пока нет товаров. Добавьте их на вкладке 'Принять Приход'.")
    else:
        with st.form("sale_form", clear_on_submit=True):
            product_sale = st.selectbox("Выберите товар:", df_prihod["Название"].tolist())
            weight_sale = st.number_input("Продано вес (кг):", min_value=0.0, step=0.1, format="%.3f")
            
            matched_rows = df_prihod[df_prihod["Название"] == product_sale]
            price = float(matched_rows["Цена за кг"].values[0])
            current_stock = float(matched_rows["Остаток (кг)"].values[0])
            
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
    st.subheader("Поступление нового товара")
    with st.form("prihod_form", clear_on_submit=True):
        product_prihod = st.text_input("Название товара (например, Говядина):")
        weight_prihod = st.number_input("Вес партии (кг):", min_value=0.0, step=0.1, format="%.3f")
        price_prihod = st.number_input("Цена продажи за кг (руб):", min_value=0.0, step=10.0)
        
        submitted_prihod = st.form_submit_button("📥 ЗАФИКСИРОВАТЬ ПРИХОД")
        
        if submitted_prihod:
            if not product_prihod or weight_prihod <= 0 or price_prihod <= 0:
                st.warning("Заполните все поля корректно!")
            else:
                if not df_prihod.empty and product_prihod in df_prihod["Название"].tolist():
                    matched_rows = df_prihod[df_prihod["Название"] == product_prihod]
                    current_stock = float(matched_rows["Остаток (кг)"].values[0])
                    row_idx = int(matched_rows.index[0]) + 2
                    new_stock = current_stock + weight_prihod
                    sheet_prihod.update_cell(row_idx, 2, new_stock)
                    sheet_prihod.update_cell(row_idx, 3, price_prihod)
                else:
                    sheet_prihod.append_row([product_prihod, weight_prihod, price_prihod])
                
                st.success(f"Товар '{product_prihod}' успешно добавлен/обновлен!")
                st.rerun()

# --- ВКЛАДКА 3: ТЕКУЩИЙ СКЛАД ---
with tab3:
    st.subheader("Актуальные остатки и розничные цены")
    if df_prihod.empty:
        st.write("Склад пуст.")
    else:
        st.dataframe(df_prihod[["Название", "Остаток (кг)", "Цена за кг"]], hide_index=True, use_container_width=True)
