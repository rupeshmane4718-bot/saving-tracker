import streamlit as st
import pandas as pd
from fpdf import FPDF2
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db

# --- Firebase Setup ---
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-key.json")  # Path to your Firebase service account key
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://orphanage-f0bb1-default-rtdb.firebaseio.com/'  # Replace with your Firebase DB URL
    })

# --- Streamlit App ---
st.set_page_config(layout="wide")
st.title("📅 Daily Expense Tracker")

# --- Expense Form ---
with st.form("expense_form"):
    date = st.date_input("Date", datetime.today())
    description = st.text_input("Expense Description")
    amount = st.number_input("Amount ($)", min_value=0.0)
    category = st.selectbox("Category", ["Food", "Transport", "Entertainment", "Bills", "Other"])

    if st.form_submit_button("Add Expense"):
        formatted_date = date.strftime("%d-%m-%Y")  # ✅ Save in dd-mm-yyyy format
        ref = db.reference(f'/expenses/{formatted_date}')
        ref.push({
            'description': description,
            'amount': amount,
            'category': category,
            'timestamp': datetime.now().isoformat()
        })
        st.success("Expense added successfully!")

# --- Display Today's Expenses ---
today = datetime.today().strftime("%d-%m-%Y")  # ✅ dd-mm-yyyy format
expenses_ref = db.reference(f'/expenses/{today}')
expenses = expenses_ref.get()

if expenses:
    # Convert Firebase data to DataFrame
    expenses_list = []
    for key, value in expenses.items():
        expenses_list.append({
            'Description': value['description'],
            'Amount ($)': value['amount'],
            'Category': value['category'],
            'Time': value['timestamp'][11:16]  # Just HH:MM
        })

    df = pd.DataFrame(expenses_list)

    st.subheader(f"Today's Expenses ({today})")
    st.dataframe(df, height=300)

    total = df['Amount ($)'].sum()
    st.metric("Total Expenses", f"${total:.2f}")

    # --- Generate PDF Report ---
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Daily Expense Report - {today}", ln=1, align='C')

    # Add table headers
    col_width = [70, 30, 30, 20]
    headers = ['Description', 'Amount ($)', 'Category', 'Time']

    pdf.set_font("Arial", 'B', 12)
    for i, header in enumerate(headers):
        pdf.cell(col_width[i], 10, header, border=1)
    pdf.ln()

    # Add rows
    pdf.set_font("Arial", size=10)
    for _, row in df.iterrows():
        pdf.cell(col_width[0], 10, str(row['Description']), border=1)
        pdf.cell(col_width[1], 10, f"${row['Amount ($)']:.2f}", border=1)
        pdf.cell(col_width[2], 10, str(row['Category']), border=1)
        pdf.cell(col_width[3], 10, str(row['Time']), border=1)
        pdf.ln()

    # Footer with total
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(sum(col_width)-col_width[-1], 10, "Total:", border=1)
    pdf.cell(col_width[-1], 10, f"${total:.2f}", border=1)

    # Save PDF in memory
    pdf_output = pdf.output(dest='S').encode('latin1')

    st.download_button(
        label="Download PDF Report",
        data=pdf_output,
        file_name=f"expense_report_{today}.pdf",  # ✅ dd-mm-yyyy in filename
        mime="application/pdf"
    )
else:
    st.info("No expenses recorded for today yet.")
