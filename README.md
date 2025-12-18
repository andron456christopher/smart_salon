💇‍♂️ Smart Salon Booking & Recommendation System

A Flask-based AI-assisted salon application that enables users to book salon appointments through chat and receive personalized hairstyle, hair color, and product recommendations based on their profile details.

This project demonstrates backend development, database handling, session management, and rule-based AI logic, making it ideal for internships and portfolio use.

📌 Project Overview

This application acts as a virtual salon assistant that:

Understands user messages

Extracts booking details automatically

Stores appointments and customer profiles

Provides intelligent grooming recommendations

Maintains chat context using session handling

🚀 Features

💬 Chat-based appointment booking

🤖 Personalized hairstyle & product recommendations

🗂️ Customer profile storage

🗓️ Appointment management with SQLite

🧠 Session-based conversational flow

📅 Flexible date & time input handling

🌐 REST API powered chatbot

🛠️ Technologies Used
Technology	Purpose
Python	Core backend language
Flask	Web framework
SQLite	Lightweight database
HTML/CSS/JS	Frontend
Regex (re)	Text & intent extraction
Datetime	Date & time handling
📂 Project Structure
salon-booking-system/
│
├── app.py                # Main Flask application
├── data/
│   └── salon.db          # SQLite database
├── templates/
│   └── index.html        # Homepage UI
├── static/               # CSS, JS, assets
└── README.md             # Documentation

⚙️ Installation & Setup
1️⃣ Clone the repository
git clone https://github.com/your-username/salon-booking-system.git
cd salon-booking-system

2️⃣ Install dependencies
pip install flask

3️⃣ Run the application
python app.py

4️⃣ Open in browser
http://localhost:5000

🗄️ Database Design
📌 Bookings Table

Stores appointment details:

Name

Phone

Gender

Age

Service

Date

Time

Status (tentative / confirmed)

📌 Customers Table

Stores profile details:

Name

Phone

Gender

Age

Skin tone

Face shape

🧠 Code Explanation (Important Concepts Used)
1️⃣ Flask Application

Initializes the web server

Handles routing and API endpoints

2️⃣ SQLite Database

Stores bookings and customer profiles

Automatically created on first run

3️⃣ Session Management (SESSIONS)

In-memory dictionary to maintain chat state

Tracks user progress in booking and profile flow

4️⃣ Rule-Based Recommendation System

Uses predefined rules for:

Face shape → hairstyle

Skin tone → hair color

Hair condition → product suggestions

5️⃣ Natural Language Parsing (Regex)

Extracts:

Name

Phone number

Service

Date & time

Gender & age

Mimics basic NLP behavior without ML models

6️⃣ Date & Time Normalization

Supports inputs like:

2025-12-20

20/12/2025

3pm, 15:30, 10

7️⃣ Chat API Endpoint (/api/chat)

Central logic handler

Routes user messages to:

Booking flow

Recommendation flow

Profile saving flow

8️⃣ Error Handling

Prevents server crashes

Returns friendly responses on failure

💬 Example Chat Commands
Book haircut on 2025-12-20 at 3pm for Rahul 9876543210 male 28

Recommend hairstyle for round face fair skin female 22

My name is Rahul 9876543210 male 28 round face fair skin

🎯 Why This Project Is Valuable

✔ Real-world use case
✔ Backend + database integration
✔ AI-style personalization
✔ Clean architecture
✔ Resume & internship ready

🔮 Future Enhancements

User authentication

Admin dashboard

Payment integration

Machine learning–based recommendations

Cloud deployment (AWS / Azure)