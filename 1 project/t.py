from flask import Flask, render_template, request, redirect, url_for
import joblib, pickle
import pandas as pd
import sqlite3

# Load the model
model = pickle.load(open("model.pkl", "rb"))

app = Flask(__name__)

# ---------------- Database Setup ----------------

def get_db_connection():
    try:
        conn = sqlite3.connect("bike_db.db")
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(e)
        return None

def create_tables():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()

        # Bike predictions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bike_prediction(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_name TEXT NOT NULL,
            owner INTEGER NOT NULL, 
            kms_driven INTEGER NOT NULL, 
            age INTEGER NOT NULL, 
            power INTEGER NOT NULL, 
            predicted_price INTEGER NOT NULL
        )
        """)

        # Registered users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL
        )
        """)

        conn.commit()
        cursor.close()
        conn.close()

create_tables()

# ---------------- Routes ----------------

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/pp')
def pp():
    return render_template('pp.html')

# --------- Bike Price Prediction Route ---------
@app.route('/predict', methods=["POST"])
def predict():
    if request.method == "POST":
        try:
            brand_name = request.form['brand_name']
            owner_name = int(request.form['owner'])
            age_bike = int(request.form['age'])
            power_bike = int(request.form['power'])
            kms_driven_bike = int(request.form['kms_driven'])

            bike_numbers = {'TVS': 0, 'Royal Enfield': 1, 'Triumph': 2, 'Yamaha': 3,
                'Honda': 4, 'Hero': 5, 'Bajaj': 6, 'Suzuki': 7, 'Benelli': 8,
                'KTM': 9, 'Mahindra': 10, 'Kawasaki': 11, 'Ducati': 12,
                'Hyosung': 13, 'Harley-Davidson': 14, 'Jawa': 15, 'BMW': 16,
                'Indian': 17, 'Rajdoot': 18, 'LML': 19, 'Yezdi': 20,
                'MV': 21, 'Ideal': 22}

            brand_name_encoded = bike_numbers.get(brand_name)
            if brand_name_encoded is None:
                return "Brand not recognized."

            input_data = [[owner_name, brand_name_encoded, kms_driven_bike, age_bike, power_bike]]
            prediction = round(model.predict(input_data)[0], 2)

            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO bike_prediction (brand_name, owner, kms_driven, age, power, predicted_price)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (brand_name, owner_name, kms_driven_bike, age_bike, power_bike, prediction))
                conn.commit()
                cursor.close()
                conn.close()

            return render_template('project.html', prediction=prediction)
        except Exception as e:
            return f"Something went wrong: {e}"

# --------- History Route ---------
@app.route('/history')
def history():
    brand_name_filter = request.args.get("brand_name_filter")
    conn = get_db_connection()
    historical_data = []
    if conn:
        cursor = conn.cursor()
        try:
            if brand_name_filter:
                query = "SELECT * FROM bike_prediction WHERE brand_name = ?"
                cursor.execute(query, (brand_name_filter,))
            else:
                query = "SELECT * FROM bike_prediction"
                cursor.execute(query)
            historical_data = [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(e)
        finally:
            cursor.close()
            conn.close()
    return render_template('history.html', historical_data=historical_data)

# --------- Register Route ---------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']  # Not stored in this version

            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, email) VALUES (?, ?)",
                               (username, email))
                conn.commit()
                cursor.close()
                conn.close()

            return redirect(url_for('show_users'))

        except Exception as e:
            return f"Registration error: {e}"

    return render_template('register.html')

# --------- Users Display Route ---------
@app.route('/users')
def show_users():
    conn = get_db_connection()
    all_users = []
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, email FROM users")
        all_users = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        conn.close()

    return render_template('users.html', users=all_users)

# ---------------- Run App ----------------
if __name__ == '__main__':
    app.run(debug=True)
