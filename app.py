from flask import Flask, render_template, request, redirect, session, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DB ----------------
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Rakesh@2004",
        database="ipl_ticket"
    )

# ---------------- CREATE DEFAULT ADMIN ----------------
def create_admin():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM users WHERE email=%s", ("admin@gmail.com",))
    admin = cursor.fetchone()

    if not admin:
        cursor.execute(
            "INSERT INTO users(name,email,password,role) VALUES(%s,%s,%s,%s)",
            ("Admin", "admin@gmail.com", "admin123", "admin")
        )
        db.commit()

create_admin()

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('index.html')

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO users(name,email,password,role) VALUES(%s,%s,%s,%s)",
            (name, email, password, "user")
        )
        db.commit()

        flash("Registered Successfully!", "success")
        return redirect('/login')

    return render_template('register.html')

# ---------------- LOGIN (USER + ADMIN) ----------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )
        user = cursor.fetchone()

        if user:
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['role'] = user[4]

            flash("Login Successful!", "success")

            # 🔥 ROLE BASED REDIRECT
            if user[4] == "admin":
                return redirect('/admin/dashboard')
            else:
                return redirect('/dashboard')
        else:
            flash("Invalid Credentials", "danger")

    return render_template('login.html')

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ---------------- USER DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if session.get('role') != 'user':
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT m.team1, m.team2, m.stadium, b.seats, b.total_price
        FROM bookings b
        JOIN matches m ON b.match_id = m.id
        WHERE b.user_id = %s
    """, (session['user_id'],))

    bookings = cursor.fetchall()

    return render_template('user_dashboard.html', bookings=bookings)

# ---------------- MATCHES ----------------
@app.route('/matches')
def matches():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM matches")
    data = cursor.fetchall()

    return render_template('matches.html', matches=data)

# ---------------- BOOK ----------------
@app.route('/book/<int:id>', methods=['GET','POST'])
def book(id):
    if session.get('role') != 'user':
        flash("Login as user first!", "warning")
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    # Get match details
    cursor.execute("SELECT * FROM matches WHERE id=%s", (id,))
    match = cursor.fetchone()

    if request.method == 'POST':
        seats = int(request.form['seats'])
        food = request.form.getlist('food')  # multiple selection

        food_items = ", ".join(food) if food else "None"

        price = match[5]
        total = seats * price

        cursor.execute("""
            INSERT INTO bookings(user_id,match_id,seats,total_price,food)
            VALUES(%s,%s,%s,%s,%s)
        """, (session['user_id'], id, seats, total, food_items))
        db.commit()

        # Pass data to acknowledgement
        return render_template(
            'acknowledgement.html',
            match=match,
            seats=seats,
            total=total,
            food=food_items
        )
    
    

    return render_template('booking.html', match=match)
# =====================================================
# 👨‍💼 ADMIN SECTION (DATABASE BASED)
# =====================================================

# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM matches")
    matches = cursor.fetchall()

    return render_template('admin_dashboard.html', matches=matches)

# ---------------- ADD MATCH ----------------
@app.route('/add_match', methods=['POST'])
def add_match():
    if session.get('role') != 'admin':
        return redirect('/login')

    team1 = request.form['team1']
    team2 = request.form['team2']
    stadium = request.form['stadium']
    date = request.form['date']
    price = request.form['price']

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO matches(team1,team2,stadium,match_date,price) VALUES(%s,%s,%s,%s,%s)",
        (team1, team2, stadium, date, price)
    )
    db.commit()

    flash("Match Added!", "success")
    return redirect('/admin/dashboard')

# ---------------- DELETE MATCH ----------------
@app.route('/delete_match/<int:id>')
def delete_match(id):
    if session.get('role') != 'admin':
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("DELETE FROM matches WHERE id=%s", (id,))
    db.commit()

    return redirect('/admin/dashboard')

# =====================================================
# ---------------- STATIC PAGES ----------------
# =====================================================

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)