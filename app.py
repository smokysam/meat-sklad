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
    # Ключи доступа мы загрузим чуть позже в настройки Streamlit Cloud
    creds_dict = st.secrets["gcp_service_account"]
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
