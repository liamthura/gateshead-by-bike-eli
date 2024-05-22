import sqlalchemy as sa
import re
from pywebio import *
from pywebio.pin import *
from pywebio.input import *
from pywebio.output import *
from pywebio.session import run_js
from functools import partial
from sqlalchemy import ForeignKey
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker, declarative_base, relationship
from datetime import datetime

# Creating a SQLite Database 'gbb-eli.db' with SQLAlchemy
sqlite_file_name = "gbb-eli.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
db = sa.create_engine(sqlite_url, echo=True)
Session = sessionmaker(bind=db)
Base = declarative_base()


# Defining the User class with table name 'users'
class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True)
    display_name: Mapped[str]
    password: Mapped[str]
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    subscription_status: Mapped[bool] = mapped_column(default=False)

    # posts: Mapped[list["ParkingPost"]] = relationship("Post", back_populates="user_id")

    # Structuring output of User object for better readability
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Role(Base):
    __tablename__ = 'roles'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True)
    # users: Mapped[list["User"]] = relationship("User", back_populates="role_id")
    color: Mapped[str] = mapped_column(nullable=True)

    # Structuring output of Role object for better readability
    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"


# Defining the Post class with table name 'posts'
class ParkingPost(Base):
    __tablename__ = 'posts'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date_time: Mapped[datetime] = mapped_column(default=datetime.now())
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    location: Mapped[str]
    content: Mapped[str]
    amt_slots: Mapped[int]

    # ratings: Mapped[list["ParkingRating"]] = relationship("Rating", back_populates="post_id")

    def __repr__(self):
        return f"<ParkingPost(id={self.id}, user_id={self.user_id}, location={self.location})>"

    pass


class ParkingRating(Base):
    __tablename__ = 'ratings'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    rating: Mapped[int]
    comment: Mapped[str] = mapped_column(nullable=True)

    def __repr__(self):
        return f"<ParkingRating(id={self.id}, post_id={self.post_id}, user_id={self.user_id}, rating={self.rating})>"


class Thread(Base):
    __tablename__ = 'threads'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str]
    content: Mapped[str]
    parent_id: Mapped[int] = mapped_column(ForeignKey("threads.id"), nullable=True)
    date_time: Mapped[datetime] = mapped_column(default=datetime.now())
    up_votes: Mapped[int]
    down_votes: Mapped[int]
    flags: Mapped[int]

    def __repr__(self):
        return f"<Thread(id={self.id}, user_id={self.user_id}, title={self.title})>"


class ContentReport(Base):
    __tablename__ = 'content_reports'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    thread_id: Mapped[int] = mapped_column(ForeignKey("threads.id"))
    comment: Mapped[str]
    date_time: Mapped[datetime] = mapped_column(default=datetime.now())

    def __repr__(self):
        return f"<ContentReport(id={self.id}, user_id={self.user_id}, thread_id={self.thread_id})>"


class CrimeReport(Base):
    __tablename__ = 'crime_reports'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str]
    category: Mapped[str]
    location: Mapped[str]
    description: Mapped[str]
    date_time: Mapped[datetime] = mapped_column(default=datetime.now())
    is_emergency: Mapped[bool]
    status: Mapped[str]

    def __repr__(self):
        return f"<CrimeReport(id={self.id}, user_id={self.user_id}, title={self.title})>"


# class PoliceNotification(Base):
#     pass
#
#
# class SiteNotification(Base):
#     pass


Base.metadata.create_all(db)

# defining global variables to keep track of font size changes
smaller_font_clicks = 0
bigger_font_clicks = 0

# define a global variable to store the dark mode status
dark_mode = False

# define a global variable to store if the user has a valid login
valid_user = None


