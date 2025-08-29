import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_ckeditor import CKEditor, CKEditorField
from sqlalchemy import Integer, String, Date, Text, Float, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import date
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField,DateField, SubmitField
from wtforms.validators import DataRequired, EqualTo
from flask_ckeditor import CKEditorField
from werkzeug.security import  generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, login_manager, login_required, logout_user,current_user, LoginManager

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
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Optional: Disable modification tracking

"""Login Manager setup"""
login_manager= LoginManager()
login_manager.init_app(app)
login_manager.login_view= "login"

"""initialize app extensions"""
db= SQLAlchemy(model_class=Base)
ckeditor = CKEditor()
db.init_app(app)
ckeditor.init_app(app)

class Articles(db.Model):
    __tablename__ = "articles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author: Mapped[str] = mapped_column(String(250), nullable=False)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    sub_title: Mapped[str] = mapped_column(String(250), nullable=False)
    post_photo: Mapped[str] = mapped_column(String(250), nullable=True)
    author_url: Mapped[str] = mapped_column(String(250), nullable=True)
    day: Mapped[date] = mapped_column(Date, nullable=False)
    body: Mapped[str] = mapped_column(String(25000), nullable=False)

    comments = relationship("Comments", back_populates="article")
    likes = relationship("Likes", back_populates="article")

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

class Users(UserMixin,db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phone_number: Mapped[int] = mapped_column(Integer, unique=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)

    comments = relationship("Comments", back_populates="user")
    likes = relationship("Likes", back_populates="user")

class Comments(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), nullable=False)
    comment_text: Mapped[str] = mapped_column(String(1000), nullable=False)

    user = relationship("Users", back_populates="comments")
    article = relationship("Articles", back_populates="comments")

class Likes(db.Model):
    __tablename__ = "likes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), nullable=False)

    user = relationship("Users", back_populates="likes")
    article = relationship("Articles", back_populates="likes")

#TODO comment out the lines below during production
with app.app_context():
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

# Create a form to register new users
class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    phone_number = StringField("Phone Number", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(),
        EqualTo('password', message="Passwords must match.")
    ])
    submit = SubmitField("Sign Me Up!")


# Create a form to login existing users
class Login(FlaskForm):
    phone_number= StringField("Phone Number", validators= [DataRequired()])
    password= PasswordField("Password", validators=[DataRequired()])
    login= SubmitField("Let me in!")

"""user loader"""
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(Users, user_id)

@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if user email is already present in the database.
        result = db.session.execute(db.select(Users).where(Users.phone_number == form.phone_number.data))
        user = result.scalar()
        if user:
            # User already exists
            flash("You've already signed up with that phone number, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = Users(
            phone_number=form.phone_number.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        print(new_user.phone_number)
        db.session.add(new_user)
        db.session.commit()
        # This line will authenticate the user with Flask-Login

        return  redirect(url_for('home'))
    return render_template("register.html", form=form)

@app.route("/login", methods= ["POST", "GET"])
def login():
    form= Login()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(Users).where(Users.phone_number == form.phone_number.data))

        # Note, phone_no in db is unique so will only have one result.
        user = result.scalar()
        # Phone_no doesn't exist
        if not user:
            flash("That phone number does not exist, please try again.")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            print(current_user.name)
            return  redirect(url_for('home'))

    return render_template("login.html", form= form)

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
        return redirect(url_for("all_articles"))
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