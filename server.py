from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, unquote
from urllib import request as urlrequest
import hmac
import json
import os
import re
import secrets
import socket
import sqlite3
import threading
import time
import uuid

ROOT = Path(__file__).parent.resolve()
PUBLIC = ROOT
DB_PATH = ROOT / "fitness_gurukul.sqlite3"
DB_SCHEMA_READY = False
MAX_JSON_BYTES = 64 * 1024
RATE_LIMIT_WINDOW = 60
RATE_LIMITS = {
    "/api/chat": 20,
    "/api/submit": 30,
    "/api/leads": 30,
    "/api/calculations": 40,
    "/api/match": 40,
}
_rate_lock = threading.Lock()
_rate_buckets = {}

BLOCKED_STATIC_PREFIXES = (
    "/.env",
    "/.git",
    "/data/",
    "/node_modules/",
    "/__pycache__/",
)
BLOCKED_STATIC_SUFFIXES = (
    ".sqlite3",
    ".pyc",
    ".py",
    ".bak",
    ".env",
)
BLOCKED_STATIC_NAMES = {
    "/server.py",
    "/server.js",
    "/package.json",
    "/package-lock.json",
    "/.gitignore",
    "/.gitattributes",
    "/.env.example",
}

def load_env_file():
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

load_env_file()

CONTACT = {
    "phone": "08042781491",
    "whatsapp": "+917207113310",
    "email": "contact@fitnessgurukul.co.in",
    "address": "H.no.1-10/2, Lakshmi Nagar Colony, near Pochamma Temple, Manikonda, Hyderabad, 500089",
    "city": "Hyderabad, India",
}

SERVICES = [
    {"name": "Personal Training", "tag": "Gym, Sports, Strength, Cross Fit", "category": "training", "summary": "FREE demo session with our Personal Trainers. Book today and get a healthy discount!", "price": "Free demo", "accent": "blue", "points": ["Strength training", "Cross fit", "Sports conditioning", "Weight management"]},
    {"name": "Personalised Doorstep Service", "tag": "Home coaching", "category": "training", "summary": "Doorstep service for strength training, weight loss, body toning, stress relief. Helping people LIVE their best life!", "price": "Custom quote", "accent": "cyan", "points": ["Home training", "Weight loss", "Body toning", "Stress relief"]},
    {"name": "Yogic Wellness", "tag": "Yoga & flexibility", "category": "recovery", "summary": "Hatha yoga, corporate yoga, personal yoga training. Free demo session for your yogic transformation.", "price": "Free demo", "accent": "red", "points": ["Hatha yoga", "Flexibility", "Weight loss", "Corporate yoga"]},
    {"name": "Swimming", "tag": "Technique & confidence", "category": "training", "summary": "Water confidence, breathing rhythm, stroke correction, endurance. Safe, guided sessions.", "price": "Custom quote", "accent": "cyan", "points": ["Breathing rhythm", "Stroke basics", "Endurance", "Water confidence"]},
    {"name": "Weight Loss & Diet Plan", "tag": "Nutrition coaching", "category": "nutrition", "summary": "Diet consultation for a balanced and healthy life. One week free demo diet plan available.", "price": "Free demo", "accent": "red", "points": ["Diet consultation", "Custom meal plan", "Balanced nutrition", "Healthy lifestyle"]},
    {"name": "Corporate Marathon Events & Management", "tag": "Running events", "category": "event", "summary": "The Race Ends At Finish Line, But The Memories Last Forever! Promoting healthy & active lifestyles.", "price": "Custom quote", "accent": "blue", "points": ["Marathon management", "Participant comms", "Route support", "Race-day energy"]},
    {"name": "Corporate Cycling Events", "tag": "Cycling adventures", "category": "event", "summary": "Active, engaging & fun one day events or multi-day tours. Build camaraderie and promote fitness.", "price": "Custom quote", "accent": "cyan", "points": ["Team bonding", "Route planning", "Safety support", "Recovery"]},
    {"name": "Kids Programs", "tag": "Age 5-12", "category": "training", "summary": "Nature-inspired yoga, animal kingdom workouts, core and lower body strengthening for kids.", "price": "From INR 3,000", "accent": "blue", "points": ["Kids fitness", "Sports skills", "Coordination", "Confidence"]},
    {"name": "TTC Certification Courses", "tag": "Teacher training", "category": "training", "summary": "200 hours TTC in Yoga and Yogic Aahaar nutrition certification.", "price": "Custom quote", "accent": "cyan", "points": ["200 hour TTC", "Yoga certification", "Nutrition course", "Teaching practice"]},
    {"name": "Group Training", "tag": "Community", "category": "event", "summary": "Sports events, recreational activities, meet events, bootcamps. Group motivation.", "price": "Batch based", "accent": "blue", "points": ["Group sessions", "Sports events", "Bootcamps", "Community"]},
    {"name": "Corporate Services", "tag": "Office wellness", "category": "event", "summary": "Office yoga, fun activities, mini shows, games and sports for corporate teams.", "price": "Custom quote", "accent": "cyan", "points": ["Office yoga", "Team activities", "Games", "Event planning"]},
    {"name": "Fitness Gurukul Born Star Running Event", "tag": "Community run", "category": "event", "summary": "Community-focused running event. INR 900 - INR 1000. For beginners and regular runners.", "price": "INR 900", "accent": "red", "points": ["Community run", "Beginner friendly", "Race experience", "Finisher medal"]},
]

PLANS = [
    {"name": "Fitness Gurukul Core", "tag": "1-on-1 Coaching", "category": "core", "summary": "Dedicated fitness and nutrition coach with hyper-personalized workout plans, tailored Indian nutrition, and weekly video check-ins.", "price": "From INR 5,999/month", "sessions": "1 session/week", "points": ["Dedicated coach", "Custom meal plan", "Video check-ins", "In-person PT", "App check-in"]},
    {"name": "Fitness Gurukul Prime", "tag": "Advanced Coaching", "category": "prime", "summary": "Complete fitness and nutrition coaching with 3x/week in-person personal training, posture correction, nutrition planning, and mandatory app check-ins.", "price": "From INR 9,500/month", "sessions": "3 sessions/week", "points": ["1:1 coach + PT", "Nutrition plan", "Video check-ins", "Structural assessment", "App check-in"]},
    {"name": "Fitness Gurukul Signature", "tag": "Intensive Coaching", "category": "signature", "summary": "Intensive transformation plan to build strength, correct movement, and transform physique with 5x/week in-person training.", "price": "INR 15,999/month", "sessions": "5 sessions/week", "points": ["1:1 coach", "In-person PT", "Nutrition plan", "Structural assessment", "App check-in"]},
    {"name": "Fitness Gurukul Endurance", "tag": "Running Coaching", "category": "endurance", "summary": "Professional running coaching for beginners through advanced PR-seekers with periodized training, strength and conditioning, endurance nutrition, and race-day strategy.", "price": "INR 1,199/month", "sessions": "Virtual", "points": ["Dedicated running coach", "Periodized running program", "Runner-specific S&C", "Endurance nutrition", "Race strategy", "Daily chat support"]},
    {"name": "Fitness Gurukul Forge", "tag": "Hyrox / OCR Prep", "category": "forge", "summary": "Functional fitness racing prep for Hyrox and OCR athletes with compounded S&C, engine building, grip strength, explosive power, and compromised running stamina.", "price": "INR 999/month", "sessions": "Virtual", "points": ["Dedicated S&C coach", "Compounded S&C workouts", "Functional engine building", "Agility and grip strength", "Explosive power drills"]},
    {"name": "Virtual 1:1 Elite Transformation", "tag": "Weight Loss & Muscle Gain", "category": "elite", "summary": "Remote 1:1 fitness and nutrition coaching for weight loss, lean muscle gain, or lifestyle overhaul with hyper-personalized plans.", "price": "From INR 1,999/month", "sessions": "Virtual", "points": ["Dedicated coach", "Custom workout plans", "Indian nutrition plan", "Video check-ins", "Daily chat support", "Progressive overload"]},
]

