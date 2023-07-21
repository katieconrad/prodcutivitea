from flask import Flask, render_template, request, flash, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from flask_bootstrap import Bootstrap
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_googlemaps import GoogleMaps, Map
from forms import FilterForm, AddForm, DeleteForm, LoginForm, RegisterForm, RateForm
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(32)

bootstrap = Bootstrap(app)

login_manager = LoginManager()
login_manager.init_app(app)

GoogleMaps(app)
app.config["GOOGLEMAPS_KEY"] = os.urandom(32)

# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Configure tables
Base = declarative_base()


class User(UserMixin, db.Model, Base):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    ratings = relationship("Rating", back_populates="rater")


class Cafe(db.Model, Base):
    __tablename__ = "cafes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    website = db.Column(db.String(500), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    ratings = relationship("Rating", back_populates="cafe")
    avg_rating = db.Column(db.Float)


class Rating(db.Model, Base):
    __tablename__ = "ratings"
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    rater_id = db.Column(db.Integer, ForeignKey("users.id"))
    rater = relationship("User", back_populates="ratings")
    cafe_id = db.Column(db.Integer, ForeignKey("cafes.id"))
    cafe = relationship("Cafe", back_populates="ratings")


with app.app_context():
    db.create_all()


# Convert boolean values
def convert_bool(form_var):
    if form_var == "y":
        return 1
    else:
        return 0


# Calculate average rating
def calculate_average(ratings_list):
    ratings_total = 0
    for item in ratings_list:
        ratings_total += item.rating
    num_ratings = len(ratings_list)
    average_rating = ratings_total / num_ratings
    return average_rating


# Create admin decorator
def admin_only(function):
    @wraps(function)
    @login_required
    def check_admin(*args, **kwargs):
        if current_user.id == 1:
            return function(*args, **kwargs)
        else:
            abort(403)
    return check_admin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# Server Routing
@app.route("/", methods=["GET", "POST"])
def home():
    """Renders home page"""
    # Apply filters
    if request.method == "POST":
        cafes = Cafe.query.order_by(Cafe.avg_rating.desc())
        filter_location = request.form["location"]
        cafes = cafes.filter_by(location=filter_location)
        filter_wifi = request.form.get("has_wifi", None)
        if filter_wifi == "y":
            filter_wifi = True
            cafes = cafes.filter_by(has_wifi=filter_wifi)
        filter_sockets = request.form.get("has_sockets", None)
        if filter_sockets == "y":
            filter_sockets = True
            cafes = cafes.filter_by(has_sockets=filter_sockets)
        filter_toilet = request.form.get("has_toilet", None)
        if filter_toilet == "y":
            filter_toilet = True
            cafes = cafes.filter_by(has_toilet=filter_toilet)
        cafes = cafes.all()
    else:
        cafes = Cafe.query.order_by(Cafe.avg_rating.desc()).all()

    # Markers list for map
    markers = [{"lat": cafe.latitude, "lng": cafe.longitude, "label": cafe.name} for cafe in cafes]

    return render_template("index.html", list=cafes, form=FilterForm(), markers=markers,
                           logged_in=current_user.is_authenticated)


