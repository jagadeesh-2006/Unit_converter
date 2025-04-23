from flask import Flask, render_template, request, redirect, url_for, session,jsonify,flash
import sqlite3

app = Flask(__name__)
app.secret_key = "your_secret_key" 


def init_db():
    conn = sqlite3.connect('database.db')
    conn.execute("PRAGMA foreign_keys = ON")  
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Email TEXT NOT NULL,
        password TEXT NOT NULL)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS conversions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category TEXT,
        from_unit TEXT,
        to_unit TEXT,
        input_value REAL,
        result_value REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )''')

    conn.commit()
    conn.close()


init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        Email = request.form['Email']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (Email, password) VALUES (?, ?)", (Email, password))
        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        Email = request.form['Email']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE Email = ? AND password = ?", (Email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]  
            session['user_email']= user[1]
            return redirect(url_for('dashboard'))  

        return redirect('/register')

    return render_template('login.html')
def get_db_connection():
    conn = sqlite3.connect('database.db') 
    conn.row_factory = sqlite3.Row 
    return conn

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    user_email = user['Email']
    history = conn.execute('''
        SELECT id, category, from_unit, to_unit, input_value, result_value, timestamp
        FROM conversions WHERE user_id = ? ORDER BY timestamp DESC
    ''', (user_id,)).fetchall()

    conn.close()

    return render_template('profile.html', user_email=user_email, history=history)


@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return redirect(url_for('l'))
    
    user_id = session['user_id']

    try:
        conn = get_db_connection()
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM conversions WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()

        session.clear()
        
    except Exception as e:
        flash(f"Error deleting account: {e}", "error")
        print("Error deleting account:", e)

    return redirect(url_for('index'))


@app.route('/save_conversion', methods=['POST'])
def save_conversion():
    if 'user_id' not in session:
        return jsonify({'status': 'unauthorized'}), 401

    data = request.get_json()
    user_id = session['user_id']
    
    from_unit = data.get('from_unit')
    to_unit = data.get('to_unit')
    input_value = data.get('input_value')
    result_value = data.get('result_value')
    category = data.get('category')

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO conversions (user_id, category, from_unit, to_unit, input_value, result_value)
        VALUES (?, ?,?, ?, ?, ?)
    ''', (user_id,category, from_unit, to_unit, input_value, result_value))
    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})


@app.route('/logout', methods=['POST'])
def logout():
    session.clear() 
    return jsonify({'success': True})


if __name__ == '__main__':
    app.run(debug=True)  


