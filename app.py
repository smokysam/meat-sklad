import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import datetime

# --- НАСТРОЙКА ИНТЕРФЕЙСА ДЛЯ СМАРТФОНОВ ---
st.set_page_config(page_title="Псы на мясе: Склад", page_icon="🥩", layout="centered")

# Стилизация под мобильный экран (крупные кнопки под палец)
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
    scope = ["https://google.com", "https://googleapis.com"]
        # Вставляем данные из вашего JSON-файла прямо в код
    creds_dict = {
      "type": "service_account",
      "project_id": "meat-sklad-app",
      "private_key_id": "d96b9800076288857de7b04105e4c9f2e589de43",
      "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCTyn/eM09T6vOG\nln6w3+RxiW41DgU+sNvNvndTmq+B9mob2baeBLgxuP4DVnCeJO/p6H5NQnaFxnER\nHh3\nwqsaCwGhFPG65OU8zPbvd+o4haL84qwwKtwgCDh6mc2tLzhj2ksDdjJ56YVZiUMI\nnvnq88s2YduBaYB8Vqoy1Yukd7JmnwSvsahQx2YRK4NjBGmFdPLSoQsHkZSyP\nn67vyMEnq7MXEdOli6V7ZyuApaxуXKlhQgnhG7G7CLYpZtpRWUoWhzZxBxSUHV1W\nnwkMVB7TKKqa9ndNK/OBJjrhcnQ3QC0tKc5Dr1uLcRXaYNNjFVQMRTVQZnz6M0H\nnj2M243VAgMBAAECggEAD/AshD9GZiW18Xa603fqW0kYBLR22RGeElDHKV1xTnqJ\nnUkPKey8MnnG3xMeAHVJ/MsDNCFptUI8XThfp+oQFLwAgjd8GgKZR7iYWa7JMc6\\\nnanz/4I2876PeqyALLDUn2KsYnJV1p6duE2MgqdXvxNX56B\n-----END PRIVATE KEY-----\n",
      "client_email": "sklad-admin@://gserviceaccount.com",
      "client_id": "10810558379729674146",
      "auth_uri": "https://google.com",
      "token_uri": "https://googleapis.com",
      "auth_provider_x509_cert_url": "https://googleapis.com",
      "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/sklad-admin%40://gserviceaccount.com",
      "universe_domain": "googleapis.com"
    }
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    # Открываем вашу Google Таблицу по точному имени файла
    sheet = client.open_by_key("1tUSQUfy61KASOwuMDeCixWWt6y68XondNohNitiW7cM")
    sheet_prihod = sheet.worksheet("Приход")
    sheet_prodazha = sheet.worksheet("Продажа")
except Exception as e:
    st.error("Ожидание настройки подключения к Google Таблице...")
    st.stop()

# --- ЗАГРУЗКА ДАННЫХ ИЗ ТАБЛИЦЫ ---
data_prihod = sheet_prihod.get_all_records()
df_prihod = pd.DataFrame(data_prihod)

# Крупные мобильные вкладки внизу экрана
tab1, tab2, tab3 = st.tabs(["🛍️ Оформить Продажу", "📥 Принять Приход", "📊 Текущий Склад"])

# --- ВКЛАДКА 1: ПРОДАЖА (РАСХОД С ОСТАТКОВ) ---
with tab1:
    st.subheader("Оформление продажи у прилавка")
    with st.form("sale_form", clear_on_submit=True):
        product_sale = st.selectbox("Выберите товар:", df_prihod["Название"].tolist())
        weight_sale = st.number_input("Продано вес (кг):", min_value=0.0, step=0.1, format="%.3f")
        
        # Автоматический расчет цены прямо на экране телефона
        price_row = df_prihod[df_prihod["Название"] == product_sale].iloc[0]
        price = float(price_row["Цена за кг"])
        current_stock = float(price_row["Остаток (кг)"])
        
        total_sum = weight_sale * price
        st.info(f"Цена за кг: {price} руб.  |  💵 К ОПЛАТЕ: {total_sum:.2f} руб.")
        
        submitted_sale = st.form_submit_button("💰 ОФОРМИТЬ ПРОДАЖУ")
        
        if submitted_sale:
            if weight_sale <= 0:
                st.warning("Введите корректный вес мяса!")
            elif current_stock < weight_sale:
                st.error(f"Недостаточно товара! На складе осталось всего: {current_stock} кг")
            else:
                # 1. Записываем сделку на лист "Продажа"
                today = datetime.date.today().strftime("%d.%m.%Y")
                sheet_prodazha.append_row([today, product_sale, weight_sale, price, total_sum])
                
                # 2. Пересчитываем и уменьшаем остаток на листе "Приход"
                row_idx = df_prihod[df_prihod["Название"] == product_sale].index[0] + 2
                new_stock = current_stock - weight_sale
                sheet_prihod.update_cell(row_idx, 2, new_stock)
                
                st.success(f"Продано {weight_sale} кг '{product_sale}'. Сумма {total_sum:.2f} руб. Остатки обновлены!")
                st.rerun()

# --- ВКЛАДКА 2: ПРИХОД (ПОСТУПЛЕНИЕ НОВОГО МЯСА) ---
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
                # Находим нужную строчку и увеличиваем остаток килограммов
                row_idx = df_prihod[df_prihod["Название"] == product_prihod].index[0] + 2
                current_stock = float(df_prihod[df_prihod["Название"] == product_prihod].iloc[0]["Остаток (кг)"])
                new_stock = current_stock + weight_prihod
                sheet_prihod.update_cell(row_idx, 2, new_stock)
                
                st.success(f"Остаток товара '{product_prihod}' успешно увеличен на {weight_prihod} кг!")
                st.rerun()

# --- ВКЛАДКА 3: ТЕКУЩИЙ СКЛАД ---
with tab3:
    st.subheader("Актуальные остатки и розничные цены")
    # Красивая адаптивная таблица остатков для экрана смартфона
    st.dataframe(df_prihod[["Название", "Остаток (кг)", "Цена за кг"]], hide_index=True, use_container_width=True)