@app.route('/register', methods=["GET", "POST"])
def register():
    """Renders registration page"""
    form = RegisterForm()
    if request.method == "POST":
        if form.validate_on_submit():
            email = request.form.get("email")
            user_exists = User.query.filter_by(email=email).first()
            if user_exists:
                flash("This user is already registered")
                return redirect(url_for("login", logged_in=current_user.is_authenticated))
            else:
                plain_text_password = request.form.get("password")
                username = request.form.get("username")
                secure_password = generate_password_hash(plain_text_password, method="pbkdf2:sha256", salt_length=8)
                new_user = User(email=email, username=username, password=secure_password)
                db.session.add(new_user)
                db.session.commit()

                login_user(new_user)

                return redirect(url_for("home", logged_in=current_user.is_authenticated))
    return render_template("register.html", form=form, logged_in=current_user.is_authenticated)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Renders login page"""
    form = LoginForm()

    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        if user is None:
            flash("This user is not registered.")
            return redirect(url_for("register", form=RegisterForm(), logged_in=current_user.is_authenticated))

        else:
            password_hash = user.password
            password_entered = request.form.get("password")
            password_correct = check_password_hash(pwhash=password_hash, password=password_entered)

            if not password_correct:
                flash("Your login credentials are incorrect.")
                return render_template("login.html", form=form, logged_in=current_user.is_authenticated)

            else:
                login_user(user)
                return redirect(url_for("home", logged_in=current_user.is_authenticated))

    return render_template("login.html", form=form, logged_in=current_user.is_authenticated)


@app.route("/add/", methods=["GET", "POST"])
@admin_only
def add_cafe():
    """Renders page where users can add a cafe"""
    # Get form fields
    if request.method == "POST":
        name = request.form.get("cafe_name")
        website = request.form.get("website")
        address = request.form.get("address")
        location = request.form.get("location")
        latitude = float(request.form.get("latitude"))
        longitude = float(request.form.get("longitude"))
        seats = request.form.get("seats")
        has_wifi = convert_bool(request.form.get("has_wifi"))
        has_sockets = convert_bool(request.form.get("has_sockets"))
        has_toilet = convert_bool(request.form.get("has_toilet"))
        tea_selection = int(request.form.get("tea_selection").split(" ")[0])

        # Return error if cafe is already in database
        current_cafe = name
        found_cafe = db.session.query(Cafe).filter_by(name=current_cafe).first()
        if found_cafe:
            flash("This cafe is already in our database.")
            return render_template("add.html", form=AddForm(), logged_in=current_user.is_authenticated)

        # Add cafe to database
        else:
            new_cafe = Cafe(
                name=name,
                website=website,
                address=address,
                location=location,
                latitude=latitude,
                longitude=longitude,
                seats=seats,
                has_toilet=has_toilet,
                has_wifi=has_wifi,
                has_sockets=has_sockets,
                avg_rating=tea_selection)
            db.session.add(new_cafe)
            new_rating = Rating(
                rating=tea_selection,
                rater=current_user,
                cafe=new_cafe)
            db.session.add(new_rating)
            db.session.commit()
            flash("Your cafe has been added to our database.")
            return redirect(url_for("home", logged_in=current_user.is_authenticated))

    else:
        return render_template("add.html", form=AddForm(), logged_in=current_user.is_authenticated)


@app.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_only
def edit(id):
    """renders a page where admin can edit a cafe"""
    if request.method == "POST":
        cafe = Cafe.query.filter_by(id=id).first()
        cafe.name = request.form.get("cafe_name")
        cafe.website = request.form.get("website")
        cafe.address = request.form.get("address")
        cafe.location = request.form.get("location")
        cafe.latitude = float(request.form.get("latitude"))
        cafe.longitude = float(request.form.get("longitude"))
        cafe.seats = request.form.get("seats")
        cafe.has_wifi = convert_bool(request.form.get("has_wifi"))
        cafe.has_sockets = convert_bool(request.form.get("has_sockets"))
        cafe.has_toilets = convert_bool(request.form.get("has_toilet"))

        # Calculate average rating
        cafe_rating = Rating.query.filter_by(cafe_id=cafe.id, rater_id=current_user.id).first()
        tea_selection = int(request.form.get("tea_selection").split(" ")[0])
        cafe_rating.rating = tea_selection
        all_ratings = Rating.query.filter_by(cafe_id=cafe.id).all()
        cafe.avg_rating = calculate_average(all_ratings)
        db.session.commit()
        return redirect(url_for("home", logged_in=current_user.is_authenticated))
    return render_template("edit.html", form=AddForm(), logged_in=current_user.is_authenticated)


@app.route("/delete/<int:id>", methods=["GET", "POST"])
@admin_only
def delete(id):
    """renders a page where admin can delete a cafe"""
    if request.method == "POST":
        if request.form.get("confirmation") == "y":
            cafe = Cafe.query.filter_by(id=id).first()
            db.session.delete(cafe)
            db.session.commit()
            flash("The cafe has been deleted from our database.")
            return redirect(url_for("home", logged_in=current_user.is_authenticated))
        else:
            flash("The cafe has not been deleted from our database.")
            return redirect(url_for("home", logged_in=current_user.is_authenticated))
    else:
        return render_template("delete.html", form=DeleteForm(), logged_in=current_user.is_authenticated)


@app.route("/rate/<int:id>", methods=["GET", "POST"])
def rate(id):
    cafe = Cafe.query.filter_by(id=id).first()
    if request.method == "POST":
        new_rating = int(request.form.get("rating").split(" ")[0])
        user_rating = Rating.query.filter_by(rater_id=current_user.id, cafe_id=cafe.id).first()
        if user_rating:
            flash(f"You had previously rated this cafe {user_rating.rating} stars. Your rating has been updated to "
                  f"{new_rating}.")
            user_rating.rating = new_rating
            all_ratings = Rating.query.filter_by(cafe_id=cafe.id).all()
            cafe.avg_rating = calculate_average(all_ratings)
            db.session.commit()
        else:
            flash(f"Your rating of {new_rating} stars has been logged.")
            new_rating_entry = Rating(rating=new_rating, rater_id=current_user.id, cafe_id=cafe.id)
            db.session.add(new_rating_entry)
            all_ratings = Rating.query.filter_by(cafe_id=cafe.id).all()
            cafe.avg_rating = calculate_average(all_ratings)
            db.session.commit()
        return render_template("rate.html", form=RateForm(), cafe=cafe, logged_in=current_user.is_authenticated)
    return render_template("rate.html", form=RateForm(), cafe=cafe, logged_in=current_user.is_authenticated)


@app.route('/logout')
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('home', logged_in=current_user.is_authenticated))


if __name__ == "__main__":
    app.run(debug=True)
