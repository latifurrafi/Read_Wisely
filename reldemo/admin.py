from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Profile, ExpensesCategory, Expense, Author, Book
# Register your models here.

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'birth_date', 'location')  # Customize list view

@admin.register(ExpensesCategory)
class ExpensesCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'date')
    list_filter = ('category', 'date')  # Add filters in Django Admin

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'bio',)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'display_authors', 'year', 'isbn', 'story', 'pdf_file', 'image_url',)

    def display_authors(self, obj):
        return ", ".join([author.name for author in obj.author.all()])
    
    display_authors.short_description = 'Author(s)'  # Optional: Customize the column name

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change:
            messages.success(request, f"Book '{obj.title}' was updated successfully!")
        else:
            messages.info(request, f"New book '{obj.title}' added successfully!")

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        messages.warning(request, f"Book '{obj.title}' was deleted.")

