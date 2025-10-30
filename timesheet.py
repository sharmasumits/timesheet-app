import streamlit as st
import json
import pandas as pd
from datetime import date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ---------- FILE PATHS ----------
USERS_FILE = "users.json"
PROJECTS_FILE = "projects.json"
TIMESHEETS_FILE = "timesheets.json"

# ---------- EMAIL SETTINGS ----------
EMAIL_SENDER = "sharmasumits12k@gmail.com"
EMAIL_PASSWORD = "vcec ovka kwpz xcvk"  # Gmail App Password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_welcome_email(to_email, username, password, projects):
    """Send an email to a new user with their login credentials."""
    subject = "Welcome to Timesheet App"
    project_list = ", ".join(projects) if projects else "No projects assigned yet."
    
    body = f"""
    Hi {username},

    Your Timesheet account has been created successfully.

    🔐 Login Details:
    --------------------
    Username: {username}
    Password: {password}

    📁 Assigned Projects:
    {project_list}

    You can now log in to the Timesheet Portal and start submitting your timesheets.

    Regards,
    Timesheet Admin
    """

    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"❌ Failed to send email: {e}")
        return False


# ---------- HELPER FUNCTIONS ----------
def load_json(file_path):
    try:
        with open(file_path, "r") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        st.error(f"Error: {file_path} has invalid JSON.")
        return []

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def authenticate(username, password):
    users = load_json(USERS_FILE)
    for user in users:
        if user['username'] == username and user['password'] == password:
            return user
    return None

# ---------- STREAMLIT PAGE CONFIG ----------
st.set_page_config(page_title="Timesheet App", layout="wide")
st.markdown("""
    <style>
        .main {
            background-color: #f8fafc;
            color: #111827;
            font-family: 'Segoe UI', sans-serif;
        }
        h1, h2, h3, h4 {
            color: #2563eb;
        }
        .stButton button {
            border-radius: 8px;
            background-color: #2563eb;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🕒 Timesheet Management App")

# ---------- SESSION STATE ----------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# ---------- LOGIN ----------
if not st.session_state.logged_in:
    st.subheader("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = authenticate(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.user = user
            st.success(f"✅ Logged in as {username}")
        else:
            st.error("❌ Invalid username or password")

# ---------- AFTER LOGIN ----------
else:
    st.sidebar.success(f"👤 Logged in as: {st.session_state.user['username']}")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({'logged_in': False, 'user': None}))

    # ---------- ADMIN PANEL ----------
    if st.session_state.user['username'] == "admin":
        st.header("🛠️ Admin Panel")
        st.divider()

        # --- Manage Projects ---
        st.subheader("📁 Manage Projects")
        projects = load_json(PROJECTS_FILE)
        new_project = st.text_input("Add New Project")
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("Add Project"):
                if new_project and new_project not in projects:
                    projects.append(new_project)
                    save_json(PROJECTS_FILE, projects)
                    st.success(f"Project '{new_project}' added.")
        with col2:
            if st.button("Clear Projects"):
                save_json(PROJECTS_FILE, [])
                st.warning("All projects cleared.")

        if projects:
            df_projects = pd.DataFrame(projects, columns=["Project Name"])
            st.dataframe(df_projects, use_container_width=True, hide_index=True)
        else:
            st.info("No projects added yet.")

        st.divider()

        # --- Manage Users ---
        st.subheader("👨‍💼 Manage Users")
        users = load_json(USERS_FILE)

        with st.expander("➕ Create New User"):
            new_user = st.text_input("Username", key="new_user")
            new_pass = st.text_input("Password", type="password", key="new_pass")
            user_email = st.text_input("User Email", key="new_email")
            assigned_projects = st.multiselect("Assign Projects", projects)

            if st.button("Create User"):
                if new_user and user_email:
                    users.append({
                        "username": new_user,
                        "password": new_pass,
                        "email": user_email,
                        "projects": assigned_projects
                    })
                    save_json(USERS_FILE, users)

                    email_sent = send_welcome_email(user_email, new_user, new_pass, assigned_projects)
                    if email_sent:
                        st.success(f"✅ User '{new_user}' created and email sent to {user_email}.")
                    else:
                        st.warning("⚠️ User created, but email could not be sent.")
                else:
                    st.error("Please enter both username and email.")

        if users:
            df_users = pd.DataFrame(users)
            st.dataframe(df_users, use_container_width=True, hide_index=True)
        else:
            st.info("No users yet.")

        st.divider()

        # --- View & Edit Timesheets ---
        st.subheader("📊 View & Edit Timesheets")
        timesheets = load_json(TIMESHEETS_FILE)

        if timesheets:
            df_timesheets = pd.DataFrame(timesheets)
            edited_df = st.data_editor(df_timesheets, num_rows="dynamic", use_container_width=True)

            if st.button("💾 Save Changes"):
                save_json(TIMESHEETS_FILE, edited_df.to_dict(orient="records"))
                st.success("✅ Timesheet data updated successfully!")
        else:
            st.info("No timesheet entries yet.")

    # ---------- EMPLOYEE PANEL ----------
    else:
        st.header("🧾 Timesheet Entry")
        st.divider()
        employee_projects = st.session_state.user.get('projects', [])
        if not employee_projects:
            st.warning("⚠️ No projects assigned yet. Contact admin.")
        else:
            entry_date = st.date_input("Date", date.today())
            project_name = st.selectbox("Project", employee_projects)
            hours_worked = st.number_input("Hours Worked", min_value=0.0, max_value=24.0, step=0.5)
            notes = st.text_area("Notes")

            if st.button("Submit Timesheet"):
                timesheets = load_json(TIMESHEETS_FILE)
                timesheets.append({
                    "username": st.session_state.user['username'],
                    "date": str(entry_date),
                    "project": project_name,
                    "hours": hours_worked,
                    "notes": notes
                })
                save_json(TIMESHEETS_FILE, timesheets)
                st.success("✅ Timesheet submitted successfully!")

            # --- Show Employee's Own Timesheets ---
            st.divider()
            st.subheader("📋 Your Previous Timesheets")
            timesheets = load_json(TIMESHEETS_FILE)
            user_entries = [t for t in timesheets if t["username"] == st.session_state.user["username"]]
            if user_entries:
                df_user = pd.DataFrame(user_entries)
                st.dataframe(df_user, use_container_width=True, hide_index=True)
            else:
                st.info("No timesheets found.")
