from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
import traceback
from .forms import BookForm
from django.contrib.auth.models import User
from .models import Profile, Expense, Book, Author
from django.http import HttpResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegisterForm
from django.utils import timezone
from django.db.models import Q
import csv
from .models import BorrowedBook, Category, BookStatus, UserPreferences
from .models import Review
from .forms import ReviewForm
from django.views.decorators.http import require_http_methods
import json
import logging
import traceback
from django.db.models import Count, Avg
from datetime import datetime, timedelta
from django.db.models.functions import TruncMonth
from django.utils.text import slugify


def user_profile(request, username):
    # Fetch the user object
    user = get_object_or_404(User, username=username)
    # Fetch the associated profile
    profile = get_object_or_404(Profile, user=user)
    
    # Get reading statistics
    currently_reading = BookStatus.objects.filter(user=user, status='reading').count()
    want_to_read = BookStatus.objects.filter(user=user, status='to-read').count()
    books_completed = BookStatus.objects.filter(user=user, status='read').count()
    
    # Get user's books with their statuses
    user_books = []
    book_statuses = BookStatus.objects.filter(user=user).select_related('book').prefetch_related('book__author')
    for status in book_statuses:
        book = status.book
        book.status = status.status
        user_books.append(book)
    
    # Monthly reading progress - Fix: Use the book's created_at instead of BookStatus.updated_at
    current_year = datetime.now().year
    monthly_progress_data = (
        BookStatus.objects.filter(
            user=user, 
            status='read', 
            book__created_at__year=current_year  # Changed from updated_at to book__created_at
        )
        .annotate(month=TruncMonth('book__created_at'))  # Changed from updated_at to book__created_at
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    
    # Convert to array of 12 months (for chart.js)
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_progress = [0] * 12
    
    for entry in monthly_progress_data:
        month_idx = entry['month'].month - 1  # 0-based index
        monthly_progress[month_idx] = entry['count']
    
    # Recent activities
    recent_activities = []
    
    # Recent borrowed books
    borrowed_books = BorrowedBook.objects.filter(user=user).order_by('-borrowed_date')[:5]
    for book in borrowed_books:
        if book.is_returned:
            activity_type = 'returned'
            description = f"Returned '{book.book.title}'"
            date = book.returned_date
        else:
            activity_type = 'borrowed'
            description = f"Borrowed '{book.book.title}'"
            date = book.borrowed_date
        
        recent_activities.append({
            'type': activity_type,
            'description': description,
            'date': date,
        })
    
    # Recent reviews
    reviews = Review.objects.filter(user=user).order_by('-created_at')[:5]
    for review in reviews:
        recent_activities.append({
            'type': 'review',
            'description': f"Reviewed '{review.book.title}' with {review.rating} stars",
            'date': review.created_at,
        })
    
    # Recent status changes - Fix: Remove ordering by updated_at
    status_changes = BookStatus.objects.filter(user=user)[:5]  # Removed order_by('-updated_at')
    for status in status_changes:
        if status.status == 'read':
            activity_description = f"Completed '{status.book.title}'"
            activity_type = 'completed'
        elif status.status == 'reading':
            activity_description = f"Started reading '{status.book.title}'"
            activity_type = 'started'
        else:
            activity_description = f"Added '{status.book.title}' to wishlist"
            activity_type = 'wishlist'
            
        recent_activities.append({
            'type': activity_type,
            'description': activity_description,
            'date': status.book.created_at,  # Use book's created_at as fallback
        })
    
    # Sort activities by date (newest first) and limit to 10
    recent_activities.sort(key=lambda x: x['date'], reverse=True)
    recent_activities = recent_activities[:10]
    
    # Get user preferences from the UserPreferences model
    # If not exists, create a new preferences object
    user_preferences, created = UserPreferences.objects.get_or_create(user=user)
    
    # Get favorite categories and authors from user preferences
    favorite_categories = user_preferences.favorite_categories.all()
    favorite_authors = user_preferences.favorite_authors.all()
    reading_goal = user_preferences.reading_goal
    
    # If no preferences are set yet, use the most frequent categories and authors as defaults
    if created or (not favorite_categories.exists() and not favorite_authors.exists()):
        # Calculate from user's books
        if user_books:
            # Get categories from user's books
            category_counts = {}
            for book in user_books:
                for category in book.categories.all():
                    if category.id in category_counts:
                        category_counts[category.id] += 1
                    else:
                        category_counts[category.id] = 1
            
            # Get top 5 categories
            if category_counts:
                top_category_ids = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                suggested_categories = Category.objects.filter(id__in=[cat_id for cat_id, _ in top_category_ids])
                # Add to preferences if no preferences were set before
                if not favorite_categories.exists():
                    for category in suggested_categories:
                        user_preferences.favorite_categories.add(category)
                    favorite_categories = suggested_categories
            
            # Get authors from user's books
            author_counts = {}
            for book in user_books:
                for author in book.author.all():
                    if author.id in author_counts:
                        author_counts[author.id] += 1
                    else:
                        author_counts[author.id] = 1
            
            # Get top 5 authors
            if author_counts:
                top_author_ids = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                suggested_authors = Author.objects.filter(id__in=[author_id for author_id, _ in top_author_ids])
                # Add to preferences if no preferences were set before
                if not favorite_authors.exists():
                    for author in suggested_authors:
                        user_preferences.favorite_authors.add(author)
                    favorite_authors = suggested_authors
    
    # Get all categories and authors for the preferences form
    all_categories = Category.objects.all()
    all_authors = Author.objects.all()
    
    # Render the profile template with all the gathered data
    return render(request, 'profile_details.html', {
        'Profile': profile,
        'currently_reading': currently_reading,
        'want_to_read': want_to_read,
        'books_completed': books_completed,
        'user_books': user_books,
        'monthly_progress': json.dumps(monthly_progress),
        'recent_activities': recent_activities,
        'favorite_categories': favorite_categories,
        'favorite_authors': favorite_authors,
        'all_categories': all_categories,
        'all_authors': all_authors,
        'reading_goal': reading_goal,
    })

def dashboard(request):
    six_months_ago = datetime.today() - timedelta(days=6 * 30)  # Approximate last 6 months

    # Get completed books per month
    progress_data = (
        Book.objects.filter(created_at__gte=six_months_ago)  # Filter last 6 months
        .annotate(month=TruncMonth('created_at'))  # Group by month
        .values('month')
        .annotate(count=Count('id'))  # Count books
        .order_by('month')
    )

    # Generate labels & data dynamically
    labelss = []
    dataa = []

    # Ensure we have all months (even if no books were read)
    all_months = [(six_months_ago + timedelta(days=30 * i)).strftime('%B') for i in range(6)]
    month_dict = {entry['month'].strftime('%B'): entry['count'] for entry in progress_data}

    for month in all_months:
        labelss.append(month)
        dataa.append(month_dict.get(month, 0))  # Default to 0 if no books completed

    # Get category distribution
    category_data = (
        Book.objects.values('categories__name')
        .annotate(count=Count('categories'))
        .order_by('-count')
    )

    labels = [entry['categories__name'] for entry in category_data]
    data = [entry['count'] for entry in category_data]

    recent_books = Book.objects.order_by('-created_at')[:5]  # Fetch the latest 5 books

    books_read = BookStatus.objects.filter(status='read').count()
    currently_read = BookStatus.objects.filter(status='reading').count()
    to_be_read = BookStatus.objects.filter(status='to-read').count()
    
    book_status_counts = {}

    for book in recent_books:
        # Count occurrences of each status for this book
        status_counts = BookStatus.objects.filter(book=book).values('status').annotate(count=Count('status'))
        
        # Convert to a dictionary: {status: count}
        status_dict = {entry['status']: entry['count'] for entry in status_counts}
        
        # Determine the most frequent status
        most_frequent_status = max(status_dict, key=status_dict.get, default='to-read')  # Default to 'to-read' if no status
        
        book.most_frequent_status = most_frequent_status
    print(book_status_counts)

    return render(request, 'dashboard.html', {
        'books': Book.objects.all(),
        'labels': json.dumps(labels), 
        'data': json.dumps(data), 
        'labelss': json.dumps(labelss),
        'dataa': json.dumps(dataa),
        'recent_books': recent_books,
        'books_read': books_read,
        'currently_read': currently_read,
        'to_be_read': to_be_read,
        # 'book_status_counts': book_status_counts,  # Pass status data to template
    })

def books_acquisition_chart(request):
    current_year = datetime.now().year

    books_monthly_data = (
        Book.objects.filter(created_at__year=current_year)  # Use `created_at` instead of `date_added`
        .annotate(month=TruncMonth('created_at'))  # Group by month using `created_at`
        .values('month')
        .annotate(total_books=Count('id'))  # Count books added in each month
        .order_by('month')
    )

    # Convert queryset into a dictionary { 'Jan': count, 'Feb': count, ... }
    monthly_books = {entry['month'].strftime('%b'): entry['total_books'] for entry in books_monthly_data}

    # Ensure all months are included (even if no books were added)
    months_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    books_added_count = [monthly_books.get(month, 0) for month in months_list]  # Fill missing months with 0

    return JsonResponse({'chart_labels': months_list, 'chart_data': books_added_count})

def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect("login")
    else:
        form = UserRegisterForm()
    return render(request, "register.html", {"form": form})

def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("book_list")
        else:
            messages.error(request, "Invalid username or password")
    return render(request, "login.html")

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect("login")

def search_book(request):
    query = request.GET.get('q', '')  # Get the search query from the request
    books = Book.objects.all()
    
    if query:
        books = books.filter(title__icontains=query)  # Filter books by title (case-insensitive)
    
    return render(request, 'book_list.html', {'books': books, 'query': query})

def demo_one_to_one(request):
    profiles = Profile.objects.select_related('user').all()
    # profiles = Profile.objects.select_related('user').filter(location="New York").all();

    profile_data = [
        {
            # "id" : profile.user.id,
            "id" : profile.user_id,
            "username" : profile.user.username,
            "email" : profile.user.email,
            "bio" : profile.bio,
            "birth_date" : profile.birth_date,
            "location" : profile.location
        }for profile in profiles
    ]
    return JsonResponse(profile_data, safe=False)

def user(request, pk):
    profile = Profile.objects.select_related('user').get(user_id=pk)

    profile_data = {
        "id" : profile.user_id,
        "username" : profile.user.username,
        "email" : profile.user.email,
        "bio" : profile.bio,
        "birth_date" : profile.birth_date,
        "location" : profile.location,
    }

    return JsonResponse(profile_data, safe=False)

def demo_one_to_many(request):
    # expenses = Expense.objects.select_related("category").filter(category="1").all()
    expenses = Expense.objects.select_related("category").filter(category__name="Food").all()


    expense_data = [
        {
            'amount': str(e.amount),
            'category': e.category.name,
            'description': e.description
        } for e in expenses
    ]

    return JsonResponse(expense_data, safe=False)

def demo_many_to_many(request):
    books = Book.objects.prefetch_related("author").all()
    book_data = [{
        'book_id': b.id,
        'title': b.title,
        'author': [a.name for a in b.author.all()],
        'isbn': b.isbn
    }for b in books]

    return JsonResponse(book_data, safe=False)

def get_book_details(request, book_title):
    try:
        # Get books whose titles contain the search term (case-insensitive)
        books = Book.objects.prefetch_related('author').filter(title__contains=book_title)

        if not books.exists():
            return JsonResponse({'error': 'No books found'}, status=404)

        # Prepare details for all matching books
        books_details = {
            'books': [{
                'title': book.title,
                'year': book.year,
                'isbn': book.isbn,
                'authors': [{
                    'name': author.name,
                    'bio': author.bio
                } for author in book.author.all()]
            } for book in books]
        }

        return JsonResponse(books_details)
    except Exception as e:
        import traceback
        print(traceback.format_exc())  # Log detailed error in terminal
        return JsonResponse({'error': str(e)}, status=500)

def get_author_details(request, author_name):
    try:
        # author_name = author_name.replace('+', ' ')  # ✅ Fix encoding issue
        
        authors = Author.objects.prefetch_related('books').filter(name__icontains=author_name)

        if not authors.exists():
            return JsonResponse({'error': "No Authors Found.."}, status=404)

        authors_details = {
            'authors': [{
                'name': author.name,
                'bio': author.bio,
                'books': [{
                    'title': book.title,
                    'year': book.year,
                    'isbn': book.isbn
                } for book in author.books.all()]
            } for author in authors]
        }
        
        return JsonResponse(authors_details)

    except Exception as e:
        import traceback
        print(traceback.format_exc())  # Log detailed error in terminal
        return JsonResponse({'error': str(e)}, status=500)

def book_create_view(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()  # Save the form data to the database
    else:
        form = BookForm()

    return render(request, 'book_form.html', {'form': form})

def book_list(request):
    books = Book.objects.all()
    # for book in books:
    #     for cat in book.categories.all():
    #         print(cat)
    # print("Books:", books)  # Debugging
    return render(request, 'book_list.html', {'books': books}) 

@login_required
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            # Prioritize uploaded image over image_url
            if 'image' in request.FILES:
                book.image_url = None  # Clear the URL field if a file is uploaded
            elif form.cleaned_data.get('image_url'):
                book.image = None  # Clear the file field if a URL is provided
            book.save()
            form.save_m2m()
            # Handle new category
            new_category_name = form.cleaned_data.get('new_category')
            if new_category_name:
                category, created = Category.objects.get_or_create(name=new_category_name)
                book.categories.add(category)
            return redirect('book_list')
        else:
            print("❌ Form Errors:", form.errors)
    else:
        form = BookForm()
    return render(request, 'add_book.html', {'form': form})

@login_required
def update_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)  # Better error handling

    if request.method == "POST":  # Fix: Change POST to "POST"
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            return redirect('book_list')

    else:
        form = BookForm(instance=book)

    return render(request, 'update_book.html', {'form': form, 'book': book})

@login_required
def delete_book(request, book_id):
    book = Book.objects.get(id=book_id)
    if book:
        book.delete()

    return redirect('book_list')

def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    reviews = book.reviews.all().order_by('-created_at')[:3]
    form = ReviewForm() if request.user.is_authenticated else None  # Show form only if user is logged in

    print("PDF URL:", book.pdf_file.url if book.pdf_file else "No PDF")

    return render(request, 'book_detail.html', {
        'book': book, 
        'reviews': reviews, 
        'form': form
    })

def similar_book(request, slug):
    book = get_object_or_404(Book, slug=slug)
    # Get related books based on categories
    related_books = Book.objects.filter(
        categories__in=book.categories.all()
    ).exclude(id=book.id).distinct()[:6]  # Limit to 6 related books
    
    context = {
        'book': book,
        'related_books': related_books,
    }
    return render(request, 'book_detail.html', context)

# New JSON endpoint for related books
def related_books_json(request, slug):
    book = get_object_or_404(Book, slug=slug)
    related_books = Book.objects.filter(
        categories__in=book.categories.all()
    ).exclude(id=book.id).distinct()[:6]
    
    books_data = []
    for related_book in related_books:
        categories = [category.name for category in related_book.categories.all()]
        books_data.append({
            'id': related_book.id,
            'title': related_book.title,
            'slug': related_book.slug,
            'image_url': related_book.image_url,
            'categories': categories,
        })
    
    return JsonResponse({'related_books': books_data})

def borrowed_book(request):
    books = BorrowedBook.objects.all()  # Fetch all borrowed books
    return render(request, 'borrowed_book.html', {'books': books})

@login_required
def borrowed_books(request):
    # Get filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    
    # Get all borrowed books for the current user that aren't returned
    borrowed_books = BorrowedBook.objects.filter(
        user=request.user,
        is_returned=False
    ).select_related('book', 'book__category')
    
    # Apply search filter if provided
    if search_query:
        borrowed_books = borrowed_books.filter(
            Q(book__title__icontains=search_query) | 
            Q(book__author__icontains=search_query)
        )
    
    # Apply status filter if provided
    today = timezone.now().date()
    if status_filter == 'overdue':
        borrowed_books = borrowed_books.filter(due_date__lt=today)
    elif status_filter == 'due-soon':
        one_week_later = today + timedelta(days=7)
        borrowed_books = borrowed_books.filter(due_date__lte=one_week_later, due_date__gte=today)
    
    # Calculate statistics
    total_borrowed = BorrowedBook.objects.filter(user=request.user, is_returned=False).count()
    overdue_count = BorrowedBook.objects.filter(user=request.user, is_returned=False, due_date__lt=today).count()
    due_soon_count = BorrowedBook.objects.filter(
        user=request.user, 
        is_returned=False, 
        due_date__lte=today + timedelta(days=7),
        due_date__gte=today
    ).count()
    
    context = {
        'books': borrowed_books,
        'today': today,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_borrowed': total_borrowed,
        'overdue_count': overdue_count,
        'due_soon_count': due_soon_count
    }
    
    return render(request, 'library/borrowed_books.html', context)

@login_required
def renew_book(request, book_id):
    borrowed_book = get_object_or_404(BorrowedBook, id=book_id, user=request.user, is_returned=False)
    
    # Standard renewal is for 14 more days from today
    today = timezone.now().date()
    borrowed_book.due_date = today + timedelta(days=14)
    borrowed_book.save()
    
    messages.success(request, f"'{borrowed_book.book.title}' has been renewed for 14 more days.")
    return redirect('borrowed_books')

@login_required
def return_book(request, book_id):
    borrowed_book = get_object_or_404(BorrowedBook, id=book_id, user=request.user, is_returned=False)
    
    # Mark as returned
    borrowed_book.is_returned = True
    borrowed_book.returned_date = timezone.now().date()
    borrowed_book.save()
    
    # Increase available copies for the book
    book = borrowed_book.book
    book.available_copies += 1
    book.save()
    
    messages.success(request, f"'{borrowed_book.book.title}' has been returned successfully.")
    return redirect('borrowed_books')

@login_required
def export_borrowed_books(request):
    borrowed_books = BorrowedBook.objects.filter(
        user=request.user,
        is_returned=False
    ).select_related('book')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="borrowed_books.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Title', 'Author', 'Category', 'Borrowed Date', 'Due Date', 'Status'])
    
    today = timezone.now().date()
    for item in borrowed_books:
        status = "Normal"
        if item.is_overdue:
            status = "Overdue"
        elif item.is_due_soon:
            status = "Due Soon"
            
        writer.writerow([
            item.book.title,
            item.book.author,
            item.book.category.name if item.book.category else 'Uncategorized',
            item.borrowed_date.strftime('%b %d, %Y'),
            item.due_date.strftime('%b %d, %Y'),
            status
        ])
    
    return response

# Set up logging
logger = logging.getLogger(__name__)
def review_detail(request, slug):
    """Display a book and its reviews."""
    book = get_object_or_404(Book, slug=slug)
    reviews = book.reviews.all().order_by('-created_at')[3:]
    
    # Check if the current user has already reviewed this book
    user_has_reviewed = False
    if request.user.is_authenticated:
        user_has_reviewed = book.reviews.filter(user=request.user).exists()
    
    context = {
        'book': book,
        'reviews': reviews,
        'user_has_reviewed': user_has_reviewed,
    }
    return render(request, 'book_detail.html', context)

@login_required
def add_review(request, book_slug):
    """Add a new review for a book."""
    book = get_object_or_404(Book, slug=book_slug)
    
    # Check if user already reviewed this book
    if book.reviews.filter(user=request.user).exists():
        return JsonResponse({'status': 'error', 'message': 'You have already reviewed this book'})
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('content')
        
        # Validate rating
        if not rating:
            return JsonResponse({'status': 'error', 'message': 'Please select a rating'})
        
        try:
            rating_value = int(rating)
            if rating_value < 1 or rating_value > 5:
                return JsonResponse({'status': 'error', 'message': 'Rating must be between 1 and 5'})
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid rating value'})
        
        # Validate comment (optional)
        if not comment:
            return JsonResponse({'status': 'error', 'message': 'Please enter a review comment'})
        
        # Create new review
        try:
            review = Review(
                book=book,
                user=request.user,
                rating=rating_value,
                comment=comment
            )
            review.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Review added successfully',
                'review': {
                    'user': request.user.username,
                    'rating': review.rating,
                    'comment': review.comment,
                    'created_at': review.created_at.strftime('%B %d, %Y')
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error saving review: {str(e)}'})
    
    return redirect('book_detail', slug=book_slug)

@login_required
def edit_review(request, review_id):
    """Edit an existing review."""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('content')
        
        if not rating or int(rating) < 1 or int(rating) > 5:
            return JsonResponse({'status': 'error', 'message': 'Please provide a valid rating'})
        
        # Update review
        review.rating = int(rating)
        review.comment = comment
        review.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Review updated successfully',
            'review': {
                'rating': review.rating,
                'comment': review.comment,
                'updated_at': review.updated_at.strftime('%B %d, %Y')
            }
        })
    
    return redirect('review_detail', slug=review.book.slug)

