import streamlit as st
import pandas as pd
import sqlite3
from fpdf import FPDF
from datetime import datetime
import os

# --- DATABASE & SESSION STATE ---
conn = sqlite3.connect('business_data.db')
c = conn.cursor()

# Existing table
c.execute('''CREATE TABLE IF NOT EXISTS transactions 
             (id INTEGER PRIMARY KEY, type TEXT, sector TEXT, client TEXT, amount REAL, date TEXT, description TEXT)''')

# New: Proforma Tracker table
c.execute('''CREATE TABLE IF NOT EXISTS proformas
             (id INTEGER PRIMARY KEY, doc_no TEXT, client TEXT, amount REAL, 
              issue_date TEXT, status TEXT, notes TEXT, last_updated TEXT)''')

# New: Assets table
c.execute('''CREATE TABLE IF NOT EXISTS assets
             (id INTEGER PRIMARY KEY, name TEXT, category TEXT, serial_no TEXT,
              purchase_date TEXT, purchase_value REAL, current_value REAL,
              location TEXT, condition TEXT, assigned_to TEXT, notes TEXT)''')

# Migration: add any missing columns to assets table (safe for existing DBs)
existing_asset_cols = [row[1] for row in c.execute("PRAGMA table_info(assets)").fetchall()]
for col, typedef in [
    ("category", "TEXT"), ("serial_no", "TEXT"), ("purchase_date", "TEXT"),
    ("purchase_value", "REAL"), ("current_value", "REAL"), ("location", "TEXT"),
    ("condition", "TEXT"), ("assigned_to", "TEXT"), ("notes", "TEXT")
]:
    if col not in existing_asset_cols:
        c.execute(f"ALTER TABLE assets ADD COLUMN {col} {typedef}")

conn.commit()

if 'rows' not in st.session_state:
    st.session_state.rows = [{"item": 1, "desc": "SACP inspection: Cargo pipelines, Hydrant pipelines, product pipelines, storage tanks and hydrant tank", "qty": 1, "unit": "lot", "rate": 25000.0}]

# --- APP SETUP ---
st.set_page_config(page_title="HAY360 Portal", layout="wide")
st.title("🏗️ HAY360 Services: Professional Manager")

menu = ["Dashboard", "Document Generator", "Proforma Tracker", "Asset Manager", "Log Transaction"]
choice = st.sidebar.selectbox("Menu", menu)

