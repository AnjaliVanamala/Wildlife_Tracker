from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key"

# --- Database Setup ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sightings.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Database Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Sighting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(80), nullable=False)
    animal = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    day = db.Column(db.String(20), nullable=True)
    time = db.Column(db.String(10), nullable=True)
    number = db.Column(db.Integer, nullable=False)
    male_count = db.Column(db.Integer, nullable=True)
    female_count = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- Initialize DB ---
with app.app_context():
    db.create_all()

# --- Routes ---
@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash("Username already taken!", "error")
            return redirect(url_for('register'))

        # Create and store user
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password", "error")

    return render_template('login.html')


@app.route('/sighting', methods=['GET', 'POST'])
def sighting():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        animals = request.form.getlist('animal[]')
        locations = request.form.getlist('location[]')
        days = request.form.getlist('day[]')
        times = request.form.getlist('time[]')
        numbers = request.form.getlist('number[]')
        sex_breakdowns = request.form.getlist('sex_breakdown[]')
        males = request.form.getlist('male_count[]')
        females = request.form.getlist('female_count[]')

        total_rows = len(animals)

        # Normalize list lengths — missing values become ''
        def safe_get(lst, idx):
            return lst[idx] if idx < len(lst) else ''

        for i in range(total_rows):
            animal = animals[i]
            location = locations[i]
            day = days[i]
            time = times[i]
            number = int(numbers[i])

            # Get male/female safely
            male_val = safe_get(males, i)
            female_val = safe_get(females, i)

            male_count = int(male_val) if male_val else None
            female_count = int(female_val) if female_val else None

            sighting = Sighting(
                user=session['user'],
                animal=animal,
                location=location,
                day=day,
                time=time,
                number=number,
                male_count=male_count,
                female_count=female_count
            )

            db.session.add(sighting)

        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('sighting.html')


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    sightings = Sighting.query.filter_by(user=session['user']).order_by(Sighting.created_at.desc()).all()
    return render_template('dashboard.html', user=session['user'], sightings=sightings)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)
