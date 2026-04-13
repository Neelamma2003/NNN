from flask import Flask, request, redirect, render_template
import sqlite3
import random, string
import datetime

app = Flask(__name__)

# =========================
# DATABASE CONNECTION
# =========================
def get_db():
    return sqlite3.connect("database.db")


# =========================
# CREATE TABLE (RUN ON START)
# =========================
def init_db():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS urls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        long_url TEXT,
        short_code TEXT,
        clicks INTEGER DEFAULT 0,
        expiry TEXT
    )''')
    db.commit()

init_db()


# =========================
# GENERATE SHORT CODE
# =========================
def generate_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))


# =========================
# HOME PAGE
# =========================
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        long_url = request.form['url']
        expiry = request.form['expiry']

        short_code = generate_code()

        db = get_db()
        db.execute("INSERT INTO urls (long_url, short_code, expiry) VALUES (?, ?, ?)",
                   (long_url, short_code, expiry))
        db.commit()

        return render_template('index.html', short=short_code)

    return render_template('index.html')


# =========================
# REDIRECT SHORT URL
# =========================
@app.route('/<code>')
def redirect_url(code):
    db = get_db()
    data = db.execute(
        "SELECT long_url, clicks, expiry FROM urls WHERE short_code=?",
        (code,)
    ).fetchone()

    if data:
        long_url = data[0]
        clicks = data[1]
        expiry = data[2]

        # CHECK EXPIRY
        if expiry:
            try:
                if datetime.datetime.now() > datetime.datetime.fromisoformat(expiry):
                    return "<h2 style='color:red;text-align:center;'>❌ Link Expired</h2>"
            except:
                pass

        # UPDATE CLICK COUNT
        db.execute(
            "UPDATE urls SET clicks = clicks + 1 WHERE short_code=?",
            (code,)
        )
        db.commit()

        return redirect(long_url)

    return "<h2 style='color:red;text-align:center;'>❌ Invalid URL</h2>"


# =========================
# DASHBOARD PAGE
# =========================
@app.route('/dashboard')
def dashboard():
    db = get_db()
    urls = db.execute("SELECT * FROM urls").fetchall()
    return render_template('dashboard.html', data=urls)


# =========================
# STATS PAGE
# =========================
@app.route('/stats/<code>')
def stats(code):
    db = get_db()
    data = db.execute(
        "SELECT * FROM urls WHERE short_code=?",
        (code,)
    ).fetchone()

    if data:
        return render_template('stats.html', data=data)

    return "<h2 style='color:red;text-align:center;'>No data found</h2>"


# =========================
# RUN SERVER
# =========================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)