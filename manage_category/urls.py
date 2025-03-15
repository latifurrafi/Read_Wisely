from django.urls import path
from .import views

urlpatterns = [
    path('categories/', views.category_list_view, name='category_list_view'),
    path('categories/<slug:category_slug>/', views.books_by_category_view, name='books_by_category_view'),
    path('categories/<slug:category_slug>/search/', views.categories_wise_search, name="categories_wise_search"),
]
