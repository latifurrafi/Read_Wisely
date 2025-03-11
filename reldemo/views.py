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

def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
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
            return redirect("homepage")
        else:
            messages.error(request, "Invalid username or password")
    return render(request, "login.html")

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect("login")


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

def homepage(request):
    books = Book.objects.all()

    return render(request, 'book_list.html', {'books': books}) 

@login_required
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('homepage')

    else:
        form = BookForm()

    return render(request, 'add_book.html', {'form': form})

def update_book(request, book_id):
    book = Book.objects.get(id=book_id)
    if request.method == POST:
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            return redirect('homepage')

    else:
        form = BookForm(instance=book)

    return render(request, 'update_book.html', {'form': form, 'book': book})

def delete_book(request, book_id):
    book = Book.objects.get(id=book_id)
    if book:
        book.delete()

    return redirect('homepage')

def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    print("PDF URL:", book.pdf_file.url if book.pdf_file else "No PDF")
    return render(request, 'book_detail.html', {'book': book})


