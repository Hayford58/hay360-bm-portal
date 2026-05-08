import streamlit as st
import pandas as pd
import sqlite3
from fpdf import FPDF
from datetime import datetime
import os
import hashlib
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

# ─────────────────────────────────────────────
# LOGO  (base64 encode for embedding in HTML)
# ─────────────────────────────────────────────
import base64
def _load_logo_b64(path="Logo.png"):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return ""
logo_b64 = _load_logo_b64()

# ─────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────
st.set_page_config(page_title="HAY360 Portal", layout="wide", page_icon="⚙️")

# ─────────────────────────────────────────────
# CUSTOM CSS — sleek dark-gold theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1117 0%, #1a1f2e 100%);
    border-right: 1px solid #c8a84b33;
}
section[data-testid="stSidebar"] * { color: #e8e0cc !important; }

/* ── Main background ── */
.main { background-color: #0f1117; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #1a1f2e 0%, #141824 100%);
    border: 1px solid #c8a84b44;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 4px 20px rgba(200,168,75,0.08);
}
[data-testid="metric-container"] label { color: #c8a84b !important; font-size: 0.75rem; letter-spacing: 1px; text-transform: uppercase; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 700; font-size: 1.6rem; }

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #c8a84b, #a07830);
    color: #0f1117 !important;
    font-weight: 700;
    border: none;
    border-radius: 8px;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #e0bc5a, #c8a84b);
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(200,168,75,0.4);
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { border-bottom: 2px solid #c8a84b33; gap: 4px; }
.stTabs [data-baseweb="tab"] { background: #1a1f2e; border-radius: 8px 8px 0 0; color: #888; padding: 8px 20px; }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg,#c8a84b,#a07830) !important; color: #0f1117 !important; font-weight: 700; }

/* ── Expanders ── */
details { background: #1a1f2e; border: 1px solid #c8a84b22; border-radius: 10px; margin-bottom: 6px; }
summary { color: #e8e0cc !important; padding: 10px 16px; }

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea, .stSelectbox div, .stNumberInput input {
    background: #1a1f2e !important;
    color: #e8e0cc !important;
    border: 1px solid #c8a84b33 !important;
    border-radius: 8px !important;
}

/* ── Dataframe ── */
.stDataFrame { border: 1px solid #c8a84b22; border-radius: 10px; }

/* ── Hero banner ── */
.hero-banner {
    background: linear-gradient(135deg, #1a1f2e 0%, #0f1117 50%, #1a1509 100%);
    border: 1px solid #c8a84b55;
    border-radius: 16px;
    padding: 32px 40px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute; top: 0; right: 0; width: 300px; height: 100%;
    background: radial-gradient(ellipse at right, rgba(200,168,75,0.12) 0%, transparent 70%);
}
.hero-title { font-size: 2rem; font-weight: 700; color: #c8a84b; margin: 0; letter-spacing: -0.5px; }
.hero-sub   { font-size: 0.95rem; color: #888; margin-top: 4px; }
.hero-stat-row { display: flex; gap: 32px; margin-top: 24px; flex-wrap: wrap; }
.hero-stat { border-left: 3px solid #c8a84b; padding-left: 12px; }
.hero-stat-val { font-size: 1.4rem; font-weight: 700; color: #fff; }
.hero-stat-lbl { font-size: 0.72rem; color: #888; letter-spacing: 1px; text-transform: uppercase; margin-top: 2px; }

/* ── Section headers ── */
.section-header {
    display: flex; align-items: center; gap: 10px;
    border-bottom: 2px solid #c8a84b33;
    padding-bottom: 8px; margin: 24px 0 16px;
}
.section-header-text { font-size: 1.05rem; font-weight: 600; color: #c8a84b; letter-spacing: 0.5px; }

/* ── KPI pill ── */
.kpi-pill {
    display: inline-block;
    background: #c8a84b22;
    border: 1px solid #c8a84b55;
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 0.75rem;
    color: #c8a84b;
    font-weight: 600;
    margin-right: 6px;
    margin-bottom: 6px;
}

/* ── Alert ── */
.stAlert { border-radius: 10px; }

/* ── Radio ── */
.stRadio label { color: #e8e0cc !important; }

/* ── Checkbox ── */
.stCheckbox label { color: #e8e0cc !important; }

/* ── Text ── */
h1,h2,h3,h4,h5,h6,p,label,span,div { color: #e8e0cc; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────────────
conn = sqlite3.connect('business_data.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT,
              full_name TEXT, role TEXT, active INTEGER DEFAULT 1, created TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS transactions
             (id INTEGER PRIMARY KEY, type TEXT, sector TEXT, client TEXT,
              amount REAL, date TEXT, description TEXT, created_by TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS proformas
             (id INTEGER PRIMARY KEY, doc_no TEXT, client TEXT, amount REAL,
              issue_date TEXT, status TEXT, notes TEXT, last_updated TEXT, created_by TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS assets
             (id INTEGER PRIMARY KEY, name TEXT, category TEXT, serial_no TEXT,
              purchase_date TEXT, purchase_value REAL, current_value REAL,
              location TEXT, condition TEXT, assigned_to TEXT, notes TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS materials
             (id INTEGER PRIMARY KEY, name TEXT, category TEXT, unit TEXT,
              qty_in_stock REAL, reorder_level REAL, unit_cost REAL,
              supplier TEXT, location TEXT, notes TEXT, last_updated TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS material_movements
             (id INTEGER PRIMARY KEY, material_id INTEGER, movement_type TEXT,
              quantity REAL, project_ref TEXT, notes TEXT, moved_by TEXT, moved_date TEXT)''')
conn.commit()

# ── Migrations ──
for col, typedef in [("category","TEXT"),("serial_no","TEXT"),("purchase_date","TEXT"),
                     ("purchase_value","REAL"),("current_value","REAL"),("location","TEXT"),
                     ("condition","TEXT"),("assigned_to","TEXT"),("notes","TEXT")]:
    if col not in [r[1] for r in c.execute("PRAGMA table_info(assets)").fetchall()]:
        c.execute(f"ALTER TABLE assets ADD COLUMN {col} {typedef}")
for col, typedef in [("created_by","TEXT")]:
    if col not in [r[1] for r in c.execute("PRAGMA table_info(proformas)").fetchall()]:
        c.execute(f"ALTER TABLE proformas ADD COLUMN {col} {typedef}")
conn.commit()

# ─────────────────────────────────────────────
# AUTH HELPERS
# ─────────────────────────────────────────────
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def verify_user(username, password):
    row = c.execute("SELECT * FROM users WHERE username=? AND active=1", (username,)).fetchone()
    if row and row[2] == hash_pw(password):
        return {"id": row[0], "username": row[1], "full_name": row[3], "role": row[4]}
    return None

if not c.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
    c.execute("INSERT INTO users (username,password_hash,full_name,role,created) VALUES (?,?,?,?,?)",
              ("admin", hash_pw("admin123"), "Administrator", "Admin", datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()

ROLE_MENUS = {
    "Admin":   ["Dashboard","Document Generator","Proforma Tracker","Material Inventory","Asset Manager","Log Transaction","User Management"],
    "Manager": ["Dashboard","Document Generator","Proforma Tracker","Material Inventory","Asset Manager","Log Transaction"],
    "Staff":   ["Dashboard","Document Generator","Material Inventory"],
    "Viewer":  ["Dashboard"],
}

ADMIN_EMAILS = ["hayforddanso@outlook.com", "hay360services@outlook.com"]
SMTP_CONFIG  = {
    "host":     "smtp.gmail.com",
    "port":     587,
    "user":     "hay360services@gmail.com",  # ← your Gmail address
    "password": "",                           # ← 16-char Gmail App Password
}

# ─────────────────────────────────────────────
# EMAIL HELPER
# ─────────────────────────────────────────────
def send_pdf_email(pdf_path, doc_type, doc_no, client, total, smtp_password=""):
    """Send PDF as attachment to admin emails. Returns (success, message)."""
    try:
        host   = SMTP_CONFIG["host"]
        port   = SMTP_CONFIG["port"]
        sender = SMTP_CONFIG["user"]
        pw     = smtp_password or SMTP_CONFIG["password"]
        if not pw:
            return False, "Gmail App Password not configured. Set it in Email Settings (sidebar)."

        subject = f"HAY360 | New {doc_type} #{doc_no} — {client}"
        body    = (f"A new {doc_type} has been generated.\n\n"
                   f"Document #: {doc_no}\n"
                   f"Client:     {client}\n"
                   f"Amount:     GHC {total:,.2f}\n"
                   f"Date:       {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
                   f"Please find the PDF attached.\n\n— HAY360 Services Portal")

        msg = MIMEMultipart()
        msg["From"]    = sender
        msg["To"]      = ", ".join(ADMIN_EMAILS)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with open(pdf_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(pdf_path)}")
        msg.attach(part)

        with smtplib.SMTP(host, port) as server:
            server.ehlo(); server.starttls(); server.ehlo()
            server.login(sender, pw)
            server.sendmail(sender, ADMIN_EMAILS, msg.as_string())
        return True, f"Email sent to {', '.join(ADMIN_EMAILS)}"
    except Exception as e:
        return False, str(e)

# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
for key, default in [("logged_in", False), ("user", None),
                     ("smtp_password", ""),
                     ("rows", [{"item":1,"desc":"SACP inspection: Cargo pipelines, Hydrant pipelines, product pipelines, storage tanks and hydrant tank","qty":1.0,"unit":"lot","rate":25000.0}]),
                     ("mat_rows", [])]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────
# LOGIN WALL
# ─────────────────────────────────────────────
if not st.session_state.logged_in:
    st.markdown(f"""
    <div style="display:flex;justify-content:center;align-items:center;min-height:60vh;flex-direction:column;">
        <div style="background:linear-gradient(135deg,#1a1f2e,#141824);border:1px solid #c8a84b55;
                    border-radius:20px;padding:48px 56px;max-width:420px;width:100%;text-align:center;
                    box-shadow:0 20px 60px rgba(200,168,75,0.12);">
            <div style="margin-bottom:12px;">
                <img src="data:image/png;base64,{logo_b64}" style="width:140px;height:140px;object-fit:contain;border-radius:12px;" />
            </div>
            <div style="color:#666;font-size:0.85rem;margin-bottom:32px;">Professional Business Portal</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_m, col_r = st.columns([1, 1.2, 1])
    with col_m:
        username = st.text_input("Username", placeholder="Enter username", label_visibility="collapsed")
        password = st.text_input("Password", type="password", placeholder="Enter password", label_visibility="collapsed")
        if st.button("Sign In →", use_container_width=True):
            u = verify_user(username.strip(), password)
            if u:
                st.session_state.logged_in = True
                st.session_state.user = u
                st.rerun()
            else:
                st.error("Invalid credentials.")
        st.caption("Default: admin / admin123")
    st.stop()

# ─────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────
user    = st.session_state.user
role    = user["role"]
allowed = ROLE_MENUS.get(role, ["Dashboard"])

# Sidebar
st.sidebar.markdown(f"""
<div style="padding:16px 0 8px;text-align:center;">
    <img src="data:image/png;base64,{logo_b64}" style="width:110px;height:110px;object-fit:contain;border-radius:10px;margin-bottom:8px;" />
    <div style="font-size:0.8rem;color:#888;margin-top:4px;">👤 {user['full_name']}</div>
    <div style="font-size:0.72rem;color:#c8a84b77;letter-spacing:1px;text-transform:uppercase;">{role}</div>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")
choice = st.sidebar.selectbox("Navigation", allowed, label_visibility="collapsed")

# Email settings in sidebar (admin only)
if role == "Admin":
    with st.sidebar.expander("📧 Email Settings"):
        smtp_pw = st.text_input("Gmail App Password", type="password",
                                value=st.session_state.smtp_password,
                                help="16-character App Password from Google Account → Security → App Passwords")
        if st.button("Save Password", key="save_smtp"):
            st.session_state.smtp_password = smtp_pw
            st.success("Saved for this session.")
        st.caption(f"Sends to:\n" + "\n".join(ADMIN_EMAILS))

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Sign Out", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()

# ─────────────────────────────────────────────
# PDF HEADER HELPER
# ─────────────────────────────────────────────
def pdf_header(pdf, mf):
    if os.path.exists("logo.png"):
        pdf.image("logo.png", 10, 8, 30)
    pdf.set_font(mf, 'B', 16); pdf.cell(0, 8, "HAY360 SERVICES", ln=True, align='C')
    pdf.set_font(mf, 'B', 9);  pdf.cell(0, 5, "ENGINEERING LOGISTICS TRANSPORT", ln=True, align='C')
    pdf.set_font(mf, size=9);  pdf.cell(0, 4, "Accra Tema | +233246241338 | hay360services@outlook.com", ln=True, align='C')
    pdf.ln(10)

def build_pdf(doc_type, doc_no, c_name, date_issue, project_info, all_rows, terms, notes_txt):
    """Builds and saves PDF, returns filename."""
    pdf = FPDF(); pdf.add_page(); mf = "Courier"
    pdf_header(pdf, mf)
    pdf.set_font(mf,'B',11); pdf.cell(0,7,f"{doc_type.upper()} # {doc_no}",ln=True,align='R')
    pdf.set_font(mf,size=9); pdf.cell(0,5,f"Date: {date_issue.strftime('%d/%m/%Y')}",ln=True,align='R')
    if project_info.strip():
        pdf.set_font(mf,'B',10); pdf.cell(0,7,"Project Details:",ln=True)
        pdf.set_font(mf,size=9); pdf.multi_cell(0,5,project_info); pdf.ln(5)
    pdf.set_font(mf,'B',10); pdf.cell(0,7,f"BILL TO: {c_name}",ln=True)
    pdf.set_font(mf,size=10); pdf.cell(0,5,"Accra, Ghana",ln=True); pdf.ln(5)

    pdf.set_font(mf,'B',8)
    w=[12,88,12,12,33,33]
    hdrs=["ITM","DESCRIPTION","QTY","UNT","RATE(GHC)","AMOUNT(GHC)"]
    for i,h in enumerate(hdrs): pdf.cell(w[i],10,h,border=1,align='C')
    pdf.ln()

    pdf.set_font(mf,size=8); grand=0
    for r in all_rows:
        amt=r['qty']*r['rate']; grand+=amt
        lh=5; lines=pdf.multi_cell(w[1],lh,str(r['desc']),split_only=True)
        rh=max(10,len(lines)*lh+4); cx,cy=pdf.get_x(),pdf.get_y()
        pdf.cell(w[0],rh,str(r['item']),border=1,align='C')
        pdf.set_xy(cx+w[0],cy); pdf.multi_cell(w[1],lh,str(r['desc']),border=0)
        pdf.rect(cx+w[0],cy,w[1],rh)
        pdf.set_xy(cx+w[0]+w[1],cy)
        pdf.cell(w[2],rh,str(r['qty']),border=1,align='C')
        pdf.cell(w[3],rh,str(r['unit']),border=1,align='C')
        pdf.cell(w[4],rh,f"{r['rate']:,.2f}",border=1,align='R')
        pdf.cell(w[5],rh,f"{amt:,.2f}",border=1,align='R'); pdf.ln(rh)

    pdf.ln(5); pdf.set_x(124); pdf.set_font(mf,'B',9)
    pdf.cell(33,8,"TOTAL DUE",border=1)
    pdf.cell(33,8,f"GHC {grand:,.2f}",border=1,align='R',ln=True)
    pdf.ln(10); pdf.set_font(mf,'B',9); pdf.cell(0,5,"TERMS OF PAYMENT",ln=True)
    pdf.set_font(mf,size=8); pdf.multi_cell(0,4,terms)
    pdf.ln(5); pdf.set_font(mf,'B',9); pdf.cell(0,5,"TECHNICAL NOTES",ln=True)
    pdf.set_font(mf,size=8); pdf.multi_cell(0,4,notes_txt)
    pdf.ln(10); pdf.set_font(mf,'I',10)
    pdf.cell(0,10,"Thank you for your continued business",ln=True,align='C')
    pdf.set_font(mf,'B',10); pdf.cell(0,5,"HAY360 SERVICES",ln=True,align='C')

    fname=f"{doc_type}_{doc_no}.pdf"; pdf.output(fname)
    return fname, grand

# =====================================================================
# USER MANAGEMENT
# =====================================================================
if choice == "User Management":
    st.markdown('<div class="section-header"><span style="font-size:1.3rem">👥</span><span class="section-header-text">USER MANAGEMENT</span></div>', unsafe_allow_html=True)
    tab_u1, tab_u2 = st.tabs(["All Users", "➕ Add User"])
    with tab_u1:
        df_users = pd.read_sql_query("SELECT id,username,full_name,role,active,created FROM users", conn)
        for _, u in df_users.iterrows():
            icon = "🟢" if u['active'] else "🔴"
            with st.expander(f"{icon} {u['full_name']} ({u['username']}) — {u['role']}"):
                eu1, eu2 = st.columns(2)
                with eu1:
                    st.write(f"**Username:** {u['username']}")
                    st.write(f"**Created:** {u['created'] or '—'}")
                    nr = st.selectbox("Role", list(ROLE_MENUS.keys()),
                                      index=list(ROLE_MENUS.keys()).index(u['role']) if u['role'] in ROLE_MENUS else 0,
                                      key=f"urole_{u['id']}")
                    na = st.selectbox("Status", ["Active","Disabled"], index=0 if u['active'] else 1, key=f"uact_{u['id']}")
                with eu2:
                    rpw = st.text_input("Reset Password", type="password", key=f"upw_{u['id']}")
                    if st.button("💾 Save", key=f"usave_{u['id']}"):
                        av = 1 if na=="Active" else 0
                        if rpw.strip():
                            c.execute("UPDATE users SET role=?,active=?,password_hash=? WHERE id=?", (nr,av,hash_pw(rpw),u['id']))
                        else:
                            c.execute("UPDATE users SET role=?,active=? WHERE id=?", (nr,av,u['id']))
                        conn.commit(); st.success("Updated!"); st.rerun()
                    if u['username']!="admin" and st.button("🗑️ Delete", key=f"udel_{u['id']}"):
                        c.execute("DELETE FROM users WHERE id=?", (u['id'],))
                        conn.commit(); st.rerun()
    with tab_u2:
        nu1,nu2 = st.columns(2)
        with nu1:
            nu_name=st.text_input("Full Name"); nu_user=st.text_input("Username")
        with nu2:
            nu_role=st.selectbox("Role",list(ROLE_MENUS.keys())); nu_pw=st.text_input("Password",type="password")
        if st.button("➕ Create User"):
            if not all([nu_name.strip(),nu_user.strip(),nu_pw.strip()]):
                st.error("All fields required.")
            else:
                try:
                    c.execute("INSERT INTO users (username,password_hash,full_name,role,created) VALUES (?,?,?,?,?)",
                              (nu_user.strip(),hash_pw(nu_pw),nu_name.strip(),nu_role,datetime.now().strftime("%Y-%m-%d %H:%M")))
                    conn.commit(); st.success(f"User '{nu_user}' created!"); st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Username already exists.")

# =====================================================================
# DOCUMENT GENERATOR  (with inventory billing + email)
# =====================================================================
elif choice == "Document Generator":
    st.markdown('<div class="section-header"><span style="font-size:1.3rem">📄</span><span class="section-header-text">DOCUMENT GENERATOR</span></div>', unsafe_allow_html=True)

    doc_type = st.radio("Document Type", ["Proforma","Invoice","Receipt"], horizontal=True)
    auto_no  = datetime.now().strftime("%Y%m%d%H%M")

    col_a, col_b = st.columns(2)
    with col_a:
        c_name       = st.text_input("BILL TO:", value="MATRIX ENERGY GROUP")
        project_info = st.text_area("Project / Work Details (Optional):", value="", key="project_info")
        doc_no       = st.text_input("Document #:", value=auto_no)
    with col_b:
        date_issue = st.date_input("Date of Issue", datetime.now())

    # ── CUSTOM LINE ITEMS ─────────────────────
    st.markdown("---")
    st.markdown("##### 📝 Custom Line Items")
    for i, row in enumerate(st.session_state.rows):
        cols = st.columns([0.5, 3.5, 1, 1, 1.8, 0.5])
        st.session_state.rows[i]["item"] = i+1
        st.session_state.rows[i]["desc"] = cols[1].text_area("Description", value=row["desc"], key=f"desc_{i}", height=60)
        st.session_state.rows[i]["qty"]  = cols[2].number_input("Qty", value=float(row["qty"]), key=f"qty_{i}", min_value=0.0, step=0.5, format="%.2f")
        st.session_state.rows[i]["unit"] = cols[3].text_input("Unit", value=row["unit"], key=f"unit_{i}")
        st.session_state.rows[i]["rate"] = cols[4].number_input("Rate (GHC)", value=float(row["rate"]), key=f"rate_{i}")
        if cols[5].button("🗑️", key=f"del_{i}"):
            st.session_state.rows.pop(i); st.rerun()
    if st.button("➕ Add Custom Row"):
        st.session_state.rows.append({"item":len(st.session_state.rows)+1,"desc":"","qty":1.0,"unit":"lot","rate":0.0})
        st.rerun()

    # ── MATERIAL BILLING ──────────────────────
    st.markdown("---")
    st.markdown("##### 🧱 Add Materials from Inventory")
    df_mats = pd.read_sql_query("SELECT id,name,unit,qty_in_stock,unit_cost FROM materials WHERE qty_in_stock>0 ORDER BY name", conn)

    if df_mats.empty:
        st.info("No materials in stock. Add materials in Material Inventory first.")
    else:
        # Show current mat_rows
        if st.session_state.mat_rows:
            mat_remove = None
            for mi, mr in enumerate(st.session_state.mat_rows):
                mc1,mc2,mc3,mc4,mc5 = st.columns([2.5,0.8,1,1.5,0.5])
                mc1.markdown(f"**{mr['desc']}**")
                st.session_state.mat_rows[mi]["qty"]  = mc2.number_input("Qty", value=float(mr["qty"]), min_value=0.01, step=0.5, format="%.2f", key=f"mq_{mi}")
                st.session_state.mat_rows[mi]["unit"] = mc3.text_input("Unit", value=str(mr["unit"]), key=f"mu_{mi}")
                st.session_state.mat_rows[mi]["rate"] = mc4.number_input("Rate (GHC)", value=float(mr["rate"]), key=f"mr_{mi}")
                if mc5.button("🗑️", key=f"mrm_{mi}"):
                    mat_remove = mi
            if mat_remove is not None:
                st.session_state.mat_rows.pop(mat_remove); st.rerun()

        # Add material picker
        ma1, ma2, ma3, ma4 = st.columns([3, 0.8, 1, 1.5])
        with ma1:
            mat_opts = {f"{r['name']} (Stock: {r['qty_in_stock']} {r['unit']})": r for _, r in df_mats.iterrows()}
            sel_label = st.selectbox("Select Material", ["— choose —"] + list(mat_opts.keys()), key="matpick")
        with ma2:
            add_qty = st.number_input("Qty to bill", min_value=0.01, value=1.0, step=0.5, format="%.2f", key="mat_add_qty")
        with ma3:
            if sel_label != "— choose —":
                sel_mat = mat_opts[sel_label]
                override_unit = st.text_input("Unit", value=str(sel_mat['unit']), key="mat_unit_override")
            else:
                override_unit = ""
        with ma4:
            if sel_label != "— choose —":
                sel_mat = mat_opts[sel_label]
                override_rate = st.number_input("Rate (GHC)", value=float(sel_mat['unit_cost']), key="mat_rate_override")
            else:
                override_rate = 0.0

        if st.button("➕ Add Material to Bill") and sel_label != "— choose —":
            sel_mat = mat_opts[sel_label]
            st.session_state.mat_rows.append({
                "item": 0, "desc": sel_mat['name'], "qty": add_qty,
                "unit": override_unit if override_unit.strip() else sel_mat['unit'], "rate": override_rate,
                "mat_id": int(sel_mat['id'])
            })
            st.rerun()

    # ── TOTALS PREVIEW ────────────────────────
    # Build all_rows every render and store in session so the generate button
    # always uses the most recent snapshot (avoids mat_rows being empty on rerun)
    _rows_snapshot = []
    _counter = 1
    for r in st.session_state.rows:
        r2 = dict(r); r2["item"] = _counter; _counter += 1; _rows_snapshot.append(r2)
    for r in st.session_state.mat_rows:
        r2 = dict(r); r2["item"] = _counter; _counter += 1; _rows_snapshot.append(r2)
    st.session_state["_all_rows_snapshot"] = _rows_snapshot

    all_rows = _rows_snapshot  # alias for compatibility below

    if all_rows:
        preview_total = sum(r['qty']*r['rate'] for r in all_rows)
        st.markdown(f"""
        <div style="background:#1a1f2e;border:1px solid #c8a84b44;border-radius:10px;
                    padding:16px 24px;margin:12px 0;display:flex;justify-content:space-between;align-items:center;">
            <span style="color:#888;">Line Items: <strong style="color:#fff;">{len(all_rows)}</strong></span>
            <span style="color:#888;">Custom: <strong style="color:#fff;">{len(st.session_state.rows)}</strong>
                  &nbsp;|&nbsp; Materials: <strong style="color:#c8a84b;">{len(st.session_state.mat_rows)}</strong></span>
            <span style="font-size:1.2rem;font-weight:700;color:#c8a84b;">Total: GHC {preview_total:,.2f}</span>
        </div>
        """, unsafe_allow_html=True)

    # ── TERMS & NOTES ─────────────────────────
    st.markdown("---")
    ct1, ct2 = st.columns(2)
    with ct1:
        terms = st.text_area("Payment Terms", value="1. 30% Advance: Mobilization fee.\n2. 40% Progress Payment.\n3. 30% Final Payment.\n4. Tax Exclusion: Total excludes all applicable taxes.", key="payment_terms")
    with ct2:
        notes_txt = st.text_area("Technical Notes", value="1. Access: Provide unrestricted site access.\n2. Reporting: Compliance against NACE/AMPP standards (-850 mV analysis).", key="technical_notes")

    # ── GENERATE OPTIONS ──────────────────────
    st.markdown("---")
    go1, go2, go3 = st.columns(3)
    with go1:
        save_tracker  = st.checkbox("📋 Save to Proforma Tracker", value=True) if doc_type=="Proforma" else False
    with go2:
        deduct_stock  = st.checkbox("📦 Deduct material qty from stock", value=True) if st.session_state.mat_rows else False
    with go3:
        send_email    = st.checkbox("📧 Email PDF to admins", value=True)

    generate_btn = st.button(f"⚡ Generate {doc_type} PDF", use_container_width=True)

    if generate_btn:
        # Use the snapshot captured just before the button rendered
        all_rows = st.session_state.get("_all_rows_snapshot", all_rows)
        if not all_rows:
            st.error("Add at least one line item before generating.")
        else:
            pdf_name, grand_total = build_pdf(doc_type, doc_no, c_name, date_issue, project_info, all_rows, terms, notes_txt)
            st.success(f"✅ Generated: **{pdf_name}**  |  Total: **GHC {grand_total:,.2f}**")

            # Deduct inventory stock
            if deduct_stock:
                for mr in st.session_state.mat_rows:
                    if "mat_id" in mr:
                        row_db = c.execute("SELECT qty_in_stock FROM materials WHERE id=?", (mr['mat_id'],)).fetchone()
                        if row_db:
                            new_q = max(0, row_db[0] - mr['qty'])
                            now = datetime.now().strftime("%Y-%m-%d %H:%M")
                            c.execute("UPDATE materials SET qty_in_stock=?,last_updated=? WHERE id=?", (new_q, now, mr['mat_id']))
                            c.execute("""INSERT INTO material_movements
                                         (material_id,movement_type,quantity,project_ref,notes,moved_by,moved_date)
                                         VALUES (?,?,?,?,?,?,?)""",
                                      (mr['mat_id'],"Issue (OUT)",mr['qty'],doc_no,
                                       f"Billed on {doc_type} #{doc_no}",user['full_name'],now))
                conn.commit()
                st.info("📦 Stock deducted and movements logged.")

            # Save to proforma tracker
            if save_tracker and doc_type=="Proforma":
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                c.execute("INSERT INTO proformas (doc_no,client,amount,issue_date,status,notes,last_updated,created_by) VALUES (?,?,?,?,?,?,?,?)",
                          (doc_no,c_name,grand_total,date_issue.strftime("%Y-%m-%d"),"Sent",project_info,now,user['username']))
                conn.commit()
                st.info(f"📋 Proforma #{doc_no} saved to Tracker.")

            # Send email
            if send_email:
                pw = st.session_state.smtp_password
                ok, msg = send_pdf_email(pdf_name, doc_type, doc_no, c_name, grand_total, pw)
                if ok:
                    st.success(f"📧 {msg}")
                else:
                    st.warning(f"📧 Email not sent: {msg}")

            # Clear material rows after generation
            st.session_state.mat_rows = []

# =====================================================================
# PROFORMA TRACKER
# =====================================================================
elif choice == "Proforma Tracker":
    st.markdown('<div class="section-header"><span style="font-size:1.3rem">📋</span><span class="section-header-text">PROFORMA TRACKER</span></div>', unsafe_allow_html=True)
    STATUS_OPTIONS = ["Draft","Sent","Under Review","Approved","Partially Paid","Fully Paid","Cancelled","Overdue"]
    STATUS_COLORS  = {"Draft":"⚪","Sent":"🔵","Under Review":"🟡","Approved":"🟢",
                      "Partially Paid":"🟠","Fully Paid":"✅","Cancelled":"🔴","Overdue":"🚨"}

    tab1, tab2 = st.tabs(["📊 All Proformas","➕ Add Manually"])
    with tab1:
        df_pf = pd.read_sql_query("SELECT * FROM proformas ORDER BY issue_date DESC", conn)
        if df_pf.empty:
            st.info("No proformas yet.")
        else:
            tv=df_pf['amount'].sum(); pv=df_pf[df_pf['status']=='Fully Paid']['amount'].sum()
            pend=df_pf[df_pf['status'].isin(['Sent','Under Review','Approved','Partially Paid'])]['amount'].sum()
            ov=len(df_pf[df_pf['status']=='Overdue'])
            m1,m2,m3,m4=st.columns(4)
            m1.metric("Total Value",f"GHC {tv:,.2f}"); m2.metric("Collected",f"GHC {pv:,.2f}")
            m3.metric("Outstanding",f"GHC {pend:,.2f}"); m4.metric("Overdue",f"{ov} invoice(s)")
            st.write("---")
            cf1,cf2=st.columns(2)
            with cf1: fs=st.multiselect("Filter Status",STATUS_OPTIONS,default=STATUS_OPTIONS)
            with cf2: fc=st.text_input("Search Client")
            filtered=df_pf[df_pf['status'].isin(fs)]
            if fc: filtered=filtered[filtered['client'].str.contains(fc,case=False,na=False)]
            for _,row in filtered.iterrows():
                icon=STATUS_COLORS.get(row['status'],"⚪")
                with st.expander(f"{icon} #{row['doc_no']} | {row['client']} | GHC {row['amount']:,.2f} | {row['issue_date']}"):
                    ci1,ci2=st.columns(2)
                    with ci1:
                        st.write(f"**Client:** {row['client']}")
                        st.write(f"**Amount:** GHC {row['amount']:,.2f}")
                        st.write(f"**Issued:** {row['issue_date']}")
                        if row['notes']: st.write(f"**Notes:** {row['notes']}")
                    with ci2:
                        if role in ["Admin","Manager"]:
                            ns=st.selectbox("Status",STATUS_OPTIONS,index=STATUS_OPTIONS.index(row['status']) if row['status'] in STATUS_OPTIONS else 0,key=f"st_{row['id']}")
                            un=st.text_input("Note",key=f"nt_{row['id']}")
                            cb1,cb2=st.columns(2)
                            with cb1:
                                if st.button("💾",key=f"upd_{row['id']}"):
                                    now=datetime.now().strftime("%Y-%m-%d %H:%M")
                                    comb=f"{row['notes']}\n[{now}] {un}".strip() if un else row['notes']
                                    c.execute("UPDATE proformas SET status=?,notes=?,last_updated=? WHERE id=?",(ns,comb,now,row['id']))
                                    conn.commit(); st.success("Updated!"); st.rerun()
                            with cb2:
                                if role=="Admin" and st.button("🗑️",key=f"dpf_{row['id']}"):
                                    c.execute("DELETE FROM proformas WHERE id=?",(row['id'],)); conn.commit(); st.rerun()
                        else:
                            st.info("View only.")
    with tab2:
        if role not in ["Admin","Manager"]:
            st.warning("No permission.")
        else:
            cm1,cm2=st.columns(2)
            with cm1:
                md=st.text_input("Doc #",value=datetime.now().strftime("%Y%m%d%H%M"))
                mc=st.text_input("Client"); ma=st.number_input("Amount (GHC)",min_value=0.0,format="%.2f")
            with cm2:
                mdt=st.date_input("Issue Date",datetime.now()); mst=st.selectbox("Status",STATUS_OPTIONS)
                mn=st.text_area("Notes", key="proforma_add_notes")
            if st.button("Add Proforma"):
                now=datetime.now().strftime("%Y-%m-%d %H:%M")
                c.execute("INSERT INTO proformas (doc_no,client,amount,issue_date,status,notes,last_updated,created_by) VALUES (?,?,?,?,?,?,?,?)",
                          (md,mc,ma,mdt.strftime("%Y-%m-%d"),mst,mn,now,user['username']))
                conn.commit(); st.success(f"#{md} added!"); st.rerun()

# =====================================================================
# MATERIAL INVENTORY
# =====================================================================
elif choice == "Material Inventory":
    st.markdown('<div class="section-header"><span style="font-size:1.3rem">🧱</span><span class="section-header-text">MATERIAL INVENTORY</span></div>', unsafe_allow_html=True)
    MAT_CAT=["Pipes & Fittings","Electrical","Chemicals","PPE / Safety","Fuel & Lubricants",
             "Structural Steel","Concrete & Aggregates","Tools & Consumables","General","Other"]

    tab_m1,tab_m2,tab_m3,tab_m4=st.tabs(["📦 Stock List","➕ Add Material","🔄 Record Movement","📊 Summary"])

    with tab_m1:
        df_mat=pd.read_sql_query("SELECT * FROM materials ORDER BY category,name",conn)
        if df_mat.empty: st.info("No materials yet.")
        else:
            low=df_mat[df_mat['qty_in_stock']<=df_mat['reorder_level']]
            if not low.empty: st.warning(f"⚠️ **{len(low)} item(s) at or below reorder level!** — "+", ".join(low['name'].tolist()))
            mf1,mf2=st.columns(2)
            with mf1: fmc=st.multiselect("Category",MAT_CAT,default=MAT_CAT)
            with mf2: smat=st.text_input("🔍 Search")
            fm=df_mat[df_mat['category'].isin(fmc)]
            if smat: fm=fm[fm['name'].str.contains(smat,case=False,na=False)|fm['supplier'].str.contains(smat,case=False,na=False)]
            for _,mat in fm.iterrows():
                si="🔴" if mat['qty_in_stock']<=mat['reorder_level'] else ("🟡" if mat['qty_in_stock']<=mat['reorder_level']*1.5 else "🟢")
                label=f"{si} {mat['name']} | {mat['category']} | {mat['qty_in_stock']:,.1f} {mat['unit']} | GHC {mat['unit_cost']:,.2f}/unit"
                with st.expander(label):
                    mv1,mv2=st.columns(2)
                    with mv1:
                        st.write(f"**Category:** {mat['category']}")
                        st.write(f"**In Stock:** {mat['qty_in_stock']:,.2f} {mat['unit']}")
                        st.write(f"**Reorder Level:** {mat['reorder_level']:,.2f}")
                        st.write(f"**Unit Cost:** GHC {mat['unit_cost']:,.2f}")
                        st.write(f"**Total Value:** GHC {mat['qty_in_stock']*mat['unit_cost']:,.2f}")
                    with mv2:
                        st.write(f"**Supplier:** {mat['supplier'] or '—'}")
                        st.write(f"**Location:** {mat['location'] or '—'}")
                        st.write(f"**Last Updated:** {mat['last_updated'] or '—'}")
                        if mat['notes']: st.write(f"**Notes:** {mat['notes']}")
                    if role in ["Admin","Manager"]:
                        st.write("---")
                        e1,e2,e3=st.columns(3)
                        with e1:
                            nq=st.number_input("Stock Qty",value=float(mat['qty_in_stock']),key=f"mat_qty_{mat['id']}")
                            nr=st.number_input("Reorder Lvl",value=float(mat['reorder_level']),key=f"mat_reorder_{mat['id']}")
                        with e2:
                            nu=st.number_input("Unit Cost",value=float(mat['unit_cost']),key=f"mat_cost_{mat['id']}")
                            nl=st.text_input("Location",value=mat['location'] or "",key=f"mat_loc_{mat['id']}")
                        with e3:
                            ns=st.text_input("Supplier",value=mat['supplier'] or "",key=f"mat_sup_{mat['id']}")
                            nn=st.text_area("Notes",value=mat['notes'] or "",key=f"mat_notes_{mat['id']}")
                            ab1,ab2=st.columns(2)
                        with ab1:
                            if st.button("💾 Save",key=f"msv_{mat['id']}"):
                               now=datetime.now().strftime("%Y-%m-%d %H:%M")
                               c.execute("UPDATE materials SET qty_in_stock=?,reorder_level=?,unit_cost=?,location=?,supplier=?,notes=?,last_updated=? WHERE id=?",
                                         (nq,nr,nu,nl,ns,nn,now,mat['id'])); conn.commit(); st.success("Updated!"); st.rerun()
                        with ab2:
                            if role=="Admin" and st.button("🗑️ Delete",key=f"mde_{mat['id']}"):
                                c.execute("DELETE FROM material_movements WHERE material_id=?",(mat['id'],))
                                c.execute("DELETE FROM materials WHERE id=?",(mat['id'],)); conn.commit(); st.rerun()
                    mvdf=pd.read_sql_query("SELECT * FROM material_movements WHERE material_id=? ORDER BY moved_date DESC LIMIT 10",conn,params=(mat['id'],))
                    if not mvdf.empty:
                        st.write("**Recent Movements:**")
                        st.dataframe(mvdf[['moved_date','movement_type','quantity','project_ref','moved_by','notes']],use_container_width=True,hide_index=True)

    with tab_m2:
        if role not in ["Admin","Manager"]: st.warning("No permission.")
        else:
            am1,am2=st.columns(2)
            with am1:
                an=st.text_input("Material Name *"); ac=st.selectbox("Category",MAT_CAT)
                au=st.text_input("Unit",value="pcs"); aq=st.number_input("Opening Qty",min_value=0.0,format="%.2f")
                are=st.number_input("Reorder Level",min_value=0.0,format="%.2f")
            with am2:
                auc=st.number_input("Unit Cost (GHC)",min_value=0.0,format="%.2f")
                asp=st.text_input("Supplier"); alo=st.text_input("Location"); ano=st.text_area("Notes", key="mat_add_notes")
            if st.button("➕ Register Material"):
                if not an.strip(): st.error("Name required.")
                else:
                    now=datetime.now().strftime("%Y-%m-%d %H:%M")
                    c.execute("INSERT INTO materials (name,category,unit,qty_in_stock,reorder_level,unit_cost,supplier,location,notes,last_updated) VALUES (?,?,?,?,?,?,?,?,?,?)",
                              (an,ac,au,aq,are,auc,asp,alo,ano,now)); conn.commit(); st.success(f"✅ '{an}' registered!"); st.rerun()

    with tab_m3:
        dml=pd.read_sql_query("SELECT id,name,qty_in_stock,unit FROM materials ORDER BY name",conn)
        if dml.empty: st.info("No materials yet.")
        else:
            rm1,rm2=st.columns(2)
            with rm1:
                opts={f"{r['name']} ({r['qty_in_stock']} {r['unit']})":r['id'] for _,r in dml.iterrows()}
                sl=st.selectbox("Material",list(opts.keys())); sid=opts[sl]
                mt=st.selectbox("Movement Type",["Receipt (IN)","Issue (OUT)","Return (IN)","Adjustment","Write-off (OUT)"])
                mq=st.number_input("Quantity",min_value=0.01,format="%.2f")
            with rm2:
                mp=st.text_input("Project / Reference"); mn2=st.text_area("Notes", key="mat_movement_notes")
                mb=st.text_input("Recorded By",value=user['full_name'])
            if st.button("✅ Save Movement"):
                now=datetime.now().strftime("%Y-%m-%d %H:%M")
                cur=c.execute("SELECT qty_in_stock FROM materials WHERE id=?",(sid,)).fetchone()
                cq=cur[0] if cur else 0
                nq=cq+mq if "IN" in mt else max(0,cq-mq)
                c.execute("UPDATE materials SET qty_in_stock=?,last_updated=? WHERE id=?",(nq,now,sid))
                c.execute("INSERT INTO material_movements (material_id,movement_type,quantity,project_ref,notes,moved_by,moved_date) VALUES (?,?,?,?,?,?,?)",
                          (sid,mt,mq,mp,mn2,mb,now)); conn.commit()
                st.success(f"✅ Recorded. New stock: {nq:.2f}"); st.rerun()

    with tab_m4:
        dms=pd.read_sql_query("SELECT * FROM materials",conn)
        if dms.empty: st.info("No materials.")
        else:
            dms['tv']=dms['qty_in_stock']*dms['unit_cost']
            ms1,ms2,ms3,ms4=st.columns(4)
            ms1.metric("Total Items",len(dms)); ms2.metric("Inventory Value",f"GHC {dms['tv'].sum():,.2f}")
            ms3.metric("Low / Out of Stock",len(dms[dms['qty_in_stock']<=dms['reorder_level']])); ms4.metric("Categories",dms['category'].nunique())
            st.write("---")
            bc=dms.groupby('category').agg(Items=('id','count'),Total_Qty=('qty_in_stock','sum'),Value=('tv','sum')).reset_index()
            bc.columns=["Category","Items","Total Qty","Value (GHC)"]; st.dataframe(bc,use_container_width=True)
            dd=dms[['name','category','qty_in_stock','unit','reorder_level','unit_cost','tv','supplier','location']].copy()
            dd.columns=['Name','Category','Stock','Unit','Reorder','Unit Cost','Total Value','Supplier','Location']
            st.dataframe(dd,use_container_width=True)

# =====================================================================
# ASSET MANAGER
# =====================================================================
elif choice == "Asset Manager":
    st.markdown('<div class="section-header"><span style="font-size:1.3rem">🗂️</span><span class="section-header-text">ASSET MANAGER</span></div>', unsafe_allow_html=True)
    CATEGORIES=["Equipment","Vehicle","Tools","IT & Electronics","Furniture","Safety Gear","Other"]
    CONDITIONS=["Excellent","Good","Fair","Needs Repair","Out of Service"]
    tab_a1,tab_a2,tab_a3=st.tabs(["📦 All Assets","➕ Add Asset","📊 Summary"])
    with tab_a1:
        da=pd.read_sql_query("SELECT * FROM assets ORDER BY category,name",conn)
        if da.empty: st.info("No assets yet.")
        else:
            af1,af2=st.columns(2)
            with af1: fc=st.multiselect("Category",CATEGORIES,default=CATEGORIES)
            with af2: fco=st.multiselect("Condition",CONDITIONS,default=CONDITIONS)
            sa=st.text_input("🔍 Search")
            fa=da[da['category'].isin(fc)&da['condition'].isin(fco)]
            if sa: fa=fa[fa['name'].str.contains(sa,case=False,na=False)|fa['serial_no'].str.contains(sa,case=False,na=False)|fa['assigned_to'].str.contains(sa,case=False,na=False)]
            CI={"Excellent":"🟢","Good":"🟢","Fair":"🟡","Needs Repair":"🟠","Out of Service":"🔴"}
            for _,asset in fa.iterrows():
                with st.expander(f"{CI.get(asset['condition'],'⚪')} {asset['name']} | {asset['category']} | {asset['location'] or '—'}"):
                    av1,av2=st.columns(2)
                    with av1:
                        st.write(f"**Category:** {asset['category']}"); st.write(f"**S/N:** {asset['serial_no'] or '—'}")
                        st.write(f"**Purchase Date:** {asset['purchase_date'] or '—'}")
                        st.write(f"**Purchase Value:** GHC {asset['purchase_value']:,.2f}" if asset['purchase_value'] else "—")
                        st.write(f"**Current Value:** GHC {asset['current_value']:,.2f}" if asset['current_value'] else "—")
                    with av2:
                        st.write(f"**Location:** {asset['location'] or '—'}"); st.write(f"**Assigned:** {asset['assigned_to'] or '—'}")
                        st.write(f"**Condition:** {asset['condition']}")
                        if asset['notes']: st.write(f"**Notes:** {asset['notes']}")
                    if role in ["Admin","Manager"]:
                        st.write("---")
                        e1,e2=st.columns(2)
                        with e1:
                            nc=st.selectbox("Condition",CONDITIONS,index=CONDITIONS.index(asset['condition']) if asset['condition'] in CONDITIONS else 1,key=f"c_{asset['id']}")
                            nl=st.text_input("Location",value=asset['location'] or "",key=f"l_{asset['id']}")
                            nas=st.text_input("Assigned To",value=asset['assigned_to'] or "",key=f"a_{asset['id']}")
                        with e2:
                            nv=st.number_input("Current Value",value=float(asset['current_value'] or 0),key=f"v_{asset['id']}")
                            nn=st.text_area("Notes",value=asset['notes'] or "",key=f"n_{asset['id']}")
                        b1,b2=st.columns(2)
                        with b1:
                            if st.button("💾 Save",key=f"sa_{asset['id']}"):
                                c.execute("UPDATE assets SET condition=?,location=?,assigned_to=?,current_value=?,notes=? WHERE id=?",(nc,nl,nas,nv,nn,asset['id'])); conn.commit(); st.success("Updated!"); st.rerun()
                        with b2:
                            if role=="Admin" and st.button("🗑️",key=f"da_{asset['id']}"):
                                c.execute("DELETE FROM assets WHERE id=?",(asset['id'],)); conn.commit(); st.rerun()
    with tab_a2:
        if role not in ["Admin","Manager"]: st.warning("No permission.")
        else:
            n1,n2=st.columns(2)
            with n1:
                an=st.text_input("Asset Name *"); ac=st.selectbox("Category *",CATEGORIES)
                ase=st.text_input("Serial / Tag"); apd=st.date_input("Purchase Date",datetime.now())
                apv=st.number_input("Purchase Value (GHC)",min_value=0.0,format="%.2f")
            with n2:
                acv=st.number_input("Current Value (GHC)",min_value=0.0,format="%.2f")
                alo=st.text_input("Location / Site"); aco=st.selectbox("Condition",CONDITIONS)
                aat=st.text_input("Assigned To"); ano=st.text_area("Notes", key="asset_add_notes")
            if st.button("➕ Register Asset"):
                if not an.strip(): st.error("Name required.")
                else:
                    c.execute("INSERT INTO assets (name,category,serial_no,purchase_date,purchase_value,current_value,location,condition,assigned_to,notes) VALUES (?,?,?,?,?,?,?,?,?,?)",
                              (an,ac,ase,apd.strftime("%Y-%m-%d"),apv,acv,alo,aco,aat,ano)); conn.commit(); st.success(f"✅ '{an}' registered!"); st.rerun()
    with tab_a3:
        ds=pd.read_sql_query("SELECT * FROM assets",conn)
        if ds.empty: st.info("No assets.")
        else:
            tp=ds['purchase_value'].sum(); tc=ds['current_value'].sum()
            s1,s2,s3,s4=st.columns(4)
            s1.metric("Total Assets",len(ds)); s2.metric("Purchase Value",f"GHC {tp:,.2f}")
            s3.metric("Current Value",f"GHC {tc:,.2f}"); s4.metric("Depreciation",f"GHC {tp-tc:,.2f}")
            st.write("---")
            bc=ds.groupby('category').agg(Count=('id','count'),Purchase=('purchase_value','sum'),Current=('current_value','sum')).reset_index()
            bc.columns=["Category","Count","Purchase (GHC)","Current (GHC)"]; st.dataframe(bc,use_container_width=True)

# =====================================================================
# LOG TRANSACTION
# =====================================================================
elif choice == "Log Transaction":
    st.markdown('<div class="section-header"><span style="font-size:1.3rem">📝</span><span class="section-header-text">LOG TRANSACTION</span></div>', unsafe_allow_html=True)
    col1,col2=st.columns(2)
    with col1:
        tt=st.selectbox("Type",["Revenue","Expenditure"]); se=st.selectbox("Sector",["Engineering","Transport","Construction"]); cl=st.text_input("Name")
    with col2:
        am=st.number_input("Amount (GHC)",min_value=0.0); dt=st.date_input("Date",datetime.now()); de=st.text_area("Details", key="txn_details")
    if st.button("Save Record"):
        c.execute("INSERT INTO transactions (type,sector,client,amount,date,description,created_by) VALUES (?,?,?,?,?,?,?)",
                  (tt,se,cl,am,dt.strftime("%Y-%m-%d"),de,user['username'])); conn.commit(); st.success("Saved!")

# =====================================================================
# DASHBOARD  — artistic
# =====================================================================
else:
    # ── Hero banner ──────────────────────────
    df_t  = pd.read_sql_query("SELECT * FROM transactions", conn)
    df_pf = pd.read_sql_query("SELECT * FROM proformas", conn)
    df_ma = pd.read_sql_query("SELECT * FROM materials", conn)
    df_as = pd.read_sql_query("SELECT * FROM assets", conn)

    rev = df_t[df_t['type']=='Revenue']['amount'].sum() if not df_t.empty else 0
    exp = df_t[df_t['type']=='Expenditure']['amount'].sum() if not df_t.empty else 0
    pf_out = df_pf[df_pf['status'].isin(['Sent','Under Review','Approved','Partially Paid'])]['amount'].sum() if not df_pf.empty else 0
    inv_val = (df_ma['qty_in_stock']*df_ma['unit_cost']).sum() if not df_ma.empty else 0

    today_str = datetime.now().strftime("%A, %d %B %Y")
    st.markdown(f"""
    <div class="hero-banner">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px;">
            <div>
                <img src="data:image/png;base64,{logo_b64}" style="width:180px;height:180px;object-fit:contain;border-radius:12px;margin-bottom:4px;" /><br/>
                <div class="hero-sub">Engineering · Logistics · Transport &nbsp;|&nbsp; {today_str}</div>
                <div style="margin-top:10px;">
                    <span class="kpi-pill">👤 {user['full_name']}</span>
                    <span class="kpi-pill">🔑 {role}</span>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:0.72rem;color:#666;letter-spacing:1px;text-transform:uppercase;">Net Position</div>
                <div style="font-size:2.2rem;font-weight:800;color:{'#4ade80' if rev-exp>=0 else '#f87171'};">
                    GHC {rev-exp:,.0f}
                </div>
            </div>
        </div>
        <div class="hero-stat-row">
            <div class="hero-stat">
                <div class="hero-stat-val">GHC {rev:,.0f}</div>
                <div class="hero-stat-lbl">Total Revenue</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-val">GHC {exp:,.0f}</div>
                <div class="hero-stat-lbl">Expenditure</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-val">GHC {pf_out:,.0f}</div>
                <div class="hero-stat-lbl">Outstanding</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-val">GHC {inv_val:,.0f}</div>
                <div class="hero-stat-lbl">Inventory Value</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI row ──────────────────────────────
    k1,k2,k3,k4,k5,k6 = st.columns(6)
    k1.metric("💼 Proformas", len(df_pf) if not df_pf.empty else 0)
    k2.metric("✅ Paid", len(df_pf[df_pf['status']=='Fully Paid']) if not df_pf.empty else 0)
    k3.metric("🚨 Overdue", len(df_pf[df_pf['status']=='Overdue']) if not df_pf.empty else 0)
    k4.metric("🧱 Materials", len(df_ma) if not df_ma.empty else 0)
    lowmat = len(df_ma[df_ma['qty_in_stock']<=df_ma['reorder_level']]) if not df_ma.empty else 0
    k5.metric("⚠️ Low Stock", lowmat)
    k6.metric("🗂️ Assets", len(df_as) if not df_as.empty else 0)

    # ── Low stock alert ───────────────────────
    if not df_ma.empty:
        low = df_ma[df_ma['qty_in_stock']<=df_ma['reorder_level']]
        if not low.empty:
            st.warning("⚠️ **Low Stock Alert:** " + " · ".join([f"{r['name']} ({r['qty_in_stock']:.1f} {r['unit']})" for _,r in low.iterrows()]))

    # ── Two-column section ────────────────────
    left, right = st.columns([1.3, 1])

    with left:
        # Recent proformas
        st.markdown('<div class="section-header"><span class="section-header-text">📋 Recent Proformas</span></div>', unsafe_allow_html=True)
        SC={"Draft":"⚪","Sent":"🔵","Under Review":"🟡","Approved":"🟢","Partially Paid":"🟠","Fully Paid":"✅","Cancelled":"🔴","Overdue":"🚨"}
        if df_pf.empty:
            st.info("No proformas yet.")
        else:
            recent_pf = df_pf.sort_values("issue_date",ascending=False).head(6)
            for _,row in recent_pf.iterrows():
                icon=SC.get(row['status'],"⚪")
                st.markdown(f"""
                <div style="background:#1a1f2e;border:1px solid #c8a84b22;border-radius:8px;
                            padding:10px 16px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="color:#c8a84b;font-weight:600;font-size:0.85rem;">#{row['doc_no']}</span>
                        <span style="color:#888;font-size:0.8rem;margin-left:8px;">{row['client']}</span>
                    </div>
                    <div style="display:flex;align-items:center;gap:16px;">
                        <span style="color:#fff;font-weight:600;">GHC {row['amount']:,.0f}</span>
                        <span style="font-size:0.8rem;">{icon} {row['status']}</span>
                        <span style="color:#555;font-size:0.75rem;">{row['issue_date']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Recent transactions
        st.markdown('<div class="section-header"><span class="section-header-text">💳 Recent Transactions</span></div>', unsafe_allow_html=True)
        if df_t.empty:
            st.info("No transactions yet.")
        else:
            rec_t = df_t.sort_values("date",ascending=False).head(5)
            for _,row in rec_t.iterrows():
                color = "#4ade80" if row['type']=="Revenue" else "#f87171"
                sign  = "+" if row['type']=="Revenue" else "−"
                st.markdown(f"""
                <div style="background:#1a1f2e;border:1px solid #c8a84b22;border-radius:8px;
                            padding:10px 16px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="color:#e8e0cc;font-size:0.85rem;">{row['client'] or '—'}</span>
                        <span style="color:#555;font-size:0.75rem;margin-left:8px;">{row.get('sector', '—')}</span>
                    </div>
                    <div style="display:flex;gap:16px;align-items:center;">
                        <span style="color:{color};font-weight:700;">{sign} GHC {row['amount']:,.0f}</span>
                        <span style="color:#555;font-size:0.75rem;">{row['date']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with right:
        # Asset health
        st.markdown('<div class="section-header"><span class="section-header-text">🗂️ Asset Health</span></div>', unsafe_allow_html=True)
        if df_as.empty:
            st.info("No assets registered.")
        else:
            CI={"Excellent":"🟢","Good":"🟢","Fair":"🟡","Needs Repair":"🟠","Out of Service":"🔴"}
            cond_counts = df_as.groupby('condition').size().reset_index(name='count')
            for _,row in cond_counts.iterrows():
                pct = int(row['count']/len(df_as)*100)
                st.markdown(f"""
                <div style="margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                        <span style="font-size:0.8rem;">{CI.get(row['condition'],'⚪')} {row['condition']}</span>
                        <span style="font-size:0.8rem;color:#c8a84b;">{row['count']} ({pct}%)</span>
                    </div>
                    <div style="background:#1a1f2e;border-radius:999px;height:6px;">
                        <div style="background:linear-gradient(90deg,#c8a84b,#a07830);width:{pct}%;height:6px;border-radius:999px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Inventory snapshot
        st.markdown('<div class="section-header"><span class="section-header-text">🧱 Top Inventory Items</span></div>', unsafe_allow_html=True)
        if df_ma.empty:
            st.info("No inventory data.")
        else:
            df_ma_sorted = df_ma.copy()
            df_ma_sorted['value'] = df_ma_sorted['qty_in_stock'] * df_ma_sorted['unit_cost']
            top5 = df_ma_sorted.nlargest(5, 'value')
            for _,row in top5.iterrows():
                stock_pct = min(100, int((row['qty_in_stock'] / max(row['reorder_level']*2, 1)) * 100))
                bar_color = "#c8a84b" if stock_pct>50 else ("#f59e0b" if stock_pct>20 else "#ef4444")
                st.markdown(f"""
                <div style="margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
                        <span style="font-size:0.8rem;color:#e8e0cc;">{row['name']}</span>
                        <span style="font-size:0.75rem;color:#888;">{row['qty_in_stock']:.1f} {row['unit']} · GHC {row['value']:,.0f}</span>
                    </div>
                    <div style="background:#1a1f2e;border-radius:999px;height:5px;">
                        <div style="background:{bar_color};width:{stock_pct}%;height:5px;border-radius:999px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Quick action links
        st.markdown('<div class="section-header"><span class="section-header-text">⚡ Quick Actions</span></div>', unsafe_allow_html=True)
        qa1, qa2 = st.columns(2)
        with qa1:
            if st.button("📄 New Document", use_container_width=True):
                st.session_state["_menu_override"] = "Document Generator"
        with qa2:
            if st.button("📝 Log Transaction", use_container_width=True):
                st.session_state["_menu_override"] = "Log Transaction"