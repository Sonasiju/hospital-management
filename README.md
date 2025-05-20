# 🏥 Hospital Management System

A web-based Hospital Management System (HMS) built with **Flask**, **MongoDB**, and **Flask-Login**. This system supports doctor-patient management, secure login, patient bookings, and trigger-like audit logs for patient records.

---

## ✨ Features

- 👨‍⚕️ **Doctor Management**  
  Add, view, and search doctors by department.

- 🧑‍💼 **Patient Management**  
  Book appointments, view patient lists, edit/delete bookings.

- 🔐 **User Authentication**  
  Login system with role-based access using Flask-Login.

- 📜 **Trigger Logging**  
  Logs updates and deletions of patient records, mimicking database triggers.

- 🔍 **Search Functionality**  
  Search doctors by department or name.

---

## 🛠️ Tech Stack

| Layer      | Technology             |
|------------|------------------------|
| Backend    | Python, Flask          |
| Frontend   | HTML, CSS, Bootstrap   |
| Database   | MongoDB (via PyMongo)  |
| Auth       | Flask-Login            |

---

## 🧪 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/hospital-management-system.git
cd hospital-management-system

2. Set Up Virtual Environment
bash
Copy
Edit
python -m venv venv
source venv/bin/activate

nstall Dependencies
bash
Copy
Edit
pip install -r requirements.txt