COACHES = [
    {"name": "Aditya Gururani", "role": "Yoga Instructor & Breathing Specialist", "slug": "aditya-gururani", "category": "yoga", "bio": "A certified yoga instructor specializing in breathwork, stress management, and functional mobility. Focused on helping individuals improve posture, flexibility, lung capacity, and mental clarity through structured yoga and scientifically grounded breathing techniques.", "focus": ["Breathwork", "Stress management", "Functional mobility"]},
    {"name": "B Yashwanth", "role": "Basketball Coach", "slug": "b-yashwanth", "category": "sports", "bio": "Basketball Coach", "focus": ["Basketball", "Sports coaching", "Conditioning"]},
    {"name": "Kritika Chauhan", "role": "Yoga Instructor", "slug": "kritika-chauhan", "category": "yoga", "bio": "Yoga Instructor", "focus": ["Yoga", "Flexibility", "Mobility"]},
    {"name": "Shivajeet Kanaujiya", "role": "Fitness Trainer", "slug": "shivajeet-kanaujiya", "category": "fitness", "bio": "Fitness Trainer", "focus": ["Fitness training", "Strength", "Daily exercise"]},
    {"name": "Anand Yadav", "role": "Children’s Athletics Coach", "slug": "anand-yadav", "category": "kids", "bio": "Children’s Athletics Coach", "focus": ["Children's athletics", "Kids fitness", "Sports"]},
    {"name": "Chandan Mondal", "role": "Bodybuilding & Fitness Coach", "slug": "chandan-mondal", "category": "fitness", "bio": "Bodybuilding & Fitness Coach", "focus": ["Bodybuilding", "Fitness", "Strength"]},
    {"name": "Aditya", "role": "Yoga Instructor & Fitness Coach", "slug": "aditya", "category": "yoga", "bio": "Yoga Instructor & Fitness Coach", "focus": ["Yoga", "Fitness", "Body toning"]},
    {"name": "Nitu Arya", "role": "Yoga Instructor", "slug": "nitu-arya", "category": "yoga", "bio": "Yoga Instructor", "focus": ["Yoga", "Flexibility", "General fitness"]},
    {"name": "Deepesh Kumar", "role": "Fitness Trainer", "slug": "deepesh-kumar", "category": "fitness", "bio": "Fitness Trainer", "focus": ["Fitness training", "Strength", "Weight loss"]},
    {"name": "S Jeetender", "role": "Fitness Trainer", "slug": "s-jeetender", "category": "fitness", "bio": "Fitness Trainer", "focus": ["Fitness training", "Daily exercise", "Strength"]},
    {"name": "Rahul Dawar", "role": "Fitness Trainer", "slug": "rahul-dawar", "category": "fitness", "bio": "Fitness Trainer", "focus": ["Fitness training", "Strength", "Health routine"]},
    {"name": "Ravi Pal", "role": "Fitness Trainer & Injury Rehabilitation Coach", "slug": "ravi-pal", "category": "rehab", "bio": "Fitness Trainer & Injury Rehabilitation Coach", "focus": ["Fitness training", "Injury rehabilitation", "Recovery"]},
    {"name": "Subedhar Yadav", "role": "Fitness Trainer (Special Children)", "slug": "subedhar-yadav", "category": "special", "bio": "Fitness Trainer (Special Children)", "focus": ["Special children", "Fitness", "Mobility"]},
    {"name": "Sanjeev", "role": "Fitness Trainer", "slug": "sanjeev", "category": "fitness", "bio": "Fitness Trainer", "focus": ["Fitness training", "Strength", "Daily exercise"]},
    {"name": "Nandlal", "role": "Fitness Trainer", "slug": "nandlal", "category": "fitness", "bio": "Fitness Trainer", "focus": ["Fitness training", "Strength", "Weight loss"]},
    {"name": "Vinay Ojha", "role": "Fitness Trainer", "slug": "vinay-ojha", "category": "fitness", "bio": "Fitness Trainer", "focus": ["Fitness training", "Strength", "General fitness"]},
    {"name": "Ankit Singh Chauhan", "role": "Fitness & Calisthenics Trainer", "slug": "ankit-singh-chauhan", "category": "fitness", "bio": "Fitness & Calisthenics Trainer", "focus": ["Fitness", "Calisthenics", "Strength"]},
    {"name": "Suresh Yadav", "role": "Fitness Trainer (Special Children)", "slug": "suresh-yadav", "category": "special", "bio": "Fitness Trainer (Special Children)", "focus": ["Special children", "Fitness", "Mobility"]},
    {"name": "Parul Danu", "role": "Yoga Instructor", "slug": "parul-danu", "category": "yoga", "bio": "Yoga Instructor", "focus": ["Yoga", "Flexibility", "Stress relief"]},
    {"name": "Raju", "role": "Fitness Trainer", "slug": "raju", "category": "fitness", "bio": "Fitness Trainer", "focus": ["Fitness training", "Strength", "Health routine"]},
    {"name": "Vishal Choudhary", "role": "Fitness Trainer", "slug": "vishal-choudhary", "category": "fitness", "bio": "Fitness Trainer", "focus": ["Fitness training", "Strength", "Personal training"]},
]

TESTIMONIALS = [
    {"name": "Priyanka", "quote": "Rohit, ur training are excellent. I can feel the difference every week, with my stamina and strength improving.", "result": "Strength & stamina"},
    {"name": "Lakshman, Sridhar & Rahul", "quote": "Thank you Shiv Narayan for your coaching, the sand exercises really pushed us to our limits.", "result": "Running prep"},
    {"name": "Undisclosed", "quote": "Vishal sir has helped me a lot in my fitness journey, its been a while that I have been training.", "result": "Personal training"},
]

UPDATES = [
    {"title": "Online Personal Trainer in Hyderabad – Flexible Coaching for Modern Lifestyles", "date": "2026-02-17", "summary": "Flexible coaching with check-ins, workouts, and nutrition support for modern schedules."},
    {"title": "Certified Personal Trainer in Hyderabad – Qualified Guidance You Can Trust", "date": "2026-02-14", "summary": "Qualified programming helps clients train safely, recover better, and build repeatable habits."},
    {"title": "Best Dietician for Weight Loss in Hyderabad – Practical Nutrition for Real Change", "date": "2026-02-14", "summary": "Food choices, portions, and routine design for sustainable weight management."},
]

SERVICE_AREAS = ["Manikonda", "Lakshmi Nagar Colony", "Puppalaguda", "Shaikpet", "Gachibowli", "Kokapet", "Narsingi", "Financial District", "HITEC City", "Madhapur", "Jubilee Hills"]