def load_more_reviews(request, slug):
    """Load more reviews for a specific book."""
    book = get_object_or_404(Book, slug=slug)
    
    offset = int(request.GET.get('offset', 3))  # Get the offset from the request
    limit = 3  # Number of reviews to load at a time

    reviews = book.reviews.filter(book = book).order_by('-created_at')[offset:offset + limit]

    review_list = [
        {
            'user': review.user.username,
            'rating': review.rating,
            'comment': review.comment,
            'created_at': review.created_at.strftime('%B %d, %Y')
        }
        for review in reviews
    ]

    return JsonResponse({'reviews': review_list})

def add_category(request):
    if request.method == "POST":
        new_category_name = request.POST.get("new_category", "").strip()
        
        if new_category_name:
            # Generate a unique slug
            base_slug = slugify(new_category_name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            category, created = Category.objects.get_or_create(name=new_category_name, defaults={'slug': slug})
            
            if created:
                return JsonResponse({"id": category.id, "name": category.name, "slug": category.slug, "created": True})
            else:
                return JsonResponse({"error": "Category already exists"}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)

def search_category(request):
    query = request.GET.get("q", "")
    categories = Category.objects.filter(name__icontains=query)[:10]
    category_list = [{"id": cat.id, "name": cat.name} for cat in categories]
    return JsonResponse({"categories": category_list})

@login_required
def reports_view(request):
    """
    Generate comprehensive reports and statistics for the library
    """
    # Get date range parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Base queryset for books
    books_queryset = Book.objects.all()
    
    # Apply date filters if provided
    if start_date and end_date:
        books_queryset = books_queryset.filter(created_at__range=[start_date, end_date])
    
    # Basic statistics
    total_books = books_queryset.count()
    
    # Books added in the last month
    thirty_days_ago = timezone.now() - timedelta(days=30)
    books_added_recently = books_queryset.filter(created_at__gte=thirty_days_ago).count()
    
    # Reading status statistics
    status_counts = BookStatus.objects.values('status').annotate(count=Count('id'))
    status_dict = {item['status']: item['count'] for item in status_counts}
    
    currently_reading = status_dict.get('reading', 0)
    books_completed = status_dict.get('read', 0)
    
    # Calculate percentages
    reading_percentage = round((currently_reading / total_books * 100) if total_books > 0 else 0)
    completion_percentage = round((books_completed / total_books * 100) if total_books > 0 else 0)
    
    # Review statistics
    reviews = Review.objects.all()
    total_reviews = reviews.count()
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Reading progress over time (last 6 months)
    six_months_ago = timezone.now() - timedelta(days=180)
    reading_progress = (
        BookStatus.objects.filter(
            status='read', 
            user=request.user
        ).filter(
            # Assuming there's a date field for when the status was set
            # If not, you might need to adjust this part
            book__created_at__gte=six_months_ago
        ).annotate(
            month=TruncMonth('book__created_at')
        ).values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    
    # Generate monthly labels and data
    months = [(six_months_ago + timedelta(days=30*i)).strftime('%B') for i in range(6)]
    reading_data = {entry['month'].strftime('%B'): entry['count'] for entry in reading_progress}
    reading_progress_data = [reading_data.get(month, 0) for month in months]
    
    # Category distribution
    category_distribution = (
        Category.objects.annotate(book_count=Count('books'))
        .values('name', 'book_count')
        .order_by('-book_count')[:7]  # Top 7 categories
    )
    
    category_labels = [entry['name'] for entry in category_distribution]
    category_data = [entry['book_count'] for entry in category_distribution]
    
    # Monthly book acquisitions (current year)
    current_year = timezone.now().year
    acquisitions = (
        Book.objects.filter(created_at__year=current_year)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    
    # Get all months of the year
    months_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    acquisition_data = [0] * 12  # Initialize with zeros
    
    # Fill in the actual data
    for entry in acquisitions:
        month_idx = entry['month'].month - 1  # 0-based index
        acquisition_data[month_idx] = entry['count']
    
    # Top authors
    top_authors = (
        Author.objects.annotate(book_count=Count('book'))
        .values('name', 'book_count')
        .order_by('-book_count')[:7]  # Top 7 authors
    )
    
    author_labels = [entry['name'] for entry in top_authors]
    author_data = [entry['book_count'] for entry in top_authors]
    
    # Recent activity (mock data - replace with actual activity tracking)
    # In a real application, you would have an Activity model to track user actions
    recent_activities = []
    
    # Get some recent books to simulate activity
    recent_books = Book.objects.order_by('-created_at')[:5]
    
    # Generate mock activities
    actions = ['Added', 'Updated', 'Started Reading', 'Finished Reading', 'Reviewed']
    colors = ['blue', 'purple', 'green', 'yellow', 'red']
    icons = [
        'M12 6v6m0 0v6m0-6h6m-6 0H6',  # Added (plus)
        'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z',  # Updated (pencil)
        'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253',  # Reading (book)
        'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',  # Finished (checkmark)
        'M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z',  # Reviewed (star)
    ]
    
    status_colors = ['green', 'yellow', 'blue', 'purple', 'red']
    statuses = ['Completed', 'In Progress', 'Available', 'Reserved', 'Overdue']
    
    category_colors = ['blue', 'green', 'purple', 'yellow', 'red', 'pink', 'gray']
    
    # Generate mock activities for demonstration
    for i, book in enumerate(recent_books):
        # Create a mock activity
        activity = {
            'action': actions[i % len(actions)],
            'book': book,
            'date': (timezone.now() - timedelta(days=i*3)).strftime('%b %d, %Y'),
            'icon': icons[i % len(icons)],
            'color': colors[i % len(colors)],
            'status': statuses[i % len(statuses)],
            'status_color': status_colors[i % len(status_colors)],
            'category_color': category_colors[i % len(category_colors)]
        }
        recent_activities.append(activity)
    
    context = {
        'total_books': total_books,
        'books_added_recently': books_added_recently,
        'currently_reading': currently_reading,
        'books_completed': books_completed,
        'reading_percentage': reading_percentage,
        'completion_percentage': completion_percentage,
        'avg_rating': avg_rating,
        'total_reviews': total_reviews,
        'reading_progress_labels': json.dumps(months),
        'reading_progress_data': json.dumps(reading_progress_data),
        'category_labels': json.dumps(category_labels),
        'category_data': json.dumps(category_data),
        'acquisition_labels': json.dumps(months_list),
        'acquisition_data': json.dumps(acquisition_data),
        'author_labels': json.dumps(author_labels),
        'author_data': json.dumps(author_data),
        'recent_activities': recent_activities,
    }
    
    return render(request, 'reports.html', context)

@login_required
def update_profile(request):
    """Update user profile information"""
    if request.method == "POST":
        # Get user and profile
        user = request.user
        profile = get_object_or_404(Profile, user=user)
        
        # Update user information
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        
        # Update profile information
        profile.bio = request.POST.get('bio', '')
        profile.location = request.POST.get('location', '')
        
        # Handle date conversion safely
        birth_date_str = request.POST.get('birth_date', '')
        if birth_date_str:
            try:
                profile.birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass  # Invalid date format, ignore
        
        # Handle profile image
        if 'image' in request.FILES:
            profile.image = request.FILES['image']
        
        profile.save()
        
        messages.success(request, "Profile updated successfully!")
        return redirect('user_profile', username=user.username)
    
    # If not POST, redirect to profile page
    return redirect('user_profile', username=request.user.username)

@login_required
def update_preferences(request):
    """Update user reading preferences"""
    if request.method == "POST":
        user = request.user
        
        # Get or create UserPreferences object
        user_preferences, created = UserPreferences.objects.get_or_create(user=user)
        
        # Get selected categories and authors
        category_ids = request.POST.getlist('favorite_categories')
        author_ids = request.POST.getlist('favorite_authors')
        reading_goal = request.POST.get('reading_goal', 12)
        
        # Update reading goal
        user_preferences.reading_goal = int(reading_goal)
        user_preferences.save()
        
        # Clear existing selections and add new ones
        user_preferences.favorite_categories.clear()
        for category_id in category_ids:
            try:
                category = Category.objects.get(id=category_id)
                user_preferences.favorite_categories.add(category)
            except Category.DoesNotExist:
                continue
                
        user_preferences.favorite_authors.clear()
        for author_id in author_ids:
            try:
                author = Author.objects.get(id=author_id)
                user_preferences.favorite_authors.add(author)
            except Author.DoesNotExist:
                continue
        
        # Future ML recommendation data could be updated here
        # For example, calculating preferred genres based on selections
        
        messages.success(request, "Reading preferences updated successfully!")
        return redirect('user_profile', username=user.username)
    
    # If not POST, redirect to profile page
    return redirect('user_profile', username=request.user.username)