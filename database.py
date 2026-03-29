# database.py
"""
Database management with improved error handling and security
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from config import DB_PATH
from utils import handle_exception, DatabaseError

logger = logging.getLogger(__name__)


# ============================================================
#  DATABASE CONNECTION
# ============================================================
class DatabaseConnection:
    """Context manager for database connections"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def __enter__(self):
        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row  # Enable dict-like access
            self.cursor = self.conn.cursor()
            return self.cursor
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise DatabaseError(f"Failed to connect to database: {e}")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.conn.rollback()
            logger.error(f"Database transaction rolled back: {exc_val}")
        else:
            self.conn.commit()
        
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


# ============================================================
#  INITIALIZATION
# ============================================================
@handle_exception
def init_db():
    """Initialize database with all required tables"""
    with DatabaseConnection() as cur:
        # Users table with additional fields
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                email TEXT UNIQUE,
                phone TEXT,
                role TEXT,
                department TEXT,
                join_date TEXT,
                profile_photo TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Attendance table with status field
        cur.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT DEFAULT 'Present',
                confidence REAL,
                location TEXT,
                device_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(user_id, date)
            )
        """)
        
        # Admin users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                role TEXT DEFAULT 'admin',
                is_active INTEGER DEFAULT 1,
                last_login TEXT,
                failed_attempts INTEGER DEFAULT 0,
                locked_until TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # System logs table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                level TEXT,
                module TEXT,
                message TEXT,
                user_id TEXT
            )
        """)
        
        # Settings table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                description TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indices for better performance
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_attendance_date 
            ON attendance(date)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_attendance_user 
            ON attendance(user_id)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_name 
            ON users(name)
        """)
        
        logger.info("Database initialized successfully")


# ============================================================
#  USER MANAGEMENT
# ============================================================
@handle_exception
def register_user(
    user_id: str,
    name: str,
    role: Optional[str] = None,
    department: Optional[str] = None,
    join_date: Optional[str] = None,
    profile_photo: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None
) -> bool:
    """Register or update user with validation"""
    
    if not user_id or not name:
        raise DatabaseError("User ID and name are required")
    
    if not join_date:
        join_date = datetime.now().strftime("%Y-%m-%d")
    
    with DatabaseConnection() as cur:
        cur.execute("""
            INSERT INTO users 
            (user_id, name, email, phone, role, department, join_date, profile_photo, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                name=excluded.name,
                email=excluded.email,
                phone=excluded.phone,
                role=excluded.role,
                department=excluded.department,
                join_date=excluded.join_date,
                profile_photo=excluded.profile_photo,
                updated_at=CURRENT_TIMESTAMP
        """, (user_id, name, email, phone, role, department, join_date, profile_photo))
        
        logger.info(f"User registered/updated: {name} ({user_id})")
        return True


@handle_exception
def delete_user(name: str) -> bool:
    """Delete user and their attendance records"""
    with DatabaseConnection() as cur:
        # Check if user exists
        cur.execute("SELECT user_id FROM users WHERE name=?", (name,))
        user = cur.fetchone()
        
        if not user:
            logger.warning(f"User not found for deletion: {name}")
            return False
        
        # Delete user
        cur.execute("DELETE FROM users WHERE name=?", (name,))
        
        # Optionally keep attendance records or delete them
        # cur.execute("DELETE FROM attendance WHERE name=?", (name,))
        
        logger.info(f"User deleted: {name}")
        return True


@handle_exception
def deactivate_user(user_id: str) -> bool:
    """Deactivate user instead of deleting"""
    with DatabaseConnection() as cur:
        cur.execute("""
            UPDATE users 
            SET is_active=0, updated_at=CURRENT_TIMESTAMP 
            WHERE user_id=?
        """, (user_id,))
        
        logger.info(f"User deactivated: {user_id}")
        return True


@handle_exception
def get_all_users(include_inactive: bool = False) -> List[Dict[str, Any]]:
    """Get all users with optional filtering"""
    with DatabaseConnection() as cur:
        if include_inactive:
            cur.execute("""
                SELECT user_id, name, email, phone, role, department, 
                       join_date, profile_photo, is_active, created_at
                FROM users
                ORDER BY name ASC
            """)
        else:
            cur.execute("""
                SELECT user_id, name, email, phone, role, department, 
                       join_date, profile_photo, is_active, created_at
                FROM users
                WHERE is_active=1
                ORDER BY name ASC
            """)
        
        rows = cur.fetchall()
        return [dict(row) for row in rows]


@handle_exception
def get_user_profile(name: str) -> Optional[Dict[str, Any]]:
    """Get user profile by name"""
    with DatabaseConnection() as cur:
        cur.execute("""
            SELECT user_id, name, email, phone, role, department, 
                   join_date, profile_photo, is_active, created_at
            FROM users 
            WHERE name=?
        """, (name,))
        
        row = cur.fetchone()
        return dict(row) if row else None


@handle_exception
def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user profile by user ID"""
    with DatabaseConnection() as cur:
        cur.execute("""
            SELECT user_id, name, email, phone, role, department, 
                   join_date, profile_photo, is_active, created_at
            FROM users 
            WHERE user_id=?
        """, (user_id,))
        
        row = cur.fetchone()
        return dict(row) if row else None


@handle_exception
def get_user_id_by_name(name: str) -> Optional[str]:
    """Get user ID by name"""
    with DatabaseConnection() as cur:
        cur.execute("SELECT user_id FROM users WHERE name=?", (name,))
        row = cur.fetchone()
        return row['user_id'] if row else None


@handle_exception
def search_users(query: str) -> List[Dict[str, Any]]:
    """Search users by name, ID, or department"""
    with DatabaseConnection() as cur:
        search_pattern = f"%{query}%"
        cur.execute("""
            SELECT user_id, name, email, phone, role, department, 
                   join_date, profile_photo, is_active
            FROM users
            WHERE (name LIKE ? OR user_id LIKE ? OR department LIKE ?)
            AND is_active=1
            ORDER BY name ASC
        """, (search_pattern, search_pattern, search_pattern))
        
        rows = cur.fetchall()
        return [dict(row) for row in rows]


# ============================================================
#  ATTENDANCE MANAGEMENT
# ============================================================
@handle_exception
def mark_attendance(
    user_id: str,
    name: str,
    confidence: Optional[float] = None,
    location: Optional[str] = None,
    device_id: Optional[str] = None
) -> str:
    """Mark attendance with additional metadata"""
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")
    
    with DatabaseConnection() as cur:
        # Check if already marked today
        cur.execute("""
            SELECT id, time FROM attendance
            WHERE user_id=? AND date=?
        """, (user_id, date))
        
        existing = cur.fetchone()
        
        if existing:
            logger.info(f"Attendance already marked for {name} on {date}")
            return f"Already Marked at {existing['time']}"
        
        # Mark attendance
        cur.execute("""
            INSERT INTO attendance 
            (user_id, name, date, time, confidence, location, device_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, name, date, time, confidence, location, device_id))
        
        logger.info(f"Attendance marked: {name} at {time} (confidence: {confidence})")
        return "Marked"


@handle_exception
def get_attendance_by_date(date: str) -> List[Dict[str, Any]]:
    """Get attendance records for a specific date"""
    with DatabaseConnection() as cur:
        cur.execute("""
            SELECT a.user_id, a.name, a.date, a.time, a.status, 
                   a.confidence, u.department, u.role
            FROM attendance a
            LEFT JOIN users u ON a.user_id = u.user_id
            WHERE a.date = ?
            ORDER BY a.time ASC
        """, (date,))
        
        rows = cur.fetchall()
        return [dict(row) for row in rows]


@handle_exception
def get_attendance_by_user(user_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """Get attendance records for a user within date range"""
    with DatabaseConnection() as cur:
        cur.execute("""
            SELECT user_id, name, date, time, status, confidence
            FROM attendance
            WHERE user_id=? AND date BETWEEN ? AND ?
            ORDER BY date DESC, time DESC
        """, (user_id, start_date, end_date))
        
        rows = cur.fetchall()
        return [dict(row) for row in rows]


@handle_exception
def get_today_attendance_count() -> int:
    """Get count of today's attendance"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    with DatabaseConnection() as cur:
        cur.execute("SELECT COUNT(*) as count FROM attendance WHERE date=?", (today,))
        return cur.fetchone()['count']


@handle_exception
def get_total_users() -> int:
    """Get total active users count"""
    with DatabaseConnection() as cur:
        cur.execute("SELECT COUNT(*) as count FROM users WHERE is_active=1")
        return cur.fetchone()['count']


@handle_exception
def get_attendance_percentage(date: str = None) -> float:
    """Calculate attendance percentage for a date"""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    total_users = get_total_users()
    if total_users == 0:
        return 0.0
    
    present_count = len(get_attendance_by_date(date))
    return (present_count / total_users) * 100


@handle_exception
def get_all_attendance(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get all attendance records with optional limit"""
    with DatabaseConnection() as cur:
        query = """
            SELECT a.user_id, a.name, a.date, a.time, a.status, 
                   a.confidence, u.department
            FROM attendance a
            LEFT JOIN users u ON a.user_id = u.user_id
            ORDER BY a.date DESC, a.time DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cur.execute(query)
        rows = cur.fetchall()
        return [dict(row) for row in rows]


@handle_exception
def get_last_attendance() -> Optional[Dict[str, Any]]:
    """Get last attendance record"""
    with DatabaseConnection() as cur:
        cur.execute("""
            SELECT user_id, name, date, time, status
            FROM attendance
            ORDER BY id DESC
            LIMIT 1
        """)
        
        row = cur.fetchone()
        return dict(row) if row else None


@handle_exception
def get_last_marked_user() -> Optional[tuple]:
    """Get last marked user (name, time)"""
    with DatabaseConnection() as cur:
        cur.execute("""
            SELECT name, time
            FROM attendance
            ORDER BY id DESC
            LIMIT 1
        """)
        
        row = cur.fetchone()
        return (row['name'], row['time']) if row else None


# ============================================================
#  ADMIN MANAGEMENT
# ============================================================
@handle_exception
def create_admin(username: str, password_hash: str, email: Optional[str] = None) -> bool:
    """Create admin user"""
    with DatabaseConnection() as cur:
        cur.execute("""
            INSERT INTO admins (username, password_hash, email)
            VALUES (?, ?, ?)
        """, (username, password_hash, email))
        
        logger.info(f"Admin created: {username}")
        return True


@handle_exception
def get_admin(username: str) -> Optional[Dict[str, Any]]:
    """Get admin by username"""
    with DatabaseConnection() as cur:
        cur.execute("""
            SELECT id, username, password_hash, email, role, is_active,
                   last_login, failed_attempts, locked_until
            FROM admins
            WHERE username=?
        """, (username,))
        
        row = cur.fetchone()
        return dict(row) if row else None


@handle_exception
def update_admin_login(username: str, success: bool = True):
    """Update admin login timestamp and failed attempts"""
    with DatabaseConnection() as cur:
        if success:
            cur.execute("""
                UPDATE admins
                SET last_login=CURRENT_TIMESTAMP, failed_attempts=0, locked_until=NULL
                WHERE username=?
            """, (username,))
        else:
            cur.execute("""
                UPDATE admins
                SET failed_attempts=failed_attempts+1
                WHERE username=?
            """, (username,))


# ============================================================
#  STATISTICS & ANALYTICS
# ============================================================
@handle_exception
def get_attendance_stats(start_date: str, end_date: str) -> Dict[str, Any]:
    """Get attendance statistics for date range"""
    with DatabaseConnection() as cur:
        # Total attendance records
        cur.execute("""
            SELECT COUNT(*) as total
            FROM attendance
            WHERE date BETWEEN ? AND ?
        """, (start_date, end_date))
        total = cur.fetchone()['total']
        
        # Unique users who attended
        cur.execute("""
            SELECT COUNT(DISTINCT user_id) as unique_users
            FROM attendance
            WHERE date BETWEEN ? AND ?
        """, (start_date, end_date))
        unique_users = cur.fetchone()['unique_users']
        
        # Daily breakdown
        cur.execute("""
            SELECT date, COUNT(*) as count
            FROM attendance
            WHERE date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date
        """, (start_date, end_date))
        daily_breakdown = [dict(row) for row in cur.fetchall()]
        
        return {
            'total_records': total,
            'unique_users': unique_users,
            'daily_breakdown': daily_breakdown,
            'total_users': get_total_users()
        }


@handle_exception
def get_user_attendance_summary(user_id: str, month: str) -> Dict[str, Any]:
    """Get attendance summary for a user in a specific month"""
    start_date = f"{month}-01"
    end_date = f"{month}-31"
    
    records = get_attendance_by_user(user_id, start_date, end_date)
    
    return {
        'user_id': user_id,
        'month': month,
        'total_days': len(records),
        'records': records
    }
