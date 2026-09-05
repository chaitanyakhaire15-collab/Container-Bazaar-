from flask import Flask, render_template, request, redirect, g
import sqlite3

app = Flask(__name__)
DATABASE = 'bazaar.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(e):
    db = getattr(g, '_database', None)
    if db is not None: db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''CREATE TABLE IF NOT EXISTS containers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, city TEXT, state TEXT, size TEXT, type TEXT,
            price TEXT, phone TEXT, seller_name TEXT, verified INTEGER DEFAULT 1
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            container_id INTEGER, buyer_name TEXT, buyer_phone TEXT, buyer_city TEXT, buyer_qty TEXT
        )''')
        db.commit()
        # Demo data - All India
        count = db.execute("SELECT COUNT(*) FROM containers").fetchone()[0]
        if count == 0:
            demo = [
                ('20ft Dry Container - Good Condition','Mumbai','Maharashtra','20ft','Dry','85000','9876543210','Mumbai Container Co'),
                ('40ft Dry Container - Cargo Worthy','Mundra','Gujarat','40ft','Dry','1,45,000','9876543211','Gujarat Logistics'),
                ('40ft Reefer Container - Working','Chennai','Tamil Nadu','40ft','Reefer','2,80,000','9876543212','Chennai Reefers'),
                ('20ft Dry - Bhiwandi Stock','Bhiwandi','Maharashtra','20ft','Dry','82000','9876543213','Bhiwandi Traders'),
                ('20ft Open Top Container','Delhi','Delhi','20ft','Open Top','1,10,000','9876543214','Delhi ICD Solutions'),
            ]
            for d in demo: db.execute("INSERT INTO containers (title,city,state,size,type,price,phone,seller_name) VALUES (?,?,?,?,?,?,?,?)", d)
            db.commit()

@app.route('/')
def home():
    db = get_db()
    q = request.args.get('q','')
    city = request.args.get('city','')
    if q:
        cons = db.execute("SELECT * FROM containers WHERE city LIKE? OR state LIKE? OR title LIKE? OR size LIKE? ORDER BY id DESC", (f'%{q}%',f'%{q}%',f'%{q}%',f'%{q}%')).fetchall()
    elif city:
        cons = db.execute("SELECT * FROM containers WHERE city LIKE? OR state LIKE? ORDER BY id DESC", (f'%{city}%',f'%{city}%')).fetchall()
    else:
        cons = db.execute("SELECT * FROM containers ORDER BY id DESC").fetchall()
    return render_template('index.html', containers=cons)

@app.route('/product/<int:id>')
def product(id):
    db = get_db()
    c = db.execute("SELECT * FROM containers WHERE id=?", (id,)).fetchone()
    return render_template('product.html', c=c)

@app.route('/inquiry/<int:id>', methods=['POST'])
def inquiry(id):
    db = get_db()
    db.execute("INSERT INTO inquiries (container_id, buyer_name, buyer_phone, buyer_city, buyer_qty) VALUES (?,?,?,?,?)",
    (id, request.form['name'], request.form['phone'], request.form['city'], request.form['qty']))
    db.commit()
    con = db.execute("SELECT * FROM containers WHERE id=?", (id,)).fetchone()
    msg = f"Hello, I need {con['title']} at {con['city']}. Buyer:{request.form['name']} {request.form['phone']} City:{request.form['city']} Qty:{request.form['qty']}"
    return redirect(f"https://wa.me/91{con['phone']}?text={msg}")

@app.route('/seller', methods=['GET','POST'])
def seller():
    if request.method == 'POST':
        db = get_db()
        db.execute("INSERT INTO containers (title,city,state,size,type,price,phone,seller_name) VALUES (?,?,?,?,?,?,?,?)",
        (request.form['title'], request.form['city'], request.form['state'], request.form['size'], request.form['type'], request.form['price'], request.form['phone'], request.form['seller']))
        db.commit()
        return redirect('/')
    return render_template('seller.html')

@app.route('/admin')
def admin():
    db = get_db()
    leads = db.execute("SELECT i.*, c.title, c.city, c.price FROM inquiries i JOIN containers c ON c.id=i.container_id ORDER BY i.id DESC").fetchall()
    return render_template('admin.html', leads=leads)

init_db()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
