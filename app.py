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

# --- ЖЕСТКО ВШИТЫЙ КЛЮЧ АВТОРИЗАЦИИ ---
try:
    creds_dict = {
      "type": "service_account",
      "project_id": "meat-sklad-app",
      "private_key_id": "cceffb92fb1b1cd160f298ff72456958b413ea60",
      "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCpgUTVv92wEbIM\n6RjVticLW5+ZSkVAsJiS3Gk/KCZKaGesiMvNNQc0CupcFhQgrpI34fdnvsLpN/yB\nQPQj1h4C3MAI8uzRS1CnGsG1fs+P5V+Ohl9DjkOm7reCG6dXdq0uPf4T4VQUwt/h\nlQA1noPmmc5pCQBiIId1pwVKuC24ovXuU3+pOllQlfbDsY9I/YtLXLdrcYN9SfMw\npMcvAmlRM3NFfl5hkjEDKidnj0tP8PCxN18xQ1akWkSGfK4RidtF+na4ZzY4wZLb\nZcPZs75L5ZBAm8jDvEAG8bawG3+Hn1GHXpigdbdNDEaIeBVPdl8rExiip4wA7HTj\n/oQy/XFXAgMBAAECggEANxUj+lYkQ2AsvRdOk7xiycUXgyfog1If8rGfnf99Gfb9\nocq+d8wAsD/P0ub12X0BVRmgXV1XV5RzAMnLzI17KTD1UrMmlAjmh7chNcqkxr0i\nJV2zPW/QukGe7q/v3HNbaciJdYpm2WxOdq8F52bAtEJNGkLrlfe+LVR+Wr6pVPNQ\ni7FaxBWL6h0B6p9nWSrYRx5prSH5Fojxy0UkwnJx5OQ+YMlw73iTHfX30BERDPWC\ne7yMneb2Px43chAB2X/h/ULLh5l1qQJPadI8auC4DLBXtj+BiUZ3TGzf2eCso5n9\ncyof81Pg5zUjNjRaVUOactYz8LOlxI/UWxcRqVzE6QKBgQDVovmiyitMAya4H+Lk\nGY1sEX0mmdT7tJ+MbTYljl8b9qTRqu20ootLC3RtLogYt9fX9/0TCvQ4hMv4j1Cb\nZSaB5AoWc1PoS7xZllHvI9x8XueiUdQe+GQG+arefDF+RHLo+4IZeX7BsFGbtRyw\nQErVsCrtKYs776tUTUPm6yzSSwKBgQDLHf+9Ymot3roYhwOw+/zvu85qOf1K5OCV\n9AUH+YbeoQ45r7kp00yiT1mhGXzjf8YdKwyXZHKsJOlSLT8vwcBuCDJb477q5UR+\nkPeIJosMcReZr6hmje6XkfTlzQlcMabutHi5stAbQmH/zmXVhwPTKQonhP3lM/A\n2zRZQ3VVpQKBgQDUA2Q4wOgNDIeNbN+PvSgTWpvYBgxPK6a3Bt8YkF0k9DYHedlj\nTXhtJlYJ0Ibx+Oj1BL+b+V/7AxclepzlSpHXkAbO1u8rdpXaVorDh9RVfR3lgc3A\nWoNyRK3lFF1N0QI04vzu6Rr5f1DN9QQeif96Z9WB/ZuXBLgD9pXvge6+VwKBgCOd\n6w5mh3/rom5Sno8WYNAY+qUd7hCH+enRlGBFnSTE0R3Edo+jAbkkeO8K7R9ndHIA\n7oBNmN4eytsiHAZfz0J8JXh/gybldRFMkltJhvBzlFPavYjeMoxZh7wULCQCgOcy\ntki51kwxY8Xbh3fd6QnKFIHBjFP4u5JJLfDJJ3YRAoGAdPkhml4ase1XLDQRa9Mk\nSVzuQK33SZ6xI/RFE0LE2IBRFfiTAYmlP7/tgmHKLfuvcPdV/F5isycfdYVlVciT\nB/pYWqPsb0pDpXFxaXVqlp92PwgDiQH2ZSPqga0+GcMXdohTSSTLPUqyJq1XJIL1\n3SgWAc6ISlIku5eXKcAWSlI=\n-----END PRIVATE KEY-----\n",
      "client_email": "sklad-final@://gserviceaccount.com",
      "client_id": "118277484571617067403",
      "auth_uri": "https://google.com",
      "token_uri": "https://googleapis.com",
      "auth_provider_x509_cert_url": "https://googleapis.com",
      "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/sklad-final%40://gserviceaccount.com",
      "universe_domain": "googleapis.com"
    }
    
    # Принудительно чиним переносы строк в оперативной памяти сервера
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
    client = gspread.service_account_from_dict(creds_dict)
    
    # Открываем по чистому текстовому названию таблицы
    sheet = client.open("Псы на мясе")
    sheet_prihod = sheet.worksheet("приход")
    sheet_prodazha = sheet.worksheet("продажа")
except Exception as e:
    st.error(f"Ошибка подключения к Google Таблице: {e}")
    st.stop()

# --- ЗАГРУЗКА ДАННЫХ ИЗ ТАБЛИЦЫ ---
data_prihod = sheet_prihod.get_all_records()
df_prihod = pd.DataFrame(data_prihod)

tab1, tab2, tab3 = st.tabs(["🛍️ Оформить Продажу", "📥 Принять Приход", "📊 Текущий Склад"])

with tab1:
    st.subheader("Оформление продажи у прилавка")
    if df_prihod.empty:
        st.info("На складе пока нет товаров. Добавьте их на вкладке 'Принять Приход'.")
    else:
        with st.form("sale_form", clear_on_submit=True):
            product_sale = st.selectbox("Выберите товар:", df_prihod["Название"].tolist())
            weight_sale = st.number_input("Продано вес (кг):", min_value=0.0, step=0.1, format="%.3f")
            
            matched_rows = df_prihod[df_prihod["Название"] == product_sale]
            price = float(matched_rows["Цена за кг"].values)
            current_stock = float(matched_rows["Остаток (кг)"].values)
            
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
                    
                    row_idx = int(matched_rows.index) + 2
                    new_stock = current_stock - weight_sale
                    sheet_prihod.update_cell(row_idx, 3, new_stock)
                    
                    st.success(f"Продано {weight_sale} кг '{product_sale}'. Остатки обновлены!")
                    st.rerun()

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
                    current_stock = float(matched_rows["Остаток (кг)"].values)
                    row_idx = int(matched_rows.index) + 2
                    new_stock = current_stock + weight_prihod
                    sheet_prihod.update_cell(row_idx, 3, new_stock)
                    sheet_prihod.update_cell(row_idx, 4, price_prihod)
                else:
                    sheet_prihod.append_row(["", product_prihod, weight_prihod, price_prihod])
                
                st.success(f"Товар '{product_prihod}' успешно добавлен/обновлен!")
                st.rerun()

with tab3:
    st.subheader("Актуальные остатки и розничные цены")
    if df_prihod.empty:
        st.write("Склад пуст.")
    else:
        st.dataframe(df_prihod[["Название", "Остаток (кг)", "Цена за кг"]], hide_index=True, use_container_width=True)
