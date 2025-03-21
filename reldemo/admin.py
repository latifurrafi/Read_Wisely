from django.contrib import admin
from django.utils import timezone
from django.urls import reverse
from django.utils.html import format_html
from django.contrib import messages
from .models import Profile, ExpensesCategory, Expense, Author, Book, BorrowedBook, Category, Review, BookStatus

# Profile Admin
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'birth_date', 'location')

# Expenses Category Admin
@admin.register(ExpensesCategory)
class ExpensesCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

# Expense Admin
@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'date')
    list_filter = ('category', 'date')

# Author Admin
@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'bio',)

# Book Admin
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    # Remove 'category' from list_display if it doesn't exist in your Book model
    list_display = ('title', 'display_authors', 'year', 'isbn', 'available_copies', 'availability_status')
    # Remove 'category' from list_filter if it doesn't exist in your Book model
    list_filter = ('available_copies', 'year')
    search_fields = ('title', 'isbn')
    list_editable = ('available_copies',)
    list_per_page = 20

    def display_authors(self, obj):
        # If 'author' is ManyToManyField
        return ", ".join([author.name for author in obj.author.all()])
    
    display_authors.short_description = 'Author(s)'

    def availability_status(self, obj):
        if obj.available_copies > 0:
            return format_html('<span style="color: green; font-weight: bold;">Available</span>')
        return format_html('<span style="color: red;">Not Available</span>')

    availability_status.short_description = 'Availability'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change:
            messages.success(request, f"Book '{obj.title}' was updated successfully!")
        else:
            messages.info(request, f"New book '{obj.title}' added successfully!")

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        messages.warning(request, f"Book '{obj.title}' was deleted.")

# Borrowed Book Admin
@admin.register(BorrowedBook)
class BorrowedBookAdmin(admin.ModelAdmin):
    list_display = ('book_title', 'borrower', 'borrowed_date', 'due_date', 'status', 'actions')
    list_filter = ('is_returned', 'borrowed_date', 'due_date')
    search_fields = ('book__title', 'user__username', 'user__email')
    list_per_page = 20
    date_hierarchy = 'borrowed_date'

    def book_title(self, obj):
        return obj.book.title

    def borrower(self, obj):
        return obj.user.username

    def status(self, obj):
        today = timezone.now().date()
        if obj.is_returned:
            return format_html('<span style="color: blue;">Returned on {}</span>', obj.returned_date.strftime('%b %d, %Y'))
        elif obj.due_date < today:
            days_overdue = (today - obj.due_date).days
            return format_html('<span style="color: red; font-weight: bold;">Overdue by {} days</span>', days_overdue)
        elif (obj.due_date - today).days <= 7:
            return format_html('<span style="color: orange;">Due soon</span>')
        return format_html('<span style="color: green;">Active</span>')

    def actions(self, obj):
        if not obj.is_returned:
            return format_html(
                '<a class="button" href="{}">Mark Returned</a>',
                reverse('admin:mark_as_returned', args=[obj.pk])
            )
        return "---"

    # Change `actions` to a list of action method names
    actions = ['mark_as_returned_action']

    def mark_as_returned_action(self, request, queryset):
        for obj in queryset:
            if not obj.is_returned:
                obj.is_returned = True
                obj.returned_date = timezone.now().date()
                obj.save()

                # Update available copies
                book = obj.book
                book.available_copies += 1
                book.save()

                messages.success(request, f"'{obj.book.title}' has been marked as returned.")

    mark_as_returned_action.short_description = "Mark selected as returned"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/mark-returned/',
                self.admin_site.admin_view(self.mark_as_returned),
                name='mark_as_returned',
            ),
        ]
        return custom_urls + urls

    def mark_as_returned(self, request, object_id, *args, **kwargs):
        from django.shortcuts import redirect
        borrowed_book = self.get_object(request, object_id)
        if borrowed_book and not borrowed_book.is_returned:
            borrowed_book.is_returned = True
            borrowed_book.returned_date = timezone.now().date()
            borrowed_book.save()

            # Update available copies
            book = borrowed_book.book
            book.available_copies += 1
            book.save()

            messages.success(request, f"'{borrowed_book.book.title}' has been marked as returned.")

        return redirect('admin:library_borrowedbook_changelist')

# Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'book_count')
    search_fields = ('name',)

    def book_count(self, obj):
        return obj.books.count()

    book_count.short_description = 'Number of Books'

# Customize Admin Site
admin.site.site_header = 'Library Management System'
admin.site.site_title = 'Library Admin'
admin.site.index_title = 'Library Administration'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'rating', 'created_at')  # Display these fields in the list view
    list_filter = ('rating', 'created_at')  # Add filters for rating and creation date
    search_fields = ('user__username', 'book__title', 'comment')  # Enable search by user, book title, and comment
    ordering = ('-created_at',)  # Order reviews by newest first
    readonly_fields = ('created_at', 'updated_at')  # Make timestamps read-only

    fieldsets = (
        (None, {
            'fields': ('book', 'user', 'rating', 'comment')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(BookStatus)
class BookStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'status')
    list_filter = ('status',)
    search_fields = ('user__username', 'book_title')
    ordering = ('user', 'book')