# =====================================================================
# DOCUMENT GENERATOR
# =====================================================================
if choice == "Document Generator":
    st.subheader("📄 Create Multi-Item Document")
    doc_type = st.radio("Type", ["Proforma", "Invoice", "Receipt"], horizontal=True)
    
    auto_no = datetime.now().strftime("%Y%m%d%H%M")
    
    col_a, col_b = st.columns(2)
    with col_a:
        c_name = st.text_input("BILL TO:", value="MATRIX ENERGY GROUP")
        project_info = st.text_area("Project / Work Details (Optional):", value="") 
        doc_no = st.text_input("Document #:", value=auto_no)
    with col_b:
        date_issue = st.date_input("Date of Issue", datetime.now())

    st.write("---")
    st.write("### Itemized Table")
    
    for i, row in enumerate(st.session_state.rows):
        cols = st.columns([1, 4, 1, 1, 2, 0.5])
        st.session_state.rows[i]["item"] = cols[0].number_input("Item", value=i+1, key=f"item_{i}")
        st.session_state.rows[i]["desc"] = cols[1].text_area("Description", value=row["desc"], key=f"desc_{i}", height=70)
        st.session_state.rows[i]["qty"] = cols[2].number_input("Qty", value=row["qty"], key=f"qty_{i}")
        st.session_state.rows[i]["unit"] = cols[3].text_input("Unit", value=row["unit"], key=f"unit_{i}")
        st.session_state.rows[i]["rate"] = cols[4].number_input("Rate", value=float(row["rate"]), key=f"rate_{i}")
        if cols[5].button("🗑️", key=f"del_{i}"):
            st.session_state.rows.pop(i)
            st.rerun()

    if st.button("➕ Add New Row"):
        st.session_state.rows.append({"item": len(st.session_state.rows)+1, "desc": "", "qty": 1, "unit": "lot", "rate": 0.0})
        st.rerun()

    st.write("---")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        terms = st.text_area("Payment Terms", value="1. 30% Advance: Mobilization fee.\n2. 40% Progress Payment.\n3. 30% Final Payment.\n4. Tax Exclusion: Total excludes all applicable taxes.")
    with col_t2:
        notes = st.text_area("Technical Notes", value="1. Access: Provide unrestricted site access.\n2. Reporting: Compliance against NACE/AMPP standards (-850 mV analysis).")

    col_gen, col_save = st.columns([2, 1])
    with col_gen:
        generate_btn = st.button(f"Generate {doc_type} PDF")
    with col_save:
        if doc_type == "Proforma":
            save_to_tracker = st.checkbox("Save to Proforma Tracker", value=True)
        else:
            save_to_tracker = False

    if generate_btn:
        pdf = FPDF()
        pdf.add_page()
        mono_font = "Courier"
        
        if os.path.exists("logo.png"):
            pdf.image("logo.png", 10, 8, 30)
        
        pdf.set_font(mono_font, 'B', 16)
        pdf.cell(0, 8, "HAY360 SERVICES", ln=True, align='C')
        pdf.set_font(mono_font, 'B', 9)
        pdf.cell(0, 5, "ENGINEERING LOGISTICS TRANSPORT", ln=True, align='C')
        pdf.set_font(mono_font, size=9)
        pdf.cell(0, 4, "Accra Tema | +233246241338 | hay360services@outlook.com", ln=True, align='C')
        pdf.ln(15)

        pdf.set_font(mono_font, 'B', 11)
        pdf.cell(0, 7, f"{doc_type.upper()} # {doc_no}", ln=True, align='R')
        pdf.set_font(mono_font, size=9)
        pdf.cell(0, 5, f"Date: {date_issue.strftime('%d/%m/%Y')}", ln=True, align='R')
        
        if project_info.strip():
            pdf.set_font(mono_font, 'B', 10)
            pdf.cell(0, 7, "Project Details:", ln=True)
            pdf.set_font(mono_font, size=9)
            pdf.multi_cell(0, 5, project_info)
            pdf.ln(5)
        
        pdf.set_font(mono_font, 'B', 10)
        pdf.cell(0, 7, f"BILL TO: {c_name}", ln=True)
        pdf.set_font(mono_font, size=10)
        pdf.cell(0, 5, "Accra, Ghana", ln=True)
        pdf.ln(5)

        pdf.set_font(mono_font, 'B', 8)
        w = [12, 88, 12, 12, 33, 33] 
        headers = ["ITM", "DESCRIPTION", "QTY", "UNT", "RATE(GHC)", "AMOUNT(GHC)"]
        for i, h in enumerate(headers):
            pdf.cell(w[i], 10, h, border=1, align='C')
        pdf.ln()

        pdf.set_font(mono_font, size=8)
        grand_total = 0
        for r in st.session_state.rows:
            amt = r['qty'] * r['rate']
            grand_total += amt
            
            line_height = 5
            text_contents = r['desc']
            lines = pdf.multi_cell(w[1], line_height, text_contents, split_only=True)
            row_height = max(10, len(lines) * line_height + 4)

            curr_x = pdf.get_x()
            curr_y = pdf.get_y()

            pdf.cell(w[0], row_height, str(r['item']), border=1, align='C')
            pdf.set_xy(curr_x + w[0], curr_y)
            pdf.multi_cell(w[1], line_height, text_contents, border=0)
            pdf.rect(curr_x + w[0], curr_y, w[1], row_height)
            pdf.set_xy(curr_x + w[0] + w[1], curr_y)
            pdf.cell(w[2], row_height, str(r['qty']), border=1, align='C')
            pdf.cell(w[3], row_height, r['unit'], border=1, align='C')
            pdf.cell(w[4], row_height, f"{r['rate']:,.2f}", border=1, align='R')
            pdf.cell(w[5], row_height, f"{amt:,.2f}", border=1, align='R')
            pdf.ln(row_height)

        pdf.ln(5)
        pdf.set_x(124)
        pdf.set_font(mono_font, 'B', 9)
        pdf.cell(33, 8, "TOTAL DUE", border=1)
        pdf.cell(33, 8, f"GHC {grand_total:,.2f}", border=1, align='R', ln=True)

        pdf.ln(10)
        pdf.set_font(mono_font, 'B', 9)
        pdf.cell(0, 5, "TERMS OF PAYMENT", ln=True)
        pdf.set_font(mono_font, size=8)
        pdf.multi_cell(0, 4, terms)
        pdf.ln(5)
        pdf.cell(0, 5, "TECHNICAL NOTES", ln=True)
        pdf.multi_cell(0, 4, notes)

        pdf.ln(10)
        pdf.set_font(mono_font, 'I', 10)
        pdf.cell(0, 10, "Thank you for your continued business", ln=True, align='C')
        pdf.set_font(mono_font, 'B', 10)
        pdf.cell(0, 5, "HAY360 SERVICES", ln=True, align='C')
        
        pdf_name = f"{doc_type}_{doc_no}.pdf"
        pdf.output(pdf_name)
        st.success(f"Generated: {pdf_name}")

        # Auto-save proforma to tracker
        if save_to_tracker and doc_type == "Proforma":
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            c.execute("""INSERT INTO proformas (doc_no, client, amount, issue_date, status, notes, last_updated)
                         VALUES (?,?,?,?,?,?,?)""",
                      (doc_no, c_name, grand_total, date_issue.strftime("%Y-%m-%d"), "Sent", project_info, now))
            conn.commit()
            st.info(f"✅ Proforma #{doc_no} saved to Tracker with status 'Sent'.")

