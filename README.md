# AasraGuide - AI StudentSupportSystem

A next-generation academic assistance platform designed to organize student life, boost productivity, and provide intelligent study support.
AasraGuide integrates multiple powerful learning tools — AI chat, smart notes, assignment planner, Pomodoro timer, and exam preparation assistant — into one seamless system.
This professional system uses structured workflows, clean UI, and intelligent processing to help students stay organized, productive, and exam-ready.

## 🌟 Features Overview

AasraGuide includes 5 core modules, each engineered to deliver a premium, reliable student experience:

## 1. 📝 Smart Notes with Attachments & Highlighting
   A powerful, rich-text notes system built for fast academic writing.
 ### Key Capabilities
     
     • Rich Editor with bold, highlight, formatting
     
     • Instant Highlighting using custom marker colors
     
     • Image & File Attachments inside notes
     
     • Preview in Lightbox (click to zoom images)
     
     • Tags Support for organizing subjects
     
     • Auto-save & Instant Update
  
#### Impact

   Enables quick concept capturing, fast revisions, and visually enriched study notes.

## 2. 📘 Assignment Manager
  A complete workflow for tracking academic tasks.
### Features
     • Add, edit, delete assignments
     
     • Subject-wise organization
     
     • Due date tracking
     
     • Auto reminders for upcoming deadlines
     
     • Clean, responsive UI
  
#### Impact

   Prevents missed deadlines and centralizes all academic work.

## 3. ⏳ Pomodoro Productivity Timer
A clean, simple focus timer with industry-standard Pomodoro cycles.
### Features
     • 25-minute focus sessions
     
     • 5-minute short breaks
     
     • 4-cycle long break logic
     
     • Start / Pause / Reset
     
     • Live countdown display
#### Impact

   Improves focus and productivity with proven time-management methodology.

## 4. 📚 AI-Powered Exam Helper

A specialized AI module designed to simplify exam preparation. 
### Features

      • Instant subject guide generation
      
      • Summaries, important points, key formulas
      
      • Clean structured output
      
      • History tracking
      
      • One-click re-view

#### Impact

   Helps students quickly revise any topic with AI-generated personalized guides.
## 5. 🤖 AI Chat Assistant

 Your personal study companion for doubt clearing and general help.

### Features

      • Intelligent responses
      
      • Study guidance
      
      • Explains concepts
      
      • Supports multi-topic conversations

#### Impact

   Acts as a virtual tutor available anytime.

## 📂 System Architecture
      AasraGuide AI
      │
      ├── __pycache__/                         // Python cache
      │
      ├── instance/
      │
      ├── static/
      │     ├── icons/
      │     │     ├── Assignment.png
      │     │     ├── bot.png
      │     │     ├── Exam.png
      │     │     ├── notes.png
      │     │     ├── pomo.png
      │     │     ├── pomo.svg
      │     │     ├── send.png
      │     │     └── user.png
      │     │
      │     ├── images/
      │     │
      │     ├── uploads/
      │     │     └── notes/                  // Uploaded note files
      │     │
      │     ├── chat.css
      │     ├── sidebar.css
      │     ├── style.css
      │     │
      │     ├── chatgpt.js
      │     ├── exam_helper.js
      │     ├── feature_assignments.js
      │     ├── notes.js
      │     ├── pomodoro.js
      │     └── sidebar.js
      │
      ├── templates/
      │     ├── fragments/
      │     │     ├── assignments.html
      │     │     ├── exam_helper.html
      │     │     ├── notes.html
      │     │     └── pomodoro.html
      │     │
      │     ├── base.html
      │     ├── chat.html
      │     ├── exam_test_standalone.html
      │     ├── login.html
      │     └── register.html
      │
      ├── venv/
      │
      ├── ai_engine.py
      ├── app.py
      ├── config.py
      ├── db.py
      ├── models.py
      ├── utils_emotion.py
      └── requirements.txt
## 🗄️ Database Schema
   ### Users
      id          INT PK
      username    TEXT
      password    TEXT (hashed)
   ### Notes
      id              INT PK
      user_id         FK -> users.id
      title           TEXT
      content         TEXT
      tags            TEXT
      attachments     TEXT (JSON)
      created_at      DATETIME
   ### Assignments
      id              INT PK
      user_id         FK -> users.id
      title           TEXT
      subject         TEXT
      due_date        DATETIME
      notes           TEXT
   ### Exam Helper History
      id              INT PK
      user_id         FK -> users.id
      topic           TEXT
      content         TEXT
      created_at      DATETIME
## 🛠️ Installation & Setup
 ### Prerequisites

     • Python 3.8+
      
     • Flask
      
     • SQLite
      
     • Internet connection for AI responses
## 1. Clone Repository
      git clone <repository-url>
      cd AasraGuide
## 2. Install Dependencies
      pip install -r requirements.txt
## 3. Initialize Database
      python
      >>> from app import db
      >>> db.create_all()
      >>> exit()
## 4. Run Application
      python app.py

## 🖼️ Screenshots

## 🔧 Configuration
### Modify Pomodoro durations
   const FOCUS_TIME = 25 * 60;
   
   const BREAK_TIME = 5 * 60;
#### Notes attachment storage:
      static/uploads/notes/

## 🐛 Troubleshooting
### Notes not saving?
   ✔ Check initQuickNotes() is running
   
   ✔ Verify /fragment/notes loaded
   
   ✔ Check console for JS errors

####Pomodoro not starting?
   ✔ Ensure pomodoro.js is loading
   
   ✔ Check console for missing file path

### Attachments not uploading?
   
   ✔ Folder must exist: static/uploads/notes/
   
   ✔ Check file permissions

## 🚀 Future Enhancements (Planned)

   Student Timetable Module
   
   Personalized Study Recommendations
   
   Daily Planner Dashboard
   
   AI-powered Chapter Summaries
   
   Cloud Sync
   
   Mobile App version

## 🤝 Contributing

   Pull requests and feature suggestions are welcome.

## 📄 License
   This project is licensed under the MIT License.
## 🎉 Final Note
   AasraGuide is built to give students a powerful, all-in-one academic support system that feels modern, intuitive, and intelligent — a companion for       every student.



