import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta

def extract_columns(data):
    columns_to_extract = [
        'Campaigns', 'Status', 'Start date', 'Portfolio', 'Budget(USD)',
        'Impressions', 'Clicks', 'Spend(USD)', 'CPC(USD)', 'Orders', 'ACOS',
        'Viewable impressions'
    ]
    return data[columns_to_extract]

def categorize_impressions(impressions):
    if impressions == 0:
        return "No Impressions"
    elif impressions < 100:
        return "1-99"
    elif impressions < 1000:
        return "100-999"
    elif impressions < 10000:
        return "1000-9999"
    else:
        return "10000+"

def process_file(uploaded_file):
    df = pd.read_csv(uploaded_file)
    df = extract_columns(df)
    df['Start date'] = pd.to_datetime(df['Start date'], format='%m/%d/%y')
    df.sort_values(by=['ACOS', 'Impressions'], ascending=[True, False], inplace=True)
    df['Category'] = df['Impressions'].apply(categorize_impressions)
    df['Note'] = ''
    df['Action'] = ''
    return df

def export_to_excel(dfs, sheet_names):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for df, name in zip(dfs, sheet_names):
            df.to_excel(writer, sheet_name=name, index=False)
    output.seek(0)
    return output

st.title("Campaign Data Review Tool")

# Step 1: Input date
selected_date = st.date_input("Chọn ngày đang xét (YYYY-MM-DD)", datetime.today())
dates = [selected_date - timedelta(days=i) for i in range(3)]

# Step 2: Upload 3 files
uploaded_files = []
for i, d in enumerate(dates):
    file = st.file_uploader(f"Upload file for {d.strftime('%Y-%m-%d')}", type='csv', key=f'file_{i}')
    uploaded_files.append(file)

if all(uploaded_files):
    dfs = [process_file(file) for file in uploaded_files]
    sheet_names = [d.strftime('%d_%m') for d in dates]

    # Export to Excel button
    excel_data = export_to_excel(dfs, sheet_names)
    st.download_button("Export to Excel", excel_data, file_name="Campaigns_3_days.xlsx")

    # Category filters
    st.subheader("Chọn Category để hiển thị")
    categories = ["No Impressions", "1-99", "100-999", "1000-9999", "10000+"]
    all_categories = ["Select all"] + categories
    selected = st.multiselect("Chọn các Category:", all_categories, default=[])

    if "Select all" in selected:
        selected = categories

    for df, name in zip(dfs, sheet_names):
        st.markdown(f"### Bảng dữ liệu ngày {name}")
        st.dataframe(df[df['Category'].isin(selected)])

    # Campaign comparison
    st.subheader("Bảng đối chiếu theo Campaign")
    search_campaign = st.text_input("Nhập tên Campaign (hoặc 1 phần tên)")
    if search_campaign:
        st.markdown("### Kết quả đối chiếu")
        for df, name in zip(dfs, sheet_names):
            filtered = df[df['Campaigns'].str.contains(search_campaign, case=False, na=False)]
            if not filtered.empty:
                st.markdown(f"**Ngày {name}:**")
                st.dataframe(filtered)
else:
    st.info("Vui lòng upload đầy đủ 3 file để tiếp tục.")
