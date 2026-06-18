# database.py
import sqlite3
from datetime import datetime, timedelta
import hashlib
from config import DB_PATH, REFERRAL_POINTS, SIGNUP_BONUS

class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._connect()
        cur = conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                join_date TEXT,
                last_active TEXT,
                points INTEGER DEFAULT 0,
                is_premium INTEGER DEFAULT 0,
                premium_expiry TEXT,
                referred_by INTEGER,
                referral_code TEXT,
                usage_count INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER,
                points_earned INTEGER DEFAULT 8,
                referral_date TEXT
            );
            CREATE TABLE IF NOT EXISTS banned_users (
                user_id INTEGER PRIMARY KEY,
                reason TEXT,
                banned_by INTEGER,
                banned_date TEXT
            );
            CREATE TABLE IF NOT EXISTS feature_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                feature_name TEXT,
                input_data TEXT,
                output_data TEXT,
                timestamp TEXT,
                status TEXT
            );
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                order_id TEXT,
                payment_id TEXT,
                amount INTEGER,
                status TEXT,
                timestamp TEXT
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)
        conn.commit()
        conn.close()

    # ----- User -----
    def register_user(self, user_id, username=None, first_name=None, last_name=None, referred_by=None):
        conn = self._connect()
        cur = conn.cursor()
        now = datetime.now().isoformat()
        cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if cur.fetchone():
            cur.execute("UPDATE users SET username=?, first_name=?, last_name=?, last_active=? WHERE user_id=?",
                        (username, first_name, last_name, now, user_id))
        else:
            ref_code = hashlib.md5(str(user_id).encode()).hexdigest()[:8]
            cur.execute("""INSERT INTO users 
                (user_id, username, first_name, last_name, join_date, last_active, referral_code, points)
                VALUES (?,?,?,?,?,?,?,?)""",
                (user_id, username, first_name, last_name, now, now, ref_code, SIGNUP_BONUS))
            if referred_by:
                cur.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (REFERRAL_POINTS, referred_by))
                cur.execute("INSERT INTO referrals (referrer_id, referred_id, points_earned, referral_date) VALUES (?,?,?,?)",
                            (referred_by, user_id, REFERRAL_POINTS, now))
        conn.commit()
        conn.close()

    def get_user(self, user_id):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        return row

    def get_all_users(self):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users")
        rows = cur.fetchall()
        conn.close()
        return rows

    def get_user_count(self):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as count FROM users")
        count = cur.fetchone()['count']
        conn.close()
        return count

    def get_points(self, user_id):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        return row['points'] if row else 0

    def add_points(self, user_id, amount):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        conn.close()

    def deduct_points(self, user_id, amount):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row and row['points'] >= amount:
            cur.execute("UPDATE users SET points = points - ? WHERE user_id = ?", (amount, user_id))
            conn.commit()
            conn.close()
            return True
        conn.close()
        return False

    def is_premium(self, user_id):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT is_premium, premium_expiry FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        if not row or row['is_premium'] == 0:
            return False
        if row['premium_expiry']:
            exp = datetime.fromisoformat(row['premium_expiry'])
            if exp > datetime.now():
                return True
            else:
                self.set_premium(user_id, 0)
                return False
        return False

    def set_premium(self, user_id, days=30):
        conn = self._connect()
        cur = conn.cursor()
        if days <= 0:
            cur.execute("UPDATE users SET is_premium=0, premium_expiry=NULL WHERE user_id=?", (user_id,))
        else:
            expiry = (datetime.now() + timedelta(days=days)).isoformat()
            cur.execute("UPDATE users SET is_premium=1, premium_expiry=? WHERE user_id=?", (expiry, user_id))
        conn.commit()
        conn.close()

    def is_banned(self, user_id):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT reason FROM banned_users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        return (True, row['reason']) if row else (False, None)

    def ban_user(self, user_id, reason=None, banned_by=None):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO banned_users (user_id, reason, banned_by, banned_date) VALUES (?,?,?,?)",
                    (user_id, reason, banned_by, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def unban_user(self, user_id):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    def get_banned_users(self):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM banned_users ORDER BY banned_date DESC")
        rows = cur.fetchall()
        conn.close()
        return rows

    def log_feature(self, user_id, feature_name, input_data=None, output_data=None, status="ok"):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("""INSERT INTO feature_logs (user_id, feature_name, input_data, output_data, timestamp, status)
                       VALUES (?,?,?,?,?,?)""",
                    (user_id, feature_name, str(input_data), str(output_data), datetime.now().isoformat(), status))
        conn.commit()
        conn.close()

    def add_transaction(self, user_id, order_id, payment_id, amount, status):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("""INSERT INTO transactions (user_id, order_id, payment_id, amount, status, timestamp)
                       VALUES (?,?,?,?,?,?)""",
                    (user_id, order_id, payment_id, amount, status, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def update_transaction(self, order_id, payment_id, status):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("UPDATE transactions SET payment_id=?, status=? WHERE order_id=?", (payment_id, status, order_id))
        conn.commit()
        conn.close()