# =====================================================================
# PROFORMA TRACKER
# =====================================================================
elif choice == "Proforma Tracker":
    st.subheader("📋 Proforma Invoice Tracker")

    STATUS_OPTIONS = ["Draft", "Sent", "Under Review", "Approved", "Partially Paid", "Fully Paid", "Cancelled", "Overdue"]
    STATUS_COLORS = {
        "Draft": "⚪", "Sent": "🔵", "Under Review": "🟡",
        "Approved": "🟢", "Partially Paid": "🟠", "Fully Paid": "✅",
        "Cancelled": "🔴", "Overdue": "🚨"
    }

    tab1, tab2 = st.tabs(["📊 All Proformas", "➕ Add Manually"])

    with tab1:
        df_pf = pd.read_sql_query("SELECT * FROM proformas ORDER BY issue_date DESC", conn)
        if df_pf.empty:
            st.info("No proformas yet. Generate one from the Document Generator or add manually below.")
        else:
            # Summary metrics
            total_val = df_pf['amount'].sum()
            paid_val = df_pf[df_pf['status'] == 'Fully Paid']['amount'].sum()
            pending_val = df_pf[df_pf['status'].isin(['Sent', 'Under Review', 'Approved', 'Partially Paid'])]['amount'].sum()
            overdue_count = len(df_pf[df_pf['status'] == 'Overdue'])

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Proformas Value", f"GHC {total_val:,.2f}")
            m2.metric("Collected", f"GHC {paid_val:,.2f}")
            m3.metric("Outstanding", f"GHC {pending_val:,.2f}")
            m4.metric("Overdue", f"{overdue_count} invoice(s)")

            st.write("---")

            # Filter controls
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filter_status = st.multiselect("Filter by Status", STATUS_OPTIONS, default=STATUS_OPTIONS)
            with col_f2:
                filter_client = st.text_input("Search by Client")

            filtered = df_pf[df_pf['status'].isin(filter_status)]
            if filter_client:
                filtered = filtered[filtered['client'].str.contains(filter_client, case=False, na=False)]

            st.write(f"Showing **{len(filtered)}** of {len(df_pf)} records")

            for _, row in filtered.iterrows():
                icon = STATUS_COLORS.get(row['status'], "⚪")
                with st.expander(f"{icon} #{row['doc_no']} | {row['client']} | GHC {row['amount']:,.2f} | {row['issue_date']}"):
                    col_i1, col_i2 = st.columns(2)
                    with col_i1:
                        st.write(f"**Client:** {row['client']}")
                        st.write(f"**Amount:** GHC {row['amount']:,.2f}")
                        st.write(f"**Issued:** {row['issue_date']}")
                        if row['notes']:
                            st.write(f"**Notes:** {row['notes']}")
                    with col_i2:
                        new_status = st.selectbox("Update Status", STATUS_OPTIONS,
                                                   index=STATUS_OPTIONS.index(row['status']) if row['status'] in STATUS_OPTIONS else 0,
                                                   key=f"status_{row['id']}")
                        update_note = st.text_input("Add a note", key=f"note_{row['id']}")
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("💾 Update", key=f"upd_{row['id']}"):
                                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                                combined_note = f"{row['notes']}\n[{now}] {update_note}".strip() if update_note else row['notes']
                                c.execute("UPDATE proformas SET status=?, notes=?, last_updated=? WHERE id=?",
                                          (new_status, combined_note, now, row['id']))
                                conn.commit()
                                st.success("Updated!")
                                st.rerun()
                        with col_btn2:
                            if st.button("🗑️ Delete", key=f"del_pf_{row['id']}"):
                                c.execute("DELETE FROM proformas WHERE id=?", (row['id'],))
                                conn.commit()
                                st.rerun()

    with tab2:
        st.write("### Manually Add a Proforma")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            m_doc_no = st.text_input("Document #", value=datetime.now().strftime("%Y%m%d%H%M"))
            m_client = st.text_input("Client Name")
            m_amount = st.number_input("Amount (GHC)", min_value=0.0, format="%.2f")
        with col_m2:
            m_date = st.date_input("Issue Date", datetime.now())
            m_status = st.selectbox("Status", STATUS_OPTIONS)
            m_notes = st.text_area("Notes")

        if st.button("Add Proforma"):
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            c.execute("""INSERT INTO proformas (doc_no, client, amount, issue_date, status, notes, last_updated)
                         VALUES (?,?,?,?,?,?,?)""",
                      (m_doc_no, m_client, m_amount, m_date.strftime("%Y-%m-%d"), m_status, m_notes, now))
            conn.commit()
            st.success(f"Proforma #{m_doc_no} added!")
            st.rerun()