def user_login(username=None, password=None):
    clear()  # to clear previous data if there is

    def validate_username(username):
        if re.match("^[a-zA-Z0-9_.-]+$", username) is None:
            return f'Username can only contain letters, numbers, ".", "_" and "-"'

    generate_header()
    put_button('Back to Homepage', onclick=lambda: main(), color='secondary').style('float:right')
    put_html("<h2>Login</h2>")

    # Defining form fields
    loginFields = [
        input("Username", name='name', required=True, validate=validate_username, value=username),
        input("Password", type=PASSWORD, name='password', value=password, required=True),
        actions("", [
            {'label': 'Login', 'value': 'login', 'type': 'submit'},
            {'label': 'Register', 'value': 'register', 'type': 'submit', 'color': 'secondary'},
        ], name="user_action"),
    ]

    data = input_group("User Log In", loginFields, cancelable=True)

    if data is None:
        toast('Login not performed', color='warning')
        user_login()
    elif data['user_action'] == 'register':
        add_user(data)
    elif data['user_action'] == 'login':
        verify_user(data['name'], data['password'])


def add_user(user_data):
    clear()

    def validate_passwords(password, confirm_password):
        if password != confirm_password:
            return 'Passwords do not match'

    generate_header()
    put_button('Back to Homepage', onclick=lambda: main(), color='secondary').style('float:right')
    put_html("<h2>Register</h2>")
    try:
        with Session() as sesh:
            user_exists = sesh.query(User).filter_by(username=user_data['name']).first()
            if user_exists is not None:
                raise ValueError('User already exists')

            registration_fields = [
                input('Username', name='name', required=True, readonly=True, value=user_data['name']),
                input('Display Name', name='display_name', required=True),
                input('Password', type=PASSWORD, name='password', required=True, value=user_data['password'],
                      readonly=True),
                input('Confirm password', type=PASSWORD, name='confirm_password', required=True,
                      validate=partial(validate_passwords, user_data['password'])),
                radio("User Role", options=[
                    {'label': 'Standard User', 'value': 1, 'selected': True},
                    {'label': 'Power User', 'value': 2},
                    {'label': 'Police Staff', 'value': 3},
                    {'label': 'Council Staff', 'value': 4}
                ], name='user_role', required=True)
            ]

            registration_data = input_group('Registration', registration_fields, cancelable=True)
            if registration_data is None:
                raise ValueError('Registration cancelled')
            if registration_data['password'] != registration_data['confirm_password']:
                toast(f'Passwords do not match', color='error')
                add_user(user_data)
            else:
                new_user = User(username=user_data['name'], password=registration_data['password'],
                                display_name=registration_data['display_name'], role_id=registration_data['user_role'])
                sesh.add(new_user)
                sesh.commit()
                print(sesh.query(User).all())
    except SQLAlchemyError:
        toast(f'An error occurred', color='error')
    except ValueError as ve:
        toast(f'{str(ve)}', color='error')
    else:
        toast(f'User added, please login with new credentials', color='success')
    finally:
        user_login()


def verify_user(username, password):
    clear()
    global valid_user
    try:
        with Session() as sesh:
            valid_user = sesh.query(User).filter_by(username=username).first()
    except SQLAlchemyError:
        toast(f'An error occurred', color='error')
    else:
        if valid_user is None:
            toast(f'Invalid user', color='error')
            user_login()
        elif valid_user.password != password:
            toast(f'Invalid login, please check your username and password', color='error')
            user_login()
        else:
            main()


def get_user_id(username=None):
    global valid_user
    if valid_user is not None and username is None:
        return valid_user.id
    elif username is not None:
        with Session() as sesh:
            selected_user = sesh.query(User).filter_by(username=username).first()
            return selected_user.id
    else:
        return None


def get_username(user_id=None):
    global valid_user
    username = None
    display_name = None
    if valid_user is not None and user_id is None:
        return valid_user.username
    elif user_id is not None:
        with Session() as sesh:
            selected_user = sesh.query(User).filter_by(id=user_id).first()
            username = selected_user.username
            display_name = selected_user.display_name
        return {'username': username, 'display_name': display_name}
    else:
        return 'Guest User'


