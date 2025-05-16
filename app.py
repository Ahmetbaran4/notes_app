from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, User, Note
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gizli-anahtar'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///veritabani.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        if User.query.filter_by(username=username).first():
            flash("Bu kullanıcı adı zaten var.")
            return redirect(url_for("register"))
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("notlar_goster"))
        flash("Hatalı kullanıcı adı veya şifre.")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/ekle", methods=["GET", "POST"])
@login_required
def ekle():
    if request.method == "POST":
        baslik = request.form["baslik"]
        icerik = request.form["icerik"]
        yeni_not = Note(title=baslik, content=icerik, user_id=current_user.id)
        db.session.add(yeni_not)
        db.session.commit()
        return redirect(url_for("notlar_goster"))
    return render_template("ekle.html")

@app.route("/notlar")
@login_required
def notlar_goster():
    q = request.args.get("q")
    if q:
        kullanici_notlari = Note.query.filter(
            Note.user_id == current_user.id,
            (Note.title.contains(q) | Note.content.contains(q))
        ).all()
    else:
        kullanici_notlari = Note.query.filter_by(user_id=current_user.id).all()
    return render_template("notlar.html", notlar=kullanici_notlari)

@app.route("/sil/<int:not_id>")
@login_required
def sil(not_id):
    not_ = Note.query.get_or_404(not_id)
    if not_.user_id != current_user.id:
        flash("Bu nota erişim izniniz yok.")
        return redirect(url_for("notlar_goster"))
    db.session.delete(not_)
    db.session.commit()
    return redirect(url_for("notlar_goster"))

@app.route("/duzenle/<int:not_id>", methods=["GET", "POST"])
@login_required
def duzenle(not_id):
    not_ = Note.query.get_or_404(not_id)
    if not_.user_id != current_user.id:
        flash("Bu nota erişim izniniz yok.")
        return redirect(url_for("notlar_goster"))
    if request.method == "POST":
        not_.title = request.form["baslik"]
        not_.content = request.form["icerik"]
        db.session.commit()
        return redirect(url_for("notlar_goster"))
    return render_template("ekle.html", baslik=not_.title, icerik=not_.content, guncelle=True)

if __name__ == "__main__":
    app.run(debug=True)
