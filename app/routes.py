from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .models import Favorite, db, User, Book, Borrow
from datetime import datetime
from flask_wtf.csrf import CSRFProtect
from werkzeug.exceptions import abort
import random

main = Blueprint('main', __name__)
csrf = CSRFProtect()

# Main Page
@main.route('/')
def home():
    if 'user_id' not in session:
        flash('Please log in to view your library.', 'warning')
        return redirect(url_for('main.login'))
    
    user_id = session['user_id']

    # Kullanıcının kitaplarını çek
    books = Book.query.filter_by(user_id=user_id)

    # Arama ve filtreleme parametrelerini al
    search_query = request.args.get("search", "").strip()
    category_filter = request.args.get("category", "")
    favorites_only = request.args.get("favorites", False)

    # Arama sorgusu varsa, başlık veya yazar içinde arama yap
    if search_query:
        books = books.filter(
            (Book.title.ilike(f"%{search_query}%")) | (Book.author.ilike(f"%{search_query}%"))
        )

    # Kategoriye göre filtreleme
    if category_filter:
        books = books.filter_by(category=category_filter)

    # Sadece favorilere eklenen kitapları listeleme
    if favorites_only:
        books = books.join(Favorite).filter(Favorite.user_id == user_id)

    books = books.all()

    # Rastgele öne çıkan kitap seç
    featured_book = random.choice(books) if books else None

    return render_template('index.html', books=books, featured_book=featured_book)


