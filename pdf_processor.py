import re
import datetime
import os
from PyPDF2 import PdfReader, PdfWriter
from database_manager import create_database, insert_into_database

def extract_name_and_date(text):
    print("Full extracted text:")
    print(text)
    print("------------------------")

    parts = text.split("4300", 1)
    if len(parts) > 1:
        text = parts[1]
    
    name_match = re.search(r'([A-Z][A-Za-z\s]+)\n', text)
    name = name_match.group(1).strip() if name_match else "Unknown"
    
    date_match = re.search(r'Cheque Date:?\s*(.*?)(?:\n|$)', text, re.IGNORECASE)
    if date_match:
        date_str = date_match.group(1).strip()
        print(f"Extracted date string: '{date_str}'")
        
        try:
            for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y', '%m-%d-%Y', '%d/%m/%y', '%d-%m-%y', '%m/%d/%y', '%m-%d-%y', '%B %d, %Y', '%d %B %Y', '%Y-%m-%d'):
                try:
                    date_obj = datetime.datetime.strptime(date_str, fmt)
                    date = date_obj.strftime('%Y-%m-%d')  # Standardize date format
                    print(f"Parsed date: {date}")
                    break
                except ValueError:
                    continue
            else:
                date = "Unknown_Date"
                print(f"Could not parse date, using: {date}")
        except Exception as e:
            date = "Unknown_Date"
            print(f"Error parsing date: {e}")
    else:
        date = "Unknown_Date"
        print("No date found in the text")
    
    print(f"Final result - Name: {name}, Date: {date}")
    return name, date

def split_pdf(input_path, output_folder):
    reader = PdfReader(input_path)
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    db_path = create_database(output_folder)
    
    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        
        text = page.extract_text()
        name, date = extract_name_and_date(text)
        
        filename = f"{name} {date}.pdf"
        filepath = os.path.join(output_folder, filename)
        
        # Always write the file, overwriting if it exists
        with open(filepath, "wb") as output_file:
            writer.write(output_file)
        print(f"Created/Updated: {filename}")
        
        inserted = insert_into_database(db_path, name, date, filename)
        if inserted:
            print(f"Added to database: {filename}")
        else:
            print(f"Skipped adding to database (duplicate): {filename}")
    
    return db_path
