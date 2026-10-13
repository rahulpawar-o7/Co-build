
# app.py

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "cobuild.db"

app = Flask(
    __name__,
    template_folder=str(BASE_DIR),
    static_folder=str(BASE_DIR),
    static_url_path="",
)


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def to_dict(row):
    return dict(row) if row else None


def get_data():
    if request.is_json:
        return request.get_json() or {}

    data = request.form.to_dict()
    for key in request.form:
        values = request.form.getlist(key)
        if len(values) > 1:
            data[key] = values
    return data


def json_list(value):
    try:
        return json.loads(value or "[]")
    except json.JSONDecodeError:
        return []


def init_database():
    with get_db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                year TEXT,
                skills TEXT NOT NULL DEFAULT '[]',
                availability_hours INTEGER DEFAULT 0,
                interests TEXT NOT NULL DEFAULT '[]',
                work_style TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                title TEXT NOT NULL,
                audience TEXT,
                problem TEXT,
                category TEXT,
                target_date TEXT,
                required_skills TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'planning',
                progress INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS project_members (
                project_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                member_role TEXT DEFAULT 'member',
                PRIMARY KEY (project_id, user_id),
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                assignee_id INTEGER,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'todo',
                due_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (assignee_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                mood INTEGER NOT NULL,
                progress_note TEXT,
                blocker TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """
        )

        user_count = db.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"]

        if user_count > 0:
            return

        users = [
            (
                "Aarav Kumar",
                "Student Builder",
                "2nd Year",
                ["Python", "Research", "Product"],
                10,
                ["Startups", "Campus Life"],
                "Structured",
            ),
            (
                "Naina Kapoor",
                "UI/UX Designer",
                "2nd Year",
                ["Figma", "User Research", "Prototyping"],
                8,
                ["Design", "Social Impact"],
                "Collaborative",
            ),
            (
                "Vihaan Desai",
                "Full-stack Developer",
                "3rd Year",
                ["React", "Python", "APIs"],
                6,
                ["Web Apps", "Startups"],
                "Focused",
            ),
            (
                "Sana Prakash",
                "Growth & Content",
                "2nd Year",
                ["Marketing", "Writing", "Community"],
                10,
                ["Campus Life", "Content"],
                "Communicative",
            ),
            (
                "Maya Shah",
                "Product Designer",
                "2nd Year",
                ["Figma", "UX Writing"],
                7,
                ["Marketplaces", "Design"],
                "Collaborative",
            ),
            (
                "Rohan Mehta",
                "Backend Developer",
                "3rd Year",
                ["Python", "Flask", "SQLite"],
                6,
                ["Web Apps", "Marketplaces"],
                "Focused",
            ),
            (
                "Isha Patel",
                "Researcher",
                "2nd Year",
                ["User Research", "Interviews"],
                5,
                ["Campus Life", "Social Impact"],
                "Structured",
            ),
        ]

        db.executemany(
            """
            INSERT INTO users
            (name, role, year, skills, availability_hours, interests, work_style)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    name,
                    role,
                    year,
                    json.dumps(skills),
                    hours,
                    json.dumps(interests),
                    work_style,
                )
                for name, role, year, skills, hours, interests, work_style in users
            ],
        )

        cursor = db.execute(
            """
            INSERT INTO projects
            (owner_id, title, audience, problem, category, target_date,
             required_skills, status, progress)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                "Campus Cart",
                "Students moving into or out of hostels",
                "Campus buying and selling is scattered across informal groups.",
                "Web / App",
                "2026-10-25",
                json.dumps(["Design", "Development", "Research", "Marketing"]),
                "in_progress",
                68,
            ),
        )

        project_id = cursor.lastrowid

        db.executemany(
            """
            INSERT INTO project_members (project_id, user_id, member_role)
            VALUES (?, ?, ?)
            """,
            [
                (project_id, 1, "owner"),
                (project_id, 5, "designer"),
                (project_id, 6, "developer"),
                (project_id, 7, "researcher"),
            ],
        )

        db.executemany(
            """
            INSERT INTO tasks (project_id, assignee_id, title, status, due_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (project_id, 5, "Review onboarding screens", "in_progress", "2026-10-13"),
                (project_id, 1, "Interview 3 potential users", "todo", "2026-10-13"),
                (project_id, 6, "Build product listing API", "review", "2026-10-15"),
                (project_id, 7, "Summarise interview notes", "done", "2026-10-12"),
            ],
        )

        db.executemany(
            """
            INSERT INTO checkins
            (project_id, user_id, mood, progress_note, blocker)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (project_id, 1, 5, "Project brief is ready.", ""),
                (project_id, 5, 4, "Onboarding flow is nearly complete.", ""),
                (project_id, 6, 5, "API is ready.", "Waiting for final design fields."),
                (project_id, 7, 4, "Interview guide is complete.", ""),
            ],
        )


def get_project(project_id):
    with get_db() as db:
        project = db.execute(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()

        if not project:
            return None

        project = dict(project)
        project["required_skills"] = json_list(project["required_skills"])

        project["members"] = [
            dict(row)
            for row in db.execute(
                """
                SELECT users.id, users.name, users.role, users.year,
                       project_members.member_role
                FROM project_members
                JOIN users ON users.id = project_members.user_id
                WHERE project_members.project_id = ?
                """,
                (project_id,),
            ).fetchall()
        ]

        project["tasks"] = [
            dict(row)
            for row in db.execute(
                """
                SELECT tasks.*, users.name AS assignee_name
                FROM tasks
                LEFT JOIN users ON users.id = tasks.assignee_id
                WHERE tasks.project_id = ?
                ORDER BY tasks.due_date
                """,
                (project_id,),
            ).fetchall()
        ]

        return project


def calculate_match_score(required_skills, person_skills, availability_hours):
    required = {skill.lower() for skill in required_skills}
    available = {skill.lower() for skill in person_skills}

    if not required:
        skill_score = 50
    else:
        skill_score = round((len(required.intersection(available)) / len(required)) * 75)

    availability_score = min(int(availability_hours), 10) * 2
    return min(skill_score + availability_score + 5, 99)


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "app": "CoBuild",
            "date": date.today().isoformat(),
        }
    )


@app.get("/api/dashboard")
def dashboard():
    with get_db() as db:
        active_projects = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM projects
            WHERE status IN ('planning', 'in_progress')
            """
        ).fetchone()["total"]

        task_data = db.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) AS completed
            FROM tasks
            """
        ).fetchone()

        team_health = db.execute(
            "SELECT ROUND(AVG(mood) * 20) AS score FROM checkins"
        ).fetchone()["score"] or 0

        projects = [
            dict(row)
            for row in db.execute(
                """
                SELECT id, title, status, progress, target_date
                FROM projects
                ORDER BY created_at DESC
                """
            ).fetchall()
        ]

    return jsonify(
        {
            "metrics": {
                "active_projects": active_projects,
                "tasks_completed": task_data["completed"] or 0,
                "tasks_total": task_data["total"] or 0,
                "team_health": team_health,
            },
            "projects": projects,
        }
    )


@app.route("/api/projects", methods=["GET", "POST"])
def projects():
    if request.method == "GET":
        with get_db() as db:
            project_rows = db.execute(
                "SELECT * FROM projects ORDER BY created_at DESC"
            ).fetchall()

        result = []
        for row in project_rows:
            project = dict(row)
            project["required_skills"] = json_list(project["required_skills"])
            result.append(project)

        return jsonify(result)

    data = get_data()
    title = str(data.get("title") or data.get("project_title") or "").strip()

    if not title:
        return jsonify({"error": "Project title is required."}), 400

    skills = data.get("required_skills") or data.get("skills") or []

    if isinstance(skills, str):
        skills = [skill.strip() for skill in skills.split(",") if skill.strip()]

    with get_db() as db:
        cursor = db.execute(
            """
            INSERT INTO projects
            (owner_id, title, audience, problem, category, target_date,
             required_skills, status, progress)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                title,
                str(data.get("audience") or "").strip(),
                str(data.get("problem") or "").strip(),
                str(data.get("category") or "").strip(),
                str(data.get("target_date") or "").strip() or None,
                json.dumps(skills),
                "planning",
                0,
            ),
        )

        project_id = cursor.lastrowid

        db.execute(
            """
            INSERT INTO project_members (project_id, user_id, member_role)
            VALUES (?, ?, ?)
            """,
            (project_id, 1, "owner"),
        )

    return jsonify(get_project(project_id)), 201


