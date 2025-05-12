# Read Wisely

A modern book management and reading tracking application that helps users organize their reading life and discover new books.

## 📚 Overview

Read Wisely is a Django-based web application that allows users to manage their personal book collections, track reading progress, discover new books based on preferences, and connect with other readers. The platform focuses on creating a personalized reading experience with future plans for machine learning-driven recommendations.

## ✨ Features

- **Book Management**: Add, update, and organize your book collection
- **Reading Progress Tracking**: Mark books as "Want to Read", "Currently Reading", or "Read"
- **User Profiles**: Personalized profiles showcasing reading statistics and preferences
- **Reading Statistics**: Visualize your reading habits and progress toward goals
- **Category & Author Management**: Browse books by categories and authors
- **Library System**: Borrow and return books with due date tracking
- **Reviews & Ratings**: Share your thoughts on books and view others' opinions
- **Admin Dashboard**: Comprehensive admin interface for content management
- **Preference-Based Recommendations**: Set reading preferences for personalized experiences

## 🛠️ Tech Stack

- **Backend**: Django 5.0+
- **Database**: SQLite (development), compatible with PostgreSQL (production)
- **Frontend**: HTML, CSS (Tailwind CSS), JavaScript
- **UI Framework**: Custom components with responsive design
- **Admin Interface**: Django Unfold for enhanced admin experience
- **Charts & Visualization**: Chart.js
- **Authentication**: Django's built-in authentication system
- **File Storage**: Django's file handling for book covers and PDFs

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- pip (Python package manager)
- Virtual environment (recommended)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/read-wisely.git
   cd read-wisely
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Apply migrations:
   ```bash
   python manage.py migrate
   ```

5. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```bash
   python manage.py runserver
   ```

7. Visit http://127.0.0.1:8000/ in your browser

## 📋 Project Structure

```
Read_Wisely/
├── demoprojects/       # Project configuration
├── reldemo/            # Main application
│   ├── migrations/     # Database migrations
│   ├── models.py       # Data models
│   ├── views.py        # View functions
│   ├── urls.py         # URL routing
│   ├── forms.py        # Form definitions
│   ├── admin.py        # Admin interface
│   └── validators.py   # Custom validators
├── manage_category/    # Category management module
├── templates/          # HTML templates
├── static/             # Static files (CSS, JS, images)
├── media/              # User-uploaded content
└── manage.py           # Django management script
```

## 🔮 Future Enhancements

- **Machine Learning Recommendations**: Implementing ML algorithms for book recommendations
- **Social Features**: Following other users, sharing reading lists
- **Reading Challenges**: Create and participate in reading challenges
- **Integration with External APIs**: Book data from services like Google Books
- **Mobile App**: Native mobile applications for iOS and Android

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Contributors

- Md.Latifur Rahman Rafi - Initial work and maintenance

---

Created with ❤️ for book lovers everywhere 