# =====================================================================
# ASSET MANAGER
# =====================================================================
elif choice == "Asset Manager":
    st.subheader("🗂️ Asset Manager")

    CATEGORIES = ["Equipment", "Vehicle", "Tools", "IT & Electronics", "Furniture", "Safety Gear", "Other"]
    CONDITIONS = ["Excellent", "Good", "Fair", "Needs Repair", "Out of Service"]

    tab_a1, tab_a2, tab_a3 = st.tabs(["📦 All Assets", "➕ Add Asset", "📊 Summary"])

    with tab_a1:
        df_assets = pd.read_sql_query("SELECT * FROM assets ORDER BY category, name", conn)
        if df_assets.empty:
            st.info("No assets recorded yet. Add your first asset in the 'Add Asset' tab.")
        else:
            col_af1, col_af2 = st.columns(2)
            with col_af1:
                filter_cat = st.multiselect("Filter by Category", CATEGORIES, default=CATEGORIES)
            with col_af2:
                filter_cond = st.multiselect("Filter by Condition", CONDITIONS, default=CONDITIONS)
            search_asset = st.text_input("🔍 Search by Name / Serial / Assigned To")

            filtered_a = df_assets[
                df_assets['category'].isin(filter_cat) &
                df_assets['condition'].isin(filter_cond)
            ]
            if search_asset:
                mask = (
                    filtered_a['name'].str.contains(search_asset, case=False, na=False) |
                    filtered_a['serial_no'].str.contains(search_asset, case=False, na=False) |
                    filtered_a['assigned_to'].str.contains(search_asset, case=False, na=False)
                )
                filtered_a = filtered_a[mask]

            CONDITION_ICON = {"Excellent": "🟢", "Good": "🟢", "Fair": "🟡", "Needs Repair": "🟠", "Out of Service": "🔴"}

            for _, asset in filtered_a.iterrows():
                icon = CONDITION_ICON.get(asset['condition'], "⚪")
                label = f"{icon} {asset['name']} | {asset['category']} | S/N: {asset['serial_no'] or 'N/A'} | {asset['location'] or 'No location'}"
                with st.expander(label):
                    col_v1, col_v2, col_v3 = st.columns(3)
                    with col_v1:
                        st.write(f"**Category:** {asset['category']}")
                        st.write(f"**Serial No:** {asset['serial_no'] or '—'}")
                        st.write(f"**Purchase Date:** {asset['purchase_date'] or '—'}")
                        st.write(f"**Purchase Value:** GHC {asset['purchase_value']:,.2f}" if asset['purchase_value'] else "**Purchase Value:** —")
                    with col_v2:
                        st.write(f"**Current Value:** GHC {asset['current_value']:,.2f}" if asset['current_value'] else "**Current Value:** —")
                        st.write(f"**Location:** {asset['location'] or '—'}")
                        st.write(f"**Assigned To:** {asset['assigned_to'] or '—'}")
                        st.write(f"**Condition:** {asset['condition']}")
                    with col_v3:
                        if asset['notes']:
                            st.write(f"**Notes:** {asset['notes']}")

                    st.write("---")
                    st.write("**Edit Asset**")
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        new_cond = st.selectbox("Update Condition", CONDITIONS,
                                                 index=CONDITIONS.index(asset['condition']) if asset['condition'] in CONDITIONS else 1,
                                                 key=f"cond_{asset['id']}")
                        new_location = st.text_input("Update Location", value=asset['location'] or "", key=f"loc_{asset['id']}")
                        new_assigned = st.text_input("Assigned To", value=asset['assigned_to'] or "", key=f"asgn_{asset['id']}")
                    with ec2:
                        new_curr_val = st.number_input("Current Value (GHC)", value=float(asset['current_value'] or 0), key=f"val_{asset['id']}")
                        new_notes = st.text_area("Notes", value=asset['notes'] or "", key=f"astnote_{asset['id']}")

                    col_ab1, col_ab2 = st.columns(2)
                    with col_ab1:
                        if st.button("💾 Save Changes", key=f"save_asset_{asset['id']}"):
                            c.execute("""UPDATE assets SET condition=?, location=?, assigned_to=?, current_value=?, notes=? WHERE id=?""",
                                      (new_cond, new_location, new_assigned, new_curr_val, new_notes, asset['id']))
                            conn.commit()
                            st.success("Asset updated!")
                            st.rerun()
                    with col_ab2:
                        if st.button("🗑️ Delete Asset", key=f"del_asset_{asset['id']}"):
                            c.execute("DELETE FROM assets WHERE id=?", (asset['id'],))
                            conn.commit()
                            st.rerun()

    with tab_a2:
        st.write("### Register New Asset")
        na1, na2 = st.columns(2)
        with na1:
            a_name = st.text_input("Asset Name *")
            a_category = st.selectbox("Category *", CATEGORIES)
            a_serial = st.text_input("Serial / Tag Number")
            a_purchase_date = st.date_input("Purchase Date", datetime.now())
            a_purchase_val = st.number_input("Purchase Value (GHC)", min_value=0.0, format="%.2f")
        with na2:
            a_curr_val = st.number_input("Current / Estimated Value (GHC)", min_value=0.0, format="%.2f")
            a_location = st.text_input("Location / Site")
            a_condition = st.selectbox("Condition", CONDITIONS)
            a_assigned = st.text_input("Assigned To")
            a_notes = st.text_area("Notes")

        if st.button("➕ Register Asset"):
            if not a_name.strip():
                st.error("Asset name is required.")
            else:
                c.execute("""INSERT INTO assets (name, category, serial_no, purchase_date, purchase_value,
                             current_value, location, condition, assigned_to, notes)
                             VALUES (?,?,?,?,?,?,?,?,?,?)""",
                          (a_name, a_category, a_serial, a_purchase_date.strftime("%Y-%m-%d"),
                           a_purchase_val, a_curr_val, a_location, a_condition, a_assigned, a_notes))
                conn.commit()
                st.success(f"✅ Asset '{a_name}' registered!")
                st.rerun()

    with tab_a3:
        st.write("### Asset Summary")
        df_sum = pd.read_sql_query("SELECT * FROM assets", conn)
        if df_sum.empty:
            st.info("No assets to summarize.")
        else:
            total_purchase = df_sum['purchase_value'].sum()
            total_current = df_sum['current_value'].sum()
            depreciation = total_purchase - total_current

            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Total Assets", len(df_sum))
            s2.metric("Total Purchase Value", f"GHC {total_purchase:,.2f}")
            s3.metric("Total Current Value", f"GHC {total_current:,.2f}")
            s4.metric("Total Depreciation", f"GHC {depreciation:,.2f}")

            st.write("---")
            st.write("**By Category**")
            by_cat = df_sum.groupby('category').agg(
                Count=('id', 'count'),
                Purchase_Value=('purchase_value', 'sum'),
                Current_Value=('current_value', 'sum')
            ).reset_index()
            by_cat.columns = ["Category", "Count", "Purchase Value (GHC)", "Current Value (GHC)"]
            st.dataframe(by_cat, use_container_width=True)

            st.write("**By Condition**")
            by_cond = df_sum.groupby('condition').agg(Count=('id', 'count')).reset_index()
            st.dataframe(by_cond, use_container_width=True)

