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
from .models import BorrowedBook  # Assuming you have a model for borrowed books
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
import csv
from .models import Book, BorrowedBook, Category
from .models import Book, Review
from .forms import ReviewForm
from django.views.decorators.http import require_http_methods
import json
import logging
import traceback
from django.db.models import Count
from datetime import datetime, timedelta
from django.db.models.functions import TruncMonth



def user_profile(request, username):
    # Fetch the user object
    user = get_object_or_404(User, username=username)
    # Fetch the associated profile
    profile = get_object_or_404(Profile, user=user)
    # Render the profile to a template
    return render(request, 'profile_details.html', {'Profile': profile})

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
    # print(labels)
    # print('----------------------------------------------------------------------')
    # print(data)
    return render(request, 'dashboard.html', {
        'books': Book.objects.all(),
        'labels': json.dumps(labels), 
        'data': json.dumps(data), 
        'labelss': json.dumps(labelss),
        'dataa': json.dumps(dataa),
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
