import os
from flask import Flask, abort, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from pathlib import Path
from sqlalchemy.exc import IntegrityError

BASE_DIR = Path(__file__).parent

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("://", "ql://", 1) if os.environ.get(
    'DATABASE_URL') else None \
                         or f"sqlite:///{BASE_DIR / 'main.db'}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class AuthorModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    surname = db.Column(db.String(64), nullable=False, server_default="Иванов")
    quotes = db.relationship('QuoteModel', backref='author', lazy='dynamic', cascade="all, delete-orphan")

    def __init__(self, name, surname):
        self.name = name
        self.surname = surname

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "surname": self.surname,
        }


class QuoteModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey(AuthorModel.id))
    text = db.Column(db.String(255), unique=False)

    def __init__(self, author, text):
        self.author_id = author.id
        self.text = text

    def to_dict(self):
        return {
            "id": self.id,
            "author": self.author.to_dict(),
            "text": self.text
        }


@app.errorhandler(404)
def not_found(e):
    response = {'status': 404, 'error': e.description}
    return response, 404


def get_object_or_404(model: db.Model, object_id):
    object = model.query.get(object_id)
    if object is None:
        abort(404, description=f"Author with id={object_id} not found")
    return object


# Resource: Author
@app.route("/authors")
def get_authors():
    authors = AuthorModel.query.all()
    authors_dict = []
    for author in authors:
        authors_dict.append(author.to_dict())
    return authors_dict


@app.route("/authors/<int:author_id>")
def get_author_by_id(author_id):
    author = get_object_or_404(AuthorModel, author_id)
    print("!!!")
    return author.to_dict(), 200


@app.route("/authors", methods=["POST"])
def create_author():
    author_data = request.json
    # author = AuthorModel(author_data["name"], author_data["surname"], ...)
    author = AuthorModel(**author_data)
    db.session.add(author)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return f"Author name must be unique", 400
    return author.to_dict(), 201


# Resource: Quote
@app.route("/quotes")
def get_all_quotes():
    quotes = QuoteModel.query.all()
    quotes_dict = []
    for quote in quotes:
        quotes_dict.append(quote.to_dict())
    return quotes_dict


@app.route("/quotes/<int:id>")
def get_quote(id):
    quote = QuoteModel.query.get(id)
    if quote is None:
        return {"error": f"Quote with id={id} not found"}, 404
    return quote.to_dict(), 200


@app.route("/authors/<int:author_id>/quotes", methods=["POST"])
def create_quote(author_id):
    author = AuthorModel.query.get(author_id)
    if author is None:
        return {"error": f"Author with id={id} not found"}, 404
    new_quote = request.json
    q = QuoteModel(author, new_quote["text"])
    db.session.add(q)
    db.session.commit()
    return q.to_dict(), 201


@app.route("/quotes/<int:id>", methods=['PUT'])
def edit_quote(id):
    quote_data = request.json
    quote = QuoteModel.query.get(id)
    if quote is None:
        return {"error": f"Quote with id={id} not found"}, 404
    for key, value in quote_data.items():
        setattr(quote, key, value)
    db.session.commit()
    return quote.to_dict(), 200


@app.route("/quotes/<int:id>", methods=['DELETE'])
def delete(id):
    quote = QuoteModel.query.get(id)
    if quote is None:
        return {"error": f"Quote with id={id} not found"}, 404
    db.session.delete(quote)
    db.session.commit()
    return {"message": f"Quote with id={id} deleted"}, 200


if __name__ == "__main__":
    app.run(debug=True)
