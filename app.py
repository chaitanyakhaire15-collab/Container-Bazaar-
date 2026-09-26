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
    if db is not None: db.close()
def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''CREATE TABLE IF NOT EXISTS containers 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT,city TEXT,state TEXT,size TEXT,type TEXT,price TEXT,phone TEXT,seller_name TEXT,paid INTEGER DEFAULT 1)''')
        db.commit()

@app.route('/')
def home():
    db=get_db()
    q=request.args.get('q','')
    my_phone = session.get('my_phone', '___NO_PHONE___')
    if q:
        cons=db.execute("SELECT * FROM containers WHERE paid=1 AND phone != ? AND (city LIKE ? OR title LIKE ?) ORDER BY id DESC", (my_phone, f'%{q}%',f'%{q}%')).fetchall()
    else:
        cons=db.execute("SELECT * FROM containers WHERE paid=1 AND phone != ? ORDER BY id DESC", (my_phone,)).fetchall()
    return render_template('index.html', containers=cons)

@app.route('/product/<int:id>')
def product(id):
    db=get_db()
    c=db.execute("SELECT * FROM containers WHERE id=?",(id,)).fetchone()
    return render_template('product.html', c=c)

@app.route('/inquiry/<int:id>', methods=['POST'])
def inquiry(id):
    db=get_db()
    con=db.execute("SELECT * FROM containers WHERE id=?",(id,)).fetchone()
    if not con: return redirect('/')
    if con['phone'] == session.get('my_phone',''): return "Apne hi container pe inquiry nahi kar sakte <a href='/'>Home</a>"
    msg=f"Hello {con['seller_name']}, Need {con['title']} at {con['city']}. Buyer:{request.form['name']} {request.form['phone']}"
    return redirect(f"https://wa.me/91{con['phone']}?text={msg}")

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        session['my_phone'] = request.form['phone'].strip()
        return redirect('/')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('my_phone', None)
    return redirect('/')

@app.route('/my-containers')
def my_containers():
    if 'my_phone' not in session: return redirect('/login')
    db = get_db()
    cons = db.execute("SELECT * FROM containers WHERE phone = ? ORDER BY id DESC", (session['my_phone'],)).fetchall()
    return render_template('my_containers.html', containers=cons, my_phone=session['my_phone'])

@app.route('/edit/<int:id>', methods=['GET','POST'])
def edit_container(id):
    if 'my_phone' not in session: return redirect('/login')
    db = get_db()
    c = db.execute("SELECT * FROM containers WHERE id=? AND phone=?", (id, session['my_phone'])).fetchone()
    if not c: return "Not allowed"
    if request.method == 'POST':
        d = request.form
        db.execute("UPDATE containers SET title=?, city=?, state=?, size=?, type=?, price=?, seller_name=? WHERE id=? AND phone=?", (d['title'], d['city'], d['state'], d['size'], d['type'], d['price'], d['seller'], id, session['my_phone']))
        db.commit()
        return redirect('/my-containers')
    return render_template('edit.html', c=c)

@app.route('/delete/<int:id>')
def delete_container(id):
    if 'my_phone' not in session: return redirect('/login')
    db = get_db()
    db.execute("DELETE FROM containers WHERE id=? AND phone=?", (id, session['my_phone']))
    db.commit()
    return redirect('/my-containers')

@app.route('/seller', methods=['GET','POST'])
def seller():
    if 'my_phone' not in session: return redirect('/login')
    if request.method=='POST':
        db=get_db()
        d=request.form
        db.execute("INSERT INTO containers (title,city,state,size,type,price,phone,seller_name,paid) VALUES (?,?,?,?,?,?,?,?,1)", (d['title'],d['city'],d['state'],d['size'],d['type'],d['price'],session['my_phone'],d['seller'],))
        db.commit()
        return redirect('/my-containers')
    return render_template('seller.html', my_phone=session['my_phone'])

init_db()
if __name__ == '__main__': app.run(debug=True)
