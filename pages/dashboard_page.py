# pages/dashboard_page.py
"""
Dashboard page with attendance statistics and visualizations
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QPushButton
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap
from datetime import datetime
import logging

from database import (
    get_today_attendance_count, get_total_users,
    get_last_marked_user, get_attendance_percentage
)

logger = logging.getLogger(__name__)


class DashboardPage(QWidget):
    """Main dashboard with statistics"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_stats)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Dashboard")
        title.setObjectName("titleLabel")
        layout.addWidget(title)
        
        subtitle = QLabel(datetime.now().strftime("%A, %B %d, %Y"))
        subtitle.setObjectName("mutedLabel")
        layout.addWidget(subtitle)
        
        # Stats grid
        stats_layout = QGridLayout()
        stats_layout.setSpacing(20)
        
        # Stat cards
        self.total_users_card = self.create_stat_card(
            "Total Users", "0", "#00e5ff"
        )
        self.today_attendance_card = self.create_stat_card(
            "Today's Attendance", "0", "#ff2bd6"
        )
        self.attendance_rate_card = self.create_stat_card(
            "Attendance Rate", "0%", "#00ff88"
        )
        self.last_marked_card = self.create_stat_card(
            "Last Marked", "None", "#ffa500"
        )
        
        stats_layout.addWidget(self.total_users_card, 0, 0)
        stats_layout.addWidget(self.today_attendance_card, 0, 1)
        stats_layout.addWidget(self.attendance_rate_card, 1, 0)
        stats_layout.addWidget(self.last_marked_card, 1, 1)
        
        layout.addLayout(stats_layout)
        
        # Quick actions
        actions_label = QLabel("Quick Actions")
        actions_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        actions_label.setStyleSheet("color: #cccccc; margin-top: 10px;")
        layout.addWidget(actions_label)
        
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(15)
        
        refresh_btn = QPushButton("🔄 Refresh Stats")
        refresh_btn.clicked.connect(self.refresh_stats)
        actions_layout.addWidget(refresh_btn)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        layout.addStretch()
        
        # Initial load
        self.refresh_stats()
    
    def create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        """Create a statistics card"""
        card = QFrame()
        card.setObjectName("glassCard")
        card.setMinimumHeight(120)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #b0b0c0; font-size: 13px;")
        card_layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Segoe UI", 28, QFont.Bold))
        value_label.setStyleSheet(f"color: {color};")
        setattr(card, 'value_label', value_label)
        card_layout.addWidget(value_label)
        
        card_layout.addStretch()
        
        return card
    
    def refresh_stats(self):
        """Refresh dashboard statistics"""
        try:
            # Total users
            total_users = get_total_users()
            self.total_users_card.value_label.setText(str(total_users))
            
            # Today's attendance
            today_count = get_today_attendance_count()
            self.today_attendance_card.value_label.setText(str(today_count))
            
            # Attendance rate
            if total_users > 0:
                rate = (today_count / total_users) * 100
                self.attendance_rate_card.value_label.setText(f"{rate:.1f}%")
            else:
                self.attendance_rate_card.value_label.setText("0%")
            
            # Last marked
            last_marked = get_last_marked_user()
            if last_marked:
                name, time = last_marked
                self.last_marked_card.value_label.setText(f"{name}")
                self.last_marked_card.value_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
            else:
                self.last_marked_card.value_label.setText("None")
            
            logger.debug("Dashboard stats refreshed")
        
        except Exception as e:
            logger.error(f"Error refreshing stats: {e}")
