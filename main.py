from flask import Flask, render_template, redirect, url_for, flash

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import func
from wtforms.validators import InputRequired
from wtforms import StringField, PasswordField, FileField
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy


from newsapi import NewsApiClient

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///login.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///news.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://xovbtwzwayuyvk:922c51f0b23ed4e91708b0e2c7f6439e16f8c6994e4b00b197572b6362a0d24f@ec2-18-209-78-11.compute-1.amazonaws.com:5432/d6e198qa8m6q7j'

app.config['UPLOAD_FOLDER'] = 'uploads/images'
app.config['SECRET_KEY'] = 'SECRET'
app.app_context().push()
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'email'


class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired()])
    password = PasswordField('password', validators=[InputRequired()])
    confirm = PasswordField('confirm', validators=[InputRequired()])


class LoginForm(FlaskForm):
    email = StringField('email', validators=[InputRequired()])
    password = PasswordField('password', validators=[InputRequired()])




class NewsForm(FlaskForm):
    title = StringField('title', validators=[InputRequired()])
    content = StringField('content', validators=[InputRequired()])
    category = StringField('category', validators=[InputRequired()])
    imageURL = StringField('imageUrl', validators=[InputRequired()])
    imagePC = FileField('image')
    source = StringField('source', validators=[InputRequired()])

class ProductsForm(FlaskForm):
    product = StringField('product', validators=[InputRequired()])
    description = StringField('description', validators=[InputRequired()])
    category = StringField('category', validators=[InputRequired()])
    imageURL = StringField('imageUrl', validators=[InputRequired()])
    seller = StringField('seller', validators=[InputRequired()])


class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    content = db.Column(db.String)
    category = db.Column(db.String)
    imageUrl = db.Column(db.String)
    filename = db.Column(db.String)
    imagePC = db.Column(db.LargeBinary)
    source = db.Column(db.String)
    author = db.Column(db.Integer, db.ForeignKey('login.id', ondelete="CASCADE"), nullable=False)
    date = db.Column(db.DateTime(timezone=True), default=func.now())

class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String)
    description = db.Column(db.String)
    category = db.Column(db.String)
    imageUrl = db.Column(db.String)
    filename = db.Column(db.String)
    seller = db.Column(db.String)
    author = db.Column(db.Integer, db.ForeignKey('login.id', ondelete="CASCADE"), nullable=False)
    date = db.Column(db.DateTime(timezone=True), default=func.now())

class Login(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Integer, unique=True, nullable=True)
    password = db.Column(db.String, nullable=True)
    posts = db.relationship('News', backref='login', passive_deletes=True)



with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return Login.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for("news"))
    else:
        if form.validate_on_submit():
            check = Login.query.filter_by(email=form.email.data).first()
            if check:
                if form.password.data == check.password:
                    login_user(check)
                    return redirect(url_for("news"))
                else:
                    flash("Your password is incorrect")
            else:
                flash("This user is not exist")
    return render_template('Authorization.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if current_user.is_authenticated:
        return redirect(url_for("news"))
    else:
        if form.validate_on_submit():
            check = Login.query.filter_by(email=form.email.data).first()
            if check is None:
                if form.password.data == form.confirm.data:
                    newUser = Login(email=form.email.data, password=form.password.data)
                    db.session.add(newUser)
                    db.session.commit()
                    login_user(newUser)
                    return redirect(url_for("news"))
                else:
                    flash("Your confirm password is incorrect")
            else:
                flash("This user is already exist")
    return render_template('registrpage.html', form=form)


@login_required
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route('/addnews', methods=['GET', 'POST'])
def addnews():
    form = NewsForm()
    if form.validate_on_submit():
        new_News = News(title=form.title.data, content=form.content.data,
                        category=form.category.data, imageUrl=form.imageURL.data,
                        filename=(form.imagePC.data).filename,
                        imagePC=(form.imagePC.data).read(), source=form.source.data,
                        author=current_user.id)
        db.session.add(new_News)
        db.session.commit()
        return redirect(url_for("mynews"))
    return render_template('Add.html', form=form)


@app.route('/mynews', methods=['GET', 'POST'])
def mynews():
    return render_template('mynews.html', news=News.query.filter(News.author == current_user.id).all())


@app.route('/news', methods=['GET', 'POST'])
def news():
    return render_template('newspage.html', news=News.query.all(),
                           category=News.query.filter(News.author == current_user.id).all())


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    form = NewsForm()
    if form.validate_on_submit():
        post = News.query.filter_by(id=id).first()
        post.title = form.title.data
        post.content = form.content.data
        post.category = form.category.data
        post.imageUrl = form.imageURL.data
        post.filename = (form.imagePC.data).filename
        post.imagePC = (form.imagePC.data).read()
        post.source = form.source.data
        db.session.commit()
        return redirect(url_for("mynews"))
    return render_template('editpage.html', form=form)


@app.route('/delete/<int:id>')
def delete(id):
    post = News.query.filter_by(id=id).first()
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("mynews"))


@app.route('/filter/All')
def filetAll():
    news = News.query.all()
    return render_template('newspage.html', news=news, category=News.query.filter(News.author == current_user.id).all())


@app.route('/filter/<category>')
def filter(category):
    news = News.query.filter_by(category=category).all()
    return render_template('newspage.html', news=news, category=News.query.filter(News.author == current_user.id).all())


@app.route('/market')
def market_page():
    items = [
        {'id': 1, 'name': 'Phone', 'barcode': '11', 'price': 500},
        {'id': 2, 'name': 'Laptop', 'barcode': '22', 'price': 900},
        {'id': 3, 'name': 'Keyboard', 'barcode': '33', 'price': 1500}
    ]
    return render_template('shop.html', items=items)

@app.route('/myproducts', methods=['GET', 'POST'])
def myproducts():
    return render_template('myproducts.html')

@app.route('/addproducts', methods=['GET', 'POST'])
def addproducts():
    form = ProductsForm()
    if form.validate_on_submit():
        new_Products = market_page(
            product=form.product.data,
            description=form.description.data,
            category=form.category.data,
            imageUrl=form.imageURL.data,
            seller=form.seller.data)
        db.session.add(new_Products)
        db.session.commit()
        return redirect(url_for("myproducts"))
    return render_template('Addproduct.html', form=form)


@app.route('/allnews')
def Index():
    newsapi = NewsApiClient(api_key="9fd19cf12ead43e1b7c4a5b8c3916b77")
    topheadlines = newsapi.get_top_headlines(sources="TechCrunch")

    articles = topheadlines['articles']

    desc = []
    news = []
    img = []

    for i in range(len(articles)):
        myarticles = articles[i]

        news.append(myarticles['title'])
        desc.append(myarticles['description'])
        img.append(myarticles['urlToImage'])

    list = zip(news, desc, img)

    return render_template('allnews.html', context=list)




@app.route('/')
def home():
    return render_template('homepage.html')


if __name__ == '__main__':
    app.run(debug=True)