CHAT_SUGGESTIONS = [
    "Which plan is best for weight loss?",
    "Compare Core, Prime and Signature",
    "Do you have running or Hyrox plans?",
    "Which coach is best for yoga?",
]

COACH_MEDIA = {
    "aditya-gururani": {"highlight": "Breathwork Expert", "color": "cyan", "image": "assets/coaches/aditya-gururani.jpg"},
    "b-yashwanth": {"highlight": "Sports Specialist", "color": "blue", "image": "assets/coaches/b-yashwanth.jpg"},
    "kritika-chauhan": {"highlight": "Flexibility Coach", "color": "cyan", "image": "https://web.s-cdn.boostkit.dev/webaction-files/67dd161916df35677e31c42c_myteam/img_0302-69538f34664ae75da3c69fce.jpg"},
    "shivajeet-kanaujiya": {"highlight": "Strength Builder", "color": "red", "image": "https://web.s-cdn.boostkit.dev/webaction-files/67dd161916df35677e31c42c_myteam/img_0300-69538ef2474cc000b54586c5.jpg"},
    "anand-yadav": {"highlight": "Kids Fitness Expert", "color": "blue", "image": "https://web.s-cdn.boostkit.dev/webaction-files/67dd161916df35677e31c42c_myteam/img_0297-69538d52664ae75da3c69fc1.jpg"},
    "chandan-mondal": {"highlight": "Bodybuilding Coach", "color": "red", "image": "assets/coaches/chandan-mondal.jpg"},
    "aditya": {"highlight": "Mind-Body Coach", "color": "cyan", "image": "https://web.s-cdn.boostkit.dev/webaction-files/67dd161916df35677e31c42c_myteam/img_0298-69538dd1474cc000b54586be.jpg"},
    "nitu-arya": {"highlight": "Holistic Yoga", "color": "cyan", "image": "https://web.s-cdn.boostkit.dev/webaction-files/67dd161916df35677e31c42c_myteam/img_0295-69538d35474cc000b54586b7.jpg"},
    "deepesh-kumar": {"highlight": "Weight Loss Specialist", "color": "red", "image": "assets/coaches/deepesh-kumar.jpg"},
    "s-jeetender": {"highlight": "Daily Fitness Pro", "color": "red", "image": "assets/coaches/s-jeetender.jpg"},
    "rahul-dawar": {"highlight": "Health & Strength", "color": "red", "image": "https://web.s-cdn.boostkit.dev/webaction-files/67dd161916df35677e31c42c_myteam/img_0291-69538ccf8c7b7b2c6178b6e1.jpg"},
    "ravi-pal": {"highlight": "Injury Recovery", "color": "blue", "image": "https://web.s-cdn.boostkit.dev/webaction-files/67dd161916df35677e31c42c_myteam/img_0289-69538c800222ba9c3d831802.jpg"},
    "subedhar-yadav": {"highlight": "Special Needs Coach", "color": "blue", "image": "assets/coaches/subedhar-yadav.jpg"},
    "sanjeev": {"highlight": "Strength Trainer", "color": "red", "image": "https://web.s-cdn.boostkit.dev/webaction-files/67dd161916df35677e31c42c_myteam/274dba00-8541-4bfc-8666-e0b5433b3781-69538a190222ba9c3d8317f4.jpg"},
    "nandlal": {"highlight": "Transformation Coach", "color": "red", "image": "https://web.s-cdn.boostkit.dev/webaction-files/67dd161916df35677e31c42c_myteam/04ea7dfe-a988-4a17-97cb-8dc44240cb59-695389c4474cc000b54586a8.jpg"},
    "vinay-ojha": {"highlight": "All-Round Fitness", "color": "red", "image": "assets/coaches/vinay-ojha.jpg"},
    "ankit-singh-chauhan": {"highlight": "Calisthenics Expert", "color": "red", "image": "assets/coaches/ankit-singh-chauhan.jpg"},
    "suresh-yadav": {"highlight": "Special Needs Expert", "color": "blue", "image": "assets/coaches/suresh-yadav.jpg"},
    "parul-danu": {"highlight": "Yoga & Wellness", "color": "cyan", "image": "https://web.s-cdn.boostkit.dev/webaction-files/67dd161916df35677e31c42c_myteam/parul-695209395c5bdcd270817773.jpeg"},
    "raju": {"highlight": "Fitness Guide", "color": "red", "image": "assets/coaches/raju.jpg"},
    "vishal-choudhary": {"highlight": "Personal Training Pro", "color": "red", "image": "https://web.s-cdn.boostkit.dev/webaction-files/67dd161916df35677e31c42c_myteam/vishal-69520b6a5c5bdcd270817783.jpeg"},
}

GOAL_MATCHES = {
    "weight-loss": {
        "goal": "weight-loss",
        "title": "Fat Loss & Body Recomposition",
        "summary": "Blend strength work with Indian nutrition coaching so fat loss stays sustainable.",
        "plan": "Fitness Gurukul Prime",
        "planCategory": "prime",
        "coachCategories": ["fitness", "yoga"],
        "cta": "book-consultation.html",
    },
    "strength": {
        "goal": "strength",
        "title": "Strength & Muscle Building",
        "summary": "Progressive personal training with form coaching and weekly accountability.",
        "plan": "Fitness Gurukul Signature",
        "planCategory": "signature",
        "coachCategories": ["fitness"],
        "cta": "book-consultation.html",
    },
    "yoga": {
        "goal": "yoga",
        "title": "Yoga, Breathwork & Stress Relief",
        "summary": "Mobility, breath, and nervous-system reset with certified yoga instructors.",
        "plan": "Yogic Wellness",
        "planCategory": "recovery",
        "coachCategories": ["yoga"],
        "cta": "coaches.html",
    },
    "running": {
        "goal": "running",
        "title": "Running & Endurance",
        "summary": "Periodized run plans plus strength support for race day performance.",
        "plan": "Fitness Gurukul Endurance",
        "planCategory": "endurance",
        "coachCategories": ["fitness", "sports"],
        "cta": "services.html",
    },
    "kids": {
        "goal": "kids",
        "title": "Kids Athletics & Confidence",
        "summary": "Age-appropriate movement, sports skills, and fun fitness for children.",
        "plan": "Kids Programs",
        "planCategory": "training",
        "coachCategories": ["kids", "special"],
        "cta": "coaches.html",
    },
    "rehab": {
        "goal": "rehab",
        "title": "Injury Rehab & Return to Train",
        "summary": "Guided recovery programming to rebuild strength safely after setbacks.",
        "plan": "Personal Training",
        "planCategory": "training",
        "coachCategories": ["rehab", "fitness"],
        "cta": "book-consultation.html",
    },
}

def enriched_coaches():
    out = []
    for coach in COACHES:
        row = dict(coach)
        media = COACH_MEDIA.get(coach.get("slug"), {})
        row["highlight"] = media.get("highlight") or row.get("highlight") or "Coach"
        row["color"] = media.get("color") or row.get("color") or "cyan"
        row["image"] = media.get("image") or row.get("image") or ""
        out.append(row)
    return out