# Add Book
@main.route('/add-book', methods=['GET', 'POST'])
def add_book():
    if 'user_id' not in session:
        flash('You must be logged in to add a book.', 'danger')
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        try:
            title = request.form.get('title')
            author = request.form.get('author')
            published_year = request.form.get('published_year')
            isbn = request.form.get('isbn')
            category = request.form.get('category')
            status = request.form.get('status')
            format = request.form.get('format')

            new_book = Book(
                title=title,
                author=author,
                published_year=int(published_year),
                isbn=isbn,
                category=category,
                status=status,
                format=format,
                user_id=session['user_id']
            )
            db.session.add(new_book)
            db.session.commit()
            flash('Book added successfully!', 'success')
            return redirect(url_for('main.home'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while adding the book: {e}', 'danger')

    return render_template('add_book.html')

# Edit Book
@main.route('/edit-book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    if book.user_id != session['user_id']:
        flash('You are not authorized to edit this book.', 'danger')
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        try:
            book.title = request.form.get('title')
            book.author = request.form.get('author')
            book.published_year = int(request.form.get('published_year'))
            book.isbn = request.form.get('isbn')
            book.category = request.form.get('category')
            book.status = request.form.get('status')
            book.format = request.form.get('format')

            db.session.commit()
            flash('Book updated successfully!', 'success')
            return redirect(url_for('main.home'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while updating the book: {e}', 'danger')

    return render_template('edit_book.html', book=book)

# Kitap silme
@main.route('/delete-book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    if book.user_id != session['user_id']:
        flash('You are not authorized to delete this book.', 'danger')
        return redirect(url_for('main.home'))

    try:
        db.session.delete(book)
        db.session.commit()
        flash('Book deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while deleting the book: {e}', 'danger')

    return redirect(url_for('main.home'))

# User Register
@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            name = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')

            if not name or not email or not password:
                flash('All fields are required!', 'warning')
                return redirect(url_for('main.register'))

            if User.query.filter_by(email=email).first():
                flash('Email is already registered!', 'danger')
                return redirect(url_for('main.register'))

            hashed_password = User.hash_password(password)
            new_user = User(name=name, email=email, password_hash=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            session['user'] = name
            session['user_id'] = new_user.id
            flash('Registration successful! Welcome!', 'success')
            return redirect(url_for('main.home'))

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration: {e}', 'danger')

    return render_template('register.html')

# User Login
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')

            if not email or not password:
                flash('Email and password are required!', 'danger')
                return redirect(url_for('main.login'))

            user = User.query.filter_by(email=email).first()
            if not user:
                flash('No user found with this email!', 'danger')
                return redirect(url_for('main.login'))

            if not user.check_password(password):
                flash('Incorrect password!', 'danger')
                return redirect(url_for('main.login'))

            # Start user session
            session['user'] = user.name
            session['user_id'] = user.id
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('main.home'))  # Redirect to home page
        except Exception as e:
            flash(f'An error occurred: {e}', 'danger')
            return redirect(url_for('main.login'))

    return render_template('login.html')

# User Logout
@main.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))


@main.route('/add_favorite/<int:book_id>', methods=['POST'])
def add_favorite(book_id):
    if 'user_id' not in session:
        flash('Please log in to add favorites.', 'warning')
        return redirect(url_for('main.login'))

    user_id = session['user_id']
    existing_favorite = Favorite.query.filter_by(user_id=user_id, book_id=book_id).first()

    if not existing_favorite:
        new_favorite = Favorite(user_id=user_id, book_id=book_id)
        db.session.add(new_favorite)
        db.session.commit()

    return redirect(request.referrer or url_for('main.home'))



@main.route('/remove-favorite/<int:book_id>', methods=['POST'])
def remove_favorite(book_id):
    if 'user_id' not in session:
        flash('You need to be logged in to perform this action.', 'danger')
        return redirect(url_for('main.login'))

    user_id = session['user_id']
    favorite = Favorite.query.filter_by(user_id=user_id, book_id=book_id).first()

    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        flash('Book removed from your favorites.', 'success')
    else:
        flash('Book not found in your favorites.', 'warning')

    return redirect(request.referrer or url_for('main.favorites'))


@main.route('/favorites')
def favorites():
    if 'user_id' not in session:
        flash('Please log in to view your favorites.', 'warning')
        return redirect(url_for('main.login'))

    user_id = session['user_id']
    favorite_books = db.session.query(Book).join(Favorite).filter(Favorite.user_id == user_id).all()

    return render_template('favorites.html', favorite_books=favorite_books)


@main.route('/toggle_favorite/<int:book_id>', methods=['POST'])
def toggle_favorite(book_id):
    favorite = Favorite.query.filter_by(user_id=session['user_id'], book_id=book_id).first()
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        flash('Removed from Favorites', 'warning')
    else:
        new_favorite = Favorite(user_id=session['user_id'], book_id=book_id)
        db.session.add(new_favorite)
        db.session.commit()
        flash('Added to Favorites', 'success')
    
    return redirect(url_for('main.home'))

@main.route('/book/<int:book_id>', methods=['GET', 'POST'])
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)

    if request.method == 'POST':
        try:
            note = request.form.get('note')  
            book.notes = note  
            db.session.commit()
            flash('Note saved successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {e}', 'danger')

    return render_template('book_detail.html', book=book)



@main.route('/toggle_status/<int:book_id>', methods=['POST'])
def toggle_status(book_id):
    if 'user_id' not in session:
        flash('You need to be logged in to perform this action.', 'danger')
        return redirect(url_for('main.login'))

    book = Book.query.get_or_404(book_id)

    if book.user_id != session['user_id']:
        flash('You are not authorized to modify this book.', 'danger')
        return redirect(url_for('main.home'))


    if book.status == 'Read':
        book.status = 'Unread'
    else:
        book.status = 'Read'

    db.session.commit()
    flash('Book status updated successfully!', 'success')
    return redirect(url_for('main.home'))

@main.route('/edit-notes/<int:book_id>', methods=['POST'])
def edit_notes(book_id):
    if 'user_id' not in session:
        flash('You need to be logged in to edit notes.', 'danger')
        return redirect(url_for('main.login'))

    book = Book.query.get_or_404(book_id)

    if book.user_id != session['user_id']:
        flash('You are not authorized to edit this book\'s notes.', 'danger')
        return redirect(url_for('main.home'))

    try:
        notes = request.form.get('notes') 
        book.notes = notes 
        db.session.commit()
        flash('Notes updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {e}', 'danger')

    return redirect(url_for('main.book_detail', book_id=book_id))