def get_role_name(user_id=None):
    global valid_user
    if valid_user is not None and user_id is None:
        with Session() as sesh:
            selected_user_role = sesh.query(Role).filter_by(id=valid_user.role_id).first()
            roleName = selected_user_role.name
        return roleName
    elif user_id is not None:
        with Session() as sesh:
            selected_user_role = sesh.query(Role).join(User, User.role_id == Role.id).filter_by(id=user_id).first()
            roleName = selected_user_role.name
        return roleName
    else:
        return None


def get_role_id(user_id=None):
    global valid_user
    if valid_user is not None and user_id is None:
        return valid_user.role_id
    elif user_id is not None:
        with Session() as sesh:
            selected_user_role = sesh.query(User).filter_by(id=user_id).first()
            roleId = selected_user_role.role_id
        return roleId
    else:
        return None


def get_role_color(role_id=None):
    global valid_user
    if valid_user is not None and role_id is None:
        with Session() as sesh:
            selected_user_role = sesh.query(Role).filter_by(id=valid_user.role_id).first()
            roleColor = selected_user_role.color
        return roleColor
    elif role_id is not None:
        with Session() as sesh:
            selected_user_role = sesh.query(Role).filter_by(id=role_id).first()
            roleColor = selected_user_role.color
        return roleColor
    else:
        return None


def user_logout():
    clear()
    global valid_user
    valid_user = None
    toast(f'You have been logged out')
    main()


@use_scope('ROOT')
def main():
    clear()
    generate_header()
    generate_nav()
    user_data = {'username': 'khantthura',
                 'date': '12-05-2024',
                 'display_name': 'Khant Thura',
                 'content': 'This is a test content to see if the function is working'}

    user_data1 = {'username': 'thura',
                  'date': '12-05-2024',
                  'display_name': 'Thura',
                  'content': 'This is a test content to see if the function is working'}

    put_html('<h2>Recent Posts</h2>')
    generate_card(user_data)
    generate_card(user_data1)

    # put_buttons(['Login', 'Register'], onclick=[login, register])


@use_scope('ROOT', clear=True)
def forum_feeds():
    clear()
    global valid_user

    generate_header()
    generate_nav()
    if valid_user is not None:
        put_buttons([
            {'label': 'Create a new thread', 'value': 'create_thread', 'color': 'success'},
            {'label': 'My threads', 'value': 'view_own_threads', 'color': 'info'}
        ], onclick=[create_thread, own_forum_feeds]).style('float:right; margin-top: 12px;')
    put_html('<h2>Community Forum</h2>')

    get_threads()


@use_scope('ROOT', clear=True)
def own_forum_feeds():
    clear()
    global valid_user

    generate_header()
    generate_nav()
    if valid_user is not None:
        put_buttons([
            {'label': 'Create a new thread', 'value': 'create_thread', 'color': 'success'},
            {'label': 'All threads', 'value': 'view_own_threads', 'color': 'info'}
        ], onclick=[create_thread, forum_feeds]).style('float:right; margin-top: 12px;')
    put_html('<h2>Community Forum</h2>')

    get_threads(valid_user.id)


def get_threads(user_id=None):
    threadBtnGroup = None
    if get_role_id(user_id) == 4 or user_id is not None:
        threadBtnGroup = put_buttons([
            {'label': 'Edit', 'value': 'edit', 'color': 'primary'},
            {'label': 'Delete', 'value': 'delete', 'color': 'danger'},
            {'label': 'Report', 'value': 'report', 'color': 'warning'}
        ], onclick=[edit_content, main, main], small=True)
    else:
        threadBtnGroup = put_buttons([
            {'label': 'Report', 'value': 'report', 'color': 'warning'}
        ], onclick=[main], small=True)

    with Session() as sesh:
        if user_id is not None:
            threads = sesh.query(Thread).filter_by(user_id=user_id).order_by(Thread.id.desc()).limit(10).all()
            threadCount = sesh.query(Thread).filter_by(user_id=user_id).count()
        else:
            threads = sesh.query(Thread).order_by(Thread.id.desc()).limit(10).all()
            threadCount = sesh.query(Thread).count()

        if threadCount == 0:
            put_html('<p class="lead text-center">There is no threads</p>')
            return

        for thread in threads:
            threadDateTime = thread.date_time.strftime('%I:%M%p – %d %b, %Y')
            put_html(f'''
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title" style="margin: 8px 0;">
                        {thread.title} <br>
                        <small class="text-body-secondary">By {get_username(thread.user_id)["display_name"]} {get_user_badge(thread.user_id)} at {threadDateTime}</small>
                    </h3>
                </div>
                <div class="card-body">
                    <p>{thread.content}</p>
                </div>
            </div>
            ''').style('margin-bottom: 10px;')
            put_row([
                # TODO Add comment function here
                put_column([put_buttons(['Leave a Comment'], onclick=[main], small=True)]),
                put_column([threadBtnGroup]).style('justify-content: end;')
            ]).style('margin-bottom: 20px;')

        if threadCount > 10:
            put_html(f'<p class="text-center">View more threads</p>')


