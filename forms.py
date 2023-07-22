from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, URLField, SelectField, BooleanField, PasswordField, EmailField
from wtforms.validators import DataRequired, URL

class FilterForm(FlaskForm):
    location = SelectField("Location", choices=["Downtown Halifax", "South End Halifax", "North End Halifax",
                                                "Dartmouth", "Clayton Park", "Spryfield", "Bedford", "Sackville"],
                           validators=[DataRequired()])
    has_wifi = BooleanField("Must have wifi")
    has_sockets = BooleanField("Must have sockets")
    has_toilet = BooleanField("Must have toilet")
    submit = SubmitField("Filter results")


class AddForm(FlaskForm):
    cafe_name = StringField("Name of Cafe:", validators=[DataRequired()])
    website = URLField("Cafe Website:", validators=[DataRequired(), URL()])
    address = StringField("Address:", validators=[DataRequired()])
    location = SelectField("Location",
                           choices=["Downtown Halifax", "South End Halifax", "North End Halifax", "Dartmouth",
                                    "Clayton Park", "Spryfield", "Bedford", "Sackville"],
                           validators=[DataRequired()])
    latitude = StringField("Latitude:", validators=[DataRequired()])
    longitude = StringField("Longitude:", validators=[DataRequired()])
    seats = SelectField("Number of Seats", choices=["0", "1-10", "11-20", "21+"], validators=[DataRequired()])
    has_wifi = BooleanField("Has wifi?")
    has_sockets = BooleanField("Has sockets?")
    has_toilet = BooleanField("Has toilet?")
    tea_selection = SelectField("Rate their tea selection",
                                choices=["1 star", "2 stars", "3 stars", "4 stars", "5 stars"],
                                validators=[DataRequired()])
    submit = SubmitField("Add cafe")


class DeleteForm(FlaskForm):
    confirmation = BooleanField("Delete this cafe?", validators=[DataRequired()])
    submit = SubmitField("Delete cafe")


class LoginForm(FlaskForm):
    email = EmailField("Email:", validators=[DataRequired()])
    password = PasswordField("Password:", validators=[DataRequired()])
    submit = SubmitField("Login")


class RegisterForm(FlaskForm):
    email = EmailField("Email:", validators=[DataRequired()])
    username = StringField("Username:", validators=[DataRequired()])
    password = PasswordField("Password:", validators=[DataRequired()])
    submit = SubmitField("Register")


class RateForm(FlaskForm):
    rating = SelectField("Rate this cafe's tea selection:",
                         choices=["1 star", "2 stars", "3 stars", "4 stars", "5 stars"],
                         validators=[DataRequired()])
    submit = SubmitField("Rate Cafe")
