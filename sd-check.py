import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# Function to extract and process campaign data
def extract_columns(data):
    columns_to_extract = [
        'Campaigns', 'Status', 'Start date', 'Portfolio', 'Budget(USD)',
        'Impressions', 'Clicks', 'Spend(USD)', 'CPC(USD)', 'Orders', 'ACOS',
        'Viewable impressions'
    ]
    extracted_data = data[columns_to_extract].copy()
    extracted_data['Start date'] = pd.to_datetime(extracted_data['Start date'], format='%m/%d/%y')
    extracted_data.sort_values(by=['ACOS', 'Impressions'], ascending=[True, False], inplace=True)

    def categorize_impressions(impressions):
        if impressions == 0:
            return "No Impressions"
        elif 0 < impressions < 100:
            return "1-99"
        elif 100 <= impressions < 1000:
            return "100-999"
        elif 1000 <= impressions < 10000:
            return "1000-9999"
        else:
            return "10000+"

    extracted_data['Category'] = extracted_data['Impressions'].apply(categorize_impressions)
    extracted_data['Note'] = ''
    extracted_data['Action'] = ''
    return extracted_data

# UI Layout
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Import File", "Preview Campaigns", "Bảng đối chiếu"])

if page == "Import File":
    st.header("Import and Process Campaign Files")
    input_date = st.date_input("Select the target date")
    date_str = input_date.strftime('%Y-%m-%d')

    uploaded_files = []
    for i in range(3):
        uploaded_file = st.file_uploader(f"Upload CSV file for {input_date - timedelta(days=i)}", type="csv", key=f"file_{i}")
        uploaded_files.append(uploaded_file)

    if all(uploaded_files):
        dataframes = [extract_columns(pd.read_csv(file)) for file in uploaded_files]

        if st.button("Export to Excel"):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                for i, df in enumerate(dataframes):
                    sheet_name = (input_date - timedelta(days=i)).strftime('%d_%m')
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            output.seek(0)
            st.download_button(label="Download Excel File", data=output, file_name="Campaigns_3_days.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        st.session_state['dataframes'] = dataframes
        st.session_state['dates'] = [input_date - timedelta(days=i) for i in range(3)]

elif page == "Preview Campaigns":
    st.header("Preview Campaigns by Category")
    if 'dataframes' in st.session_state:
        selected_categories = st.multiselect("Select categories to display", ["No Impressions", "1-99", "100-999", "1000-9999", "10000+"], default=["10000+"])
        for i, df in enumerate(st.session_state['dataframes']):
            filtered_df = df[df['Category'].isin(selected_categories)]
            st.subheader(f"Data for {(st.session_state['dates'][i]).strftime('%d-%m-%Y')}")
            st.dataframe(filtered_df)
    else:
        st.warning("Please import files first from the 'Import File' tab.")

elif page == "Bảng đối chiếu":
    st.header("Bảng đối chiếu Campaign")
    if 'dataframes' in st.session_state:
        campaign_name = st.text_input("Enter campaign name to compare")
        if campaign_name:
            comparison_rows = []
            for i, df in enumerate(st.session_state['dataframes']):
                match = df[df['Campaigns'].str.contains(campaign_name, case=False, na=False)]
                if not match.empty:
                    match['Date'] = st.session_state['dates'][i].strftime('%Y-%m-%d')
                    comparison_rows.append(match)

            if comparison_rows:
                result_df = pd.concat(comparison_rows).sort_values(by='Date')
                st.dataframe(result_df)

                # Line chart default: Impressions + Viewable impressions
                st.subheader("Biểu đồ chỉ số theo ngày")
                chart_data = result_df[['Date', 'Impressions', 'Viewable impressions']].copy()
                chart_data['Date'] = pd.to_datetime(chart_data['Date'])
                chart_data.set_index('Date', inplace=True)

                optional_metrics = st.multiselect("Chọn thêm chỉ số để hiển thị", ['Orders', 'Spend(USD)', 'ACOS'])
                for metric in optional_metrics:
                    chart_data[metric] = result_df.set_index('Date')[metric]

                st.line_chart(chart_data)

            else:
                st.warning("Không tìm thấy campaign phù hợp trong 3 ngày.")
    else:
        st.warning("Please import files first from the 'Import File' tab.")
