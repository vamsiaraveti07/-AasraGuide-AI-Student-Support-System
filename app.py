# app.py
import os
import re
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta, timezone, date
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from config import Config
from db import db
from models import User, ChatSession, Message, Assignment, Note, ExamHelper
from ai_engine import generate_ai_reply
from datetime import datetime, date, timedelta
from flask import jsonify, request, render_template
from flask_login import login_required, current_user


STOPWORDS = {
    "i","me","my","we","our","you","your","the","a","an","and","or","but","to","for","of","in","on",
    "is","are","was","were","this","that","these","those","with","by","from","at","be","as","it's","its"
}
ALLOWED_EXT = {"png","jpg","jpeg","gif","pdf","txt","docx","pptx"}

def make_title_from_text(text, max_words=4):
    t = re.sub(r"[^0-9A-Za-z\s]", " ", (text or "")).lower()
    words = [w for w in t.split() if w and w not in STOPWORDS]
    if not words:
        words = [w for w in t.split()][:max_words]
    words = words[:max_words]
    title = " ".join(w.capitalize() for w in words).strip()
    return title or "New Chat"

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(uid):
        try:
            return db.session.get(User, int(uid))
        except Exception:
            return None

    # cleanup empty old chats
    def cleanup_old_empty_chats(user_id, older_than_minutes=60):
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=older_than_minutes)
        empty_sessions = (ChatSession.query
                          .filter_by(user_id=user_id)
                          .outerjoin(Message, ChatSession.id == Message.session_id)
                          .group_by(ChatSession.id)
                          .having(db.func.count(Message.id) == 0)
                          .filter(ChatSession.created_at < cutoff)
                          .all())
        for s in empty_sessions:
            db.session.delete(s)
        if empty_sessions:
            db.session.commit()

    @app.context_processor
    def inject_sessions():
        if not current_user.is_authenticated:
            return {"chat_sessions": []}
        try:
            cleanup_old_empty_chats(current_user.id, older_than_minutes=60)

            # chats that have messages (active not archived)
            sub = (db.session.query(Message.session_id.label("sid"))
                   .group_by(Message.session_id)
                   .subquery())

            active_chats = (ChatSession.query
                            .filter(ChatSession.user_id == current_user.id, ChatSession.archived == False)
                            .join(sub, ChatSession.id == sub.c.sid)
                            .order_by(ChatSession.updated_at.desc())
                            .all())

            archived = (ChatSession.query
                        .filter_by(user_id=current_user.id, archived=True)
                        .order_by(ChatSession.updated_at.desc())
                        .all())

            # return active first then archived appended so templates can render both
            return {"chat_sessions": active_chats + archived}
        except Exception:
            return {"chat_sessions": []}

    # ------------------ routes ------------------
    @app.route("/")
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for("login"))
        s = ChatSession.query.filter_by(user_id=current_user.id).order_by(ChatSession.updated_at.desc()).first()
        return redirect(url_for("chat", session_id=s.id)) if s else redirect(url_for("new_chat"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for("index"))
            flash("Invalid username or password", "danger")
        return render_template("login.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            fullname = request.form.get("fullname").strip()
            username = request.form.get("username").strip()
            password = request.form.get("password")

            if not fullname or not username or not password:
                flash("All fields are required", "danger")
                return redirect(url_for("register"))

            if User.query.filter_by(username=username).first():
                flash("Username already exists", "danger")
                return redirect(url_for("register"))

            new_user = User(fullname=fullname, username=username)
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()

            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))

        return render_template("register.html")



    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))

    @app.route("/new_chat")
    @login_required
    def new_chat():
        s = ChatSession(user_id=current_user.id, title="New Chat")
        db.session.add(s)
        db.session.commit()
        return redirect(url_for("chat", session_id=s.id))

    @app.route("/chat")
    @login_required
    def chat_redirect():
        s = ChatSession.query.filter_by(user_id=current_user.id).order_by(ChatSession.updated_at.desc()).first()
        if not s:
            return redirect(url_for("new_chat"))
        return redirect(url_for("chat", session_id=s.id))

    @app.route("/chat/<int:session_id>")
    @login_required
    def chat(session_id):
        s = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
        msgs = Message.query.filter_by(session_id=session_id).order_by(Message.created_at.asc()).all()
        return render_template("chat.html", session=s, recent_messages=msgs, due_today=[])

    def get_history(session_id):
        msgs = Message.query.filter_by(session_id=session_id).order_by(Message.created_at.asc()).all()
        arr = []
        for m in msgs:
            role = "assistant" if m.emotion == "bot_reply" else "user"
            arr.append({"role": role, "content": m.text})
        return arr

    @app.route("/send/<int:session_id>", methods=["POST"])
    @login_required
    def send(session_id):
        s = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
        text = (request.form.get("message") or "").strip()
        if not text:
            return jsonify({"reply": "Empty message", "suggestions": []})

        user_msg = Message(user_id=current_user.id, session_id=session_id, text=text, emotion="user")
        db.session.add(user_msg)
        db.session.commit()

        # auto-name chat from first user message
        if not s.title or s.title.strip().lower().startswith("new chat"):
            new_title = make_title_from_text(text, max_words=4)
            s.title = new_title[:120]
            s.updated_at = datetime.now(timezone.utc)
            db.session.commit()

        history = get_history(session_id)
        try:
            ai_result = generate_ai_reply(history, text)
            if isinstance(ai_result, tuple):
                bot_reply = ai_result[0] or "Sorry, I couldn't generate a reply."
                suggestions = ai_result[1] if len(ai_result) > 1 else []
            else:
                bot_reply = ai_result or "Sorry, I couldn't generate a reply."
                suggestions = []
        except Exception:
            bot_reply = "Sorry, I'm having trouble right now."
            suggestions = []

        bot_msg = Message(user_id=current_user.id, session_id=session_id, text=bot_reply, emotion="bot_reply")
        db.session.add(bot_msg)

        s.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        return jsonify({"reply": bot_reply, "suggestions": suggestions})

    # rename - supports AJAX (json) and form submit
    @app.route("/rename_chat/<int:session_id>", methods=["POST"])
    @login_required
    def rename_chat(session_id):
        s = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
        if request.is_json:
            data = request.get_json()
            title = (data.get("new_title") or "").strip() if data else ""
        else:
            title = (request.form.get("new_title") or "").strip()
        title = title or "Untitled Chat"
        s.title = title[:120]
        s.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"ok": True, "title": s.title})
        flash("Chat renamed", "success")
        return redirect(url_for("chat", session_id=session_id))

    @app.route("/archive_chat/<int:session_id>", methods=["POST"])
    @login_required
    def archive_chat(session_id):
        s = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
        s.archived = True
        s.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return jsonify({"ok": True, "sid": s.id, "title": s.title})

    @app.route("/unarchive_chat/<int:session_id>", methods=["POST"])
    @login_required
    def unarchive_chat(session_id):
        s = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
        s.archived = False
        s.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return jsonify({"ok": True, "sid": s.id, "title": s.title})
    
    @app.route("/delete_chat/<int:session_id>", methods=["POST"])
    @login_required
    def delete_chat(session_id):
        s = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
        Message.query.filter_by(session_id=session_id).delete()
        db.session.delete(s)
        db.session.commit()
        return jsonify({"ok": True, "sid": session_id})
    


    @app.route("/fragment/assignments")
    @login_required
    def fragment_assignments():
        today = date.today()
        assignments = Assignment.query.filter_by(user_id=current_user.id).order_by(Assignment.due_date.asc()).all()
        return render_template("fragments/assignments.html", assignments=assignments, today=today)
    @app.route("/api/assignments", methods=["GET"])
    @login_required
    def api_get_assignments():
        assignments = Assignment.query.filter_by(user_id=current_user.id).order_by(Assignment.due_date.asc()).all()
        return jsonify([{
            "id": a.id,
            "title": a.title,
            "subject": a.subject,
            "due_date": a.due_date.isoformat() if a.due_date else None,
            "notes": a.notes,
            "priority": a.priority if a.priority else "medium",
            "status": a.status if a.status else "not_started",
            "progress": a.progress if a.progress is not None else 0,
            "is_overdue": a.due_date < date.today() if a.due_date else False
        } for a in assignments])

    @app.route("/api/assignments", methods=["POST"])
    @login_required
    def api_create_assignment():
        try:
            data = request.get_json()
            title = (data.get("title") or "").strip()
            subject = (data.get("subject") or "").strip()
            due_date_str = data.get("due_date")
            notes = (data.get("notes") or "").strip()
            priority = data.get("priority", "medium")
            status = data.get("status", "not_started")
            progress = int(data.get("progress", 0))
            if not title:
                return jsonify({"error": "Title is required"}), 400
            due_date_obj = None
            if due_date_str:
                due_date_obj = datetime.strptime(due_date_str, "%Y-%m-%d").date()

            assignment = Assignment(
                user_id=current_user.id,
                title=title,
                subject=subject,
                due_date=due_date_obj,
                notes=notes,
                priority=priority,
                status=status,
                progress=progress
            )
            db.session.add(assignment)
            db.session.commit()
            return jsonify({
                "ok": True,
                "assignment": {
                    "id": assignment.id,
                    "title": assignment.title,
                    "subject": assignment.subject,
                    "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
                    "notes": assignment.notes,
                    "priority": assignment.priority,
                    "status": assignment.status,
                    "progress": assignment.progress,
                    "is_overdue": assignment.due_date < date.today() if assignment.due_date else False
                }
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    @app.route("/api/assignments/<int:assignment_id>", methods=["PUT"])
    @login_required
    def api_update_assignment(assignment_id):
        try:
            assignment = Assignment.query.filter_by(id=assignment_id, user_id=current_user.id).first_or_404()
            data = request.get_json()
            assignment.title = (data.get("title") or "").strip() or assignment.title
            assignment.subject = (data.get("subject") or "").strip() or assignment.subject
            assignment.notes = (data.get("notes") or "").strip() or assignment.notes
            assignment.priority = data.get("priority", assignment.priority)
            assignment.status = data.get("status", assignment.status)
            assignment.progress = int(data.get("progress", assignment.progress) or 0)
            due_date_str = data.get("due_date")
            if due_date_str:
                assignment.due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            db.session.commit()
            return jsonify({
                "ok": True,
                "assignment": {
                    "id": assignment.id,
                    "title": assignment.title,
                    "subject": assignment.subject,
                    "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
                    "notes": assignment.notes,
                    "priority": assignment.priority,
                    "status": assignment.status,
                    "progress": assignment.progress,
                    "is_overdue": assignment.due_date < date.today() if assignment.due_date else False
                }
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

   
    @app.route("/api/assignments/<int:assignment_id>", methods=["DELETE"])
    @login_required
    def api_delete_assignment(assignment_id):
        try:
            assignment = Assignment.query.filter_by(id=assignment_id, user_id=current_user.id).first_or_404()
            db.session.delete(assignment)
            db.session.commit()
            return jsonify({"ok": True, "id": assignment_id})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    @app.route("/api/assignments/reminders", methods=["GET"])
    @login_required
    def api_assignments_reminders():
        try:
            n_days = int(request.args.get("days", 3))
            today = date.today()
            soon = today + timedelta(days=n_days)

            rows = Assignment.query.filter(
                Assignment.user_id == current_user.id,
                Assignment.due_date.isnot(None),        # must have due date
                Assignment.due_date >= today,
                Assignment.due_date <= soon,
                Assignment.status != "completed"        # don’t remind completed ones
            ).order_by(Assignment.due_date.asc()).all()

            return jsonify([
                {
                    "id": r.id,
                    "title": r.title,
                    "subject": r.subject,
                    "due_date": r.due_date.isoformat() if r.due_date else None,
                    "notes": r.notes,
                    "priority": getattr(r, "priority", "medium"),
                    "status": getattr(r, "status", "not_started"),
                    "progress": int(getattr(r, "progress", 0)),
                }
                for r in rows
            ])
        except Exception as e:
            print("REMINDER ERROR:", e)
            return jsonify({"error": str(e)}), 500


    @app.route("/api/assignments/due_today", methods=["GET"])
    @login_required
    def api_assignments_due_today():
        try:
            today = date.today()
            assignments = Assignment.query.filter(
                Assignment.user_id == current_user.id,
                Assignment.due_date == today
            ).all()
            return jsonify([{
                "id": a.id,
                "title": a.title,
                "subject": a.subject,
                "priority": getattr(a, "priority", "medium"),
                "status": getattr(a, "status", "not_started"),
                "progress": getattr(a, "progress", 0)
            } for a in assignments])
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # --- NOTES FEATURE ROUTES ---
    
    UPLOAD_FOLDER = "static/uploads/notes"
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


    @app.route('/fragment/notes')
    @login_required
    def fragment_notes():
        return render_template('fragments/notes.html')


    @app.route('/notes/add', methods=['POST'])
    @login_required
    def notes_add():
        title = (request.form.get('title') or "Untitled").strip()
        content = (request.form.get('content') or "").strip()
        tags = (request.form.get('tags') or "").strip()
        reminder_at_str = request.form.get('reminder_at') or ""
        reminder_at = None
        if reminder_at_str:
            try:
                reminder_at = datetime.strptime(reminder_at_str, "%Y-%m-%dT%H:%M")
            except Exception:
                reminder_at = None
        if not content:
            return jsonify({"error": "Content required"}), 400
        note = Note(user_id=current_user.id, title=title, content=content, tags=tags, reminder_at=reminder_at)
        db.session.add(note)
        db.session.commit()
        return jsonify({"ok": True, "id": note.id})


    @app.route('/notes/delete/<int:nid>', methods=['POST'])
    @login_required
    def notes_delete(nid):
        n = Note.query.filter_by(id=nid, user_id=current_user.id).first_or_404()
        db.session.delete(n)
        db.session.commit()
        return jsonify({"ok": True})
    
    @app.route('/notes/list')
    @login_required
    def notes_list():
        user_notes = Note.query.filter_by(user_id=current_user.id)
        shared_notes = Note.query.filter(Note.shared_with.like(f"%{current_user.username}%"))
        notes = user_notes.union(shared_notes).order_by(Note.created_at.desc()).all()
        return jsonify([
            {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "tags": n.tags,
                "reminder_at": n.reminder_at.strftime("%Y-%m-%d %H:%M") if n.reminder_at else "",
                "shared_with": n.shared_with,
                "attachments": n.attachments.split(",") if n.attachments else []
            }
            for n in notes
            ])

    @app.route('/notes/share/<int:nid>', methods=['POST'])
    @login_required
    def notes_share(nid):
        note = Note.query.filter_by(id=nid, user_id=current_user.id).first_or_404()
        username = (request.form.get('username') or "").strip()
        if not username or username == current_user.username:
            return jsonify({"error": "Invalid username"}), 400
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"error": "No such user"}), 404
        shared = [u for u in (note.shared_with or "").split(",") if u]
        if username in shared:
            return jsonify({"error": "Already shared"}), 400
        shared.append(username)
        note.shared_with = ",".join(shared)
        db.session.commit()
        return jsonify({"ok": True, "shared_with": note.shared_with})
    
    @app.route('/notes/attach/<int:nid>', methods=['POST'])
    @login_required
    def notes_attach(nid):
        note = Note.query.filter_by(id=nid, user_id=current_user.id).first_or_404()

        file = request.files.get("file")
        if not file or file.filename == "":
            return jsonify({"error": "No file selected"}), 400

    # Create upload folder
        upload_dir = os.path.join(app.root_path, "static/uploads/notes")
        os.makedirs(upload_dir, exist_ok=True)

    # Save file
        filename = f"{current_user.id}_{nid}_{int(datetime.utcnow().timestamp())}_{file.filename}"
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)

    # Update DB
        existing = note.attachments.split(",") if note.attachments else []
        existing.append(filename)
        note.attachments = ",".join(existing)

        db.session.commit()

        return jsonify({
            "ok": True,
            "filename": filename,
            "url": f"/static/uploads/notes/{filename}"
        })


    def allowed_filename(fn):
        return "." in fn and fn.rsplit(".",1)[1].lower() in ALLOWED_EXT

    @app.route('/notes/upload/<int:nid>', methods=['POST'])
    @login_required
    def notes_upload(nid):
        note = Note.query.filter_by(id=nid, user_id=current_user.id).first_or_404()
        if 'file' not in request.files:
            return jsonify({"error":"No file sent"}), 400
        f = request.files['file']
        if f.filename == '':
            return jsonify({"error":"Empty filename"}), 400
        if not allowed_filename(f.filename):
            return jsonify({"error":"File type not allowed"}), 400

        filename = secure_filename(f.filename)
    # optionally prefix with uid + timestamp to avoid collisions
        from time import time
        fname = f"{current_user.id}_{int(time())}_{filename}"
        upload_dir = os.path.join(app.root_path, "static", "uploads", "notes")
        os.makedirs(upload_dir, exist_ok=True)
        save_path = os.path.join(upload_dir, fname)
        f.save(save_path)

    # update attachments field (comma-separated)
        existing = (note.attachments or "").strip()
        lst = [x for x in existing.split(",") if x] if existing else []
        lst.append(fname)
        note.attachments = ",".join(lst)
        db.session.commit()

    # return the updated attachments array so frontend can refresh
        return jsonify({"ok": True, "attachments": lst, "filename": fname})
    

    @app.route("/fragment/exam_helper")
    @login_required
    def fragment_exam_helper():
        """Display the exam helper page"""
        return render_template("fragments/exam_helper.html")


    @app.route("/exam_helper/generate", methods=["POST"])
    @login_required
    def exam_generate():
        """Generate AI-powered exam guide"""
        
        print("=" * 60)
        print("🚀 EXAM HELPER CALLED")
        print(f"User: {current_user.username}")
        print(f"Topic: {request.form.get('topic', '')}")
        print("=" * 60)
        
        topic = request.form.get("topic", "").strip()
        
        if not topic:
            return jsonify({"ok": False, "error": "Please enter a subject"}), 400
        
        try:
            # Import AI function
            from ai_engine import generate_exam_helper
            
            # Generate AI response
            print(f"🤖 Generating AI content for: {topic}")
            ai_response = generate_exam_helper(topic)
            print(f"✅ AI generated {len(ai_response)} characters")
            
            # Save to database
            exam_helper = ExamHelper(
                user_id=current_user.id,
                topic=topic,
                generated_content=ai_response
            )
            db.session.add(exam_helper)
            db.session.commit()
            print(f"💾 Saved to database with ID: {exam_helper.id}")
            
            return jsonify({
                "ok": True,
                "answer": ai_response,
                "saved_id": exam_helper.id
            })
        
        except Exception as e:
            db.session.rollback()
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            
            return jsonify({
                "ok": False,
                "error": f"Server error: {str(e)}"
            }), 500
            
    @app.route("/api/exam_helper/history", methods=["GET"])
    @login_required
    def get_exam_helper_history():
        """Get user's exam helper history"""
        try:
            limit = request.args.get('limit', 10, type=int)
            
            history = ExamHelper.query.filter_by(
                user_id=current_user.id
            ).order_by(
                ExamHelper.created_at.desc()
            ).limit(limit).all()
            
            return jsonify({
                "ok": True,
                "history": [
                    {
                        "id": h.id,
                        "topic": h.topic,
                        "content": h.generated_content,
                        "created_at": h.created_at.strftime('%b %d, %Y at %I:%M %p')
                    }
                    for h in history
                ]
            })
        
        except Exception as e:
            print(f"Error fetching history: {e}")
            return jsonify({
                "ok": False,
                "error": str(e)
            }), 500


    @app.route("/api/exam_helper/delete/<int:helper_id>", methods=["DELETE"])
    @login_required
    def delete_exam_helper(helper_id):
        """Delete an exam helper entry"""
        try:
            helper = ExamHelper.query.filter_by(
                id=helper_id,
                user_id=current_user.id
            ).first_or_404()
            
            db.session.delete(helper)
            db.session.commit()
            
            return jsonify({
                "ok": True,
                "message": "Deleted successfully"
            })
        
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "ok": False,
                "error": str(e)
            }), 500
