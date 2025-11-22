
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from db import db


# ===================== USER =====================
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150), nullable=False)   # ← ADD THIS
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assignments = db.relationship("Assignment", backref="user", lazy=True)
    sessions = db.relationship("ChatSession", backref="user", lazy=True)
    messages = db.relationship("Message", backref="user", lazy=True)
    

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



# ===================== CHAT SESSION =====================
class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(120), default="New Chat")
    archived = db.Column(db.Boolean, default=False)
    pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship(
        "Message",
        backref="session",
        lazy=True,
        cascade="all, delete-orphan"
    )


# ===================== MESSAGE =====================
class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    session_id = db.Column(
        db.Integer,
        db.ForeignKey("chat_sessions.id"),
        nullable=False
    )
    text = db.Column(db.Text, nullable=False)
    emotion = db.Column(db.String(50))
    score = db.Column(db.Float)
    crisis_flag = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ===================== ASSIGNMENT =====================
class Assignment(db.Model):
    __tablename__ = "assignments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(200))
    due_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    priority = db.Column(db.String(20), default="medium")       
    status = db.Column(db.String(20), default="not_started")    
    progress = db.Column(db.Integer, default=0)                
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    

class Note(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), default="Untitled")
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(200), default="")
    reminder_at = db.Column(db.DateTime, nullable=True)
    shared_with = db.Column(db.String(400), default="")
    attachments = db.Column(db.String(1000), default="") 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class ExamHelper(db.Model):
    __tablename__ = 'exam_helpers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    generated_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('exam_helpers', lazy=True))
    
    def __repr__(self):
        return f'<ExamHelper {self.topic}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'topic': self.topic,
            'content': self.generated_content,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }



