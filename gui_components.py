import os
import sqlite3
from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, 
                             QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
                             QLineEdit, QLabel, QDialog, QInputDialog, QSplitter, QAbstractItemView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl
from pdf_processor import split_pdf
from database_manager import (create_database, insert_into_database, update_individual_info,
                              get_individuals, get_pay_statements)

class DatabaseViewer(QWidget):
    def __init__(self, db_path, pdf_folder):
        super().__init__()
        self.db_path = db_path
        self.pdf_folder = pdf_folder
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        
        # Create a splitter for resizable sections
        splitter = QSplitter(Qt.Vertical)
        
        # Individuals section
        individuals_widget = QWidget()
        individuals_layout = QVBoxLayout(individuals_widget)
        individuals_layout.addWidget(QLabel("Individuals:"))
        self.individuals_table = QTableWidget()
        individuals_layout.addWidget(self.individuals_table)
        splitter.addWidget(individuals_widget)
        
        # Pay Statements section
        pay_statements_widget = QWidget()
        pay_statements_layout = QVBoxLayout(pay_statements_widget)
        self.pay_statements_label = QLabel("Pay Statements:")
        pay_statements_layout.addWidget(self.pay_statements_label)
        self.pay_statements_table = QTableWidget()
        pay_statements_layout.addWidget(self.pay_statements_table)
        splitter.addWidget(pay_statements_widget)
        
        layout.addWidget(splitter)
        
        self.setLayout(layout)
        self.setWindowTitle('Database Viewer')
        self.setGeometry(300, 300, 800, 600)
        self.load_individuals()

    def load_individuals(self):
        individuals = get_individuals(self.db_path)
        self.individuals_table.setColumnCount(5)
        self.individuals_table.setHorizontalHeaderLabels(["ID", "Name", "Address", "Phone", "Email"])
        self.individuals_table.setRowCount(len(individuals))

        for row, record in enumerate(individuals):
            for col, value in enumerate(record):
                item = QTableWidgetItem(str(value))
                self.individuals_table.setItem(row, col, item)

        self.individuals_table.resizeColumnsToContents()
        self.individuals_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.individuals_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.individuals_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.individuals_table.clicked.connect(self.on_individual_selected)

    def on_individual_selected(self, index):
        row = index.row()
        individual_id = int(self.individuals_table.item(row, 0).text())
        name = self.individuals_table.item(row, 1).text()
        self.load_pay_statements(individual_id, name)

    def load_pay_statements(self, individual_id, name):
        self.pay_statements_label.setText(f"Pay Statements for {name}:")
        pay_statements = get_pay_statements(self.db_path, individual_id)
        self.pay_statements_table.setColumnCount(5)
        self.pay_statements_table.setHorizontalHeaderLabels(["ID", "Date", "Filename", "Extraction Date", "Open PDF"])
        self.pay_statements_table.setRowCount(len(pay_statements))

        for row, record in enumerate(pay_statements):
            for col, value in enumerate(record[1:]):  # Skip individual_id
                item = QTableWidgetItem(str(value))
                self.pay_statements_table.setItem(row, col, item)
            
            open_btn = QPushButton("Open PDF")
            open_btn.clicked.connect(lambda _, f=record[3]: self.open_pdf(f))
            self.pay_statements_table.setCellWidget(row, 4, open_btn)

        self.pay_statements_table.resizeColumnsToContents()
        self.pay_statements_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def open_pdf(self, filename):
        pdf_path = os.path.join(self.pdf_folder, filename)
        if os.path.exists(pdf_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_path))
        else:
            QMessageBox.warning(self, "Error", f"PDF file not found: {pdf_path}")

class IndividualInfoDialog(QDialog):
    def __init__(self, db_path, name):
        super().__init__()
        self.db_path = db_path
        self.name = name
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        
        self.address_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()
        
        layout.addWidget(QLabel("Address:"))
        layout.addWidget(self.address_input)
        layout.addWidget(QLabel("Phone:"))
        layout.addWidget(self.phone_input)
        layout.addWidget(QLabel("Email:"))
        layout.addWidget(self.email_input)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_info)
        layout.addWidget(save_btn)
        
        self.setLayout(layout)
        self.setWindowTitle(f"Update Info for {self.name}")

    def save_info(self):
        update_individual_info(self.db_path, self.name,
                               self.address_input.text(),
                               self.phone_input.text(),
                               self.email_input.text())
        self.accept()

class PDFSplitterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.db_path = None
        self.pdf_folder = None
        self.initUI()
        self.initialize_database()

    def initUI(self):
        layout = QVBoxLayout()
        split_btn = QPushButton('Select and Split PDF', self)
        split_btn.clicked.connect(self.select_pdf)
        layout.addWidget(split_btn)
        
        view_btn = QPushButton('View Database', self)
        view_btn.clicked.connect(self.view_database)
        layout.addWidget(view_btn)
        
        update_info_btn = QPushButton('Update Individual Info', self)
        update_info_btn.clicked.connect(self.update_individual_info)
        layout.addWidget(update_info_btn)
        
        self.status_label = QLabel("Database Status: Initializing...", self)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        self.setWindowTitle('PDF Splitter')
        self.setGeometry(300, 300, 300, 200)
        self.show()

    def initialize_database(self):
        current_dir = os.getcwd()
        self.pdf_folder = os.path.join(current_dir, "Split")
        if not os.path.exists(self.pdf_folder):
            os.makedirs(self.pdf_folder)
        
        self.db_path = os.path.join(self.pdf_folder, "pdf_data.db")
        
        if not os.path.exists(self.db_path):
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute('''CREATE TABLE IF NOT EXISTS individuals
                             (id INTEGER PRIMARY KEY AUTOINCREMENT,
                              name TEXT UNIQUE,
                              address TEXT,
                              phone_number TEXT,
                              email TEXT)''')
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
                print(f"Created new database at {self.db_path}")
                self.status_label.setText(f"Database Status: Created - {self.db_path}")
            except sqlite3.Error as e:
                print(f"Error creating database: {e}")
                self.status_label.setText("Database Status: Creation Failed")
                self.db_path = None
        else:
            print(f"Found existing database at {self.db_path}")
            self.status_label.setText(f"Database Status: Found - {self.db_path}")

    def select_pdf(self):
        input_path, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if input_path:
            self.db_path = split_pdf(input_path, self.pdf_folder)
            self.status_label.setText(f"Database Status: Updated - {self.db_path}")
            QMessageBox.information(self, "Complete", f"PDF split complete and data stored in database at {self.db_path}!")
        else:
            QMessageBox.warning(self, "Warning", "Please select a PDF file.")

    def view_database(self):
        if not self.db_path or not os.path.exists(self.db_path):
            QMessageBox.warning(self, "Warning", "No valid database found. Please split a PDF first.")
            return

        self.db_viewer = DatabaseViewer(self.db_path, self.pdf_folder)
        self.db_viewer.show()

    def get_employee_list(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT name FROM individuals ORDER BY name")
        employees = [row[0] for row in c.fetchall()]
        conn.close()
        return employees

    def update_individual_info(self):
        if not self.db_path or not os.path.exists(self.db_path):
            QMessageBox.warning(self, "Warning", "No valid database found. Please split a PDF first.")
            return

        employees = self.get_employee_list()
        if not employees:
            QMessageBox.warning(self, "Warning", "No employees found in the database.")
            return

        name, ok = QInputDialog.getItem(self, "Update Individual Info", 
                                        "Select an employee:", employees, 0, False)
        if ok and name:
            dialog = IndividualInfoDialog(self.db_path, name)
            dialog.exec_()