def create_thread():
    clear()
    global valid_user

    generate_header()
    generate_nav()
    put_buttons(['Back to Forum'], onclick=[forum_feeds]).style('float:right; margin-top: 12px;')
    put_html('<h2>Create a new thread</h2>')

    createThreadFields = [
        input('Title', name='title', required=True),
        textarea('Content', name='content', required=True),
        actions('', [
            {'label': 'Create', 'value': 'create', 'type': 'submit'},
            {'label': 'Cancel', 'value': 'cancel', 'type': 'cancel'}
        ], name='thread_actions')
    ]

    thread_data = input_group('Create Thread', createThreadFields, cancelable=True)
    try:
        if thread_data is None:
            raise ValueError('Thread creation cancelled')
        if thread_data['thread_actions'] == 'create':
            with Session() as sesh:
                new_thread = Thread(user_id=get_user_id(), title=thread_data['title'], content=thread_data['content'],
                                    up_votes=0, down_votes=0, flags=0)
                sesh.add(new_thread)
                sesh.commit()
    except ValueError as ve:
        toast(f'{str(ve)}', color='error')
    except SQLAlchemyError:
        toast('An error occurred', color='error')
    else:
        toast('Thread created successfully', color='success')
    finally:
        forum_feeds()


@use_scope('ROOT')
def edit_content():
    popup('Edit Content', [
        put_input('pin_name', label='Say Something'),
        put_button('Submit', onclick=lambda: print(pin.pin_name))
    ], closable=True)


# function that switches between dark and light mode
# we used pywebio config to save lines of css codes
def toggle_dark_mode():
    global dark_mode
    dark_mode = not dark_mode
    if dark_mode:
        config(theme='dark')
    else:
        config(theme='default')
    print(dark_mode)
    run_js('window.location.reload()')


def smaller_font():
    global smaller_font_clicks, bigger_font_clicks
    js_code = f'''
        let allElements = document.querySelectorAll('p,h2,h3,h4,h5,h6,label,input');
        allElements.forEach(function(element) {{
            var style = window.getComputedStyle(element, null).getPropertyValue('font-size');
            var currentSize = parseFloat(style);
            if ({smaller_font_clicks} < 5) {{
                element.style.fontSize = (currentSize - 1) + "px";
            }} else {{
                return;
            }}
        }});
    '''
    if smaller_font_clicks < 5:
        smaller_font_clicks += 1
        bigger_font_clicks -= 1
    run_js(js_code)
    print(smaller_font_clicks, bigger_font_clicks)


def bigger_font():
    global smaller_font_clicks, bigger_font_clicks
    js_code = f'''
            let allElements = document.querySelectorAll('p, h2, h3, h4, h5, h6,label,input');
            allElements.forEach(function(element) {{
                var style = window.getComputedStyle(element, null).getPropertyValue('font-size');
                var currentSize = parseFloat(style);
                if ({bigger_font_clicks} < 6) {{
                    element.style.fontSize = (currentSize + 1) + "px";
                }} else {{
                    return;
                }}
            }});
        '''
    if bigger_font_clicks < 6:
        bigger_font_clicks += 1
        smaller_font_clicks -= 1
    run_js(js_code)
    print(smaller_font_clicks, bigger_font_clicks)


