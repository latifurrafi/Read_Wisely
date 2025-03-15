from django import forms
from .models import Book, Author, Category
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Review


# User Registration Form
class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class BookForm(forms.ModelForm):
    author = forms.ModelMultipleChoiceField(
        queryset=Author.objects.all(),  # Fetch all authors
        widget=forms.CheckboxSelectMultiple,  # Allow multiple selections
        required=False  # Ensure an author is selected
    )
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # Change widget if needed
        required=False  # Make optional if desired
    )
    year = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'border p-2 rounded w-full'  # Add Tailwind classes
        })
    )
    language = forms.CharField(
    widget=forms.TextInput(attrs={
        'type': 'text',
        'class': 'border p-2 rounded w-full',  # Tailwind styles
        'placeholder': 'Enter language'  # Optional placeholder
    })
)

    

    class Meta:
        model = Book
        fields = ['title', 'author', 'year', 'isbn', 'story', 'pdf_file', 'page', 'image', 'image_url', 'available_copies', 'categories' , 'language']
        widgets = {
            'image_url': forms.TextInput(attrs={'class': 'border p-2 rounded w-full', 'placeholder': 'Paste image URL'}),
            'image': forms.ClearableFileInput(attrs={'class': 'border p-2 rounded w-full'}),
            'year': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'story': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Enter book description...',
                'class': 'form-control'
            }),
            'page': forms.NumberInput(attrs={
                'min': 1,
                'class': 'form-control'
            }),
            'isbn': forms.TextInput(attrs={
                'placeholder': 'Enter ISBN...',
                'class': 'form-control'
            }),
            'pdf_file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'image_url': forms.URLInput(attrs={
                'placeholder': 'Enter cover image URL...',
                'class': 'form-control'
            }),
            'available_copies': forms.NumberInput(attrs={
                'placeholder': 'Enter available copies...',
                'class': 'form-control'
            }),
            # 'categories': forms.TextInput(attrs={
            #     'placeholder': 'Enter categories of book...',
            #     'class': 'form-control'
            # }),
            'language': forms.TextInput(attrs={
                'placeholder': 'Enter language...',
                'class': 'form-control'
            }),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']