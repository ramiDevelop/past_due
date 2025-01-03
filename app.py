import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

# Initialize session state for data storage
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=[
        "Customer Name", "Invoice Number", "Amount", "Date", "Days", "Total Amount", "Admin Notes", "Comments"
    ])

if "bad_debt_data" not in st.session_state:
    st.session_state.bad_debt_data = pd.DataFrame(columns=[
        "Customer Name", "Invoice Number", "Amount", "Date", "Days", "Total Amount", "Admin Notes", "Comments"
    ])

# Function to calculate "Days" and "Total Amount"
def recalculate():
    # Ensure "Date" column is in datetime format
    st.session_state.data["Date"] = pd.to_datetime(st.session_state.data["Date"], errors="coerce")
    st.session_state.bad_debt_data["Date"] = pd.to_datetime(st.session_state.bad_debt_data["Date"], errors="coerce")
    # Handle invalid dates
    if st.session_state.data["Date"].isna().any() or st.session_state.bad_debt_data["Date"].isna().any():
        st.warning("Some records have invalid dates that were converted to 'NaT'.")
    # Calculate "Days"
    st.session_state.data["Days"] = st.session_state.data["Date"].apply(
        lambda x: (datetime.date.today() - x.date()).days if pd.notna(x) else None
    )
    st.session_state.bad_debt_data["Days"] = st.session_state.bad_debt_data["Date"].apply(
        lambda x: (datetime.date.today() - x.date()).days if pd.notna(x) else None
    )
    # Calculate "Total Amount" per customer
    st.session_state.data["Total Amount"] = st.session_state.data.groupby("Customer Name")["Amount"].transform("sum")
    st.session_state.bad_debt_data["Total Amount"] = st.session_state.bad_debt_data.groupby("Customer Name")["Amount"].transform("sum")

# Function to highlight rows with high past due days (greater than a threshold, e.g., 30)
def highlight_high_past_due(row):
    color = '#FFB3B3' if row["Days"] > 30 else 'white'
    return [f'background-color: {color}' for _ in row]

# App layout
st.set_page_config(layout="wide")

# Sidebar with logo and "Add Record"
with st.sidebar:
    st.image("C:\\Users\\hahas\\Downloads\\png_logo-removebg-preview.png", use_column_width=False, width=150)
    st.title("Add New Record")
    with st.form("add_record_form", clear_on_submit=True):
        customer_name = st.text_input("Customer Name")
        invoice_number = st.text_input("Invoice Number")
        amount = st.number_input("Amount", min_value=0.0, step=0.01)
        date = st.date_input("Date", value=datetime.date.today())
        admin_notes = st.text_area("Admin Notes")
        comments = st.text_input("Comments")
        submitted = st.form_submit_button("Add Record")
        if submitted:
            if not customer_name or not invoice_number:
                st.error("Customer Name and Invoice Number are required.")
            else:
                new_record = {
                    "Customer Name": customer_name,
                    "Invoice Number": invoice_number,
                    "Amount": amount,
                    "Date": date,
                    "Days": (datetime.date.today() - date).days,
                    "Total Amount": 0.0,
                    "Admin Notes": admin_notes,
                    "Comments": comments,
                }
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_record])], ignore_index=True)
                recalculate()
                st.success("Record added successfully!")

# Tabs for navigation
tab1, tab2, tab3, tab4 = st.tabs(["All Records", "Report", "Reminders", "Bad Debt"])

# "All Records" Tab
with tab1:
    st.subheader("All Records")
    if not st.session_state.data.empty:
        st.dataframe(
            st.session_state.data.style.format({
                "Amount": "${:,.2f}",
                "Total Amount": "${:,.2f}",
                "Days": "{:,.0f}",
            }).apply(highlight_high_past_due, axis=1),
            use_container_width=True
        )
    else:
        st.write("No records to display.")
    
    # Option to mark customer as bad debt
    st.subheader("Move Record to Bad Debt")
    if not st.session_state.data.empty:
        record_to_transfer = st.selectbox("Select an Invoice Number to Transfer to Bad Debt", st.session_state.data["Invoice Number"])
        if st.button("Transfer to Bad Debt"):
            # Find the record and move it to bad debt, then remove it from "All Records"
            record = st.session_state.data[st.session_state.data["Invoice Number"] == record_to_transfer]
            st.session_state.bad_debt_data = pd.concat([st.session_state.bad_debt_data, record], ignore_index=True)
            st.session_state.data = st.session_state.data[st.session_state.data["Invoice Number"] != record_to_transfer]
            recalculate()
            st.success(f"Record with Invoice Number {record_to_transfer} transferred to Bad Debt.")

# "Bad Debt" Tab
with tab4:
    st.subheader("Bad Debt Records")
    if not st.session_state.bad_debt_data.empty:
        st.dataframe(
            st.session_state.bad_debt_data.style.format({
                "Amount": "${:,.2f}",
                "Total Amount": "${:,.2f}",
                "Days": "{:,.0f}",
            }).apply(highlight_high_past_due, axis=1),
            use_container_width=True
        )
    else:
        st.write("No bad debt records to display.")

# "Report" Tab
with tab2:
    st.subheader("Customer Report")
    if not st.session_state.data.empty:
        report = (
            st.session_state.data.groupby("Customer Name")
            .agg(
                Invoice_Count=("Invoice Number", "count"),
                Total_Amount=("Amount", "sum")
            )
            .reset_index()
        )
        st.write("### Summary Report")
        st.dataframe(
            report.style.format({
                "Total_Amount": "${:,.2f}"
            }),
            use_container_width=True
        )
        
        # Analytics Graph
        st.write("### Analytics: Total Amount by Customer")
        fig = px.bar(
            report, 
            x="Customer Name", 
            y="Total_Amount", 
            text="Total_Amount", 
            title="Total Amount by Customer",
            labels={"Total_Amount": "Total Amount ($)", "Customer Name": "Customer Name"}
        )
        fig.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
        fig.update_layout(xaxis_title="Customer Name", yaxis_title="Total Amount ($)", 
                          height=500, width=800, margin=dict(l=40, r=40, t=50, b=40))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No records to display in the report.")

# "Reminders" Tab
with tab3:
    st.subheader("Reminders")
    st.info("📅 Don't forget to call customers every Tuesday and Friday at 11:00 AM!")

# Footer
st.markdown("---")
st.caption("Developed by Rami Aldoush")
