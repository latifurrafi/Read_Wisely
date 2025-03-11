from django import forms
from .models import Book, Author
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'year', 'isbn', 'story', 'pdf_file', 'page', 'image_url']  # Fields to be included in the form
        widgets = {
            'year': forms.DateInput(attrs={'type': 'date'}),  # Ensure the date input widget is applied
            'author': forms.CheckboxSelectMultiple(),  # Use a multiple select widget for the authors
        }
