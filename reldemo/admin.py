from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Profile, ExpensesCategory, Expense, Author, 
    Category, Book, BorrowedBook, Review, BookStatus, UserPreferences
)


class ProfileInline(TabularInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "Profile"
    fields = ('bio', 'image', 'birth_date', 'location')
    show_change_link = True


class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    inlines = [ProfileInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions')
    readonly_fields = ('date_joined', 'last_login')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )


class ExpenseInline(TabularInline):
    model = Expense
    extra = 1
    fields = ('amount', 'date', 'description')


@admin.register(ExpensesCategory)
class ExpensesCategoryAdmin(ModelAdmin):
    list_display = ('name', 'description', 'get_expenses_count', 'get_total_expenses')
    search_fields = ('name',)
    inlines = [ExpenseInline]
    
    def get_expenses_count(self, obj):
        return obj.expense_set.count()
    get_expenses_count.short_description = 'Expenses Count'
    
    def get_total_expenses(self, obj):
        total = sum(expense.amount for expense in obj.expense_set.all())
        return f"${total:.2f}"
    get_total_expenses.short_description = 'Total Expenses'


@admin.register(Expense)
class ExpenseAdmin(ModelAdmin):
    list_display = ('category', 'amount', 'date', 'description')
    list_filter = ('category', 'date', 'amount')
    search_fields = ('description', 'category__name')
    date_hierarchy = 'date'
    list_editable = ('amount', 'description')


@admin.register(Author)
class AuthorAdmin(ModelAdmin):
    list_display = ('name', 'nationality', 'birth_date', 'get_books_count')
    list_filter = ('nationality', 'birth_date')
    search_fields = ('name', 'bio', 'nationality')
    fieldsets = (
        (None, {
            'fields': ('name', 'nationality')
        }),
        ('Biographical Information', {
            'fields': ('bio', 'birth_date'),
            'classes': ('collapse',)
        }),
    )
    
    def get_books_count(self, obj):
        return obj.book_set.count()
    get_books_count.short_description = 'Books Count'


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'get_books_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

    def get_books_count(self, obj):
        return obj.books.count()
    get_books_count.short_description = 'Books Count'


class ReviewInline(TabularInline):
    model = Review
    extra = 0
    fields = ('user', 'rating', 'comment', 'created_at')
    readonly_fields = ('created_at',)


class BorrowedBookInline(TabularInline):
    model = BorrowedBook
    extra = 0
    fields = ('user', 'borrowed_date', 'due_date', 'returned_date', 'is_returned')
    readonly_fields = ('borrowed_date',)


class BookStatusInline(TabularInline):
    model = BookStatus
    extra = 0
    fields = ('user', 'status')


@admin.register(Book)
class BookAdmin(ModelAdmin):
    list_display = ('title', 'display_authors', 'year', 'isbn', 'available_copies', 'display_categories')
    list_filter = ('categories', 'year', 'available_copies', 'language')
    search_fields = ('title', 'author__name', 'isbn', 'story')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('author', 'categories')
    inlines = [BorrowedBookInline, ReviewInline, BookStatusInline]

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'author', 'year', 'isbn', 'language')
        }),
        ('Content', {
            'fields': ('story', 'page', 'categories')
        }),
        ('Media', {
            'fields': ('image', 'image_url', 'pdf_file'),
            'classes': ('collapse',)
        }),
        ('Inventory', {
            'fields': ('available_copies',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def display_authors(self, obj):
        return ", ".join([author.name for author in obj.author.all()])
    display_authors.short_description = 'Authors'
    
    def display_categories(self, obj):
        return ", ".join([category.name for category in obj.categories.all()])
    display_categories.short_description = 'Categories'


@admin.register(BorrowedBook)
class BorrowedBookAdmin(ModelAdmin):
    list_display = ('book_title', 'user_username', 'borrowed_date', 'due_date', 'returned_date', 'is_returned', 'status')
    list_filter = ('borrowed_date', 'due_date', 'is_returned')
    search_fields = ('book__title', 'user__username')
    readonly_fields = ('borrowed_date',)
    date_hierarchy = 'borrowed_date'
    list_editable = ('is_returned', 'returned_date')
    
    def book_title(self, obj):
        return format_html('<a href="{}">{}</a>',
            reverse('admin:reldemo_book_change', args=[obj.book.id]),
            obj.book.title
        )
    book_title.short_description = 'Book'
    
    def user_username(self, obj):
        return format_html('<a href="{}">{}</a>',
            reverse('admin:auth_user_change', args=[obj.user.id]),
            obj.user.username
        )
    user_username.short_description = 'User'
    
    def status(self, obj):
        if obj.is_returned:
            return format_html('<span style="color:green;">Returned</span>')
        elif obj.is_overdue:
            return format_html('<span style="color:red;">Overdue</span>')
        elif obj.is_due_soon:
            return format_html('<span style="color:orange;">Due Soon</span>')
        else:
            return format_html('<span style="color:blue;">Active</span>')
    status.short_description = 'Status'


@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = ('book_title', 'user_username', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('book__title', 'user__username', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    
    def book_title(self, obj):
        return format_html('<a href="{}">{}</a>',
            reverse('admin:reldemo_book_change', args=[obj.book.id]),
            obj.book.title
        )
    book_title.short_description = 'Book'
    
    def user_username(self, obj):
        return format_html('<a href="{}">{}</a>',
            reverse('admin:auth_user_change', args=[obj.user.id]),
            obj.user.username
        )
    user_username.short_description = 'User'


@admin.register(BookStatus)
class BookStatusAdmin(ModelAdmin):
    list_display = ('book_title', 'user_username', 'status')
    list_filter = ('status',)
    search_fields = ('book__title', 'user__username')
    list_editable = ('status',)
    
    def book_title(self, obj):
        return format_html('<a href="{}">{}</a>',
            reverse('admin:reldemo_book_change', args=[obj.book.id]),
            obj.book.title
        )
    book_title.short_description = 'Book'
    
    def user_username(self, obj):
        return format_html('<a href="{}">{}</a>',
            reverse('admin:auth_user_change', args=[obj.user.id]),
            obj.user.username
        )
    user_username.short_description = 'User'


@admin.register(UserPreferences)
class UserPreferencesAdmin(ModelAdmin):
    list_display = ('user_username', 'reading_goal', 'favorite_category_count', 'favorite_author_count')
    search_fields = ('user__username',)
    filter_horizontal = ('favorite_categories', 'favorite_authors')
    
    def user_username(self, obj):
        return format_html('<a href="{}">{}</a>',
            reverse('admin:auth_user_change', args=[obj.user.id]),
            obj.user.username
        )
    user_username.short_description = 'User'
    
    def favorite_category_count(self, obj):
        return obj.favorite_categories.count()
    favorite_category_count.short_description = 'Categories'
    
    def favorite_author_count(self, obj):
        return obj.favorite_authors.count()
    favorite_author_count.short_description = 'Authors'


# Unregister the default User admin and register the custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)