import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "database.db"

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "local-educational-demo-change-before-deployment"
)

USERNAME = "student"
PASSWORD_HASH = generate_password_hash("Demo@123")

MAX_ATTEMPTS = 5
LOCK_SECONDS = 60


def get_db():
    db = sqlite3.connect(DATABASE, timeout=10)
    db.row_factory = sqlite3.Row
    return db


def initialize_database():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                event TEXT NOT NULL,
                status TEXT NOT NULL,
                event_time TEXT NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS login_security (
                username TEXT PRIMARY KEY,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until REAL NOT NULL DEFAULT 0
            )
        """)


def record_activity(db, username, event, status):
    db.execute("""
        INSERT INTO activity
        (username, event, status, event_time)
        VALUES (?, ?, ?, ?)
    """, (
        username[:50] or "unknown",
        event,
        status,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))


def get_recent_activity():
    with get_db() as db:
        rows = db.execute("""
            SELECT username, event, status, event_time
            FROM activity
            ORDER BY id DESC
            LIMIT 20
        """).fetchall()

        return [dict(row) for row in rows]


def get_statistics():
    with get_db() as db:
        total = db.execute(
            "SELECT COUNT(*) FROM activity"
        ).fetchone()[0]

        failed = db.execute("""
            SELECT COUNT(*) FROM activity
            WHERE status = 'FAILED'
        """).fetchone()[0]

        blocked = db.execute("""
            SELECT COUNT(*) FROM activity
            WHERE status = 'BLOCKED'
        """).fetchone()[0]

        successful = db.execute("""
            SELECT COUNT(*) FROM activity
            WHERE status = 'SUCCESS'
        """).fetchone()[0]

        active_locks = db.execute("""
            SELECT COUNT(*) FROM login_security
            WHERE locked_until > ?
        """, (time.time(),)).fetchone()[0]

    return {
        "total": total,
        "failed": failed,
        "blocked": blocked,
        "successful": successful,
        "active_locks": active_locks
    }


@app.route("/", methods=["GET", "POST"])
def login():
    message = ""
    message_type = "error"

    if request.method == "POST":
        username = request.form.get(
            "username", ""
        ).strip()[:50]

        password = request.form.get("password", "")

        if not username or not password:
            message = "Please enter your username and password."

        else:
            now = time.time()

            with get_db() as db:
                row = db.execute("""
                    SELECT failed_attempts, locked_until
                    FROM login_security
                    WHERE username = ?
                """, (username,)).fetchone()

                if row is None:
                    attempts = 0
                    locked_until = 0.0

                    db.execute("""
                        INSERT INTO login_security
                        (username, failed_attempts, locked_until)
                        VALUES (?, 0, 0)
                    """, (username,))
                else:
                    attempts = row["failed_attempts"]
                    locked_until = row["locked_until"]

                if locked_until > now:
                    seconds_left = max(
                        1, int(locked_until - now + 0.999)
                    )

                    message = (
                        "Account temporarily locked. "
                        f"Try again in {seconds_left} seconds."
                    )

                    record_activity(
                        db,
                        username,
                        "Login blocked by temporary lockout",
                        "BLOCKED"
                    )

                else:
                    if locked_until > 0:
                        attempts = 0
                        locked_until = 0.0

                    valid_login = (
                        username == USERNAME
                        and check_password_hash(
                            PASSWORD_HASH, password
                        )
                    )

                    if valid_login:
                        db.execute("""
                            UPDATE login_security
                            SET failed_attempts = 0,
                                locked_until = 0
                            WHERE username = ?
                        """, (username,))

                        record_activity(
                            db,
                            username,
                            "Successful login",
                            "SUCCESS"
                        )

                        session.clear()
                        session["username"] = username

                        return redirect(url_for("dashboard"))

                    attempts += 1

                    if attempts >= MAX_ATTEMPTS:
                        locked_until = now + LOCK_SECONDS
                        attempts = MAX_ATTEMPTS

                        message = (
                            "Too many failed attempts. "
                            "Login locked for 60 seconds."
                        )
                    else:
                        remaining = MAX_ATTEMPTS - attempts
                        word = (
                            "attempt"
                            if remaining == 1
                            else "attempts"
                        )

                        message = (
                            "Invalid credentials. "
                            f"{remaining} {word} remaining."
                        )

                    db.execute("""
                        UPDATE login_security
                        SET failed_attempts = ?,
                            locked_until = ?
                        WHERE username = ?
                    """, (attempts, locked_until, username))

                    record_activity(
                        db,
                        username,
                        "Failed login attempt",
                        "FAILED"
                    )

    return render_template(
        "login.html",
        message=message,
        message_type=message_type
    )


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        username=session["username"],
        stats=get_statistics(),
        activities=get_recent_activity()
    )


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


initialize_database()


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )