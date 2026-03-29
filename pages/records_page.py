# pages/records_page.py
"""
Attendance Records Page
View, filter, and export attendance records
"""
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFrame, QLineEdit,
    QComboBox, QDateEdit, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor
import logging
import csv

from database import (
    get_all_attendance, get_attendance_by_date,
    get_all_users, get_attendance_stats
)
from config import EXPORT_DIR

logger = logging.getLogger(__name__)


class RecordsPage(QWidget):
    """Attendance records viewing and management"""
    
    def __init__(self):
        super().__init__()
        self.all_records = []
        self.filtered_records = []
        self.init_ui()
        self.load_records()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("📋 Attendance Records")
        title.setObjectName("titleLabel")
        header.addWidget(title)
        
        header.addStretch()
        
        # Export button
        export_btn = QPushButton("📥 Export to CSV")
        export_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ff88, stop:1 #00cc66);
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ff99, stop:1 #00dd77);
            }
        """)
        export_btn.clicked.connect(self.export_to_csv)
        header.addWidget(export_btn)
        
        layout.addLayout(header)
        
        subtitle = QLabel("View and manage all attendance records")
        subtitle.setObjectName("mutedLabel")
        layout.addWidget(subtitle)
        
        # Filters
        filter_container = QFrame()
        filter_container.setObjectName("glassCard")
        
        filter_layout = QVBoxLayout(filter_container)
        filter_layout.setContentsMargins(20, 20, 20, 20)
        filter_layout.setSpacing(15)
        
        filter_title = QLabel("🔍 Filters")
        filter_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        filter_title.setStyleSheet("color: #00e5ff;")
        filter_layout.addWidget(filter_title)
        
        filter_row1 = QHBoxLayout()
        filter_row1.setSpacing(15)
        
        # Search box
        search_layout = QVBoxLayout()
        search_layout.addWidget(QLabel("Search Name"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter name to search...")
        self.search_input.textChanged.connect(self.apply_filters)
        search_layout.addWidget(self.search_input)
        filter_row1.addLayout(search_layout)
        
        # Department filter
        dept_layout = QVBoxLayout()
        dept_layout.addWidget(QLabel("Department"))
        self.dept_combo = QComboBox()
        self.dept_combo.addItems([
            "All Departments",
            "IT", "HR", "Finance", "Marketing",
            "Operations", "Sales", "Engineering", "Other"
        ])
        self.dept_combo.currentTextChanged.connect(self.apply_filters)
        dept_layout.addWidget(self.dept_combo)
        filter_row1.addLayout(dept_layout)
        
        # Date from
        from_layout = QVBoxLayout()
        from_layout.addWidget(QLabel("From Date"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.dateChanged.connect(self.apply_filters)
        from_layout.addWidget(self.date_from)
        filter_row1.addLayout(from_layout)
        
        # Date to
        to_layout = QVBoxLayout()
        to_layout.addWidget(QLabel("To Date"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.dateChanged.connect(self.apply_filters)
        to_layout.addWidget(self.date_to)
        filter_row1.addLayout(to_layout)
        
        filter_layout.addLayout(filter_row1)
        
        # Filter buttons
        filter_buttons = QHBoxLayout()
        filter_buttons.setSpacing(10)
        
        today_btn = QPushButton("Today")
        today_btn.clicked.connect(self.filter_today)
        filter_buttons.addWidget(today_btn)
        
        week_btn = QPushButton("This Week")
        week_btn.clicked.connect(self.filter_week)
        filter_buttons.addWidget(week_btn)
        
        month_btn = QPushButton("This Month")
        month_btn.clicked.connect(self.filter_month)
        filter_buttons.addWidget(month_btn)
        
        clear_btn = QPushButton("Clear Filters")
        clear_btn.clicked.connect(self.clear_filters)
        filter_buttons.addWidget(clear_btn)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_records)
        filter_buttons.addWidget(refresh_btn)
        
        filter_buttons.addStretch()
        filter_layout.addLayout(filter_buttons)
        
        layout.addWidget(filter_container)
        
        # Stats row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        self.total_label = QLabel("Total Records: 0")
        self.total_label.setStyleSheet("color: #00e5ff; font-size: 14px; font-weight: bold;")
        stats_layout.addWidget(self.total_label)
        
        self.showing_label = QLabel("Showing: 0")
        self.showing_label.setStyleSheet("color: #ff2bd6; font-size: 14px; font-weight: bold;")
        stats_layout.addWidget(self.showing_label)
        
        stats_layout.addStretch()
        
        layout.addLayout(stats_layout)
        
        # Table
        table_container = QFrame()
        table_container.setObjectName("glassCard")
        
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(5, 5, 5, 5)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "User ID", "Name", "Department", "Date", "Time", "Status"
        ])
        
        # Table styling
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #080810;
                gridline-color: #262637;
                color: #f0f0f0;
                border: none;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #1a1a2e;
            }
            QTableWidget::item:selected {
                background-color: rgba(0, 229, 255, 0.2);
                color: #00e5ff;
            }
            QHeaderView::section {
                background-color: #101020;
                color: #00e5ff;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #00e5ff;
                font-weight: bold;
            }
        """)
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        
        table_layout.addWidget(self.table)
        layout.addWidget(table_container)
    
    def load_records(self):
        """Load all attendance records"""
        try:
            self.all_records = get_all_attendance()
            self.total_label.setText(f"Total Records: {len(self.all_records)}")
            self.apply_filters()
            logger.info(f"Loaded {len(self.all_records)} records")
        except Exception as e:
            logger.error(f"Load records error: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load records:\n{str(e)}")
    
    def apply_filters(self):
        """Apply all filters"""
        search_text = self.search_input.text().lower()
        department = self.dept_combo.currentText()
        date_from = self.date_from.date().toPyDate()
        date_to = self.date_to.date().toPyDate()
        
        self.filtered_records = []
        
        for record in self.all_records:
            # Search filter
            if search_text and search_text not in record['name'].lower():
                continue
            
            # Department filter
            if department != "All Departments":
                if record.get('department') != department:
                    continue
            
            # Date filter
            try:
                record_date = datetime.strptime(record['date'], "%Y-%m-%d").date()
                if record_date < date_from or record_date > date_to:
                    continue
            except:
                continue
            
            self.filtered_records.append(record)
        
        self.update_table()
    
    def update_table(self):
        """Update table with filtered records"""
        self.table.setRowCount(0)
        
        for record in self.filtered_records:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # User ID
            item = QTableWidgetItem(record['user_id'])
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, item)
            
            # Name
            item = QTableWidgetItem(record['name'])
            item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table.setItem(row, 1, item)
            
            # Department
            dept = record.get('department', 'N/A')
            item = QTableWidgetItem(dept if dept else 'N/A')
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, item)
            
            # Date
            item = QTableWidgetItem(record['date'])
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, item)
            
            # Time
            item = QTableWidgetItem(record['time'])
            item.setTextAlignment(Qt.AlignCenter)
            item.setForeground(QColor("#00e5ff"))
            self.table.setItem(row, 4, item)
            
            # Status
            status = record.get('status', 'Present')
            item = QTableWidgetItem(status)
            item.setTextAlignment(Qt.AlignCenter)
            
            if status == "Present":
                item.setForeground(QColor("#00ff88"))
            else:
                item.setForeground(QColor("#ffa500"))
            
            self.table.setItem(row, 5, item)
        
        self.showing_label.setText(f"Showing: {len(self.filtered_records)}")
    
    def filter_today(self):
        """Show today's records"""
        today = QDate.currentDate()
        self.date_from.setDate(today)
        self.date_to.setDate(today)
        self.apply_filters()
    
    def filter_week(self):
        """Show this week's records"""
        today = QDate.currentDate()
        week_start = today.addDays(-today.dayOfWeek() + 1)
        self.date_from.setDate(week_start)
        self.date_to.setDate(today)
        self.apply_filters()
    
    def filter_month(self):
        """Show this month's records"""
        today = QDate.currentDate()
        month_start = QDate(today.year(), today.month(), 1)
        self.date_from.setDate(month_start)
        self.date_to.setDate(today)
        self.apply_filters()
    
    def clear_filters(self):
        """Clear all filters"""
        self.search_input.clear()
        self.dept_combo.setCurrentIndex(0)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_to.setDate(QDate.currentDate())
        self.apply_filters()
    
    def export_to_csv(self):
        """Export filtered records to CSV"""
        try:
            if not self.filtered_records:
                QMessageBox.warning(self, "No Data", "No records to export!")
                return
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = EXPORT_DIR / f"attendance_export_{timestamp}.csv"
            
            # Write CSV
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    'User ID', 'Name', 'Department', 'Date', 'Time', 'Status'
                ])
                
                # Data
                for record in self.filtered_records:
                    writer.writerow([
                        record['user_id'],
                        record['name'],
                        record.get('department', 'N/A'),
                        record['date'],
                        record['time'],
                        record.get('status', 'Present')
                    ])
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Exported {len(self.filtered_records)} records to:\n\n{filename}"
            )
            
            logger.info(f"Exported {len(self.filtered_records)} records to {filename}")
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export:\n{str(e)}")
