from django.shortcuts import render, get_object_or_404
from reldemo.models import Category, Book, BookStatus
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import BookSerializer
from django.http import JsonResponse

def category_list_view(request):
    filter_type = request.GET.get('filter')  # Get filter from URL

    if filter_type == 'recent':
        books = Book.objects.order_by('-created_at')[:10]  # 10 most recent books
    else:
        books = Book.objects.all()

    category_data = Category.objects.all()

    return render(request, 'category_list.html', {
        'category_data': category_data,
        'books': books,  # Send books to template
        'filter_type': filter_type  # Optional: Send filter type for UI updates
    })

def books_by_category_view(request, category_slug):
    category_instance = get_object_or_404(Category, slug=category_slug)
    book_data = Book.objects.filter(categories=category_instance)
    category_data = Category.objects.all()
    return render(request, 'category_list.html', {
        'category_instance': category_instance,
        'book_data': book_data,
        'category_data': category_data
    })

def categories_wise_search(request, category_slug):
    query = request.GET.get('q', '')
    filters = request.GET.get('filter','')

    category_instance = get_object_or_404(Category, slug=category_slug)

    if filters:
        books = Book.objects.all().order_by('-id')
    else:
        # Make sure to use the same field name as in books_by_category_view
        books = Book.objects.filter(categories=category_instance)
    
    if query:
        books = books.filter(title__icontains=query)
    
    category_data = Category.objects.all()
    
    return render(request, 'category_list.html', {
        'category_instance': category_instance,
        'book_data': books,  # Use the same variable name as in books_by_category_view
        'category_data': category_data,
        'query': query
    })

def recent_books_view(request):
    books = Book.objects.all().order_by('-created_at')[:10]  # Get 10 most recent books
    context = {
        'books': books,
        'title': 'Recently Added Books'
    }
    return render(request, 'recent_book.html', context)  # Use a separate template for clarity

@api_view(['GET'])
def recent_book_for_category_list(request):
    books = Book.objects.all().order_by('-created_at')[:10]
    serializer = BookSerializer(books, many=True)
    return Response(serializer.data)

def update_book_status(request, book_id, status):

    book = get_object_or_404(Book, id=book_id)
    book_status, created = BookStatus.objects.get_or_create(user=request.user, book=book)
    book_status.status = status
    book_status.save()

    return JsonResponse({"messages": "Status Updated", "status": status})
