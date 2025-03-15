from django.shortcuts import render, get_object_or_404
from reldemo.models import Category, Book

def category_list_view(request):
    category_data = Category.objects.all()
    return render(request, 'category_list.html', {'category_data': category_data})

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
