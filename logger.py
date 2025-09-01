import streamlit as st
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import sqlite3
from datetime import date
import os

# Load environment variables
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# LLM setup
llm = ChatGroq(model='llama3-8b-8192', api_key=api_key, temperature=0.6)

# Prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful assistant that helps me log what I have learned for the day into a logbook. 
    I will provide you with the date and what I have learned, which would usually be long and unstructured. 
    You will help me summarize it into a concise log entry. It should not exceed 4 sentences and should be easy to read. 
    The language should not be too formal, more like a student writing their own notes."""),
    ("user", "What I learned: {learned}")
])

# Database setup
def create_db():
    conn = sqlite3.connect("logbook.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE,
                    entry TEXT)''')
    conn.commit()
    return conn, cursor

def insert_entry(conn, cursor, today, completed_entry):
    cursor.execute("INSERT INTO logs (date, entry) VALUES (?, ?)", (today, completed_entry))
    conn.commit()

def view_entries(cursor):
    cursor.execute("SELECT * FROM logs ORDER BY date DESC")
    return cursor.fetchall()

# Summarization
def refine_entry(what_i_learned):
    message = prompt.format_prompt(learned=what_i_learned)
    response = llm.invoke(message)
    return response.content

# ---------- STREAMLIT APP ---------- #
st.set_page_config(page_title="Learning Logbook", page_icon="📒", layout="centered")

st.title("📒 Learning Logbook")
st.write("Keep track of what you learn each day!")

# DB connection (persisting during session)
conn, cursor = create_db()

# Sidebar with "View Entries"
with st.sidebar:
    st.header("📜 Your Logs")
    rows = view_entries(cursor)

    if not rows:
        st.info("No entries yet.")
    else:
        # Group entries by date
        logs_by_date = {}
        for row in rows:
            log_date, entry = row[1], row[2]
            if log_date not in logs_by_date:
                logs_by_date[log_date] = []
            logs_by_date[log_date].append(entry)

        # Show only dates, expand to see entries
        for log_date, entries in logs_by_date.items():
            with st.expander(f"📅 {log_date}"):
                for i, entry in enumerate(entries, start=1):
                    st.markdown(f"**Entry {i}:** {entry}")
                st.markdown("---")
# Chat-like input
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display conversation
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input from user

# Add date picker at the top of the chat input section
selected_date = st.date_input(
    "📅 Pick a date for this entry:",
    value=date.today()  # defaults to today's date
).strftime("%Y-%m-%d")

if prompt_text := st.chat_input("What did you learn today?"):

    # Show user input
    st.session_state.messages.append({"role": "user", "content": prompt_text})
    with st.chat_message("user"):
        st.markdown(prompt_text)

    # Generate log entry
    with st.chat_message("assistant"):
        with st.spinner("Summarizing..."):
            completed_entry = refine_entry(prompt_text)
            st.markdown(f"**{selected_date}** — {completed_entry}")  # show date with entry

    # Save to DB
    insert_entry(conn, cursor, selected_date, completed_entry)

    # Add to session history
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"**{selected_date}** — {completed_entry}"
    })