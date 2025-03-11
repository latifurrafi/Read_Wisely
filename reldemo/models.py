from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    # picture = models.ImageField(upload_to="avatars/", null=True, blank=True)
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

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ManyToManyField(Author, related_name='books')
    year = models.DateField()
    isbn = models.CharField(max_length=13)
    story = models.TextField()
    page = models.CharField(max_length=10)
    image_url = models.URLField(max_length=500, blank=True, null=True)  # New field for image URL
    pdf_file = models.FileField(upload_to='books_pdfs/', null=True, blank=True)

    def __str__(self):
        return self.title
