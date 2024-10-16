import os
import sqlite3
import datetime

def create_database(output_folder):
    db_path = os.path.join(output_folder, 'pdf_data.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create a table for individuals
    c.execute('''CREATE TABLE IF NOT EXISTS individuals
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE,
                  address TEXT,
                  phone_number TEXT,
                  email TEXT)''')
    
    # Create a table for pay statements with a unique constraint
    c.execute('''CREATE TABLE IF NOT EXISTS pay_statements
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  individual_id INTEGER,
                  date TEXT,
                  filename TEXT,
                  extraction_date TEXT,
                  FOREIGN KEY (individual_id) REFERENCES individuals(id),
                  UNIQUE(individual_id, date))''')
    
    conn.commit()
    conn.close()
    return db_path

def insert_into_database(db_path, name, date, filename):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:
        # First, try to insert or get the individual
        c.execute("INSERT OR IGNORE INTO individuals (name) VALUES (?)", (name,))
        c.execute("SELECT id FROM individuals WHERE name = ?", (name,))
        individual_id = c.fetchone()[0]
        
        # Check if a pay statement already exists for this individual and date
        c.execute("SELECT filename FROM pay_statements WHERE individual_id = ? AND date = ?", (individual_id, date))
        existing_filename = c.fetchone()
        
        if existing_filename:
            print(f"Pay statement already exists for {name} on {date}. Skipping.")
            result = False
        else:
            # Insert the new pay statement
            extraction_date = datetime.date.today().strftime('%Y-%m-%d')
            c.execute('''INSERT INTO pay_statements 
                         (individual_id, date, filename, extraction_date) 
                         VALUES (?, ?, ?, ?)''',
                      (individual_id, date, filename, extraction_date))
            
            print(f"Inserted new pay statement for {name}: {filename}")
            result = True
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        result = False
    finally:
        conn.close()
    
    return result

def update_individual_info(db_path, name, address=None, phone_number=None, email=None):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    update_fields = []
    update_values = []
    if address is not None:
        update_fields.append("address = ?")
        update_values.append(address)
    if phone_number is not None:
        update_fields.append("phone_number = ?")
        update_values.append(phone_number)
    if email is not None:
        update_fields.append("email = ?")
        update_values.append(email)
    
    if update_fields:
        update_query = f"UPDATE individuals SET {', '.join(update_fields)} WHERE name = ?"
        update_values.append(name)
        c.execute(update_query, update_values)
        conn.commit()
        print(f"Updated information for {name}")
    
    conn.close()

def get_individuals(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM individuals")
    individuals = c.fetchall()
    conn.close()
    return individuals

def get_pay_statements(db_path, individual_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM pay_statements WHERE individual_id = ?", (individual_id,))
    pay_statements = c.fetchall()
    conn.close()
    return pay_statements