# ---- POMODORO STORAGE (in-memory for now) ----
    pomodoro_sessions = []


    @app.route("/fragment/pomodoro")
    @login_required
    def fragment_pomodoro():
        return render_template("fragments/pomodoro.html")


    @app.route("/pomodoro/log", methods=["POST"])
    @login_required
    def log_pomodoro():
        """Log one pomodoro session (success or cancelled)."""
        success_raw = str(request.form.get("success", "")).lower()
        success = success_raw == "true"

        # Work minutes used in that session (for stats)
        try:
            work_minutes = int(request.form.get("work_minutes", "25"))
        except ValueError:
            work_minutes = 25

        now = datetime.now()

        session = {
            "start": request.form.get("start"),
            "end": request.form.get("end"),
            "success": success,
            "note": request.form.get("note", ""),
            "reflection": request.form.get("reflection", ""),

            # extra fields for charts
            "date": now.date().isoformat(),  # e.g. 2025-11-22
            "weekday": now.weekday(),        # 0=Mon, 6=Sun
            "work_minutes": work_minutes,
        }

        pomodoro_sessions.append(session)
        return jsonify({"ok": True})


    @app.route("/pomodoro/history")
    @login_required
    def pomodoro_history():
        return jsonify(pomodoro_sessions)

  
    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