def generate_header():
    global smaller_font_clicks, bigger_font_clicks
    smaller_font_clicks, bigger_font_clicks = 0, 0
    put_buttons([
        {'label': 'Aa+', 'value': 'bigger', 'color': 'primary'},
        {'label': 'Aa-', 'value': 'smaller', 'color': 'info'},
        {'label': 'Dark Mode', 'value': 'dark_mode', 'color': 'dark'}
    ], onclick=[bigger_font, smaller_font, toggle_dark_mode]).style(
        'float:right')
    put_html(f'''
        <h1>
        Welcome to GBB-ELI
        <p class="h5">A parking lot social platform for Gateshead Bike Users</p>
        </h1>
        ''')


def generate_nav():
    global valid_user
    if valid_user is None:
        put_buttons([
            {'label': 'Login / Register', 'value': 'login', 'color': 'primary'},
        ], onclick=[user_login]).style("float:right; margin-left:20px; margin-top: -5px;")
        put_html(f'<p class="lead">Hello, <span class="font-weight-bold">Guest User</span></p>').style('float:right;')
    else:
        put_buttons([
            {'label': 'Logout', 'value': 'login', 'color': 'danger'},
        ], onclick=[user_logout]).style("float:right; margin-left:20px;")
        put_html(
            f'''
            <p class="lead mb-n2">Hello, <span class="font-weight-bold">{valid_user.display_name}</span></p>
            {get_user_badge(valid_user.id)}
            ''').style(
            'float:right; text-align:right;')

    globalNavBtns = [
        {'label': 'Home', 'value': 'home', 'color': 'primary'},
        {'label': 'Community Forum', 'value': 'admin', 'color': 'info'}
    ]

    if valid_user is None or valid_user.role_id == 1:
        put_buttons([
            globalNavBtns[0],
            globalNavBtns[1]
        ], onclick=[main, forum_feeds])
    elif valid_user.role_id == 2:
        # TODO:  Attach navigation screens here
        put_buttons([
            globalNavBtns[0],
            globalNavBtns[1],
            {'label': 'Report Incident', 'value': 'report_crime', 'color': 'warning'}
        ], onclick=[main, forum_feeds, main])
    elif valid_user.role_id == 3:
        put_buttons([
            globalNavBtns[0],
            globalNavBtns[1],
            {'label': 'Manage Crime Reports', 'value': 'manage_users', 'color': 'danger'}
        ], onclick=[main, forum_feeds, main])
    elif valid_user.role_id == 4:
        put_buttons([
            globalNavBtns[0],
            globalNavBtns[1],
            {'label': 'Announce Updates', 'value': 'manage_users', 'color': 'success'}
        ], onclick=[main, forum_feeds, main])


# function to generate a card from post data
def generate_card(post):
    put_html(f'''
        <div class="card">
            <div class="card-header">
            <h3 class="card-title" style="margin: 8px 0;">
                {post['display_name']}
                <small class="text-body-secondary">{post['date']}</small>
            </h3>
            </div>
            <div class="card-body">
                <p>{post['content']}.</p>
            </div>
            <div class="card-footer">
                <p>By: {post['username']}</p>
            </div>
        </div>
        ''').style('margin-bottom: 10px;')
    put_buttons(['Edit', 'Delete'], onclick=[edit_content, main]).style('margin-bottom: 20px;')


def get_user_badge(user_id=None):
    if user_id is not None:
        return f'<span class="badge bg-{get_role_color(get_role_id(user_id))} text-light">{get_role_name(user_id)}</span>'
    else:
        return ''


if __name__ == '__main__':
    # Defining routes for the server so that it is navigable through html buttons and links
    routes = {
        'index': main,
        'edit': edit_content
    }
    start_server(routes, port=8080, host='localhost', debug=True)
