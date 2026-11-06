#!/usr/bin/env python3
"""
Mahjong Riichi - Database Manager
MySQL database for leaderboard and user management
"""

import mysql.connector
from mysql.connector import Error
import hashlib
import secrets
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path


@dataclass
class User:
    user_id: int
    username: str
    password_hash: str
    created_at: str
    games_played: int = 0
    games_won: int = 0
    total_score: int = 0
    highest_score: int = 0
    best_hand_value: int = 0
    is_online: bool = False


class Database:
    """MySQL database manager for Mahjong game"""

    def __init__(self, host='localhost', user='root', password='', database='mahjong'):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.conn = None
        self._connect()
        self._init_db()

    def _connect(self):
        """Connect to MySQL database"""
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
        except Error as e:
            # Try without database first to create it
            try:
                self.conn = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    charset='utf8mb4',
                    collation='utf8mb4_unicode_ci'
                )
                cursor = self.conn.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                cursor.close()
                self.conn.close()
                # Now connect with database
                self.conn = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    charset='utf8mb4',
                    collation='utf8mb4_unicode_ci'
                )
                print(f"Database '{self.database}' created successfully!")
            except Error as e2:
                print(f"Error connecting to MySQL: {e2}")
                raise e2

    def _init_db(self):
        """Initialize database tables"""
        cursor = self.conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                games_played INT DEFAULT 0,
                games_won INT DEFAULT 0,
                total_score INT DEFAULT 0,
                highest_score INT DEFAULT 0,
                best_hand_value INT DEFAULT 0,
                INDEX idx_username (username),
                INDEX idx_total_score (total_score)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Game history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS game_history (
                game_id INT AUTO_INCREMENT PRIMARY KEY,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                player_count INT,
                winner_id INT,
                max_score INT,
                duration_seconds INT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        self.conn.commit()
        cursor.close()

    def close(self):
        """Close database connection"""
        if self.conn and self.conn.is_connected():
            self.conn.close()

    # =========================================================================
    # USER MANAGEMENT
    # =========================================================================

    def _hash_password(self, password: str, salt: str = None) -> tuple:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return salt + hash_obj.hex(), salt

    def create_user(self, username: str, password: str) -> Optional[User]:
        """Create a new user"""
        try:
            password_hash, salt = self._hash_password(password)
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute(
                """INSERT INTO users (username, password_hash) VALUES (%s, %s)""",
                (username, password_hash)
            )
            self.conn.commit()
            cursor.close()
            return self.get_user_by_username(username)
        except mysql.connector.IntegrityError:
            return None  # Username already exists

    def verify_user(self, username: str, password: str) -> Optional[User]:
        """Verify user credentials"""
        user = self.get_user_by_username(username)
        if user is None:
            return None

        cursor = self.conn.cursor(dictionary=True)
        cursor.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        cursor.close()

        if row is None:
            return None

        # Verify password (stored hash format: salt + hash)
        stored_hash = row['password_hash']
        salt = stored_hash[:32]  # First 32 chars is salt
        stored_password_hash = stored_hash[32:]

        password_hash, _ = self._hash_password(password, salt)
        if password_hash == stored_hash:
            return user
        return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        return self._row_to_user(row) if row else None

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        cursor.close()
        return self._row_to_user(row) if row else None

    def _row_to_user(self, row: dict) -> Optional[User]:
        """Convert row to User object"""
        if row is None:
            return None
        return User(
            user_id=row['user_id'],
            username=row['username'],
            password_hash=row['password_hash'],
            created_at=str(row['created_at']),
            games_played=row.get('games_played', 0),
            games_won=row.get('games_won', 0),
            total_score=row.get('total_score', 0),
            highest_score=row.get('highest_score', 0),
            best_hand_value=row.get('best_hand_value', 0)
        )

    # =========================================================================
    # GAME STATISTICS
    # =========================================================================

    def record_game(self, winner_id: int, scores: List[int],
                   player_ids: List[int], duration: int = 0) -> int:
        """Record a completed game"""
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO game_history (winner_id, max_score, duration_seconds, player_count)
               VALUES (%s, %s, %s, %s)""",
            (winner_id, max(scores) if scores else 0, duration, len(scores))
        )
        game_id = cursor.lastrowid

        # Update user statistics
        for i, (player_id, score) in enumerate(zip(player_ids, scores)):
            is_winner = player_id == winner_id
            cursor.execute(
                """UPDATE users SET
                   games_played = games_played + 1,
                   games_won = games_won + %s,
                   total_score = total_score + %s,
                   highest_score = GREATEST(highest_score, %s)
                   WHERE user_id = %s""",
                (1 if is_winner else 0, score, score, player_id)
            )

        self.conn.commit()
        cursor.close()
        return game_id

    def record_hand_value(self, user_id: int, hand_value: int):
        """Record a hand value for user"""
        cursor = self.conn.cursor()
        cursor.execute(
            """UPDATE users SET
               best_hand_value = GREATEST(best_hand_value, %s)
               WHERE user_id = %s""",
            (hand_value, user_id)
        )
        self.conn.commit()
        cursor.close()

    # =========================================================================
    # LEADERBOARD
    # =========================================================================

    def get_leaderboard(self, limit: int = 20) -> List[Dict]:
        """Get top players"""
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT
                user_id,
                username,
                games_played,
                games_won,
                ROUND(games_won * 100.0 / NULLIF(games_played, 0), 1) as win_rate,
                highest_score,
                best_hand_value,
                total_score
            FROM users
            WHERE games_played > 0
            ORDER BY total_score DESC
            LIMIT %s""",
            (limit,)
        )
        result = [dict(row) for row in cursor.fetchall()]
        # Add rank manually
        for i, entry in enumerate(result):
            entry['rank'] = i + 1
        cursor.close()
        return result

    def get_user_rank(self, user_id: int) -> Optional[int]:
        """Get user's rank"""
        cursor = self.conn.cursor(dictionary=True)
        # Get user's total score first
        cursor.execute("SELECT total_score FROM users WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            return None

        user_score = row['total_score']

        # Count how many players have higher score
        cursor.execute("""
            SELECT COUNT(*) + 1 as user_rank
            FROM users
            WHERE games_played > 0 AND total_score > %s
        """, (user_score,))
        row = cursor.fetchone()
        cursor.close()
        return row['user_rank'] if row else None

    def get_player_stats(self, user_id: int) -> Optional[Dict]:
        """Get detailed player statistics"""
        user = self.get_user_by_id(user_id)
        if user is None:
            return None

        rank = self.get_user_rank(user_id)
        win_rate = (user.games_won / user.games_played * 100) if user.games_played > 0 else 0

        return {
            'user_id': user.user_id,
            'username': user.username,
            'rank': rank,
            'games_played': user.games_played,
            'games_won': user.games_won,
            'win_rate': round(win_rate, 1),
            'total_score': user.total_score,
            'highest_score': user.highest_score,
            'best_hand_value': user.best_hand_value,
            'created_at': user.created_at
        }

    def get_recent_games(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's recent games"""
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT * FROM game_history
               ORDER BY played_at DESC LIMIT %s""",
            (limit,)
        )
        result = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        return result

    # =========================================================================
    # MIGRATION FROM SQLITE
    # =========================================================================

    @staticmethod
    def migrate_from_sqlite(sqlite_path: str, host='localhost', user='root', password='', database='mahjong'):
        """Migrate data from SQLite database to MySQL"""
        import sqlite3

        # First create MySQL tables
        mysql_db = Database(host, user, password, database)

        # Connect to SQLite
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row

        sqlite_cursor = sqlite_conn.cursor()

        # Migrate users
        sqlite_cursor.execute("SELECT * FROM users")
        users = sqlite_cursor.fetchall()

        mysql_cursor = mysql_db.conn.cursor()

        for user_row in users:
            try:
                mysql_cursor.execute("""
                    INSERT INTO users (user_id, username, password_hash, created_at,
                                     games_played, games_won, total_score,
                                     highest_score, best_hand_value)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    games_played = VALUES(games_played),
                    games_won = VALUES(games_won),
                    total_score = VALUES(total_score),
                    highest_score = VALUES(highest_score),
                    best_hand_value = VALUES(best_hand_value)
                """, (
                    user_row['user_id'],
                    user_row['username'],
                    user_row['password_hash'],
                    user_row['created_at'],
                    user_row.get('games_played', 0),
                    user_row.get('games_won', 0),
                    user_row.get('total_score', 0),
                    user_row.get('highest_score', 0),
                    user_row.get('best_hand_value', 0)
                ))
            except Exception as e:
                print(f"Error migrating user {user_row['username']}: {e}")

        mysql_db.conn.commit()

        # Migrate game history
        sqlite_cursor.execute("SELECT * FROM game_history")
        games = sqlite_cursor.fetchall()

        for game_row in games:
            mysql_cursor.execute("""
                INSERT INTO game_history (game_id, played_at, player_count, winner_id, max_score, duration_seconds)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                game_row['game_id'],
                game_row['played_at'],
                game_row['player_count'],
                game_row['winner_id'],
                game_row['max_score'],
                game_row.get('duration_seconds', 0)
            ))

        mysql_db.conn.commit()
        mysql_cursor.close()

        sqlite_conn.close()
        mysql_db.close()

        print(f"Migration from {sqlite_path} to MySQL completed!")


# Singleton instance
_db_instance: Optional[Database] = None

def get_database() -> Database:
    """Get or create database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


# Demo function
if __name__ == "__main__":
    db = get_database()

    # Create test users
    print("Creating test users...")
    db.create_user("player1", "password123")
    db.create_user("player2", "password123")
    db.create_user("player3", "password123")

    # Record some games
    print("Recording games...")
    db.record_game(winner_id=1, scores=[35000, 28000, 25000, 12000],
                  player_ids=[1, 2, 3, 4], duration=600)
    db.record_game(winner_id=2, scores=[40000, 32000, 18000, 10000],
                  player_ids=[1, 2, 3, 4], duration=720)

    # Get leaderboard
    print("\n=== Leaderboard ===")
    leaderboard = db.get_leaderboard()
    for entry in leaderboard:
        print(f"{entry['rank']}. {entry['username']} - Score: {entry['total_score']}, "
              f"Win Rate: {entry['win_rate']}%")

    # Get player stats
    print("\n=== Player 1 Stats ===")
    stats = db.get_player_stats(1)
    for key, value in stats.items():
        print(f"{key}: {value}")

    db.close()
