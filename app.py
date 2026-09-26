from flask import Flask, render_template, request, redirect, g, session
import sqlite3

app = Flask(__name__)
app.secret_key = "bazaar123"
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
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''CREATE TABLE IF NOT EXISTS containers 
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,city TEXT,state TEXT,size TEXT,
        type TEXT,price TEXT,phone TEXT,seller_name TEXT,paid INTEGER DEFAULT 1)''')
        db.commit()

@app.route('/')
def home():
    db=get_db()
    q=request.args.get('q','')
    city=request.args.get('city','')
    
    # FIX: Seller ka phone session se lo
    my_phone = session.get('my_phone', '')

    if q:
        cons=db.execute("SELECT * FROM containers WHERE paid=1 AND phone != ? AND (city LIKE ? OR title LIKE ?) ORDER BY id DESC", (my_phone, f'%{q}%',f'%{q}%')).fetchall()
    elif city:
        cons=db.execute("SELECT * FROM containers WHERE paid=1 AND phone != ? AND city LIKE ? ORDER BY id DESC", (my_phone, f'%{city}%',)).fetchall()
    else:
        cons=db.execute("SELECT * FROM containers WHERE paid=1 AND phone != ? ORDER BY id DESC", (my_phone,)).fetchall()
    return render_template('index.html', containers=cons)

@app.route('/product/<int:id>')
def product(id):
    db=get_db()
    c=db.execute("SELECT * FROM containers WHERE id=?",(id,)).fetchone()
    
    # FIX: Product page pe bhi "Similar containers" me khud ka hatao
    # Agar tum similar dikha rahe ho to ye query use karo:
    # similar = db.execute("SELECT * FROM containers WHERE city=? AND id != ? AND phone != ? LIMIT 4", (c['city'], id, session.get('my_phone',''))).fetchall()

    return render_template('product.html', c=c)

@app.route('/inquiry/<int:id>', methods=['POST'])
def inquiry(id):
    db=get_db()
    con=db.execute("SELECT * FROM containers WHERE id=?",(id,)).fetchone()
    if not con:
        return redirect('/')
    # Buyer apne aap ko inquiry na kar paye
    if con['phone'] == session.get('my_phone',''):
        return "Aap apne hi container pe inquiry nahi kar sakte"
    msg=f"Hello {con['seller_name']}, Need {con['title']} at {con['city']}. Buyer:{request.form['name']} {request.form['phone']}"
    return redirect(f"https://wa.me/91{con['phone']}?text={msg}")

@app.route('/seller', methods=['GET','POST'])
def seller():
    if request.method=='POST':
        db=get_db()
        d=request.form
        db.execute("INSERT INTO containers (title,city,state,size,type,price,phone,seller_name,paid) VALUES (?,?,?,?,?,?,?,?,1)",
        (d['title'],d['city'],d['state'],d['size'],d['type'],d['price'],d['phone'],d['seller'],))
        db.commit()
        # FIX: Phone session me save
        session['my_phone'] = d['phone']
        return redirect('/')
    return render_template('seller.html')

init_db()

if __name__ == '__main__':
    app.run(debug=True)
