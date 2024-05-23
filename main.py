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
    notifications: Mapped[list["Notification"]] = relationship("Notification", back_populates="creator")

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
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
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
    reports: Mapped[list["ContentReport"]] = relationship("ContentReport", back_populates="associated_thread",
                                                          cascade="all, delete")

    def __repr__(self):
        return f"<Thread(id={self.id}, user_id={self.user_id}, title={self.title})>"


class ContentReport(Base):
    __tablename__ = 'content_reports'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    thread_id: Mapped[int] = mapped_column(ForeignKey("threads.id"))
    comment: Mapped[str]
    date_time: Mapped[datetime] = mapped_column(default=datetime.now())
    associated_thread: Mapped[list["Thread"]] = relationship("Thread", back_populates="reports")

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


class Notification(Base):
    __tablename__ = 'notifications'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    by_role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    title: Mapped[str]
    content: Mapped[str]
    date_time: Mapped[datetime] = mapped_column(default=datetime.now())
    category: Mapped[str]
    status: Mapped[str]
    creator: Mapped[list["User"]] = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<SiteNotification(id={self.id}, user_id={self.user_id}, title={self.title})>"


Base.metadata.create_all(db)

# defining global variables to keep track of font size changes
smaller_font_clicks = 0
bigger_font_clicks = 0

# define a global variable to store the dark mode status
dark_mode = False

# define a global variable to store if the user has a valid login
valid_user = None