def live_payload():
    base_clients = 1000
    base_events = 50
    coaches = len(COACHES)
    try:
        with get_connection() as conn:
            leads = conn.execute("SELECT COUNT(*) AS c FROM submissions").fetchone()["c"]
            calcs = conn.execute("SELECT COUNT(*) AS c FROM calculator_results").fetchone()["c"]
            chats = conn.execute("SELECT COUNT(*) AS c FROM chat_messages WHERE role = 'user'").fetchone()["c"]
            today = conn.execute(
                "SELECT COUNT(*) AS c FROM submissions WHERE created_at >= ?",
                (int(time.time()) - 24 * 60 * 60,),
            ).fetchone()["c"]
    except Exception:
        leads = calcs = chats = today = 0
    pulse = [
        "A Hyderabad member just booked a free consultation",
        "Coach match completed for yoga & mobility",
        "Macro calculator used for Indian meal planning",
        "Doorstep training inquiry from Gachibowli",
        "Running plan comparison opened on Services",
    ]
    # Rotate pulse by minute so the site feels alive without fake realtime sockets.
    idx = int(time.time() // 45) % len(pulse)
    return {
        "ok": True,
        "clientsTransformed": base_clients + max(leads, 0),
        "years": 13,
        "events": base_events,
        "coaches": coaches,
        "specialties": 7,
        "inquiriesToday": today,
        "toolUses": calcs,
        "chatSessions": chats,
        "activeNow": 3 + ((int(time.time()) // 30) % 9),
        "pulse": pulse[idx],
        "updatedAt": int(time.time()),
    }

def match_goal(payload):
    goal = clip(str(payload.get("goal", "")).lower().replace(" ", "-"), 40)
    experience = clip(str(payload.get("experience", "beginner")).lower(), 40)
    preference = clip(str(payload.get("preference", "in-person")).lower(), 40)
    match = GOAL_MATCHES.get(goal) or GOAL_MATCHES["weight-loss"]
    coaches = [
        c for c in enriched_coaches()
        if c.get("category") in match["coachCategories"]
    ][:3]
    plan = next((p for p in PLANS if p.get("category") == match.get("planCategory")), None)
    if not plan:
        plan = next((s for s in SERVICES if s.get("name") == match.get("plan")), SERVICES[0])
    tip = {
        "beginner": "Start with a free consultation and a gentle 2-week ramp-up.",
        "intermediate": "Expect progressive overload with weekly check-ins.",
        "advanced": "We will bias intensity, recovery, and race or physique peaking.",
    }.get(experience, "Start with a free consultation.")
    mode = "Doorstep or studio sessions available in Hyderabad." if preference in {"in-person", "doorstep", "home"} else "Virtual coaching with app check-ins works great for your schedule."
    return {
        "ok": True,
        "match": match,
        "plan": plan,
        "coaches": coaches,
        "tip": tip,
        "mode": mode,
        "score": 92 if goal in GOAL_MATCHES else 78,
    }

def content_payload():
    coaches = enriched_coaches()
    return {
        "heroHeadline": "Train Smarter. Live Stronger.",
        "heroSubhead": "1:1 personal training in Hyderabad — Indian nutrition and doorstep coaching built around your body and schedule.",
        "services": SERVICES,
        "plans": PLANS,
        "coaches": coaches,
        "testimonials": TESTIMONIALS,
        "updates": UPDATES,
        "serviceAreas": SERVICE_AREAS,
        "contact": CONTACT,
        "goals": list(GOAL_MATCHES.values()),
        "stats": {
            "clients": 1000,
            "years": 13,
            "events": 50,
            "coaches": len(coaches),
            "specialties": len({c.get("category") for c in coaches}),
        },
        "live": live_payload(),
    }

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    global DB_SCHEMA_READY
    with get_connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS leads (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, phone TEXT NOT NULL, goal TEXT NOT NULL, program TEXT NOT NULL, message TEXT, created_at INTEGER NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS newsletter (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL UNIQUE, created_at INTEGER NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS checkins (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, weight REAL NOT NULL, stamina INTEGER NOT NULL, mood TEXT NOT NULL, created_at INTEGER NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS ai_scans (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, focus TEXT NOT NULL, summary TEXT NOT NULL, coach_route TEXT NOT NULL, camera_used INTEGER NOT NULL DEFAULT 0, created_at INTEGER NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS calculator_results (id INTEGER PRIMARY KEY AUTOINCREMENT, calculator TEXT NOT NULL, title TEXT NOT NULL, result TEXT NOT NULL, unit TEXT, rating TEXT, created_at INTEGER NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS chat_messages (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, source TEXT NOT NULL DEFAULT 'local', created_at INTEGER NOT NULL)")
        conn.execute(
            """CREATE TABLE IF NOT EXISTS submissions (
                id TEXT PRIMARY KEY,
                form_type TEXT NOT NULL DEFAULT 'consultation',
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                program TEXT,
                goal TEXT,
                message TEXT,
                coach TEXT,
                company TEXT,
                event_type TEXT,
                attendees TEXT,
                preferred_date TEXT,
                budget TEXT,
                location TEXT,
                status TEXT NOT NULL DEFAULT 'new',
                created_at INTEGER NOT NULL
            )"""
        )
        # Backward-compatible migration for older DBs.
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(submissions)").fetchall()}
        if "status" not in cols:
            conn.execute("ALTER TABLE submissions ADD COLUMN status TEXT NOT NULL DEFAULT 'new'")
        conn.commit()
    DB_SCHEMA_READY = True


LOCAL_DEFAULT_PASSWORD = "fitnessgurukul"
ADMIN_CRED_MODE = "unconfigured"  # configured | local-default | generated

def admin_token():
    """Primary staff password. ADMIN_PASSWORD is accepted as a friendly alias."""
    return (
        os.environ.get("ADMIN_TOKEN", "").strip()
        or os.environ.get("ADMIN_PASSWORD", "").strip()
    )

def ensure_admin_credentials(host="127.0.0.1"):
    """
    Make local backend access easy: on localhost, default to a memorable
    password when none is configured. On LAN/public binds, generate a strong token.
    Returns one of: "configured", "local-default", "generated".
    """
    global ADMIN_CRED_MODE
    if admin_token():
        ADMIN_CRED_MODE = "configured"
        return ADMIN_CRED_MODE
    if host in {"127.0.0.1", "localhost", "::1"}:
        os.environ["ADMIN_TOKEN"] = LOCAL_DEFAULT_PASSWORD
        ADMIN_CRED_MODE = "local-default"
        return ADMIN_CRED_MODE
    generated = secrets.token_urlsafe(24)
    os.environ["ADMIN_TOKEN"] = generated
    ADMIN_CRED_MODE = "generated"
    return ADMIN_CRED_MODE


def clip(value, max_len=500):
    text = str(value or "").strip()
    return text[:max_len]


def client_ip(handler):
    return handler.client_address[0] if handler.client_address else "unknown"


def check_rate_limit(handler, path):
    limit = RATE_LIMITS.get(path)
    if not limit:
        return True
    key = (client_ip(handler), path)
    now = time.time()
    with _rate_lock:
        bucket = [ts for ts in _rate_buckets.get(key, []) if now - ts < RATE_LIMIT_WINDOW]
        if len(bucket) >= limit:
            _rate_buckets[key] = bucket
            return False
        bucket.append(now)
        _rate_buckets[key] = bucket
    return True


def is_blocked_static(path):
    decoded = unquote(path).lower()
    if decoded in BLOCKED_STATIC_NAMES or decoded.rstrip("/") in BLOCKED_STATIC_NAMES:
        return True
    if any(decoded.startswith(prefix) for prefix in BLOCKED_STATIC_PREFIXES):
        return True
    if any(decoded.endswith(suffix) for suffix in BLOCKED_STATIC_SUFFIXES):
        return True
    return False


def require_admin(handler):
    token = admin_token()
    if not token:
        handler.send_json({"error": "Admin access is disabled. Set ADMIN_TOKEN in .env."}, 503)
        return False
    provided = (
        handler.headers.get("X-Admin-Token")
        or handler.headers.get("X-Admin-Password")
        or ""
    ).strip()
    auth = (handler.headers.get("Authorization") or "").strip()
    if not provided and auth.lower().startswith("bearer "):
        provided = auth[7:].strip()
    if not provided or not hmac.compare_digest(provided, token):
        handler.send_json({"error": "Unauthorized. Use the staff password from .env (ADMIN_TOKEN)."}, 401)
        return False
    return True


def row_to_submission(row):
    item = dict(row)
    item["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(item.get("created_at") or 0))
    item["status"] = item.get("status") or "new"
    return item


def save_submission(payload):
    form_type = clip(payload.get("form_type") or "consultation", 64)
    name = clip(payload.get("name") or payload.get("contact_name"), 120)
    phone = clip(payload.get("phone"), 40)
    email = clip(payload.get("email"), 160)
    program = clip(payload.get("program"), 120)
    goal = clip(payload.get("goal"), 200)
    message = clip(payload.get("message"), 2000)
    coach = clip(payload.get("coach"), 120)
    company = clip(payload.get("company"), 160)
    event_type = clip(payload.get("event_type"), 120)
    attendees = clip(payload.get("attendees"), 80)
    preferred_date = clip(payload.get("preferred_date"), 80)
    budget = clip(payload.get("budget"), 80)
    location = clip(payload.get("location"), 160)

    if form_type == "corporate_event":
        missing = [field for field, value in [
            ("company", company), ("contact_name", name), ("email", email),
            ("phone", phone), ("event_type", event_type), ("attendees", attendees),
        ] if not value]
        if missing:
            return None, missing
    else:
        missing = [field for field, value in [
            ("name", name), ("phone", phone), ("program", program), ("goal", goal),
        ] if not value]
        if missing:
            return None, missing

    submission_id = uuid.uuid4().hex
    created_at = int(time.time())
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO submissions (
                id, form_type, name, phone, email, program, goal, message, coach,
                company, event_type, attendees, preferred_date, budget, location, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                submission_id, form_type, name, phone, email, program, goal, message, coach,
                company, event_type, attendees, preferred_date, budget, location, "new", created_at,
            ),
        )
        # Keep legacy leads table in sync for the owner-data viewer.
        if form_type != "corporate_event":
            conn.execute(
                "INSERT INTO leads (name, phone, goal, program, message, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (name, phone, goal or event_type or "consultation", program or event_type or "general", message, created_at),
            )
        else:
            conn.execute(
                "INSERT INTO leads (name, phone, goal, program, message, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (name, phone, event_type or "corporate_event", company or "corporate", message or f"{attendees} attendees", created_at),
            )
        conn.commit()
    return submission_id, None

def build_chat_system_prompt():
    plan_lines = []
    for plan in PLANS:
        points = ", ".join(plan.get("points", [])[:5])
        plan_lines.append(f"- {plan['name']} ({plan['price']}, {plan['sessions']}): {plan['summary']} Highlights: {points}.")
    service_lines = []
    for service in SERVICES:
        points = ", ".join(service.get("points", [])[:4])
        service_lines.append(f"- {service['name']} ({service['price']}): {service['summary']} Highlights: {points}.")
    coach_lines = []
    for coach in COACHES[:12]:
        focus = ", ".join(coach.get("focus", [])[:3])
        coach_lines.append(f"- {coach['name']}, {coach['role']}. Focus: {focus}.")
    return (
        "You are the Fitness Gurukul AI assistant for a premium fitness studio in Hyderabad, India. "
        "Behave like a helpful fitness consultant, not a scripted FAQ bot. Ask one useful follow-up question when the user's goal is vague. "
        "Recommend relevant plans, coaches, or next steps from the website context. Never invent prices, coaches, dates, medical claims, or contact details. "
        "For medical, injury, pregnancy, or disease-related questions, give general fitness guidance only and recommend speaking with a qualified professional. "
        "Answer clearly in 2-5 short sentences unless the user asks for detail. If unsure, invite the user to book a free consultation.\n\n"
        f"Contact phone: {CONTACT['phone']}. WhatsApp: {CONTACT['whatsapp']}. Email: {CONTACT['email']}. "
        f"Address: {CONTACT['address']}. Service areas: {', '.join(SERVICE_AREAS[:8])}.\n\n"
        "Current coaching plans from the website:\n" + "\n".join(plan_lines) + "\n\n"
        "Services:\n" + "\n".join(service_lines) + "\n\n"
        "Sample coaches:\n" + "\n".join(coach_lines)
    )

def normalize_chat_text(value):
    return re.sub(r"\s+", " ", str(value or "").strip())

def chat_contains_any(text, words):
    return any(word in text for word in words)

def find_matching_coaches(text):
    matches = []
    for coach in COACHES:
        haystack = " ".join([
            coach.get("name", ""),
            coach.get("role", ""),
            coach.get("category", ""),
            " ".join(coach.get("focus", [])),
            coach.get("bio", ""),
        ]).lower()
        if any(token in haystack for token in text.split() if len(token) > 3):
            matches.append(coach)
    if matches:
        return matches[:3]
    if chat_contains_any(text, ["yoga", "breath", "flexibility", "stress"]):
        return [coach for coach in COACHES if coach.get("category") == "yoga"][:3]
    if chat_contains_any(text, ["kid", "child", "children"]):
        return [coach for coach in COACHES if coach.get("category") in {"kids", "special"}][:3]
    if chat_contains_any(text, ["injury", "rehab", "recovery"]):
        return [coach for coach in COACHES if coach.get("category") == "rehab"][:3]
    if chat_contains_any(text, ["sport", "basketball", "running", "calisthenics"]):
        return [coach for coach in COACHES if coach.get("category") in {"sports", "fitness", "hybrid"}][:3]
    return []

def find_matching_services(text):
    matches = []
    for service in SERVICES:
        haystack = " ".join([
            service.get("name", ""),
            service.get("tag", ""),
            service.get("category", ""),
            service.get("summary", ""),
            " ".join(service.get("points", [])),
        ]).lower()
        if any(token in haystack for token in text.split() if len(token) > 3):
            matches.append(service)
    if matches:
        return matches[:3]
    keyword_map = [
        (["yoga", "breath", "flexibility", "wellness"], ["Yogic Wellness"]),
        (["doorstep", "home", "at home"], ["Personalised Doorstep Service"]),
        (["weight", "fat", "diet", "nutrition"], ["Weight Loss & Diet Plan", "Personal Training"]),
        (["swim", "pool", "water"], ["Swimming"]),
        (["kid", "child", "children"], ["Kids Programs"]),
        (["corporate", "office", "team"], ["Corporate Services", "Corporate Marathon Events & Management"]),
        (["run", "marathon", "race"], ["Corporate Marathon Events & Management", "Fitness Gurukul Born Star Running Event"]),
        (["cycl", "bike", "ride"], ["Corporate Cycling Events"]),
        (["group", "bootcamp", "community"], ["Group Training", "Fitness Gurukul Born Star Running Event"]),
    ]
    for keywords, names in keyword_map:
        if chat_contains_any(text, keywords):
            return [service for service in SERVICES if service["name"] in names][:3]
    return SERVICES[:3]

def plan_score(plan, text):
    haystack = " ".join([
        plan.get("name", ""),
        plan.get("tag", ""),
        plan.get("category", ""),
        plan.get("summary", ""),
        plan.get("price", ""),
        plan.get("sessions", ""),
        " ".join(plan.get("points", [])),
    ]).lower()
    tokens = [token for token in re.split(r"[^a-z0-9]+", text.lower()) if len(token) > 2]
    score = sum(1 for token in tokens if token in haystack)
    if chat_contains_any(text, ["weight", "fat", "loss", "slim", "transform", "muscle", "body", "lifestyle"]) and plan.get("category") in {"elite", "core", "prime", "signature"}:
        score += 3
    if chat_contains_any(text, ["home", "doorstep", "personal", "offline", "trainer", "pt", "in person", "session"]) and plan.get("category") in {"core", "prime", "signature"}:
        score += 3
    if chat_contains_any(text, ["run", "running", "marathon", "race", "endurance", "5k", "10k"]) and plan.get("category") == "endurance":
        score += 6
    if chat_contains_any(text, ["hyrox", "ocr", "obstacle", "functional", "forge"]) and plan.get("category") == "forge":
        score += 6
    if chat_contains_any(text, ["budget", "cheap", "low", "affordable", "online", "virtual"]) and plan.get("category") in {"elite", "forge", "endurance"}:
        score += 3
    if chat_contains_any(text, ["daily", "intense", "fast", "maximum", "premium", "five", "5"]) and plan.get("category") == "signature":
        score += 5
    if chat_contains_any(text, ["three", "3", "advanced", "complete"]) and plan.get("category") == "prime":
        score += 4
    if chat_contains_any(text, ["one", "1", "weekly", "starter", "beginner", "basic", "core"]) and plan.get("category") == "core":
        score += 4
    return score

def find_matching_plans(text):
    ranked = sorted(
        ((plan_score(plan, text), plan) for plan in PLANS),
        key=lambda item: item[0],
        reverse=True,
    )
    matches = [plan for score, plan in ranked if score > 0]
    return (matches or PLANS)[:3]

def format_plan_reply(plans, intro=None):
    lines = [intro or "Here are the best-fit Fitness Gurukul plans:"]
    for plan in plans[:3]:
        points = ", ".join(plan.get("points", [])[:3])
        lines.append(f"- {plan['name']} - {plan['price']}, {plan['sessions']}. {plan['summary']} Key inclusions: {points}.")
    lines.append("For the exact fit, share your goal, schedule, location, and whether you prefer virtual or in-person coaching.")
    return " ".join(lines)

def compare_core_prime_signature_reply():
    core = next(plan for plan in PLANS if plan["category"] == "core")
    prime = next(plan for plan in PLANS if plan["category"] == "prime")
    signature = next(plan for plan in PLANS if plan["category"] == "signature")
    return (
        f"{core['name']} is the starter personalized plan: {core['price']} with {core['sessions']}. "
        f"{prime['name']} is more hands-on: {prime['price']} with {prime['sessions']} and fuller fitness plus nutrition support. "
        f"{signature['name']} is the intensive option: {signature['price']} with {signature['sessions']} for faster transformation, in-person PT, nutrition, posture assessment, and app check-ins."
    )

def format_service_reply(services):
    lines = ["Here are the best-fit options I found:"]
    for service in services:
        lines.append(f"• {service['name']} — {service['price']}. {service['summary']}")
    lines.append("Want a free consultation? Visit the Contact page or WhatsApp us at +91 72071 13310.")
    return " ".join(lines)

def format_coach_reply(coaches):
    if not coaches:
        return (
            "We have 24 expert coaches across yoga, strength, sports, kids fitness, rehab, and special-needs training. "
            "Browse coaches.html or tell me your goal and I will narrow it down."
        )
    lines = ["These coaches look like a strong match:"]
    for coach in coaches:
        focus = ", ".join(coach.get("focus", [])[:3])
        lines.append(f"• {coach['name']} — {coach['role']}. Focus: {focus}.")
    lines.append("You can view full profiles on the Coaches page or book a call to get matched faster.")
    return " ".join(lines)

def generate_local_chat_reply(message, history=None):
    text = normalize_chat_text(message).lower()
    if not text:
        return "Ask me about training plans, coaches, pricing, events, or how to book a free consultation."

    greetings = ["hi", "hello", "hey", "good morning", "good evening", "namaste"]
    if text in greetings or any(text.startswith(g + " ") or text == g for g in greetings):
        return (
            "Hi! I am the Fitness Gurukul assistant. I can help with programs, coach matching, "
            "pricing, events, and booking a free consultation in Hyderabad."
        )

    if chat_contains_any(text, ["thank", "thanks", "thank you"]):
        return "Happy to help. If you want to take the next step, book a free consultation on the Contact page."

    if chat_contains_any(text, ["contact", "phone", "call", "whatsapp", "email", "address", "location", "where"]):
        return (
            f"You can reach us at {CONTACT['phone']} or WhatsApp {CONTACT['whatsapp']}. "
            f"Email: {CONTACT['email']}. Studio address: {CONTACT['address']}."
        )

    if chat_contains_any(text, ["compare", "difference", "core", "prime", "signature"]):
        return compare_core_prime_signature_reply()

    if chat_contains_any(text, ["price", "cost", "fee", "how much", "pricing", "plan", "package", "weight", "muscle", "hyrox", "running", "virtual", "online"]):
        return format_plan_reply(find_matching_plans(text))

    if chat_contains_any(text, ["doorstep", "home", "in person", "personal trainer"]):
        return format_plan_reply(
            find_matching_plans("in person personal training core prime signature"),
            "Yes. For in-person or doorstep-style coaching, these are the closest plan fits:",
        )

    if chat_contains_any(text, ["coach", "trainer", "instructor", "who should", "recommend"]):
        return format_coach_reply(find_matching_coaches(text))

    if chat_contains_any(text, ["event", "marathon", "cycling", "ride", "camp", "born star", "obstacle"]):
        events = [service for service in SERVICES if service.get("category") == "event"]
        return format_service_reply(events[:4] if events else SERVICES[:3])

    if chat_contains_any(text, ["demo", "trial", "consultation", "book", "join", "start", "signup", "sign up"]):
        return (
            "Great next step: book a free consultation on contact.html. Share your goal, schedule, and area "
            "and we will match you with the right coach or program."
        )

    if chat_contains_any(text, ["program", "offer", "training", "personal", "fitness", "strength", "transformation"]):
        return format_plan_reply(find_matching_plans(text))

    if chat_contains_any(text, ["service", "doorstep", "yoga", "swim", "diet", "kids", "corporate"]):
        return format_service_reply(find_matching_services(text))

    if chat_contains_any(text, ["area", "manikonda", "gachibowli", "hyderabad", "near", "local"]):
        return (
            "We serve Hyderabad including "
            + ", ".join(SERVICE_AREAS[:6])
            + ". Doorstep coaching availability depends on your exact location and preferred time."
        )

    if chat_contains_any(text, ["app", "download", "android", "iphone", "ios"]):
        return (
            "Download the Fitness Gurukul app on Google Play or the App Store to track workouts, book sessions, "
            "and stay connected with your coach."
        )

    return (
        "I can help with Fitness Gurukul programs, coach recommendations, pricing, events, and booking. "
        "Try asking about personal training, yoga, weight loss, doorstep coaching, or upcoming events."
    )

def extract_openai_text(body):
    if isinstance(body.get("output_text"), str):
        return normalize_chat_text(body.get("output_text"))
    output = body.get("output") or []
    parts = []
    for item in output:
        for content in item.get("content", []) or []:
            text = content.get("text")
            if isinstance(text, str):
                parts.append(text)
    return normalize_chat_text(" ".join(parts))

def call_openai_chat(message, history=None):
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    model = os.environ.get("OPENAI_MODEL", "gpt-5.6").strip() or "gpt-5.6"
    messages = []
    for item in (history or [])[-8:]:
        role = str(item.get("role", "")).strip()
        content = normalize_chat_text(item.get("content", ""))
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": normalize_chat_text(message)})
    payload = json.dumps({
        "model": model,
        "instructions": build_chat_system_prompt(),
        "input": messages,
        "max_output_tokens": 450,
    }).encode("utf-8")
    req = urlrequest.Request(
        "https://api.openai.com/v1/responses",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=25) as res:
            body = json.loads(res.read().decode("utf-8"))
        return extract_openai_text(body) or None
    except Exception as exc:
        print("OpenAI chat error:", exc)
        return None

def generate_chat_reply(message, history=None):
    ai_reply = call_openai_chat(message, history)
    if ai_reply:
        return ai_reply, "openai"
    return generate_local_chat_reply(message, history), "local"

def save_chat_exchange(session_id, user_message, assistant_message, source):
    sid = normalize_chat_text(session_id) or "anonymous"
    now = int(time.time())
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO chat_messages (session_id, role, content, source, created_at) VALUES (?, ?, ?, ?, ?)",
            (sid, "user", normalize_chat_text(user_message), source, now),
        )
        conn.execute(
            "INSERT INTO chat_messages (session_id, role, content, source, created_at) VALUES (?, ?, ?, ?, ?)",
            (sid, "assistant", normalize_chat_text(assistant_message), source, now),
        )
        conn.commit()

def ensure_database():
    if not DB_SCHEMA_READY or not DB_PATH.exists():
        init_db()

class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC), **kwargs)

    def log_message(self, format, *args):
        print("%s - %s" % (self.address_string(), format % args))

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise ValueError("Invalid Content-Length")
        if length < 0:
            raise ValueError("Invalid Content-Length")
        if length > MAX_JSON_BYTES:
            raise ValueError("Payload too large")
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_GET(self):
        ensure_database()
        path = urlparse(self.path).path
        # Two interfaces:
        # - User website: /, index.html, public pages
        # - Owner portal: /me, /owner, /dashboard
        if path in {"/me", "/owner", "/dashboard", "/leads"}:
            self.path = "/dashboard.html"
            path = self.path
        elif path in {"/backend", "/office", "/admin", "/staff"}:
            self.path = "/office.html"
            path = self.path

        if path.startswith("/api/"):
            if path == "/api/health":
                return self.send_json({
                    "ok": True,
                    "engine": "python",
                    "databaseExists": DB_PATH.exists(),
                    "adminConfigured": bool(admin_token()),
                    "backendUrl": "/backend",
                    "aiEnabled": bool(os.environ.get("OPENAI_API_KEY", "").strip()),
                })
            if path == "/api/backend-info":
                # Non-sensitive helper so the login screen can guide staff.
                host_hdr = (self.headers.get("Host") or f"127.0.0.1:{os.environ.get('PORT', '8000')}").strip()
                mode = ADMIN_CRED_MODE if ADMIN_CRED_MODE != "unconfigured" else (
                    "configured" if admin_token() else "unconfigured"
                )
                return self.send_json({
                    "ok": True,
                    "backendUrl": "/backend",
                    "dashboardUrl": "/me",
                    "ownerUrl": "/me",
                    "userUrl": "/",
                    "adminConfigured": bool(admin_token()),
                    "mode": mode,
                    "localDefaultPassword": LOCAL_DEFAULT_PASSWORD if mode == "local-default" else "",
                    "openUrl": f"http://{host_hdr}/me",
                    "hint": (
                        f"Local default password: {LOCAL_DEFAULT_PASSWORD}"
                        if mode == "local-default"
                        else "Enter the staff password from your .env file (ADMIN_TOKEN or ADMIN_PASSWORD)."
                    ),
                })
            if path == "/api/content":
                return self.send_json(content_payload())
            if path == "/api/live":
                return self.send_json(live_payload())
            if path == "/api/goals":
                return self.send_json({"ok": True, "goals": list(GOAL_MATCHES.values())})
            if path == "/api/chat/status":
                has_openai = bool(os.environ.get("OPENAI_API_KEY", "").strip())
                return self.send_json({
                    "ok": True,
                    "aiEnabled": has_openai,
                    "engine": "openai" if has_openai else "local",
                    "model": os.environ.get("OPENAI_MODEL", "gpt-5.6").strip() or "gpt-5.6",
                    "suggestions": CHAT_SUGGESTIONS,
                })
            if path == "/api/admin-data":
                if not require_admin(self):
                    return
                with get_connection() as conn:
                    leads = conn.execute("SELECT * FROM leads ORDER BY created_at DESC LIMIT 100").fetchall()
                    checkins = conn.execute("SELECT * FROM checkins ORDER BY created_at DESC LIMIT 100").fetchall()
                    newsletter = conn.execute("SELECT * FROM newsletter ORDER BY created_at DESC LIMIT 100").fetchall()
                    ai_scans = conn.execute("SELECT * FROM ai_scans ORDER BY created_at DESC LIMIT 100").fetchall()
                    calculations = conn.execute("SELECT * FROM calculator_results ORDER BY created_at DESC LIMIT 100").fetchall()
                    chat_messages = conn.execute("SELECT * FROM chat_messages ORDER BY created_at DESC LIMIT 100").fetchall()
                    submissions = conn.execute("SELECT * FROM submissions ORDER BY created_at DESC LIMIT 300").fetchall()
                return self.send_json({
                    "ok": True,
                    "leads": [dict(r) for r in leads],
                    "checkins": [dict(r) for r in checkins],
                    "newsletter": [dict(r) for r in newsletter],
                    "ai_scans": [dict(r) for r in ai_scans],
                    "calculations": [dict(r) for r in calculations],
                    "chat_messages": [dict(r) for r in chat_messages],
                    "submissions": [row_to_submission(r) for r in submissions],
                })
            if path == "/api/submissions":
                if not require_admin(self):
                    return
                with get_connection() as conn:
                    rows = conn.execute("SELECT * FROM submissions ORDER BY created_at DESC LIMIT 300").fetchall()
                data = [row_to_submission(r) for r in rows]
                return self.send_json({"ok": True, "count": len(data), "data": data})
            if path == "/api/office-stats":
                if not require_admin(self):
                    return
                with get_connection() as conn:
                    total = conn.execute("SELECT COUNT(*) AS c FROM submissions").fetchone()["c"]
                    today = conn.execute(
                        "SELECT COUNT(*) AS c FROM submissions WHERE created_at >= ?",
                        (int(time.time()) - 24 * 60 * 60,),
                    ).fetchone()["c"]
                    new_count = conn.execute(
                        "SELECT COUNT(*) AS c FROM submissions WHERE COALESCE(status, 'new') = 'new'"
                    ).fetchone()["c"]
                    corp = conn.execute(
                        "SELECT COUNT(*) AS c FROM submissions WHERE form_type = 'corporate_event'"
                    ).fetchone()["c"]
                    calcs = conn.execute("SELECT COUNT(*) AS c FROM calculator_results").fetchone()["c"]
                return self.send_json({
                    "ok": True,
                    "total": total,
                    "today": today,
                    "new": new_count,
                    "corporate": corp,
                    "calculations": calcs,
                })
            return self.send_json({"error": "Not found"}, 404)

        if is_blocked_static(path):
            return self.send_json({"error": "Not found"}, 404)
        if not (PUBLIC / path.lstrip("/")).exists() and path != "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_PATCH(self):
        ensure_database()
        path = urlparse(self.path).path
        if path.startswith("/api/submissions/") and path.endswith("/status"):
            if not require_admin(self):
                return
            try:
                payload = self.read_json()
            except (ValueError, json.JSONDecodeError):
                return self.send_json({"error": "Invalid JSON"}, 400)
            submission_id = clip(unquote(path[len("/api/submissions/"):-len("/status")]), 64)
            status = clip(payload.get("status"), 32).lower()
            if status not in {"new", "contacted", "qualified", "closed"}:
                return self.send_json({"error": "Invalid status"}, 400)
            with get_connection() as conn:
                cur = conn.execute(
                    "UPDATE submissions SET status = ? WHERE id = ?",
                    (status, submission_id),
                )
                conn.commit()
                if cur.rowcount < 1:
                    return self.send_json({"error": "Not found"}, 404)
            return self.send_json({"ok": True, "id": submission_id, "status": status})
        return self.send_json({"error": "Not found"}, 404)

    def do_DELETE(self):
        ensure_database()
        path = urlparse(self.path).path
        if path.startswith("/api/submissions/"):
            if not require_admin(self):
                return
            submission_id = clip(unquote(path.split("/api/submissions/", 1)[1]), 64)
            if not submission_id or "/" in submission_id:
                return self.send_json({"error": "Not found"}, 404)
            with get_connection() as conn:
                cur = conn.execute("DELETE FROM submissions WHERE id = ?", (submission_id,))
                conn.commit()
                if cur.rowcount < 1:
                    return self.send_json({"error": "Not found"}, 404)
            return self.send_json({"ok": True})
        return self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        ensure_database()
        path = urlparse(self.path).path
        try:
            payload = self.read_json()
        except ValueError as exc:
            status = 413 if "too large" in str(exc).lower() else 400
            return self.send_json({"error": str(exc)}, status)
        except json.JSONDecodeError:
            return self.send_json({"error": "Invalid JSON"}, 400)

        if path in RATE_LIMITS and not check_rate_limit(self, path):
            return self.send_json({"error": "Too many requests. Please wait a minute."}, 429)

        if path in {"/api/submit", "/api/leads"}:
            if path == "/api/leads" and not payload.get("form_type"):
                payload = {
                    "form_type": "consultation",
                    "name": payload.get("name"),
                    "phone": payload.get("phone"),
                    "goal": payload.get("goal"),
                    "program": payload.get("program"),
                    "message": payload.get("message"),
                    "email": payload.get("email"),
                    "coach": payload.get("coach"),
                }
            submission_id, missing = save_submission(payload)
            if missing:
                return self.send_json({"ok": False, "error": "Missing required fields", "fields": missing}, 400)
            return self.send_json({"ok": True, "id": submission_id, "message": "Saved."}, 201)

        if path == "/api/calculations":
            required = ["calculator", "title", "result"]
            missing = [f for f in required if not str(payload.get(f, "")).strip()]
            if missing:
                return self.send_json({"error": "Missing required fields", "fields": missing}, 400)
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO calculator_results (calculator, title, result, unit, rating, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        clip(payload["calculator"], 80),
                        clip(payload["title"], 160),
                        clip(payload["result"], 160),
                        clip(payload.get("unit", ""), 40),
                        clip(payload.get("rating", ""), 80),
                        int(time.time()),
                    ),
                )
                conn.commit()
            return self.send_json({"ok": True, "message": "Saved."}, 201)

        if path == "/api/match":
            return self.send_json(match_goal(payload))

        if path == "/api/chat":
            message = normalize_chat_text(payload.get("message", ""))
            if not message:
                return self.send_json({"error": "Message is required"}, 400)
            if len(message) > 2000:
                return self.send_json({"error": "Message is too long"}, 400)
            history = payload.get("history") if isinstance(payload.get("history"), list) else []
            # Cap client-controlled history to limit cost/prompt injection surface.
            history = history[-6:]
            session_id = clip(payload.get("sessionId", ""), 80) or "anonymous"
            reply, source = generate_chat_reply(message, history)
            try:
                save_chat_exchange(session_id, message, reply, source)
            except Exception as exc:
                print("Chat save error:", exc)
            return self.send_json({
                "ok": True,
                "reply": reply,
                "source": source,
                "aiEnabled": source == "openai",
                "suggestions": CHAT_SUGGESTIONS,
            })
        return self.send_json({"error": "Not found"}, 404)

if __name__ == "__main__":
    init_db()
    host = os.environ.get("HOST", "127.0.0.1").strip() or "127.0.0.1"
    port = int(os.environ.get("PORT", "8000"))
    cred_mode = ensure_admin_credentials(host)
    server = ThreadingHTTPServer((host, port), AppHandler)
    print("")
    print("=" * 56)
    print(" Fitness Gurukul")
    print("=" * 56)
    print(f" USER WEBSITE:  http://127.0.0.1:{port}/")
    print(f" OWNER PORTAL:  http://127.0.0.1:{port}/me")
    print(f" FULL BACKEND:  http://127.0.0.1:{port}/backend")
    if cred_mode == "local-default":
        print(" Owner password (local default): fitnessgurukul")
        print(" Tip: /me unlocks automatically on this computer.")
    elif cred_mode == "generated":
        print(f" Owner password (generated): {admin_token()}")
        print(" Tip: add ADMIN_TOKEN to .env so it stays the same next restart.")
    else:
        print(" Owner password: loaded from .env (ADMIN_TOKEN / ADMIN_PASSWORD)")
    if host in {"0.0.0.0", "::"}:
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except OSError:
            local_ip = "YOUR-LAPTOP-IP"
        print(f" LAN user site: http://{local_ip}:{port}/")
        print(f" LAN owner portal: http://{local_ip}:{port}/me")
    else:
        print(" Bound to localhost only. Set HOST=0.0.0.0 to share on Wi-Fi.")
    print("=" * 56)
    print("")
    server.serve_forever()
