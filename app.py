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
        db.execute('''CREATE TABLE IF NOT EXISTS containers (id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT,city TEXT,state TEXT,size TEXT,type TEXT,price TEXT,phone TEXT,seller_name TEXT)''')
        db.commit()
        if db.execute("SELECT COUNT(*) FROM containers").fetchone()[0]==0:
            for d in [('20ft Dry Container Good','Mumbai','Maharashtra','20ft','Dry','85000','9876543210','Mumbai Co'),('40ft Dry Cargo Worthy','Mundra','Gujarat','40ft','Dry','145000','9876543211','Gujarat Log'),('40ft Reefer Working','Chennai','Tamil Nadu','40ft','Reefer','280000','9876543212','Chennai Reefers')]:
                db.execute("INSERT INTO containers (title,city,state,size,type,price,phone,seller_name) VALUES (?,?,?,?,?,?,?,?)",d)
            db.commit()
@app.route('/')
def home():
    db=get_db(); q=request.args.get('q',''); city=request.args.get('city','')
    if q: cons=db.execute("SELECT * FROM containers WHERE city LIKE? OR title LIKE? ORDER BY id DESC", (f'%{q}%',f'%{q}%')).fetchall()
    elif city: cons=db.execute("SELECT * FROM containers WHERE city LIKE? ORDER BY id DESC", (f'%{city}%',)).fetchall()
    else: cons=db.execute("SELECT * FROM containers ORDER BY id DESC").fetchall()
    return render_template('index.html',containers=cons)
@app.route('/product/<int:id>')
def product(id):
    db=get_db(); c=db.execute("SELECT * FROM containers WHERE id=?",(id,)).fetchone()
    return render_template('product.html',c=c)
@app.route('/inquiry/<int:id>',methods=['POST'])
def inquiry(id):
    db=get_db(); con=db.execute("SELECT * FROM containers WHERE id=?",(id,)).fetchone()
    msg=f"Hello {con['seller_name']}, Need {con['title']} at {con['city']}. Buyer:{request.form['name']} {request.form['phone']} City:{request.form['city']} Qty:{request.form['qty']}"
    return redirect(f"https://wa.me/91{con['phone']}?text={msg}")
@app.route('/seller',methods=['GET','POST'])
def seller():
    if request.method=='POST':
        db=get_db(); db.execute("INSERT INTO containers (title,city,state,size,type,price,phone,seller_name) VALUES (?,?,?,?,?,?,?,?)",(request.form['title'],request.form['city'],request.form['state'],request.form['size'],request.form['type'],request.form['price'],request.form['phone'],request.form['seller']))
        db.commit(); return redirect('/')
    return render_template('seller.html')
    @app.route('/clear-all')
def clear_all():
    db=get_db()
    db.execute("DELETE FROM containers")
    db.commit()
    return "All Fake Deleted - <a href='/'>Go Home</a>"
init_db()