def user_login(username=None):
    clear()  # to clear previous data if there is

    def validate_username(username):
        if re.match("^[a-zA-Z0-9_.-]+$", username) is None:
            return f'Username can only contain letters, numbers, ".", "_" and "-"'

    def validate_password(password):
        if re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)", password) is None:
            toast(f'Password must contain a lowercase letter, an uppercase letter and a number', color='error',
                  duration=3)
            return False
        else:
            return True

    generate_header()
    put_button('Back to Homepage', onclick=lambda: main(), color='secondary').style('float:right')
    put_html("<h2>Login</h2>")

    # Defining form fields
    loginFields = [
        input("Username", name='name', required=True, validate=validate_username, value=username),
        input("Password", type=PASSWORD, name='password', required=True, minlength=6),
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
        add_user(data) if validate_password(data['password']) is True else user_login(data['name'])
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
        user_login(user_data['name'])


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


def add_rating():
    popup('Rate this spot',
          [
              put_radio('rateLevels', [
                  {'label': '1', 'value': 1},
                  {'label': '2', 'value': 2},
                  {'label': '3', 'value': 3},
                  {'label': '4', 'value': 4},
                  {'label': '5', 'value': 5}
              ], label='Rate this spot', inline=True, help_text='1 - Least helpful, 5 - Most helpful'),
              put_textarea('comment', label='Feedback', placeholder='Say something', rows=2),
              put_buttons(['Save', 'Cancel'], onclick=[save_rate, main])], closable=True)

    if pin.rateLevels is None:
        toast('Cannot rate without selecting any ratings.',
              position='center', color='#2188ff', duration=5)
    else:
        main()


def save_rate(post_id, rateLevels, comment):
    global valid_user
    if valid_user is None:
        user_id = None
    else:
        user_id = valid_user.id

    with Session() as sesh:
        rating = ParkingRating(post_id=post_id,
                               user_id=user_id,
                               rating=rateLevels,
                               comment=comment)
        sesh.add(rating)
        sesh.commit()

    close_popup()
    main()


@use_scope('ROOT', clear=True)
def forum_feeds():
    clear()
    global valid_user

    generate_header()
    generate_nav()
    if valid_user is not None and get_role_id(valid_user.id) == 4:
        put_buttons([
            {'label': 'Create a new thread', 'value': 'create_thread', 'color': 'success'},
            {'label': 'My threads', 'value': 'view_own_threads', 'color': 'info'},
            {'label': 'Reported threads', 'value': 'view_all_threads', 'color': 'warning'}
        ], onclick=[create_thread, own_forum_feeds, content_reports]).style('float:right; margin-top: 12px;')
    elif valid_user is not None:
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
    if valid_user is not None and get_role_id(valid_user.id) == 4:
        put_buttons([
            {'label': 'Create a new thread', 'value': 'create_thread', 'color': 'success'},
            {'label': 'All threads', 'value': 'view_own_threads', 'color': 'info'},
            {'label': 'Reported threads', 'value': 'view_all_threads', 'color': 'warning'}
        ], onclick=[create_thread, forum_feeds, content_reports]).style('float:right; margin-top: 12px;')
    elif valid_user is not None:
        put_buttons([
            {'label': 'Create a new thread', 'value': 'create_thread', 'color': 'success'},
            {'label': 'All threads', 'value': 'view_own_threads', 'color': 'info'}
        ], onclick=[create_thread, forum_feeds]).style('float:right; margin-top: 12px;')
    put_html('<h2>Community Forum</h2>')

    get_threads(valid_user.id)


def get_threads(user_id=None):
    global valid_user
    threadBtnGroup = None

    with Session() as sesh:
        if user_id is not None:
            threads = sesh.query(Thread).filter_by(user_id=user_id, parent_id=None).order_by(Thread.id.desc()).limit(
                10).all()
        else:
            threads = sesh.query(Thread).filter_by(parent_id=None).order_by(Thread.id.desc()).limit(10).all()

        threadCount = len(threads)
        if threadCount == 0:
            put_html('<p class="lead text-center">There is no threads</p>')
            return

        for thread in threads:
            # we use use_scope function to later scroll to the thread after adding a comment
            # we use the thread.id as the scope to avoid conflicts with other threads
            with use_scope(f'thread-{thread.id}'):
                if user_id is not None:
                    threadBtnGroup = put_buttons([
                        {'label': 'Edit', 'value': 'edit', 'color': 'primary'},
                        {'label': 'Delete', 'value': 'delete', 'color': 'danger'},
                        # won't allow users to report their own threads
                        # {'label': 'Report', 'value': 'report', 'color': 'warning'}
                    ], onclick=[partial(edit_thread, thread.id), partial(delete_thread, thread.id)
                                ], small=True)
                elif valid_user is not None and thread.user_id != valid_user.id:
                    threadBtnGroup = put_buttons([
                        {'label': 'Report', 'value': 'report', 'color': 'warning'}
                    ], onclick=[partial(report_thread, thread.id)], small=True)
                elif valid_user is not None and thread.user_id == valid_user.id:
                    threadBtnGroup = None
                else:
                    threadBtnGroup = put_buttons([
                        {'label': 'Report', 'value': 'report', 'color': 'warning'}
                    ], onclick=[partial(report_thread, thread.id)], small=True)

                threadDateTime = thread.date_time.strftime('%I:%M%p – %d %b, %Y')
                put_html(f'''
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title" style="margin: 8px 0;">{thread.title}</h3>
                        <p class="card-subtitle mt-0">By <strong>{get_username(thread.user_id)["display_name"]}</strong> {get_user_badge(thread.user_id)} at {threadDateTime}</p>
                    </div>
                    <div class="card-body">
                        <p style="white-space: pre-wrap;">{thread.content}</p>
                    </div>
                </div>
                ''').style('margin-bottom: 10px;')
                put_row([
                    put_column([put_buttons([
                        {'label': 'Add Comment', 'value': 'add_comment', 'color': 'info'},
                        {'label': f'Upvote {thread.up_votes}', 'value': 'upvote', 'color': 'success'},
                        {'label': f'Downvote {thread.down_votes}', 'value': 'downvote', 'color': 'secondary'},
                    ], onclick=[partial(add_comment, thread.id), partial(vote_thread, thread.id, 'up'),
                                partial(vote_thread, thread.id, 'down')], small=True)]),
                    put_column([threadBtnGroup]).style('justify-content: end;')
                ])

                comments = sesh.query(Thread).filter_by(parent_id=thread.id).order_by(Thread.id.desc()).all()
                print(len(comments))
                if len(comments) != 0:
                    put_html('<p class="h5 fw-bolder">Comments</p>')
                    for comment in comments:
                        commentDateTime = comment.date_time.strftime('%I:%M%p – %d %b, %Y')
                        put_html(f'''
                        <div class="card p-2">
                            <div class="card-body p-2">
                            <p class="h6 card-title m-0">
                            <strong>{get_username(comment.user_id)['display_name']}</strong>
                            {get_user_badge(comment.user_id) if get_role_id(comment.user_id) in [3, 4] else ''} 
                            <small class="card-subtitle">{commentDateTime}</small>
                            </p>
                            <p class="card-text">{comment.content}</p>
                            </div>
                        </div>
                        ''').style('margin-bottom: 10px;')
                put_html('<hr>').style('margin: 32px auto; width: 30%;')

        if threadCount > 10:
            put_html(f'<p class="text-center">View more threads</p>')


def add_comment(parent_thread_id):
    global valid_user

    def create_comment(comment_data):
        if comment_data == '':
            toast('Comment cannot be empty', color='warning')
            return
        try:
            with Session() as sesh:
                parent_thread = sesh.query(Thread).filter_by(id=parent_thread_id).first()
                new_comment = Thread(user_id=valid_user.id,
                                     title=f'Comment by {get_username(valid_user.id)} to thread: {parent_thread.title}',
                                     content=comment_data, parent_id=parent_thread.id, date_time=datetime.now(),
                                     up_votes=0, down_votes=0, flags=0)
                sesh.add(new_comment)
                sesh.commit()
        except SQLAlchemyError:
            toast('An error occurred', color='error')
        else:
            toast('Comment posted', color='success')
            close_popup()
        finally:
            forum_feeds()
            scroll_to(f'thread-{parent_thread_id}', position='middle')  # Scroll to the thread after adding a comment
            return

    if valid_user is None:
        toast(f'You need to login to comment', color='warning')
        user_login()
    else:
        popup(
            'Leave a Comment',
            [
                put_textarea('comment', label='Comment', rows=3),
                put_buttons([
                    {'label': 'Submit', 'value': 'submit', 'color': 'primary'},
                    {'label': 'Cancel', 'value': 'cancel', 'color': 'danger'}
                ], onclick=[lambda: create_comment(pin.comment), close_popup])
            ],
            closable=True
        )
        print(f'pin comment here {pin.comment}')


def vote_thread(thread_id, vote_type):
    if valid_user is None:
        toast(f'Login / register to vote', color='warning')
        user_login()
        return
    try:
        with Session() as sesh:
            thread = sesh.query(Thread).filter_by(id=thread_id).first()
            if vote_type == 'up':
                thread.up_votes += 1
            elif vote_type == 'down':
                thread.down_votes += 1
            sesh.add(thread)
            sesh.commit()
    except SQLAlchemyError:
        toast('An error occurred', color='error')
    else:
        toast(f' The thread has been {vote_type}voted', color='info')
    finally:
        forum_feeds()
        scroll_to(f'thread-{thread_id}', position='middle')


def create_thread():
    clear()
    global valid_user

    generate_header()
    generate_nav()
    put_buttons(['Back to Forum'], onclick=[forum_feeds]).style('float:right; margin-top: 12px;')
    put_html('<h2>Create a new thread</h2>')

    createThreadFields = [
        input('Title', name='title', required=True),
        textarea('Content', name='content', required=True, wrap='hard'),
        actions('', [
            {'label': 'Create', 'value': 'create', 'type': 'submit'},
            {'label': 'Cancel', 'value': 'cancel', 'type': 'cancel', 'color': 'warning'}
        ], name='thread_actions')
    ]

    thread_data = input_group('Create Thread', createThreadFields, cancelable=True)
    try:
        if thread_data is None:
            raise ValueError('Thread creation cancelled')
        if thread_data['thread_actions'] == 'create':
            with Session() as sesh:
                new_thread = Thread(user_id=get_user_id(), title=thread_data['title'], content=thread_data['content'],
                                    date_time=datetime.now(),
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


def edit_thread(thread_id):
    clear()

    generate_header()
    generate_nav()

    with Session() as sesh:
        thread = sesh.query(Thread).filter_by(id=thread_id).first()
        updateThreadFields = [
            input('Title', name='title', required=True, value=thread.title),
            textarea('Content', name='content', required=True, value=thread.content, wrap='hard'),
            actions('', [
                {'label': 'Update', 'value': 'update', 'type': 'submit'},
                {'label': 'Cancel', 'value': 'cancel', 'type': 'cancel', 'color': 'warning'}
            ], name='thread_actions')
        ]

    thread_data = input_group('Edit Thread', updateThreadFields, cancelable=True)
    try:
        if thread_data is None:
            raise ValueError('Thread not updated')
        if thread_data['thread_actions'] == 'update':
            with Session() as sesh:
                thread.title = thread_data['title']
                thread.content = thread_data['content']
                sesh.add(thread)
                sesh.commit()
    except SQLAlchemyError:
        toast('An error occurred', color='error')
    except ValueError as ve:
        toast(f'{str(ve)}', color='error')
    else:
        toast('Thread updated successfully', color='success')
    finally:
        forum_feeds()
        scroll_to(f'thread-{thread_id}', position='middle')
        return


def delete_thread(thread_id):
    """
        When a forum thread is deleted, all threads with the same parent_id to the thread in deletion should be deleted as well
        to avoid orphaned threads.
        """
    clear()

    generate_header()

    def confirm_delete():
        with Session() as sesh:
            thread = sesh.query(Thread).filter_by(id=thread_id).first()
            sesh.delete(thread)
            sesh.commit()
            sesh.query(Thread).filter_by(parent_id=thread.id).delete()
            sesh.commit()
        toast(f'Thread "{thread.title}" and its comments have been deleted', color='success')
        # routing council staff to all forum feeds and all other users to their own forum feeds
        # because councils have the permission to delete any thread
        forum_feeds() if valid_user.role_id == 4 else own_forum_feeds()

    with Session() as sesh:
        thread = sesh.query(Thread).filter_by(id=thread_id).first()
    put_warning(put_markdown(f'''## Warning!   
                             Are you sure you want to delete the thread: "**{thread.title}**" and its comments. This action cannot be undone.'''))
    put_buttons([
        {'label': 'Yes, confirm deletion', 'value': 'confirm', 'color': 'danger'},
        {'label': 'Cancel', 'value': 'cancel', 'color': 'secondary'}
    ], onclick=[confirm_delete, forum_feeds if valid_user.role_id == 4 else own_forum_feeds])


@use_scope('ROOT', clear=True)
def content_reports(thread_id=None):
    clear()
    global valid_user
    if valid_user is None or get_role_id() != 4:
        toast('You do not have permission to view this page', color='warning')
        main()
        return

    generate_header()
    generate_nav()
    put_buttons([
        {'label': 'Reports by Thread', 'value': 'reports_thread', 'color': 'secondary'},
    ], onclick=[content_reports_by_thread]).style('float:right; margin-top: 12px;')
    put_html('<h2>Individual Content Reports</h2>')

    report_table_data = []
    with Session() as sesh:
        if thread_id is not None:
            reports = sesh.query(ContentReport).join(Thread).filter(ContentReport.thread_id == thread_id).all()
        else:
            reports = sesh.query(ContentReport).join(Thread).filter(ContentReport.thread_id == Thread.id).all()
        reportCount = len(reports)
        if reportCount == 0:
            put_html('<p class="lead text-center">There is no reports</p>')
            return

        for report in reports:
            reportDateTime = report.date_time.strftime('%d %b, %Y')
            report_table_data.append([
                report.id,
                get_username(report.user_id)['display_name'],
                report.associated_thread.title, report.associated_thread.flags,
                report.comment,
                reportDateTime,
                put_buttons([
                    {'label': 'View Thread', 'value': 'view_thread', 'color': 'info'},
                    {'label': 'Delete Thread', 'value': 'delete_thread', 'color': 'danger'},
                ], onclick=[partial(view_thread, report.associated_thread.id),
                            partial(delete_thread, report.associated_thread.id)], group=True
                )])
        put_table(report_table_data, header=[
            'ID',
            'Made by',
            'Reported Thread',
            'Reported Count',
            'Reason',
            'Reported Date',
            'Actions'
        ])


def content_reports_by_thread():
    clear()
    global valid_user
    if valid_user is None or get_role_id() != 4:
        toast('You do not have permission to view this page', color='warning')
        main()
        return

    generate_header()
    generate_nav()
    put_buttons([
        {'label': 'Individual Reports', 'value': 'reports_each', 'color': 'secondary'},
    ], onclick=[content_reports]).style('float:right; margin-top: 12px;')
    put_html('<h2>Content Reports by Thread</h2>')

    report_table_data = []
    with Session() as sesh:
        threads = sesh.query(Thread).filter(Thread.flags > 0).order_by(Thread.flags.desc()).all()
        threadCount = len(threads)
        if threadCount == 0:
            put_html('<p class="lead text-center">There is no threads with reports</p>')
            return

        serialNum = 1
        for thread in threads:
            credibility = thread.up_votes - thread.down_votes
            report_table_data.append([
                serialNum,
                thread.title,
                thread.flags,
                credibility,
                put_buttons([
                    {'label': 'View Thread', 'value': 'view_thread', 'color': 'info'},
                    {'label': 'Delete Thread', 'value': 'delete_thread', 'color': 'danger'},
                    {'label': 'View Reports', 'value': 'view_reports', 'color': 'warning'}
                ], onclick=[partial(view_thread, thread.id),
                            partial(delete_thread, thread.id),
                            partial(content_reports, thread.id)], group=True
                )])
            serialNum += 1

        put_table(report_table_data, header=[
            'No',
            'Reported Thread',
            'Reported Count',
            'Credibility',
            'Actions'
        ])


def view_thread(thread_id):
    clear()
    global valid_user

    generate_header()
    generate_nav()
    put_buttons(['Back to Content Reports'], onclick=[content_reports]).style('float:right; margin-top: 12px;')
    put_html('<h2>View Reported Thread</h2>')

    with Session() as sesh:
        thread = sesh.query(Thread).filter_by(id=thread_id).first()
        threadDateTime = thread.date_time.strftime('%I:%M%p – %d %b, %Y')
        put_html(f'''
        <div class="card">
            <div class="card-header">
                <h3 class="card-title" style="margin: 8px 0;">{thread.title}</h3>
                <p class="card-subtitle">By <strong>{get_username(thread.user_id)['display_name']}</strong> {get_user_badge(thread.user_id)} at {threadDateTime}</p>
            </div>
            <div class="card-body">
                <p style="white-space: pre-wrap;">{thread.content}</p>
            </div>
        </div>
        ''').style('margin-bottom: 10px;')

        comments = sesh.query(Thread).filter_by(parent_id=thread.id).order_by(Thread.id.desc()).all()
        if len(comments) != 0:
            put_html('<p class="h5 fw-bolder">Comments</p>')
            for comment in comments:
                commentDateTime = comment.date_time.strftime('%I:%M%p – %d %b, %Y')
                put_html(f'''
                <div class="card p-2">
                    <div class="card-body p-2">
                    <p class="h6 card-title my-1">
                    <strong>{get_username(comment.user_id)['display_name']}</strong>
                    <small class="card-subtitle">{commentDateTime}</small>
                    </p>
                    <p class="card-text">{comment.content}</p>
                    </div>
                </div>
                ''').style('margin-bottom: 10px;')
        put_html('<hr>').style('margin: 32px auto; width: 30%;')


def report_thread(thread_id):
    global valid_user

    def create_report(report_data):
        if report_data == '':
            toast('Reason cannot be empty', color='warning')
            return
        try:
            with Session() as sesh:
                thread = sesh.query(Thread).filter_by(id=thread_id).first()
                new_report = ContentReport(user_id=valid_user.id, thread_id=thread_id, comment=report_data,
                                           date_time=datetime.now())
                thread.flags += 1
                sesh.add(new_report)
                sesh.commit()
        except SQLAlchemyError:
            toast('An error occurred', color='error')
        else:
            toast('Report submitted! Thank you for helping our platform safe!', color='success')
            close_popup()
        finally:
            forum_feeds()
            scroll_to(f'thread-{thread_id}', position='middle')  # Scroll to the thread after adding a comment
            return

    if valid_user is None:
        toast(f'You need to login to report threads', color='warning')
        user_login()
    elif valid_user.id is not None:
        with Session() as sesh:
            thread = sesh.query(Thread).filter_by(id=thread_id).first()
            if thread.user_id == valid_user.id:
                toast(f'Silly, let\'s not report your own thread :)', color='warning')
                forum_feeds()
            else:
                popup(
                    'Report a Thread',
                    [
                        put_textarea('reason', label='Reason of Report', rows=3),
                        put_buttons([
                            {'label': 'Submit', 'value': 'submit', 'color': 'primary'},
                            {'label': 'Cancel', 'value': 'cancel', 'color': 'danger'}
                        ], onclick=[lambda: create_report(pin.reason), close_popup])
                    ],
                    closable=True
                )


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
    ], onclick=[bigger_font, smaller_font, toggle_dark_mode], group=True).style(
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
    put_buttons(['Rate', 'Delete'], onclick=[add_rating, main]).style('margin-bottom: 20px;')


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
