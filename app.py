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
    # ИСПРАВЛЕНО: Указаны корректные scope для работы с Google Drive и Google Sheets API
    scope = [
        "https://googleapis.com",
        "https://googleapis.com"
    ]
    
    # Вставляем данные из вашего JSON-файла прямо в код
    creds_dict = {
      "type": "service_account",
      "project_id": "meat-sklad-app",
      "private_key_id": "d96b9800076288857de7b04105e4c9f2e589de43",
      "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCtym/eM09T6vQG\n6w3+RWiW41DgU+sNvNvndTmq+89mob2baeBLgxuP4VmCeJO/p0H5NqNaFxmfRhH3\nwqswCGhFPG65OU0zPbvd+o4hwL84qwwKtWgCDh6Gmc2rLzhj2ksDdjj56YVZrUMI\nvnq88s2YdUbaY0BVqoy1Yiukd7JtmnwSvswhQx2YRk4NjBqGMFdPLSoQ8sHkZSyP\n67vyrMemq7MXEdOliGV7ZyuApaxyXKlhQgnh07G7CLYpZtpRwUoWhzZxbxSUHVlW\nWkMVB7TKKkqa9mdNK/OBjjrhcnQ3qC0tKc5Dr1uLcRXaYNNjFVQMRTVo2qzn6M0H\nj24M243vAgMBAAECggEAD/AshD9GZiwlBxa603fqw0kY8LR22RgElDHkVlxTmquj\nUkPKey0MnmG3WMeAHVJ/MsDNCFptUiBrThfp+ooQLfwAgjd8GgKZCR7iYWa7jWc6\nanz/4I2076PeqyALLDUn2KsYnJV1p6duf2MgqdVxVNW56BYJdLx4Z7tsxIo/Bd1p\n+z9vzLJK1fd0H75p/A1gl0Q9Tbkg7XyUmuZXQFLNFL5S/Be68BD4l3HU0TsZm4qE\nxenO/fDueWd7Nw0uxcUiR+q4kEymukaQbC+7vU8jUOHhcAR7UVLlnlFrppHIO+8z\njnibnG2DIZQKXcqvshnTCKqWB7L9PMe4c9TEBZC74QKBgQDiys5viVAAUIZBq/Lu\noXlMeVp9L33wywCbAouMMsi9/81HB/VrlV+TnW16zgKhjFvL59YF/GwENMyqtVL\nAInVfKB8+BBRbrdxdwTSxfZ4X/AIw6UM23W0LX2Qpi6KPOKkttftbv6HzDszlw10\nArYdmNZBBJULqqOmI4Lz7pTC0QKBgQDELDUBglnXSdbRVqhGd0qksox4sPd6w8XZ\nCCHH6D0VRVO8VGTe4PSr+EBpkHdkLNSncpUM/1jPkzXmJW6nrsFpvNspR9p3YC25\nTNWiLw57wBZaApFQbci/4Unlw2AFDXc5w4GQp4z/HgQQ89Df0Yxw6R7oBwjPLc9/\n0Pxs9P/0vwKBgEomCpZ263we17ZS9KtGifUR3B7/zwpSJNGJZHyjAfT01HW7yWay\nQLxvhSLYhg2xaTXih5wQQsoAxjxTlEbgVzBAfew94n/tVfa39hC/fpTesQj8hlMM\n0Y/mK56GZsL1oxg9W52aY4eco2J7qX9bf5VvqeU6DUzyLm0cQS1lvKdxAoGACjH5\n90AdBzFRNsP4LuFYQcL9xe/8jKbMC4F+r/MD6a0Wsvz32RV74cwfHN1jNxOVYbZ0\nxJ4osXEHJhTf8VsFtkcYZMbVNcsL1UuG9szXRdsvzjG/95wdCMvemVBUFy8h+SCO\nBUSP8VpP/8mMG3W6hMu4zXpAHPRWimAEHm2FN+UCgYEA1ZQxjueHQru0IjmPQKYu\n6JzR1kt9n8cDxVTCEDilFW5ZRI58sr24OsNgE5S84r5sfdnQCQ0jtWPehrdr/q1i\nXFDouygFC4qCBqF9asboUnLshAcONXW6MswUkNj/GCNNe/jbO2hkYW6g/jUChf/D\ny4Kq2wtbJ1saf314oQT1dlc=\n-----END PRIVATE KEY-----\n",
      "client_email": "sklad-admin@meat-sklad-app.iam.gserviceaccount.com",
      "client_id": "108105508379729674146",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token",
      "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
      "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/sklad-admin%40meat-sklad-app.iam.gserviceaccount.com",
      "universe_domain": "googleapis.com"
    }
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    # Открываем вашу Google Таблицу по ID
    sheet = client.open_by_key("1tUSQUfy61KASOwuMDeCixWWt6y68XondNohNitiW7cM")
    sheet_prihod = sheet.worksheet("Приход")
    sheet_prodazha = sheet.worksheet("Продажа")
except Exception as e:
    # ИСПРАВЛЕНО: Выводим точную техническую ошибку, чтобы понять, в чем затык
    st.error(f"Ошибка подключения к Google Таблице: {e}")
    st.info("Пожалуйста, убедитесь, что вы открыли доступ (Share) к вашей Google Таблице для email: sklad-admin@meat-sklad-app.iam.gserviceaccount.com")
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
    # Таблица остатков
    st.dataframe(df_prihod[["Название", "Остаток (кг)", "Цена за кг"]], hide_index=True, use_container_width=True)
