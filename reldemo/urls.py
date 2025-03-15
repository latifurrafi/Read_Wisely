from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .import views


urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("one-to-one/", views.demo_one_to_one, name="one-to-one"),
    path("user/<int:pk>/", views.user, name="user"),
    path("one-to-many/", views.demo_one_to_many, name="one-to-many"),
    path("many-to-many/", views.demo_many_to_many, name="many-to-many"),
    path('book/<str:book_title>/', views.get_book_details, name='get_book_details'),
    path('author/<str:author_name>/', views.get_author_details, name='get_author_details'),
    path('', views.book_list, name="book_list"),
    path('add/', views.add_book, name="add_book"),
    path('update/<int:book_id>/', views.update_book, name="update_book"),
    path('delete/<int:book_id>/', views.delete_book, name="delete_book"),
    path('book_details/<int:book_id>/', views.book_detail, name='book_detail'),
    path('profile/<str:username>/', views.user_profile, name='user_profile'),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('books/', views.search_book, name='search_book'),
    path('borrowed-books/', views.borrowed_book, name='borrowed_book'),
    path('renew-book/<int:book_id>/', views.renew_book, name='renew_book'),
    path('return-book/<int:book_id>/', views.return_book, name='return_book'),
    path('export-borrowed-books/', views.export_borrowed_books, name='export_borrowed_books'),
    path('book/<slug:slug>/', views.similar_book, name='similar_book'),
    # New JSON endpoint
    path('api/book/<slug:slug>/related/', views.related_books_json, name='related_books_json'),
    path('api/books-acquisition/', views.books_acquisition_chart, name='books_acquisition_chart'),
    path('books/<slug:slug>/', views.review_detail, name='review_detail'),
    path('books/<slug:book_slug>/add_review/', views.add_review, name='add_review'),
    path('books/edit_review/<int:review_id>/', views.edit_review, name='edit_review'),
    path('book/<slug:slug>/load-more-reviews/', views.load_more_reviews, name='load_more_reviews'),
    
]  