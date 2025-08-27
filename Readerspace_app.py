import streamlit as st
import sqlite3
import datetime
from twilio.rest import Client

# ----------------- Database Setup -----------------
conn = sqlite3.connect("library.db")
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS users (
    library_code TEXT PRIMARY KEY,
    name TEXT,
    email TEXT,
    contact TEXT,
    seatno TEXT,
    paid INTEGER,
    last_paid_month TEXT
)
''')
conn.commit()

# ----------------- Twilio Setup -----------------
ACCOUNT_SID = "your_twilio_sid"
AUTH_TOKEN = "your_twilio_auth_token"
TWILIO_PHONE = "+1234567890"  # Replace with your Twilio phone number
client = Client(ACCOUNT_SID, AUTH_TOKEN)

def send_message(phone, message):
    try:
        client.messages.create(
            body=message,
            from_=TWILIO_PHONE,
            to=phone
        )
        st.success(f"📩 Reminder sent to {phone}")
    except Exception as e:
        st.error(f"❌ Error sending message: {e}")

# ----------------- Database Functions -----------------
def create_user(code, name, email, contact, seatno):
    try:
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (code, name, email, contact, seatno, 0, None))
        conn.commit()
        return True
    except:
        return False

def get_user(code):
    c.execute("SELECT * FROM users WHERE library_code=?", (code,))
    return c.fetchone()

def update_fee(code):
    current_month = datetime.datetime.now().strftime("%B %Y")
    c.execute("UPDATE users SET paid=?, last_paid_month=? WHERE library_code=?",
              (1, current_month, code))
    conn.commit()

# ----------------- Streamlit UI -----------------
st.title("📚 Library Management System")

menu = st.sidebar.radio("Menu", ["Create Account", "Login"])

# ---------- Create New User ----------
if menu == "Create Account":
    st.subheader("🆕 Create New Account")
    name = st.text_input("Enter Name")
    email = st.text_input("Enter Email")
    contact = st.text_input("Enter Contact (with country code, e.g. +91XXXXXXXXXX)")
    seatno = st.text_input("Enter Seat No")
    library_code = st.text_input("Choose Library Code (Unique)")

    if st.button("Create Account"):
        if name.strip() == "" or email.strip() == "" or contact.strip() == "" or library_code.strip() == "":
            st.warning("⚠ Please fill all fields.")
        else:
            if create_user(library_code, name, email, contact, seatno):
                st.success(f"✅ Account created! Your Library Code is {library_code}")
            else:
                st.error("❌ Library Code already exists. Try another one.")

# ---------- Login ----------
elif menu == "Login":
    st.subheader("🔑 Login with Library Code")
    library_code = st.text_input("Enter your Library Code")

    if st.button("Login"):
        user = get_user(library_code)
        if user:
            st.success(f"👋 Welcome {user[1]}")
            st.write(f"📧 Email: {user[2]}")
            st.write(f"📞 Contact: {user[3]}")
            st.write(f"💺 Seat: {user[4]}")
            st.write(f"💰 Fee Paid: {'✅ Yes' if user[5] else '❌ No'}")
            st.write(f"🗓 Last Paid Month: {user[6] if user[6] else '❌ Not Paid Yet'}")

            if not user[5]:  
                if st.button("Mark Fee as Paid"):
                    update_fee(library_code)
                    st.success("✅ Fee updated successfully!")

            # Reminder Section
            current_month = datetime.datetime.now().strftime("%B %Y")
            if user[6] != current_month:
                reminder_msg = f"Hello {user[1]}, your library fee for {current_month} is DUE. Please pay soon."
            else:
                reminder_msg = f"Hello {user[1]}, your library fee for {current_month} is already PAID. ✅"

            st.info(reminder_msg)

            if st.button("📩 Send Reminder via SMS/WhatsApp"):
                send_message(user[3], reminder_msg)

        else:
            st.error("❌ Invalid Library Code")
