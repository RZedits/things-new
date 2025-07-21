import os
from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_ckeditor import CKEditor, CKEditorField
from sqlalchemy import Integer, String, Date, Text, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import date
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField,DateField, SubmitField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditorField

class Base(DeclarativeBase):
    pass

app = Flask(__name__, instance_relative_config=True)  # Enable instance folder

# Ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass  # Already exists

# Define DB path relative to instance folder for better portability
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
db_path = os.path.join(app.instance_path, "atn.db")
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:kiHkUijdnyVTkGfzNYOIItXmIfCYeqgU@postgres.railway.internal:5432/railway"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Optional: Disable modification tracking

"""initialize app extensions"""
db= SQLAlchemy(model_class=Base)
ckeditor = CKEditor()
db.init_app(app)
ckeditor.init_app(app)

class Articles(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author: Mapped[str] = mapped_column(String(250), nullable=False)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    sub_title: Mapped[str] = mapped_column(String(250), nullable=False)
    post_photo: Mapped[str] = mapped_column(String(250), nullable=True)
    author_url: Mapped[str] = mapped_column(String(250), nullable=True)
    day: Mapped[date] = mapped_column(Date, nullable=False)
    body: Mapped[str] = mapped_column(String(25000), nullable=False)

    def to_dict(self):
        return {
           "id": self.id,
            "author": self.author,
            "title": self.title,
            "sub_title": self.sub_title,
            "post_photo": self.post_photo,
            "author_url": self.author_url,
            "day": self.day,
            "body": self.body
        }
with app.app_context():
    db.drop_all()
    db.create_all()
# WTForm for new article
class Article(FlaskForm):
    author = StringField("Author's name", validators=[DataRequired()])
    title = StringField("Post title", validators=[DataRequired()])
    sub_title= StringField("Post sub-title", validators=[DataRequired()])
    post_photo = StringField("Photo url", validators=[DataRequired()])
    author_url = StringField("Author url", validators=[DataRequired()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    day = DateField("Date", validators=[DataRequired()])
    submit = SubmitField("Submit")


@app.route("/", methods= ["GET", "POST"])
def home():
    return render_template("index.html")

@app.route("/bulls")
def bulls():
    return render_template("bulls.html")

@app.route("/create_article", methods = ["GET", "POST"])
def create_article():
    form = Article()
    if form.validate_on_submit():
        new_article = Articles(
            author=form.author.data,
            title = form.title.data,
            sub_title= form.sub_title.data,
            post_photo= form.post_photo.data,
            author_url = form.author_url.data,
            day= form.day.data,
            body = form.body.data
        )
        db.session.add(new_article)
        db.session.commit()
        return redirect(url_for("main.all_articles"))
    return render_template("create_article.html", form= form)

@app.route("/all_articles")
def all_articles():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page

    articles = Articles.query.order_by(Articles.day.desc()).offset(offset).limit(per_page).all()
    sorted_articles= [article.to_dict() for article in articles ]

    has_more = Articles.query.count() > offset + per_page

    return render_template("all_articles.html",articles=sorted_articles, page= page, has_more= has_more)

@app.route("/article/<int:article_id>")
def article(article_id):
    post= db.session.execute(db.select(Articles).where(Articles.id == article_id )).scalar()
    selected_post= post.to_dict()
    return render_template("article.html", post = selected_post)

@app.route("/podcasts")
def podcasts():
    return render_template("podcast.html")

"""Routes for the diffrent categories of videos"""
@app.route("/kingdom_videos")
def kingdom_videos():
    return render_template("kingdom_videos.html")

""" Healing streams route"""
@app.route("/anointing_streams")
def anointing_streams():
    return render_template("anointing_streams.html")

if __name__ == '__main__':
    app.run(debug=True)