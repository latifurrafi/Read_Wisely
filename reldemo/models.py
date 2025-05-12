from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.timezone import now  # Import 'now' correctly
from django.db.models import Count
from django.db.models import Q
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from .validators import validate_file_size

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    image = models.ImageField(upload_to='book_images/', default='book_images/default.jpg',blank=True, null=True)
    birth_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.username


class ExpensesCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name


class Expense(models.Model):
    category = models.ForeignKey(ExpensesCategory, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.amount} for {self.category.name}"


class Author(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)  # Allow NULL values
    nationality = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ManyToManyField(Author)
    slug = models.SlugField(max_length=200, unique=True, blank=True, null=True)
    year = models.DateField()
    isbn = models.CharField(max_length=13)
    story = models.TextField()
    page = models.IntegerField()
    image = models.ImageField(
        upload_to='book_images/',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif']),
            validate_file_size
        ]
    )
    image_url = models.URLField(max_length=500, blank=True, null=True)
    pdf_file = models.FileField(
        upload_to='books_pdfs/',
        default='default.pdf',
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf']),
            validate_file_size
        ]
    )
    available_copies = models.IntegerField(default=1)
    categories = models.ManyToManyField(Category, related_name='books')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    language = models.CharField(max_length=30)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['isbn']),
            models.Index(fields=['created_at']),
        ]

    def clean(self):
        if self.available_copies < 0:
            raise ValidationError('Available copies cannot be negative.')
        if not self.slug:
            self.slug = slugify(self.title)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Clean up files when deleting the book
        if self.image:
            self.image.delete(save=False)
        if self.pdf_file:
            self.pdf_file.delete(save=False)
        super().delete(*args, **kwargs)

    def get_related_books(self, limit=3):
        # Optimize query by using prefetch_related and annotate to sort by relevance
        return Book.objects.prefetch_related('categories', 'author').filter(
            categories__in=self.categories.all()
        ).exclude(id=self.id).annotate(
            common_categories=Count('categories', filter=Q(categories__in=self.categories.all()))
        ).order_by('-common_categories', '-created_at')[:limit]

    def __str__(self):
        return self.title

class BorrowedBook(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrowed_books', default=1)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrowing_records', default=1)  # Change 1 to an existing book ID
    borrowed_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    returned_date = models.DateField(null=True, blank=True)
    is_returned = models.BooleanField(default=False)

    
    @property
    def is_overdue(self):
        if not self.is_returned and self.due_date < timezone.now().date():
            return True
        return False
    
    @property
    def is_due_soon(self):
        if not self.is_returned and not self.is_overdue:
            days_until_due = (self.due_date - timezone.now().date()).days
            return days_until_due <= 7
        return False
    
    def __str__(self):
        return f"{self.book.title} borrowed by {self.user.username}"
        

class Review(models.Model):
    book = models.ForeignKey('Book', on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('book', 'user')  # Each user can only review a book once
        
    def __str__(self):
        return f"{self.user.username}'s review of {self.book.title}"


class BookStatus(models.Model):
    STATUS_CHOICES = [
        ('reading', 'Currently Reading'),
        ('read', 'Finished Reading'),
        ('to-read', 'Want to Read'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='to-read')

    class Meta:
        unique_together = ('user', 'book')

    def __str__(self):
        return f"{self.user.username} - {self.book.title} - {self.status}"


class UserPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    favorite_categories = models.ManyToManyField(Category, blank=True, related_name='favorited_by')
    favorite_authors = models.ManyToManyField(Author, blank=True, related_name='favorited_by')
    reading_goal = models.PositiveIntegerField(default=12)
    
    # Fields for ML recommendations
    preferred_genres = models.TextField(blank=True, help_text="JSON data of preferred genres with weights")
    recommendation_history = models.TextField(blank=True, help_text="JSON data of recommendation history")
    
    def __str__(self):
        return f"{self.user.username}'s Preferences"
    
    def get_top_categories(self, limit=5):
        """Get user's top categories for recommendations"""
        return self.favorite_categories.all()[:limit]
    
    def get_top_authors(self, limit=5):
        """Get user's top authors for recommendations"""
        return self.favorite_authors.all()[:limit]
