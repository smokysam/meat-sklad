import streamlit as st
import gspread
import pandas as pd
import datetime
import json

st.set_page_config(page_title="Псы на мясе: Склад", page_icon="🥩", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div.stButton > button:first-child { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; font-size: 16px; }
    .stSelectbox, .stNumberInput { font-size: 16px !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🥩 Псы на мясе: Склад")

# --- ЗАГРУЗКА ФАЙЛА КЛЮЧА ИЗ ИНТЕРФЕЙСА ---
if "creds" not in st.session_state:
    st.info("🔑 Пожалуйста, загрузите ваш файл ключа key.json для авторизации:")
    uploaded_file = st.file_uploader("Выберите файл key.json с компьютера", type="json")
    if uploaded_file is not None:
        try:
            st.session_state["creds"] = json.load(uploaded_file)
            st.success("Ключ успешно загружен!")
            st.rerun()
        except Exception as e:
            st.error(f"Не удалось прочитать файл: {e}")
    st.stop()

# --- ПОДКЛЮЧЕНИЕ К GOOGLE ТАБЛИЦЕ ЧЕРЕЗ ЗАГРУЖЕННЫЙ КЛЮЧ ---
try:
    client = gspread.service_account_from_dict(st.session_state["creds"])
    
    # Открываем вашу Google Таблицу по её точному ID
    sheet = client.open_by_key("1POR8PXdF8jH-Yvi8KUNBFDKgI57knZW5EqoWqgYEHsM")
    sheet_prihod = sheet.worksheet("приход")
    sheet_prodazha = sheet.worksheet("продажа")
except Exception as e:
    st.error(f"Ошибка подключения к Google Таблице: {e}")
    if st.button("🔄 Сбросить ключ и войти заново"):
        del st.session_state["creds"]
        st.rerun()
    st.stop()

# --- ЗАГРУЗКА ДАННЫХ ИЗ ТАБЛИЦЫ ---
# Читаем все данные с листа "приход"
raw_data = sheet_prihod.get_all_values()

# Если таблица не пустая, убираем шапку (первая строка) и создаем DataFrame
if len(raw_data) > 1:
    headers = raw_data[0]
    df_prihod = pd.DataFrame(raw_data[1:], columns=headers)
else:
    df_prihod = pd.DataFrame()

tab1, tab2, tab3 = st.tabs(["🛍️ Оформить Продажу", "📥 Принять Приход", "📊 Текущий Склад"])

# --- ВКЛАДКА 1: ПРОДАЖА ---
with tab1:
    st.subheader("Оформление продажи у прилавка")
    if df_prihod.empty or "Название" not in df_prihod.columns:
        st.info("На складе пока нет товаров или таблица пуста.")
    else:
        # Фильтруем пустые строки, оставляем только реальные названия товаров
        valid_products = df_prihod[df_prihod["Название"].str.strip() != ""]["Название"].tolist()
        
        with st.form("sale_form", clear_on_submit=True):
            product_sale = st.selectbox("Выберите товар:", valid_products)
            weight_sale = st.number_input("Продано вес (кг):", min_value=0.0, step=0.1, format="%.3f")
            
            # Находим данные выбранного товара по его названию
            matched_idx = df_prihod[df_prihod["Название"] == product_sale].index[0]
            
            # Приводим к числам цену и остаток
            try:
                price = float(str(df_prihod.loc[matched_idx, "Цена за кг"]).replace(",", ".").strip())
            except:
                price = 0.0
                
            try:
                current_stock = float(str(df_prihod.loc[matched_idx, "Остаток (кг)"]).replace(",", ".").strip())
            except:
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
                    # Записываем на лист "продажа": Дата в А, Товар в B, Вес в C, Цена в D, Сумма в E
                    sheet_prodazha.append_row([today, product_sale, weight_sale, price, total_sum])
                    
                    # Вычисляем точный номер физической строки в Google Таблице (+2 из-за индексов Pandas и шапки)
                    row_in_sheet = int(matched_idx) + 2
                    new_stock = current_stock - weight_sale
                    
                    # Жестко обновляем ячейку остатка: строка товара, столбец 3 (C)
                    sheet_prihod.update_cell(row_in_sheet, 3, str(new_stock).replace(".", ","))
                    
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
                titles_list = [str(t).strip().lower() for t in df_prihod["Название"].tolist()]
                search_title = str(product_prihod).strip().lower()
                
                if search_title in titles_list:
                    matched_idx = titles_list.index(search_title)
                    try:
                        current_stock = float(str(df_prihod.loc[matched_idx, "Остаток (кг)"]).replace(",", ".").strip())
                    except:
                        current_stock = 0.0
                        
                    row_in_sheet = int(matched_idx) + 2
                    new_stock = current_stock + weight_prihod
                    
                    # Обновляем остаток в C (3) и цену в D (4)
                    sheet_prihod.update_cell(row_in_sheet, 2, str(new_stock).replace(".", ","))
                    sheet_prihod.update_cell(row_in_sheet, 3, str(price_prihod).replace(".", ","))
                    st.success(f"Товар '{product_prihod}' успешно обновлен на складе!")
                else:
                    # Если товара нет, пишем: пустой А (1), Название в B (2), Вес в C (3), Цена в D (4)
                    sheet_prihod.append_row(["", product_prihod, str(weight_prihod).replace(".", ","), str(price_prihod).replace(".", ",")])
                    st.success(f"Новый товар '{product_prihod}' добавлен в конец таблицы!")
                st.rerun()

# --- ВКЛАДКА 3: ТЕКУЩИЙ СКЛАД ---
with tab3:
    st.subheader("Актуальные остатки и розничные цены")
    if df_prihod.empty:
        st.write("Склад пуст.")
    else:
        # Показываем только заполненные столбцы, скрывая пустой столбец A
        display_df = df_prihod[df_prihod["Название"].str.strip() != ""]
        st.dataframe(display_df[["Название", "Остаток (кг)", "Цена за кг"]], hide_index=True, use_container_width=True)
