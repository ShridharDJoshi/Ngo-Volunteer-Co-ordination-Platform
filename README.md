# NGO Volunteer Co-ordination Platform

A Django-based web application that connects **Volunteers** and **NGOs** through a centralized platform for complaint management, volunteer coordination, and task tracking. The system simplifies communication between volunteers and NGOs while improving transparency and efficiency in community service activities.

---

## 📖 Project Description

The **NGO Volunteer Co-ordination Platform** is designed to bridge the gap between NGOs and volunteers by providing an easy-to-use online platform.

Volunteers can register, join NGOs, submit complaints related to community issues, and track the progress of their requests. NGOs can manage complaints, assign volunteers to tasks, monitor task completion, and update the status of ongoing activities. An admin panel is available to manage the entire system.

This project was developed using **Python**, **Django**, **HTML**, **CSS**, **JavaScript**, and **SQLite**.

---

## ✨ Features

### 👤 Volunteer
- Register and Login
- Join NGOs
- Submit complaints
- View complaint history
- Track complaint status
- Receive task assignments
- View notifications

### 🏢 NGO
- NGO Registration and Login
- View complaints
- Accept or Reject complaints
- Assign volunteers to tasks
- Update task progress
- Manage volunteers

### 📋 Complaint Management
- Submit complaints
- Complaint status tracking
- Complaint history
- Progress updates

### ✅ Task Management
- Create tasks
- Assign volunteers
- Update task status
- Track completion

### 🔔 Notification System
- Complaint updates
- Task notifications
- Status updates

### 🔐 Admin
- Manage Users
- Manage NGOs
- Manage Complaints
- Monitor system activities

---

## 🛠️ Tech Stack

### Backend
- Python
- Django

### Frontend
- HTML
- CSS
- JavaScript

### Database
- SQLite

### Tools
- Django ORM
- Django Templates
- Static Files
- Media File Handling

---

## 📁 Project Structure

```
Final/
│
├── complaints/
├── ngos/
├── notifications/
├── tasks/
├── users/
├── templates/
├── static/
├── media/
├── Final/
├── manage.py
├── requirements.txt
└── .gitignore
```

---

# 🚀 Getting Started

## 1️⃣ Clone the Repository

```bash
git clone https://github.com/ShridharDJoshi/Ngo-Volunteer-Co-ordination-Platform.git
```

---

## 2️⃣ Navigate to the Project Folder

```bash
cd Ngo-Volunteer-Co-ordination-Platform/Final
```

---

## 3️⃣ Create a Virtual Environment

### Windows

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 4️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 5️⃣ Apply Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 6️⃣ Create a Superuser (Optional)

```bash
python manage.py createsuperuser
```

Follow the prompts to create the admin account.

---

## 7️⃣ Run the Development Server

```bash
python manage.py runserver
```

---

## 8️⃣ Open the Application

Open your browser and visit:

```
http://127.0.0.1:8000/
```

For the Admin Panel:

```
http://127.0.0.1:8000/admin/
```

---

# 🔄 Workflow

1. Volunteer registers and logs in.
2. NGO registers and logs in.
3. Volunteer submits a complaint.
4. NGO reviews the complaint.
5. NGO accepts or rejects the complaint.
6. Accepted complaints become tasks.
7. NGO assigns volunteers.
8. Volunteers complete assigned tasks.
9. NGO verifies task completion.
10. Notifications keep users updated throughout the process.

---

# 📚 Learning Outcomes

This project demonstrates practical knowledge of:

- Django Framework
- Python Programming
- User Authentication
- Role-Based Access Control
- CRUD Operations
- Database Management
- Django ORM
- Task Management
- Complaint Management
- Notification System
- Frontend and Backend Integration

---

# 🚀 Future Enhancements

- Email Notifications
- SMS Notifications
- Live Chat
- Real-Time Notifications
- GPS Location Tracking
- Analytics Dashboard
- Cloud Deployment
- Mobile Application
- AI-based Complaint Prioritization

---

# 👨‍💻 Author

**Shridhar D. Joshi**

GitHub: https://github.com/ShridharDJoshi

---

# 📄 License

This project is developed for educational and learning purposes.