@app.get("/api/projects/<int:project_id>")
def project_detail(project_id):
    project = get_project(project_id)

    if not project:
        return jsonify({"error": "Project not found."}), 404

    return jsonify(project)


@app.post("/api/projects/<int:project_id>/tasks")
def create_task(project_id):
    data = get_data()
    title = str(data.get("title") or "").strip()
    status = str(data.get("status") or "todo")

    valid_statuses = {"todo", "in_progress", "review", "done"}

    if not title:
        return jsonify({"error": "Task title is required."}), 400

    if status not in valid_statuses:
        return jsonify({"error": "Invalid task status."}), 400

    with get_db() as db:
        project = db.execute(
            "SELECT id FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()

        if not project:
            return jsonify({"error": "Project not found."}), 404

        cursor = db.execute(
            """
            INSERT INTO tasks
            (project_id, assignee_id, title, status, due_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                project_id,
                data.get("assignee_id") or None,
                title,
                status,
                data.get("due_date") or None,
            ),
        )

        task = db.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

    return jsonify(to_dict(task)), 201


@app.patch("/api/tasks/<int:task_id>")
def update_task(task_id):
    data = get_data()
    status = data.get("status")

    if status not in {"todo", "in_progress", "review", "done"}:
        return jsonify({"error": "Invalid task status."}), 400

    with get_db() as db:
        db.execute(
            "UPDATE tasks SET status = ? WHERE id = ?",
            (status, task_id),
        )

        task = db.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

    if not task:
        return jsonify({"error": "Task not found."}), 404

    return jsonify(to_dict(task))


@app.get("/api/projects/<int:project_id>/matches")
def teammate_matches(project_id):
    with get_db() as db:
        project = db.execute(
            "SELECT required_skills FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()

        if not project:
            return jsonify({"error": "Project not found."}), 404

        members = db.execute(
            "SELECT user_id FROM project_members WHERE project_id = ?",
            (project_id,),
        ).fetchall()

        member_ids = [member["user_id"] for member in members]

        if member_ids:
            placeholders = ",".join("?" for _ in member_ids)
            users = db.execute(
                f"SELECT * FROM users WHERE id NOT IN ({placeholders})",
                member_ids,
            ).fetchall()
        else:
            users = db.execute("SELECT * FROM users").fetchall()

    required_skills = json_list(project["required_skills"])
    matches = []

    for row in users:
        user = dict(row)
        user["skills"] = json_list(user["skills"])
        user["interests"] = json_list(user["interests"])
        user["match_score"] = calculate_match_score(
            required_skills,
            user["skills"],
            user["availability_hours"],
        )
        matches.append(user)

    matches.sort(key=lambda user: user["match_score"], reverse=True)

    return jsonify(matches)


@app.post("/api/projects/<int:project_id>/checkins")
def create_checkin(project_id):
    data = get_data()

    try:
        mood = int(data.get("mood", 0))
    except (TypeError, ValueError):
        mood = 0

    if mood not in range(1, 6):
        return jsonify({"error": "Mood must be between 1 and 5."}), 400

    with get_db() as db:
        project = db.execute(
            "SELECT id FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()

        if not project:
            return jsonify({"error": "Project not found."}), 404

        cursor = db.execute(
            """
            INSERT INTO checkins
            (project_id, user_id, mood, progress_note, blocker)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                project_id,
                int(data.get("user_id") or 1),
                mood,
                str(data.get("progress_note") or "").strip(),
                str(data.get("blocker") or "").strip(),
            ),
        )

        checkin = db.execute(
            "SELECT * FROM checkins WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

    return jsonify(to_dict(checkin)), 201


if __name__ == "__main__":
    init_database()
    app.run(host="127.0.0.1", port=5000, debug=True)