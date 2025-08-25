from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import sqlite3
from datetime import date
import os

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

llm = ChatGroq(model='llama3-8b-8192', api_key=api_key, temperature=0.6)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant that help me log what I have learned for the day into a logbook, mostly because I always procrastinnate doing it myself. I will provide you with the date and waht I have learned, which would usually be long and unstructured. You will help me summarize it into a concise log entry. It should not exceed 4 sentences and it should be easy to read. The language should not be too formal. It should seem as if a student wrote it. Here is an example of a good log entry: 'Today I learned about the basics of Python programming, including variables, data types, and control structures. I also explored functions and how to use them to organize code. Additionally, I got introduced to lists and dictionaries for storing collections of data. Overall, it was a productive day of learning!'"),("user", "What I learned: {learned}")])



def create_db():
    conn = sqlite3.connect('logbook.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE,
                    entry TEXT)''')
    conn.commit()
    return conn, cursor

conn, cursor = create_db()

def view_entries(cursor):
    cursor.execute("SELECT * FROM logs")
    rows = cursor.fetchall()
    if not rows:
        print("No entries found.")
    else:
        for row in rows:
            print(f"\nID: {row[0]}\nDate: {row[1]}\nEntry: {row[2]}\n{'-'*40}")


def get_date():
    while True:
        date_check = input("Is today the date you want to log? (y/n): ")
        if date_check.lower() == 'n':
            custom_date = input("Enter the date (YYYY-MM-DD): ")
            today = custom_date
            return today
        elif date_check.lower() == 'y':
            today = date.today().strftime("%Y-%m-%d")
            return today
        else:
            print("Please enter 'y' or 'n'")
        

def entry():
    today = get_date()
    while True:
        what_i_learned = input("What did you learn today? ")
        if what_i_learned.strip() == "":
            print("You must enter something you learned today.")
        else:
            return today, what_i_learned

def refine_entry(what_i_learned):
    message = prompt.format_prompt(learned=what_i_learned)
    print("Generating log entry...")
    response = llm.invoke(message)
    completed_entry = response.content
    print(f"Here is your log entry:\n{response.content}")
    return completed_entry

def insert_entry(conn, cursor, today, completed_entry):
    print("Inserting log entry into database...")
    cursor.execute("INSERT INTO logs (date, entry) VALUES (?, ?)", (today, completed_entry))
    conn.commit()
    print("Log entry added successfully!")

print("Welcome to your learning logbook!")
        

while True:
    while True:
        choice = input("Do you want to view or add entries (v/a): ")
        if choice.lower() == 'v':
            view_entries(cursor)
        elif choice.lower() == 'a':
            break
    today, what_i_learned = entry()
    completed_entry = refine_entry(what_i_learned)
    insert_entry(conn, cursor, today, completed_entry)
    again = input("Do you want to add another entry? (y/n): ")
    if again.lower() != 'y':
        break
    continue

conn.close()
print('Connection Closed')