import os
import random
import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from reldemo.models import (
    Profile, ExpensesCategory, Expense, Author, Category, Book, 
    BorrowedBook, Review, BookStatus, UserPreferences
)
from django.db import transaction
from django.core.files import File
from django.conf import settings

class Command(BaseCommand):
    help = 'Generate dummy data for Read Wisely application'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=5, help='Number of users to create')
        parser.add_argument('--books', type=int, default=15, help='Number of books to create')
        parser.add_argument('--authors', type=int, default=10, help='Number of authors to create')
        parser.add_argument('--categories', type=int, default=8, help='Number of categories to create')
        parser.add_argument('--reviews', type=int, default=30, help='Number of reviews to create')
        parser.add_argument('--clear', action='store_true', help='Clear existing data before generating')

    def handle(self, *args, **options):
        if options['clear']:
            self.clear_data()
            self.stdout.write(self.style.SUCCESS('Cleared existing data'))

        try:
            with transaction.atomic():
                # Create data in the proper order to maintain relationships
                self.create_users(options['users'])
                self.create_expense_categories()
                self.create_categories(options['categories'])
                self.create_authors(options['authors'])
                self.create_books(options['books'])
                self.create_book_statuses()
                self.create_borrowed_books()
                self.create_reviews(options['reviews'])
                self.create_user_preferences()
                
            self.stdout.write(self.style.SUCCESS('Successfully generated dummy data'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error generating data: {str(e)}'))

    def clear_data(self):
        """Clear existing data from the database."""
        Review.objects.all().delete()
        BookStatus.objects.all().delete()
        BorrowedBook.objects.all().delete()
        Book.objects.all().delete()
        Author.objects.all().delete()
        Category.objects.all().delete()
        ExpensesCategory.objects.all().delete()
        Expense.objects.all().delete()
        UserPreferences.objects.all().delete()
        Profile.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()  # Keep superusers

    def create_users(self, count):
        """Create users with profiles."""
        self.stdout.write('Creating users...')
        existing_count = User.objects.count()
        
        # Create admin user if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpassword'
            )
            Profile.objects.create(
                user=admin_user,
                bio="Admin user for the Read Wisely application",
                location="Admin Office"
            )
            self.stdout.write(self.style.SUCCESS('Admin user created'))
        
        # Create regular users
        usernames = [f'user{i}' for i in range(existing_count + 1, existing_count + count + 1)]
        for username in usernames:
            user = User.objects.create_user(
                username=username,
                email=f'{username}@example.com',
                password='password123',
                first_name=random.choice(['John', 'Jane', 'Robert', 'Sarah', 'Michael', 'Emma']),
                last_name=random.choice(['Smith', 'Johnson', 'Williams', 'Jones', 'Brown', 'Davis']),
            )
            
            Profile.objects.create(
                user=user,
                bio=f"This is {user.first_name}'s profile bio. They love reading books.",
                birth_date=datetime.date(random.randint(1975, 2000), random.randint(1, 12), random.randint(1, 28)),
                location=random.choice(['New York', 'London', 'Paris', 'Tokyo', 'Berlin', 'Sydney'])
            )
        
        self.stdout.write(self.style.SUCCESS(f'Created {count} users'))

    def create_expense_categories(self):
        """Create expense categories."""
        self.stdout.write('Creating expense categories...')
        categories = [
            {'name': 'Books', 'description': 'Expenses related to book purchases'},
            {'name': 'Equipment', 'description': 'Equipment for reading and storing books'},
            {'name': 'Subscriptions', 'description': 'Subscriptions to reading services'},
            {'name': 'Events', 'description': 'Book events and fairs'},
            {'name': 'Shipping', 'description': 'Shipping costs for books'},
        ]
        
        for cat in categories:
            ExpensesCategory.objects.get_or_create(
                name=cat['name'],
                defaults={'description': cat['description']}
            )
            
            # Create some expenses for each category
            category = ExpensesCategory.objects.get(name=cat['name'])
            for _ in range(3):
                Expense.objects.create(
                    category=category,
                    amount=round(random.uniform(10, 100), 2),
                    date=timezone.now() - datetime.timedelta(days=random.randint(1, 90)),
                    description=f"Sample expense for {category.name}"
                )
        
        self.stdout.write(self.style.SUCCESS('Created expense categories and expenses'))

    def create_categories(self, count):
        """Create book categories."""
        self.stdout.write('Creating book categories...')
        categories = [
            'Fiction', 'Science Fiction', 'Mystery', 'Fantasy', 
            'Romance', 'Thriller', 'Horror', 'Biography', 
            'History', 'Science', 'Self-Help', 'Philosophy', 
            'Poetry', 'Children', 'Young Adult', 'Business'
        ]
        
        created_count = 0
        for cat in categories[:count]:
            _, created = Category.objects.get_or_create(
                name=cat,
                defaults={'slug': slugify(cat)}
            )
            if created:
                created_count += 1
                
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} book categories'))

    def create_authors(self, count):
        """Create book authors."""
        self.stdout.write('Creating authors...')
        
        first_names = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda', 
                       'William', 'Elizabeth', 'David', 'Susan', 'Richard', 'Jessica', 'Joseph', 'Sarah']
        last_names = ['Smith', 'Johnson', 'Williams', 'Jones', 'Brown', 'Davis', 'Miller', 'Wilson', 
                      'Moore', 'Taylor', 'Anderson', 'Thomas', 'Jackson', 'White', 'Harris', 'Martin']
        nationalities = ['American', 'British', 'Canadian', 'Australian', 'Irish', 'Indian', 'French', 'German']
        
        created_count = 0
        for _ in range(count):
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            
            if not Author.objects.filter(name=name).exists():
                birth_year = random.randint(1940, 1990)
                birth_month = random.randint(1, 12)
                birth_day = random.randint(1, 28)  # Avoiding potential issues with month lengths
                
                Author.objects.create(
                    name=name,
                    bio=f"{name} is a renowned author known for their compelling storytelling and unique perspective.",
                    birth_date=datetime.date(birth_year, birth_month, birth_day),
                    nationality=random.choice(nationalities)
                )
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} authors'))

    def create_books(self, count):
        """Create books with relationships to authors and categories."""
        self.stdout.write('Creating books...')
        
        # Use random titles and descriptions if specific ones aren't provided
        book_titles = [
            "The Silent Echo", "Midnight's Embrace", "Beyond the Horizon", "The Lost Key",
            "Whispers in the Dark", "The Final Chapter", "Echoes of Tomorrow", "The Hidden Path",
            "Shadows of the Past", "The Forgotten Gate", "Beneath the Surface", "The Secret Garden",
            "Dreams of Destiny", "The Last Voyage", "Chronicles of the Unknown", "The Immortal Quest",
            "Voices in the Wind", "The Enchanted Forest", "Legends of the Ancient", "The Broken Mirror"
        ]
        
        languages = ['English', 'Spanish', 'French', 'German', 'Chinese', 'Japanese', 'Russian']
        
        authors = list(Author.objects.all())
        categories = list(Category.objects.all())
        
        if not authors or not categories:
            self.stdout.write(self.style.ERROR('No authors or categories available to create books'))
            return
        
        created_count = 0
        
        for i in range(count):
            # Ensure unique title by appending a number if needed
            title_base = random.choice(book_titles)
            title = f"{title_base} {i+1}" if i >= len(book_titles) else title_base
            
            # Create a unique slug
            slug = slugify(title)
            
            # Generate a random date in the past 10 years
            year = timezone.now() - datetime.timedelta(days=random.randint(1, 3650))
            
            # Random ISBN (13 digits)
            isbn = ''.join([str(random.randint(0, 9)) for _ in range(13)])
            
            # Random page count
            page_count = random.randint(100, 800)
            
            # Create book
            book = Book.objects.create(
                title=title,
                slug=slug,
                year=year,
                isbn=isbn,
                story=f"This is the story of {title}. " + 
                      "It takes readers on a journey through imagination and discovery. " +
                      "The characters face numerous challenges and grow throughout the narrative.",
                page=page_count,
                available_copies=random.randint(1, 5),
                language=random.choice(languages),
                image_url=f"https://picsum.photos/id/{random.randint(1, 1000)}/200/300",
            )
            
            # Add random authors (1-3)
            num_authors = random.randint(1, min(3, len(authors)))
            for author in random.sample(authors, num_authors):
                book.author.add(author)
            
            # Add random categories (1-3)
            num_categories = random.randint(1, min(3, len(categories)))
            for category in random.sample(categories, num_categories):
                book.categories.add(category)
            
            created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} books'))

    def create_book_statuses(self):
        """Create book statuses for users."""
        self.stdout.write('Creating book statuses...')
        
        users = User.objects.all()
        books = Book.objects.all()
        
        if not users or not books:
            self.stdout.write(self.style.ERROR('No users or books available to create book statuses'))
            return
        
        status_choices = ['reading', 'read', 'to-read']
        statuses_created = 0
        
        # For each user, assign statuses to some books
        for user in users:
            # Select random books (30-70% of total books)
            num_books = random.randint(int(len(books) * 0.3), int(len(books) * 0.7))
            selected_books = random.sample(list(books), min(num_books, len(books)))
            
            for book in selected_books:
                status = random.choice(status_choices)
                
                # Avoid duplicate entries
                if not BookStatus.objects.filter(user=user, book=book).exists():
                    BookStatus.objects.create(
                        user=user,
                        book=book,
                        status=status
                    )
                    statuses_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {statuses_created} book statuses'))

    def create_borrowed_books(self):
        """Create borrowed books records."""
        self.stdout.write('Creating borrowed books records...')
        
        users = User.objects.all()
        books = Book.objects.filter(available_copies__gt=0)
        
        if not users or not books:
            self.stdout.write(self.style.ERROR('No users or available books for borrowing'))
            return
        
        borrowed_count = 0
        
        # For each user, borrow some books
        for user in users:
            # Borrow 1-3 books
            num_to_borrow = random.randint(1, 3)
            available_books = list(books.filter(available_copies__gt=0))
            
            if not available_books:
                continue
                
            selected_books = random.sample(available_books, min(num_to_borrow, len(available_books)))
            
            for book in selected_books:
                # Random borrow date in the past 30 days
                borrow_date = timezone.now() - datetime.timedelta(days=random.randint(1, 30))
                
                # Due date is 14 days after borrowing
                due_date = borrow_date + datetime.timedelta(days=14)
                
                # Some books should be returned, some still borrowed
                is_returned = random.choice([True, False])
                returned_date = None
                
                if is_returned:
                    # Return date between borrow date and now
                    days_until_return = random.randint(1, min(14, (timezone.now().date() - borrow_date.date()).days))
                    returned_date = borrow_date + datetime.timedelta(days=days_until_return)
                else:
                    # Reduce available copies for non-returned books
                    book.available_copies = max(0, book.available_copies - 1)
                    book.save()
                
                BorrowedBook.objects.create(
                    user=user,
                    book=book,
                    borrowed_date=borrow_date,
                    due_date=due_date,
                    returned_date=returned_date,
                    is_returned=is_returned
                )
                
                borrowed_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {borrowed_count} borrowed book records'))

    def create_reviews(self, count):
        """Create book reviews."""
        self.stdout.write('Creating reviews...')
        
        users = User.objects.all()
        # Get books that are marked as read
        read_book_statuses = BookStatus.objects.filter(status='read')
        books_read = [status.book for status in read_book_statuses]
        
        if not users or not books_read:
            self.stdout.write(self.style.ERROR('No users or read books available for reviews'))
            return
        
        review_count = 0
        review_texts = [
            "Absolutely loved this book! The character development was incredible.",
            "A decent read, but the plot was somewhat predictable.",
            "Couldn't put it down - the suspense kept me engaged throughout.",
            "Beautiful prose but the pacing was too slow for my taste.",
            "An instant classic. Will definitely read again.",
            "Interesting premise but the execution fell flat.",
            "The author's best work yet. Highly recommended.",
            "A disappointing follow-up to the author's previous work.",
            "The world-building in this book is exceptional.",
            "A perfect summer read - light and entertaining."
        ]
        
        # Create reviews
        for _ in range(min(count, len(books_read) * len(users))):
            # Get a random user who has read a book
            user = random.choice(users)
            
            # Get a book the user has read
            user_read_statuses = BookStatus.objects.filter(user=user, status='read')
            if not user_read_statuses.exists():
                continue
                
            book_status = random.choice(user_read_statuses)
            book = book_status.book
            
            # Check if user already reviewed this book
            if Review.objects.filter(user=user, book=book).exists():
                continue
            
            rating = random.randint(1, 5)
            comment = random.choice(review_texts)
            
            # Create review with a date after the book was added
            created_at = book.created_at + datetime.timedelta(days=random.randint(5, 90))
            
            Review.objects.create(
                book=book,
                user=user,
                rating=rating,
                comment=comment,
                created_at=created_at,
                updated_at=created_at
            )
            
            review_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {review_count} reviews'))

    def create_user_preferences(self):
        """Create user preferences."""
        self.stdout.write('Creating user preferences...')
        
        users = User.objects.all()
        categories = Category.objects.all()
        authors = Author.objects.all()
        
        if not users or not categories or not authors:
            self.stdout.write(self.style.ERROR('Missing users, categories, or authors for preferences'))
            return
        
        preferences_count = 0
        
        for user in users:
            # Skip if preferences already exist
            if UserPreferences.objects.filter(user=user).exists():
                continue
                
            # Create preferences
            preferences = UserPreferences.objects.create(
                user=user,
                reading_goal=random.randint(5, 50)
            )
            
            # Add favorite categories (2-5)
            num_categories = random.randint(2, min(5, categories.count()))
            for category in random.sample(list(categories), num_categories):
                preferences.favorite_categories.add(category)
            
            # Add favorite authors (1-3)
            num_authors = random.randint(1, min(3, authors.count()))
            for author in random.sample(list(authors), num_authors):
                preferences.favorite_authors.add(author)
            
            preferences_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {preferences_count} user preferences')) 