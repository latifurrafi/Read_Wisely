
from rest_framework import serializers
from reldemo.models import Book

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'  # Include all fields or specify needed ones
