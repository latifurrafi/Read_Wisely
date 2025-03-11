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
    path('', views.homepage, name="homepage"),
    path('add/', views.add_book, name="add_book"),
    path('update/<int:book_id>/', views.update_book, name="update_book"),
    path('delete/<int:book_id>/', views.delete_book, name="delete_book"),
    path('book_details/<int:book_id>/', views.book_detail, name='book_detail'),
]  

