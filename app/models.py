from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    published_year = db.Column(db.Integer, nullable=False)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    available = db.Column(db.Boolean, default=True)
    category = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='Unread')  # 'Read', 'Reading', 'Unread'
    description = db.Column(db.Text, nullable=True)  # Açıklama alanı
    notes = db.Column(db.Text, nullable=True)  # Notlar alanı
    archived = db.Column(db.Boolean, default=False)
    format = db.Column(db.String(20), nullable=False)  # 'E-book', 'Physical'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Kullanıcı ile ilişkilendirme
    
    owner = db.relationship('User', backref='books', lazy=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    @staticmethod
    def hash_password(password):
        return generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Borrow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    borrow_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime, nullable=True)
    returned = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref='borrows', lazy=True)
    book = db.relationship('Book', backref='borrows', lazy=True)

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user = db.relationship('User', backref='favorites', lazy=True)
    book = db.relationship('Book', backref='favorites', lazy=True)