# =====================================================================
# LOG TRANSACTION
# =====================================================================
elif choice == "Log Transaction":
    st.subheader("📝 Record Entry")
    col1, col2 = st.columns(2)
    with col1:
        t_type = st.selectbox("Type", ["Revenue", "Expenditure"])
        sector = st.selectbox("Sector", ["Engineering", "Transport", "Construction"])
        client = st.text_input("Name")
    with col2:
        amount = st.number_input("Amount (GHC)", min_value=0.0)
        date_t = st.date_input("Date", datetime.now())
        desc_t = st.text_area("Details")

    if st.button("Save Record"):
        c.execute("INSERT INTO transactions (type, sector, client, amount, date, description) VALUES (?,?,?,?,?,?)",
                  (t_type, sector, client, amount, date_t.strftime("%Y-%m-%d"), desc_t))
        conn.commit()
        st.success("Transaction saved!")

# =====================================================================
# DASHBOARD
# =====================================================================
else:
    st.subheader("📊 Business Intelligence")

    # Transactions summary
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    if not df.empty:
        rev = df[df['type'] == 'Revenue']['amount'].sum()
        exp = df[df['type'] == 'Expenditure']['amount'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Revenue", f"GHC {rev:,.2f}")
        c2.metric("Total Expenditure", f"GHC {exp:,.2f}")
        c3.metric("Net Profit", f"GHC {rev - exp:,.2f}")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No financial records found.")

    st.write("---")

    # Proforma quick summary
    df_pf = pd.read_sql_query("SELECT * FROM proformas", conn)
    if not df_pf.empty:
        st.write("### 📋 Proforma Overview")
        p1, p2, p3 = st.columns(3)
        p1.metric("Total Proformas", len(df_pf))
        p2.metric("Outstanding Value", f"GHC {df_pf[df_pf['status'].isin(['Sent','Under Review','Approved','Partially Paid'])]['amount'].sum():,.2f}")
        p3.metric("Fully Paid", f"GHC {df_pf[df_pf['status']=='Fully Paid']['amount'].sum():,.2f}")

    # Asset quick summary
    df_ast = pd.read_sql_query("SELECT * FROM assets", conn)
    if not df_ast.empty:
        st.write("### 🗂️ Asset Overview")
        a1, a2, a3 = st.columns(3)
        a1.metric("Total Assets", len(df_ast))
        a2.metric("Total Asset Value", f"GHC {df_ast['current_value'].sum():,.2f}")
        a3.metric("Needs Attention", len(df_ast[df_ast['condition'].isin(['Needs Repair','Out of Service'])]))