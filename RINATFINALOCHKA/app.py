from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from models import db, User, Request, Review
from forms import RegistrationForm, LoginForm, RequestForm

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()
        try:
            # Проверка и создание/обновление админа
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                new_admin = User(
                    username='Admin26', 
                    password=generate_password_hash('Demo20'), 
                    full_name='Администратор Системы',
                    email='admin@portal.ru',
                    phone='+7 (999) 000-00-00',
                    birth_date='01.01.1990',
                    is_admin=True, 
                    status='Активен'
                )
                db.session.add(new_admin)
                db.session.commit()
                print("✅ Администратор создан (login: Admin26, pass: Demo20)")
            else:
                # Обновляем пароль админа при каждом запуске для надежности
                admin_user.password = generate_password_hash('Demo20')
                admin_user.full_name = 'Администратор Системы'
                admin_user.email = 'admin@portal.ru'
                admin_user.phone = '+7 (999) 000-00-00'
                admin_user.birth_date = '01.01.1990'
                admin_user.is_admin = True
                admin_user.status = 'Активен'
                db.session.commit()
                print("✅ Данные администратора обновлены")
        except Exception as e:
            db.session.rollback()
            print(f"⚠️ Ошибка при инициализации БД: {e}")

    # --- PUBLIC ROUTES ---

    @app.route('/')
    def index():
        slider_images = [
            url_for('static', filename='images/slide1.jpg'),
            url_for('static', filename='images/slide2.jpg'),
            url_for('static', filename='images/slide3.jpg')
        ]
        reviews = Review.query.order_by(Review.id.desc()).all()
        return render_template('index.html', slider_images=slider_images, reviews=reviews)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated: 
            return redirect(url_for('index'))
        form = RegistrationForm()
        if form.validate_on_submit():
            new_user = User(
                username=form.username.data,
                password=generate_password_hash(form.password.data),
                full_name=form.full_name.data,
                email=form.email.data,
                phone=form.phone.data,
                birth_date=form.birth_date.data
            )
            db.session.add(new_user)
            db.session.commit()
            flash('Регистрация успешна! Теперь войдите.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated: 
            return redirect(url_for('index'))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and check_password_hash(user.password, form.password.data):
                if user.status == 'Заблокирован':
                    flash('Ваш аккаунт заблокирован. Обратитесь в поддержку.', 'danger')
                    return render_template('login.html', form=form)
                
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('profile'))
            else:
                flash('Неверный логин или пароль.', 'danger')
        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))

    # --- USER ROUTES ---

    @app.route('/profile')
    @login_required
    def profile():
        user_requests = Request.query.filter_by(user_id=current_user.id).order_by(Request.created_at.desc()).all()
        user_reviews = Review.query.filter_by(user_id=current_user.id).order_by(Review.id.desc()).all()
        return render_template('profile.html', requests=user_requests, reviews=user_reviews)

    @app.route('/actions')
    @login_required
    def actions():
        req_form = RequestForm()
        # Ищем завершенные заявки БЕЗ отзыва
        pending_reviews = Request.query.filter(
            Request.user_id == current_user.id,
            Request.status == 'Завершено'
        ).outerjoin(Review).filter(Review.id.is_(None)).all()
        return render_template('actions.html', req_form=req_form, pending_reviews=pending_reviews)

    @app.route('/new_request', methods=['POST'])
    @login_required
    def new_request():
        form = RequestForm()
        if form.validate_on_submit():
            req = Request(
                title=form.title.data,
                category=form.category.data,
                date_str=form.date_str.data,
                description=form.description.data,
                user_id=current_user.id
            )
            db.session.add(req)
            db.session.commit()
            flash('Заявка отправлена!', 'success')
        else:
            # Показываем ошибки валидации
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Ошибка в поле {getattr(form, field).label.text}: {error}", 'danger')
        return redirect(url_for('actions'))

    @app.route('/add_review_dynamic', methods=['POST'])
    @login_required
    def add_review_dynamic():
        req_id = request.form.get('request_id')
        rating = request.form.get('rating', type=int)
        text = request.form.get('text')
        
        if not req_id or not rating or not text:
            flash('Заполните все поля', 'danger')
            return redirect(url_for('actions'))
        
        req = Request.query.get_or_404(req_id)
        
        # Проверки безопасности
        if req.user_id != current_user.id:
            flash('Нельзя оставить отзыв к чужой заявке', 'danger')
            return redirect(url_for('actions'))
        if req.status != 'Завершено':
            flash('Отзыв можно оставить только на завершенную заявку', 'warning')
            return redirect(url_for('actions'))
        if req.review:
            flash('Отзыв к этой заявке уже оставлен', 'warning')
            return redirect(url_for('actions'))

        try:
            review = Review(text=text, rating=rating, request_id=req_id, user_id=current_user.id)
            db.session.add(review)
            db.session.commit()
            flash('Спасибо за ваш отзыв!', 'success')
        except Exception:
            db.session.rollback()
            flash('Ошибка при сохранении отзыва', 'danger')
            
        return redirect(url_for('actions'))

    # --- ADMIN ROUTES ---

    @app.route('/admin')
    @login_required
    def admin_panel():
        if not current_user.is_admin: 
            flash('Доступ запрещен', 'danger')
            return redirect(url_for('index'))
        
        status_filter = request.args.get('status', '')
        query = Request.query
        if status_filter: 
            query = query.filter_by(status=status_filter)
        query = query.order_by(Request.created_at.desc())
        
        return render_template('admin.html', requests=query.all(), current_status=status_filter)

    @app.route('/update_status/<int:req_id>', methods=['POST'])
    @login_required
    def update_status(req_id):
        if not current_user.is_admin: 
            return redirect(url_for('index'))
        
        req = Request.query.get_or_404(req_id)
        new_status = request.form.get('status')
        req.status = new_status
        db.session.commit()
        flash(f'Статус заявки #{req.id} изменен на {new_status}', 'info')
        return redirect(url_for('admin_panel'))

    @app.route('/admin/users')
    @login_required
    def admin_users():
        if not current_user.is_admin: 
            flash('Доступ запрещен', 'danger')
            return redirect(url_for('index'))
        
        sort_by = request.args.get('sort', 'username')
        status_filter = request.args.get('status', '')
        
        query = User.query
        if status_filter: 
            query = query.filter_by(status=status_filter)
        
        if sort_by == 'status': 
            query = query.order_by(User.status)
        else: 
            query = query.order_by(User.username)
            
        users = query.all()
        return render_template('admin_users.html', users=users, current_status=status_filter, current_sort=sort_by)

    @app.route('/admin/update_user/<int:user_id>', methods=['POST'])
    @login_required
    def update_user(user_id):
        if not current_user.is_admin: 
            return redirect(url_for('index'))
        
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            flash('Нельзя изменять настройки собственного аккаунта', 'warning')
            return redirect(url_for('admin_users'))
        
        new_status = request.form.get('status')
        new_role = request.form.get('role')
        
        if new_status in ['Активен', 'Заблокирован']:
            user.status = new_status
        if new_role in ['user', 'admin']:
            user.is_admin = (new_role == 'admin')
            
        db.session.commit()
        flash(f'Настройки пользователя {user.username} успешно обновлены', 'success')
        return redirect(url_for('admin_users'))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)