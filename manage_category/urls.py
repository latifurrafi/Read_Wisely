from django.urls import path
from .import views

urlpatterns = [
    path('categories/', views.category_list_view, name='category_list_view'),
    path('categories/<slug:category_slug>/', views.books_by_category_view, name='books_by_category_view'),
    path('categories/<slug:category_slug>/search/', views.categories_wise_search, name="categories_wise_search"),
    path('recent/', views.recent_books_view, name='recent_books_view'),
    path('api/recent/', views.recent_book_for_category_list, name='recent_books_api'),
    path("update-book-status/<int:book_id>/<str:status>/", views.update_book_status, name="update-book-status"),
    
]
