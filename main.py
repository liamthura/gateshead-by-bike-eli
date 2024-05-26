import sqlalchemy as sa
import pandas as pd
import re
from pywebio import *
from pywebio.pin import *
from pywebio.input import *
from pywebio.output import *
from pywebio.session import run_js
from functools import partial
from sqlalchemy import ForeignKey, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker, declarative_base, relationship
from datetime import datetime

#### DATABASE SETUP ####

rolesImport = pd.read_csv('db/roles.csv')
locationsImport = pd.read_csv('db/locations.csv')
usersImport = pd.read_csv('db/users.csv')
postsImport = pd.read_csv('db/posts.csv')
threadsImport = pd.read_csv('db/threads.csv')
flagsImport = pd.read_csv('db/content_reports.csv')
crimeReportsImport = pd.read_csv('db/crime_reports.csv')
notificationsImport = pd.read_csv('db/notifications.csv')

# Creating a SQLite Database 'gbb-eli.db' with SQLAlchemy
sqlite_file_name = "gbb-eli.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
db = sa.create_engine(sqlite_url, echo=True)
Session = sessionmaker(bind=db)
Base = declarative_base()


# Defining the User class with table name 'users'
class User(Base):
    """
    User class to define the structure of the 'users' table
    :param Base: Base class from SQLAlchemy to inherit from
    :var id: User ID, the primary key of the table
    :var username: Username of the user, this must be unique
    :var display_name: Display name of the user
    :var password: Password of the user
    :var role_id: Role of the user, Connect to roles table as a foreign key to the id of "roles" table
    :var subscription_status: Subscription status of the user, default is False
    """
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True)
    display_name: Mapped[str]
    password: Mapped[str]
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    # subscription_status: Mapped[bool] = mapped_column(default=False)
    associated_role: Mapped[list["Role"]] = relationship("Role", back_populates="users")
    notifications: Mapped[list["Notification"]] = relationship("Notification", back_populates="creator")

    # posts: Mapped[list["ParkingPost"]] = relationship("Post", back_populates="user_id")

    # Structuring output of User object for better readability
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Role(Base):
    """
    Role class to define the structure of the 'roles' table
    :param Base: Base class from SQLAlchemy to inherit from
    :var id: Role ID, the primary key of the table
    :var name: Name of the role, this must be unique
    :var color: Color of the role for badge and other differentiation purposes, default is None. Uses color names from Bootstrap
    """
    __tablename__ = 'roles'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True)
    users: Mapped[list["User"]] = relationship("User", back_populates="associated_role",
                                               cascade='all, delete')  # deleting a role will delete all users with that role
    color: Mapped[str] = mapped_column(nullable=True)

    # Structuring output of Role object for better readability
    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"


# Defining the Location class with table name 'locations'
class Location(Base):
    """
    Location class to define the structure of the 'locations' table -- for storing locations of parking spots
    :param Base: Base class from SQLAlchemy to inherit from
    :var id: Location ID, the primary key of the table
    :var name: Name of the location
    """
    __tablename__ = 'locations'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    posts: Mapped[list["ParkingPost"]] = relationship("ParkingPost", back_populates="associated_location")
    reports: Mapped[list["CrimeReport"]] = relationship("CrimeReport", back_populates="associated_location")

    # Structuring output of Location object for better readability
    def __repr__(self):
        return f"<Location(id={self.id}, name={self.name})>"


# Defining the Post class with table name 'posts'
class ParkingPost(Base):
    """
    ParkingPost class to define the structure of the 'posts' table -- for posts related to parking spots
    :param Base: Base class from SQLAlchemy to inherit from
    :var id: Post ID, the primary key of the table
    :var date_time: Date and time of the post, default is the current date and time
    :var user_id: User ID of the user who created the post, Connect to users table as a foreign key to the id of "users" table
    :var location: Location of the parking spot
    :var type: Type of the parking spot
    :var content: Description / Content of the post
    :var amt_slots: Number of available slots
    :var ratings: List of ratings for the post, Connect to ratings table as a foreign key
    """
    __tablename__ = 'posts'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date_time: Mapped[datetime] = mapped_column(default=datetime.now())
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    location: Mapped[str] = mapped_column(ForeignKey("locations.name"))
    type: Mapped[str]
    content: Mapped[str]
    amt_slots: Mapped[int]
    ratings: Mapped[list["ParkingRating"]] = relationship("ParkingRating", back_populates="associated_post",
                                                          cascade='all, delete')
    associated_location: Mapped[list["Location"]] = relationship("Location", back_populates="posts")

    # ratings: Mapped[list["ParkingRating"]] = relationship("Rating", back_populates="post_id")

    def __repr__(self):
        return f"<ParkingPost(id={self.id}, user_id={self.user_id}, location={self.location})>"

    pass


# Defining the Rating class with table name 'ratings'
class ParkingRating(Base):
    """
    ParkingRating class to define the structure of the 'ratings' table -- for ratings of parking spots
    :param Base: Base class from SQLAlchemy to inherit from
    :var id: Rating ID, the primary key of the table
    :var post_id: Post ID of the post that is being rated, Connect to posts table as a foreign key to the id of "posts" table
    :var user_id: User ID of the user who rated the post, Connect to users table as a foreign key to the id of "users" table
    :var rating: Rating given by the user
    :var comment: Comment given by the user, default is None
    :var associated_post: List of posts associated with the rating, Connect to posts table as a foreign key
    """
    __tablename__ = 'ratings'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    rating: Mapped[int]
    comment: Mapped[str] = mapped_column(nullable=True)
    associated_post: Mapped[list["ParkingPost"]] = relationship("ParkingPost", back_populates="ratings")

    def __repr__(self):
        return f"<ParkingRating(id={self.id}, post_id={self.post_id}, user_id={self.user_id}, rating={self.rating})>"


# Defining the Thread class with table name 'threads'
class Thread(Base):
    """
    Thread class to define the structure of the 'threads' table -- for threads in the community forum
    :param Base: Base class from SQLAlchemy to inherit from
    :var id: Thread ID, the primary key of the table
    :var user_id: User ID of the user who created the thread, Connect to users table as a foreign key to the id of "users" table
    :var title: Title of the thread
    :var content: Content of the thread
    :var parent_id: Parent ID of the thread, default is None, This is for comments on a thread which all have a parent thread ID
    :var date_time: Date and time of the thread, default is the current date and time
    :var up_votes: Number of up votes for the thread
    :var down_votes: Number of down votes for the thread
    :var flags: Number of flags for the thread (i.e. reports made to the thread for inappropriate content)
    :var reports: List of flags / reports for the thread, Connect to reports table as a foreign key
    """
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


# Defining the ContentReport class with table name 'content_reports'
class ContentReport(Base):
    """
    ContentReport class to define the structure of the 'content_reports' table -- for reports on threads in the community forum
    :param Base: Base class from SQLAlchemy to inherit from
    :var id: Report ID, the primary key of the table
    :var user_id: User ID of the user who reported the thread, Connect to users table as a foreign key to the id of "users" table
    :var thread_id: Thread ID of the thread that is reported, Connect to threads table as a foreign key to the id of "threads" table
    :var comment: Comment given by the user for the report, default is None
    :var date_time: Date and time of the report, default is the current date and time
    :var associated_thread: List of threads associated with the report, Connect to threads table as a foreign key
    """
    __tablename__ = 'content_reports'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    thread_id: Mapped[int] = mapped_column(ForeignKey("threads.id"))
    comment: Mapped[str]
    date_time: Mapped[datetime] = mapped_column(default=datetime.now())
    associated_thread: Mapped[list["Thread"]] = relationship("Thread", back_populates="reports")

    def __repr__(self):
        return f"<ContentReport(id={self.id}, user_id={self.user_id}, thread_id={self.thread_id})>"


# Defining the CrimeReport class with table name 'crime_reports'
class CrimeReport(Base):
    """
    CrimeReport class to define the structure of the 'crime_reports' table -- for Power User and Police, about reports on crimes in the community
    :param Base: Base class from SQLAlchemy to inherit from
    :var id: Report ID, the primary key of the table
    :var user_id: User ID of the user who reported the crime, Connect to users table as a foreign key to the id of "users" table
    :var title: Title of the crime report
    :var category: Category / Nature of the crime
    :var location: Location of the crime
    :var description: Description of the crime
    :var date_time: Date and time of the report, default is the current date and time
    :var is_emergency: Boolean to check if the report is an emergency, default is False
    :var status: Status of the report, default is 'Pending'
    """
    __tablename__ = 'crime_reports'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str]
    category: Mapped[str]
    location: Mapped[str] = mapped_column(ForeignKey("locations.name"))
    description: Mapped[str]
    date_time: Mapped[datetime] = mapped_column(default=datetime.now())
    is_emergency: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(default='Pending')
    associated_location: Mapped[list["Location"]] = relationship("Location", back_populates="reports")

    def __repr__(self):
        return f"<CrimeReport(id={self.id}, user_id={self.user_id}, title={self.title})>"


# Defining the Notification class with table name 'notifications'
class Notification(Base):
    """
    Notification class to define the structure of the 'notifications' table --
    for notifications (announcements) to users made by Police and Council
    :param Base: Base class from SQLAlchemy to inherit from
    :var id: Notification ID, the primary key of the table
    :var user_id: User ID of the user who made / created the notification, Connect to users table as a foreign key to the id of "users" table
    :var by_role_id: Role ID of the role that made / created the notification, Connect to roles table as a foreign key to the id of "roles" table
    :var title: Title of the notification
    :var content: Content of the notification
    :var date_time: Date and time of the notification, default is the current date and time
    :var category: Category of the notification (if it's an announcement, alert, etc.)
    :var status: Status of the notification, default is 'Active'
    :var creator: For joining the users table, Connect to users table as a foreign key
    """
    __tablename__ = 'notifications'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    by_role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    title: Mapped[str]
    content: Mapped[str]
    date_time: Mapped[datetime] = mapped_column(default=datetime.now())
    category: Mapped[str]
    status: Mapped[str] = mapped_column(default='Active')
    creator: Mapped[list["User"]] = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<SiteNotification(id={self.id}, user_id={self.user_id}, title={self.title})>"


# Creating the tables in the database
Base.metadata.create_all(db)

# Inserting default user roles and other dummy data into the respective tables if they are empty (for first run)
with Session() as sesh:
    if sesh.query(Role).count() == 0:
        rolesImport.to_sql('roles', db, if_exists='append', index=False)
    if sesh.query(Location).count() == 0:
        locationsImport.to_sql('locations', db, if_exists='append', index=False)
    if sesh.query(User).count() == 0:
        usersImport.to_sql('users', db, if_exists='append', index=False)
    if sesh.query(ParkingPost).count() == 0:
        postsImport.to_sql('posts', db, if_exists='append', index=False)
    if sesh.query(Thread).count() == 0:
        threadsImport.to_sql('threads', db, if_exists='append', index=False)
    if sesh.query(ContentReport).count() == 0:
        flagsImport.to_sql('content_reports', db, if_exists='append', index=False)
    if sesh.query(CrimeReport).count() == 0:
        crimeReportsImport.to_sql('crime_reports', db, if_exists='append', index=False)
    if sesh.query(Notification).count() == 0:
        notificationsImport.to_sql('notifications', db, if_exists='append', index=False)

#### GLOBAL VARIABLES ####

# defining global variables to keep track of font size changes
smaller_font_clicks = 0
bigger_font_clicks = 0

# define a global variable to store the appearance status (counter)
appearance = 0

# define a global variable to store if the user has a valid login
valid_user = None

# define a global variable to store the locations list so that session won't be necessary to query it again in form fields
with Session() as sesh:
    locations_list = []
    locations = sesh.query(Location).all()
    for location in locations:
        locations_list.append(str(location.name))


#### USER SYSTEM FUNCTIONS ####

def user_login(username=None):
    """
    Function to handle user login and registration
    :param username: Username of the user, default is None, Used to pre-fill the username field if the user has already entered it
    :return:
    """
    clear()  # to clear previous data if there is

    def validate_username(username):
        """
        Internal function to validate the username entered by the user
        :param username: form field value of the username
        :return:
        """
        if re.match("^[a-zA-Z0-9_.-]+$",
                    username) is None:  # check if username contains only letters, numbers, ".", "_" and "-"
            return f'Username can only contain letters, numbers, ".", "_" and "-"'

    def validate_password(password):
        """
        Internal function to validate the password entered by the user
        :param password: form field value of the password
        :return:
        """
        if re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)",
                    password) is None:  # check if password contains lowercase, uppercase and number
            toast(f'Password must contain a lowercase letter, an uppercase letter and a number', color='error',
                  duration=3)
            return False
        else:
            return True

    generate_header()
    put_html("<h2>Login or Register</h2>")

    # Defining form fields
    loginFields = [
        input("Username", name='name', required=True, validate=validate_username, value=username),
        input("Password", type=PASSWORD, name='password', required=True, minlength=6),
        actions("", [
            {'label': 'Login', 'value': 'login', 'type': 'submit'},
            {'label': 'Register', 'value': 'register', 'type': 'submit', 'color': 'secondary'},
            {'label': 'Back to Homepage', 'value': 'cancel', 'type': 'cancel', 'color': 'warning'}
        ], name="user_action"),
    ]

    data = input_group("User Log In", loginFields, cancelable=True)

    if data is None or data['user_action'] == 'cancel':  # if user cancels the login with no data
        toast('Login not performed', color='warning')
        clear()
        main()
    elif data['user_action'] == 'register':
        add_user(data) if validate_password(data['password']) is True else user_login(data['name'])
    elif data['user_action'] == 'login':
        verify_user(data['name'], data['password'])


def add_user(user_data):
    """
    Function to add a new user to the database
    :param user_data: a dictionary containing the user data (username, display name, password, role)
    :return:
    """
    clear()

    def validate_passwords(password, confirm_password):
        """
        Internal function to validate the match of passwords entered by the user
        :param password: form field value of the password
        :param confirm_password: form field value of the confirm password
        :return:
        """
        if password != confirm_password:
            return 'Passwords do not match'

    generate_header()
    put_html("<h2>Register</h2>")
    try:
        with Session() as sesh:
            user_exists = sesh.query(User).filter_by(username=user_data['name']).first()
            if user_exists is not None:
                raise ValueError('User already exists')  # if user already exists shows a custom error message

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
            if registration_data is None:  # if user cancels the registration
                clear()
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
        toast(f'An error occurred', color='error')  # if there is an error in the database operation
    except ValueError as ve:
        toast(f'{str(ve)}', color='error')  # if there is a custom error message
    else:
        toast(f'User added, please login with new credentials', color='success')
    finally:
        user_login(user_data['name'])  # redirect to login screen with the username pre-filled


def verify_user(username, password):
    """
    Function to verify the user login credentials
    :param username: username entered by the user
    :param password: password entered by the user
    :return:
    """
    clear()
    global valid_user
    try:
        with Session() as sesh:
            valid_user = sesh.query(User).filter_by(username=username).first()  # check if the user exists
    except SQLAlchemyError:
        toast(f'An error occurred', color='error')
    else:
        if valid_user is None:  # if user does not exist
            toast(f'Invalid user', color='error')
            user_login()
        elif valid_user.password != password:  # if password does not match with the correct one
            toast(f'Invalid login, please check your username and password', color='error')
            user_login()
        else:
            main()
            scroll_to('ROOT', position='top')  # scroll to the top of the home page


def get_user_id(username=None):
    """
    Function to get the user ID from the database
    :param username: username of the user for role ID, default is None
    :return: None if the user is not logged in, user ID if the user is logged in, or the user ID of the username provided
    """
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
    """
    Function to get the username from the database
    :param user_id: User ID of the user to get the name information for, default is None
    :return: "Guest User" if the user is not logged in, a dictionary of username and display name if the user is logged in, or that of the user ID provided
    """
    global valid_user
    if valid_user is not None and user_id is None:
        return valid_user.username
    elif valid_user is not None and user_id is not None:
        with Session() as sesh:
            selected_user = sesh.query(User).filter_by(id=user_id).first()
            username = selected_user.username
            display_name = selected_user.display_name
        return {'username': username, 'display_name': display_name}
    else:
        return {'display_name': 'Guest User'}


def get_role_name(user_id=None):
    """
    Function to get the role name from the database
    :param user_id: User ID of the user to get the role name for, default is None
    :return: None if the user is not logged in, the role name if the user is logged in, or that of the user ID provided
    """
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
    """
    Function to get the role ID from the database
    :param user_id: User ID of the user to get the role ID for, default is None
    :return: None if the user is not logged in, the role ID if the user is logged in, or that of the user ID provided
    """
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


def get_user_badge(user_id=None):
    """
    This function returns a badge of the use based on their role.
    :param user_id: The ID of the user to get the badge of.
    :return:
    """
    if user_id is not None:
        return f'<span class="badge bg-{get_role_color(get_role_id(user_id))} text-light">{get_role_name(user_id)}</span>'
    else:
        return ''


def get_role_color(role_id=None):
    """
    Function to get the role color from the database
    :param role_id: Role ID of the role to get the color for, default is None
    :return: None if the user is not logged in, the role color if the user is logged in, or that of the role ID provided
    """
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
    """
    Function to log out the user
    :return:
    """
    clear()
    global valid_user
    valid_user = None
    toast(f'You have been logged out')
    main()


#### PARKING POST FUNCTIONS by KS and MTK####

# all posts screen
@use_scope('ROOT', clear=True)
def post_feeds():
    """
    Function to display all the posts in the database
    :return:
    """
    clear()
    global valid_user

    generate_header()
    generate_nav()
    if valid_user is not None:  # if user is logged in
        put_buttons([
            {'label': 'Create a new post', 'value': 'create_post', 'color': 'success'},
            {'label': 'My posts', 'value': 'view_own_post', 'color': 'info'}
        ], onclick=[create_post, own_post_feeds]).style('float:right; margin-top: 12px')
    elif valid_user is None:  # if user is not logged in (Guest User)
        put_buttons([
            {'label': 'Create a new post', 'value': 'create_post', 'color': 'success'}
        ], onclick=[create_post]).style('float:right; margin-top: 12px')

    put_html('<h2>Recent Parking Posts</h2>')

    get_posts()


# own posts screen
@use_scope('ROOT', clear=True)
def own_post_feeds():
    """
    Function to display the posts created by the logged in user
    :return:
    """
    clear()
    global valid_user

    generate_header()
    generate_nav()
    if valid_user is not None:
        put_buttons([
            {'label': 'Create a new post', 'value': 'create_post', 'color': 'success'},
            {'label': 'All posts', 'value': 'post_feeds', 'color': 'info'}
        ], onclick=[create_post, post_feeds]).style('float:right; margin-top: 12px')
    put_html('<h2>My Parking Posts</h2>')

    get_posts(valid_user.id)


# accessing posts from ParkingPost
def get_posts(user_id=None):
    """
    Function to get the posts from the database
    :param user_id: User ID of the posts to be retrieved, default is None which retrieves all posts
    :return:
    """
    global valid_user
    postBtnGroup = None

    with Session() as sesh:
        if user_id is not None:  # if user is logged in and wants to see their own posts
            posts = sesh.query(ParkingPost).filter_by(user_id=user_id).order_by(ParkingPost.id.desc()).limit(10).all()
        else:
            posts = sesh.query(ParkingPost).order_by(ParkingPost.id.desc()).limit(10).all()

        postCount = len(posts)
        if postCount == 0:
            put_html('<p class="lead text-center">There is no posts</p>')
            return

        for post in posts:
            # we use the post.id as the scope to avoid conflicts with other posts when going back after editing
            with use_scope(f'post-{post.id}'):
                if user_id is not None or (
                        user_id is None and valid_user is not None and post.user_id == valid_user.id):
                    postBtnGroup = put_buttons([
                        {'label': 'Edit', 'value': 'edit', 'color': 'primary'},
                        {'label': 'Delete', 'value': 'delete', 'color': 'danger'}
                    ], onclick=[partial(edit_post, post.id), partial(delete_post, post.id)], small=True)

            postDateTime = post.date_time.strftime('%I:%M%p – %d %b, %Y')
            put_html(f'''
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title" style="margin: 8px 0;">{post.location}</h3>
                    <p class="card-subtitle mt-0">Amount of Spaces: <strong>{post.amt_slots}</strong> at {postDateTime}</p>
                </div>
                <div class="card-body">
                    <h4 class="card-title" style="margin: 8px 0;">Parking Slot Type: <span class="">{post.type}</span></h4>    
                    <p style="white-space: pre-wrap;">{post.content}</p>
                </div>
                <div class="card-footer text-muted">
                    <p class="mb-0">Average Rating: {get_avg_rating(post.id) if get_avg_rating(post.id) is not None else 'No ratings yet'}</p>
                </div>
            </div>
            ''').style('margin-bottom: 10px;')
            put_row([
                put_column([put_buttons([
                    {'label': 'Rate', 'value': 'add_rating', 'color': 'info'}
                ], onclick=[partial(add_rating, post.id)], small=True)]),
                put_column([postBtnGroup]).style('justify-content: end;')  # align the buttons to the right
            ])
            postBtnGroup = None
        if postCount > 10:
            put_html(f'<p class="text-center">View more posts</p>')


def add_rating(post_id):  # post_id need to be passed here by ivy (set default 1 for testing)
    """
    Function to add a rating to a post
    :param post_id: ID of the post to be rated
    :return:
    """
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
              put_buttons(['Save', 'Cancel'], onclick=[
                  partial(save_rate, post_id),
                  close_popup])], closable=True)


def save_rate(post_id):  # saving the rating details to the database
    global valid_user

    # Get user input
    rate_levels = pin.rateLevels
    comment = pin.comment

    if rate_levels is None:
        toast('Cannot rate without selecting any ratings.',
              position='center', color='#2188ff', duration=5)
        return

    if valid_user is None:
        user_id = None
    else:
        user_id = valid_user.id

    with Session() as sesh:
        rating = ParkingRating(post_id=post_id,
                               user_id=user_id,
                               rating=rate_levels,
                               comment=comment)
        sesh.add(rating)
        sesh.commit()
    close_popup()
    toast('Rating saved successfully!', position='center', color='#2188ff', duration=6)

    # print("===============", get_avg_rating(post_id), "===============") # for testing
    main()
    scroll_to(f'post-{post_id}', position='middle')  # scroll to the post after rating


# saving post to ParkingPost
def create_post():
    """
    Function to create a new post for parking locations
    :return:
    """
    clear()
    global valid_user

    generate_header()
    generate_nav()
    put_html('<h2>Create a new post</h2>')

    createPostFields = [
        select('Location', options=locations_list, name='location', required=True),
        select('Type', options=[
            {'label': 'Rack', 'value': 'Rack', 'selected': True},
            {'label': 'Locker', 'value': 'Locker'},
            {'label': 'Shelter', 'value': 'Shelter'},
            {'label': 'Corral', 'value': 'Corral'},
            {'label': 'Indoor', 'value': 'Indoor'}
        ], name='type', required=True),
        input('Amount of Available Space', type=NUMBER, name='amount', min='0', required=True),
        textarea('Description', name='content', required=True, wrap='hard',
                 help_text='Describe the parking spot in detail including exact location'),
        actions('', [
            {'label': 'Create', 'value': 'create', 'type': 'submit'},
            {'label': 'Cancel', 'value': 'cancel', 'type': 'cancel', 'color': 'warning'}
        ], name='post_actions')
    ]

    post_data = input_group('Create Post', createPostFields, cancelable=True)
    try:
        if post_data is None or post_data['post_actions'] == 'cancel':  # if user cancels the post creation
            clear()
            raise ValueError('Post creation cancelled')  # shows a custom error message
        if post_data['post_actions'] == 'create':
            with Session() as sesh:
                new_post = ParkingPost(user_id=get_user_id(), location=post_data['location'], type=post_data['type'],
                                       amt_slots=post_data['amount'], content=post_data['content'])
                sesh.add(new_post)
                sesh.commit()
    except ValueError as ve:
        toast(f'{str(ve)}', color='error')  # if there is a custom error message
    except SQLAlchemyError:
        toast('An error occurred', color='error')  # if there is an error in the database operation
    else:
        toast('Post created successfully', color='success')
    finally:
        post_feeds()


# editing post from ParkingPost
def edit_post(post_id):
    """
    Function to edit a post in the ParkingPost table
    :param post_id: ID of the post to be edited
    :return:
    """
    clear()

    generate_header()
    generate_nav()

    with Session() as sesh:
        post = sesh.query(ParkingPost).filter_by(
            id=post_id).first()  # get the details of post being edited from the database
        updatePostFields = [
            select('Location', options=locations_list, name='location', required=True, value=post.location),
            select('Type', options=[
                {'label': 'Rack', 'value': 'Rack'},
                {'label': 'Locker', 'value': 'Locker'},
                {'label': 'Shelter', 'value': 'Shelter'},
                {'label': 'Corral', 'value': 'Corral'},
                {'label': 'Indoor', 'value': 'Indoor'}
            ], name='type', required=True, value=post.type),
            input('Amount of Available Space', name='amount', type=NUMBER, min='0', required=True,
                  value=post.amt_slots),
            textarea('Content', name='content', required=True, value=post.content, wrap='hard',
                     help_text='Describe the parking spot in detail including exact location'),
            actions('', [
                {'label': 'Update', 'value': 'update', 'type': 'submit'},
                {'label': 'Cancel', 'value': 'cancel', 'type': 'cancel', 'color': 'warning'}
            ], name='post_actions')
        ]
    post_data = input_group('Edit Post', updatePostFields, cancelable=True)
    try:
        if post_data is None:
            clear()
            raise ValueError('Post not updated')
        if post_data['post_actions'] == 'update':
            with Session() as sesh:
                post.location = post_data['location']
                post.type = post_data['type']
                post.amt_slots = post_data['amount']
                post.content = post_data['content']
                sesh.add(post)
                sesh.commit()
    except ValueError as ve:
        toast(f'{str(ve)}', color='error')
    except SQLAlchemyError:
        toast('An error occurred', color='error')
    else:
        toast('Post updated successfully', color='success')
    finally:
        post_feeds()
        scroll_to(f'post-{post_id}', position='middle')
        return


# deleting post from ParkingPost

def delete_post(post_id):
    """
    Function to delete a post from the ParkingPost table
    :param post_id: ID of the post to be deleted
    :return:
    """
    clear()

    generate_header()

    def confirm_delete():  # function to confirm the deletion of the post
        with Session() as sesh:
            post = sesh.query(ParkingPost).filter_by(
                id=post_id).first()  # get the details of post being deleted from the database
            sesh.delete(post)
            sesh.commit()
        toast(f'The post at {post.location} has been deleted', color='success')
        # routing council staff to all posts feed and all other users to their own posts feed
        # because councils have the permission to delete any posts
        post_feeds() if valid_user.role_id == 4 else own_post_feeds()

    put_warning(put_markdown(f'''## Warning!
                                Are you sure you want to delete the post. This action cannot be undone.'''))

    put_buttons([
        {'label': 'Yes, confirm delete', 'value': 'confirm', 'color': 'danger'},
        {'label': 'Cancel', 'value': 'cancel', 'color': 'secondary'}
    ], onclick=[confirm_delete, post_feeds if valid_user.role_id == 4 else own_post_feeds])


def get_avg_rating(post_id):
    """
    Function to get the average rating of a post
    :param post_id: ID of the post to get the average rating for
    :return: None if no rating is detected, the average rating of the post if ratings are detected
    """
    total_rating = 0
    with Session() as sesh:
        rating_post = sesh.query(ParkingRating).filter_by(post_id=post_id).all()
        post_count = len(rating_post)

        # when no rating is detected
        if post_count == 0:
            return None
        else:
            for rating in rating_post:
                total_rating += rating.rating
            avg_result = total_rating / post_count
            return round(avg_result, 1)  # round the average rating to 1 decimal place


#### FORUM FUNCTIONS by KT ####
@use_scope('ROOT', clear=True)
def forum_feeds():
    """
    Function to display all the threads in the database
    :return:
    """
    clear()
    global valid_user

    generate_header()
    generate_nav()
    if valid_user is not None and get_role_id(valid_user.id) == 4:  # if user is a council staff
        put_buttons([
            {'label': 'Create a new thread', 'value': 'create_thread', 'color': 'success'},
            {'label': 'My threads', 'value': 'view_own_threads', 'color': 'info'},
            {'label': 'Moderate threads', 'value': 'view_all_threads', 'color': 'warning'}
        ], onclick=[create_thread, own_forum_feeds, content_reports]).style('float:right; margin-top: 12px;')
    elif valid_user is not None:  # if user is not a council staff / all other logged-in users
        put_buttons([
            {'label': 'Create a new thread', 'value': 'create_thread', 'color': 'success'},
            {'label': 'My threads', 'value': 'view_own_threads', 'color': 'info'}
        ], onclick=[create_thread, own_forum_feeds]).style('float:right; margin-top: 12px;')
    put_html('<h2>Community Forum</h2>')

    get_threads()


@use_scope('ROOT', clear=True)
def own_forum_feeds():
    """
    Function to display the threads created by the logged-in user
    :return:
    """
    clear()
    global valid_user

    generate_header()
    generate_nav()
    if valid_user is not None and get_role_id(valid_user.id) == 4:
        put_buttons([
            {'label': 'Create a new thread', 'value': 'create_thread', 'color': 'success'},
            {'label': 'All threads', 'value': 'view_all_threads', 'color': 'info'},
            {'label': 'Moderate threads', 'value': 'view_all_threads', 'color': 'warning'}
        ], onclick=[create_thread, forum_feeds, content_reports]).style('float:right; margin-top: 12px;')
    elif valid_user is not None:
        put_buttons([
            {'label': 'Create a new thread', 'value': 'create_thread', 'color': 'success'},
            {'label': 'All threads', 'value': 'view_all_threads', 'color': 'info'}
        ], onclick=[create_thread, forum_feeds]).style('float:right; margin-top: 12px;')
    put_html('<h2>Community Forum</h2>')

    get_threads(valid_user.id)


def get_threads(user_id=None):
    """
    Function to get the threads from the database
    :param user_id: User ID of the threads to be retrieved, default is None which retrieves all threads
    :return:
    """
    global valid_user
    threadBtnGroup = None

    with Session() as sesh:
        if user_id is not None:  # if user is logged in and wants to see their own threads
            threads = sesh.query(Thread).filter_by(user_id=user_id, parent_id=None).order_by(Thread.id.desc()).limit(
                10).all()
        else:  # if user is not logged in or wants to see all threads (Community Forum)
            threads = sesh.query(Thread).filter_by(parent_id=None).order_by(Thread.id.desc()).limit(10).all()

        threadCount = len(threads)
        if threadCount == 0:
            put_html('<p class="lead text-center">There is no threads</p>')
            return

        for thread in threads:
            # we use use_scope function to later scroll to the thread after adding a comment
            # we use the thread.id as the scope to avoid conflicts with other threads
            with use_scope(f'thread-{thread.id}'):
                if user_id is not None or (
                        user_id is None and valid_user is not None and thread.user_id == valid_user.id):
                    threadBtnGroup = put_buttons([
                        {'label': 'Edit', 'value': 'edit', 'color': 'primary'},
                        {'label': 'Delete', 'value': 'delete', 'color': 'danger'},
                        # won't allow users to report their own threads
                    ], onclick=[partial(edit_thread, thread.id), partial(delete_thread, thread.id)]
                        , small=True)
                elif valid_user is None or (valid_user is not None and thread.user_id != valid_user.id):
                    threadBtnGroup = put_buttons([
                        {'label': 'Report', 'value': 'report', 'color': 'warning'}
                    ], onclick=[partial(report_thread, thread.id)], small=True)

                threadDateTime = thread.date_time.strftime('%I:%M%p – %d %b, %Y')
                put_html(f'''
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title" style="margin: 8px 0;">{thread.title}</h3>
                        <p class="card-subtitle mt-0">By <strong>{get_username(thread.user_id)["display_name"]}</strong> {get_user_badge(thread.user_id) if get_role_id(thread.user_id) != 1 else ''} at {threadDateTime}</p>
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
                # print(len(comments))
                if len(comments) != 0:  # show if there are comments in the thread
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
    """
    Function to add a comment to a thread
    :param parent_thread_id: ID of the thread to add a comment to
    :return:
    """
    global valid_user

    def create_comment(comment_data):  # function to create a comment
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
    """
    Function to vote on a thread
    :param thread_id: ID of the thread to vote on
    :param vote_type: Up or down vote
    :return:
    """
    if valid_user is None:  # if user is not logged in
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
    """
    Function to create a new thread
    :return:
    """
    clear()
    global valid_user

    generate_header()
    generate_nav()
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
        if thread_data is None or thread_data['thread_actions'] == 'cancel':
            clear()
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
    """
    Function to edit a thread
    :param thread_id: ID of the thread to be edited
    :return:
    """
    clear()

    generate_header()
    generate_nav()

    with Session() as sesh:
        thread = sesh.query(Thread).filter_by(
            id=thread_id).first()  # get the details of thread being edited from the database
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
        scroll_to(f'thread-{thread_id}', position='middle')  # Scroll to the same thread after editing
        return


def delete_thread(thread_id):
    """
    When a forum thread is deleted, all threads with the same parent_id to the thread in deletion should be deleted as well
    to avoid orphaned threads.
    :param thread_id: ID of the thread to be deleted
    """
    clear()

    generate_header()

    def confirm_delete():
        with Session() as sesh:
            thread = sesh.query(Thread).filter_by(
                id=thread_id).first()  # get the details of thread being deleted from the database
            sesh.delete(thread)
            sesh.commit()
            sesh.query(Thread).filter_by(
                parent_id=thread_id).delete()  # delete all comments with the same parent thread
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
    """
    Function to display all the content reports for threads in the database or for a specific thread (for council staff)
    :param thread_id: ID of the thread to view reports for, default is None which retrieves all reports
    :return:
    """
    clear()
    global valid_user
    if valid_user is None or get_role_id() != 4:  # if user is not a council staff
        toast('You do not have permission to view this page', color='warning')
        main()
        return

    generate_header()
    generate_nav()
    put_buttons([
        {'label': 'Reports by Thread', 'value': 'reports_thread', 'color': 'secondary'},
    ], onclick=[content_reports_by_thread]).style('float:right; margin-top: 12px;')
    put_html('<h2>Individual Content Reports</h2>')

    report_table_data = []  # table data to store columns for the reports
    with Session() as sesh:
        if thread_id is not None:  # if a specific thread is selected
            reports = sesh.query(ContentReport).join(Thread).filter(
                ContentReport.thread_id == thread_id).all()  # get reports for the specific thread
        else:  # if all reports are selected
            reports = sesh.query(ContentReport).join(Thread).filter(
                ContentReport.thread_id == Thread.id).all()  # get all reports
        reportCount = len(reports)
        if reportCount == 0:
            put_html('<p class="lead text-center">There is no reports</p>')
            return

        for report in reports:
            reportDateTime = report.date_time.strftime('%d %b, %Y')
            report_table_data.append([
                report.id,
                get_username(report.user_id)['display_name'],
                report.associated_thread.title,
                report.comment,
                reportDateTime,
                put_buttons([
                    {'label': 'View', 'value': 'view_thread', 'color': 'info'},
                    {'label': 'Delete', 'value': 'delete_thread', 'color': 'danger'},
                ], onclick=[partial(view_thread, report.associated_thread.id),
                            partial(delete_thread, report.associated_thread.id)]
                ).style('display: flex; justify-content: start; flex-direction: column; gap: 5px;')])
        put_table(report_table_data, header=[
            'ID',
            'Made by',
            'Reported Thread',
            'Reason',
            'Reported Date',
            'Actions'
        ])


def content_reports_by_thread():
    """
    Function to display all the threads with that have been reported in the database
    :return:
    """
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
        threads = sesh.query(Thread).filter(Thread.flags > 0).order_by(
            Thread.flags.desc()).all()  # get threads with reports / flags
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
    """
    Function to view a thread that has been reported or an individual thread
    :param thread_id: ID of the thread to view
    :return:
    """
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
    """
    Function to report a thread
    :param thread_id: ID of the thread to report
    :return:
    """
    global valid_user

    def create_report(report_data):  # function to create a report and save it to the database
        if report_data == '':
            toast('Reason cannot be empty', color='warning')
            return
        try:
            with Session() as sesh:
                thread = sesh.query(Thread).filter_by(id=thread_id).first()
                new_report = ContentReport(user_id=valid_user.id, thread_id=thread_id, comment=report_data,
                                           date_time=datetime.now())
                thread.flags += 1  # increment the flags of the thread
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
            # if thread.user_id == valid_user.id:
            #     toast(f'Silly, let\'s not report your own thread :)', color='warning')
            #     forum_feeds()
            # else:
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


#### CRIME REPORT FUNCTIONS by KT and IVY ####
@use_scope('ROOT', clear=True)
def crime_report_feeds(view='all'):
    """
    This function will display all the police reports made by the user.
    If the user is a police staff, it will display all the police reports made by all users.
    :param view: The view of the police reports to be displayed, default is 'all' which displays all police reports
    """
    clear()
    global valid_user

    generate_header()
    generate_nav()
    if valid_user is not None and valid_user.id == 3:  # police staff
        if view == 'all':
            put_buttons([
                {'label': 'Emergency Crime Reports', 'value': 'crime_report_feeds_by_emergency', 'color': 'danger'},
                {'label': 'Crime Statistics', 'value': 'crime_stats', 'color': 'warning'}
            ], onclick=[partial(crime_report_feeds, 'emergency'), crime_stats]).style('float:right; margin-top: 12px;')
            put_html('<h2>All Crime Reports</h2>')
        elif view == 'emergency':
            put_buttons([
                {'label': 'All Crime Reports', 'value': 'crime_report_feeds', 'color': 'secondary'},
                {'label': 'Crime Statistics', 'value': 'crime_stats', 'color': 'warning'}
            ], onclick=[partial(crime_report_feeds, 'all'), crime_stats]).style('float:right; margin-top: 12px;')
            put_html('<h2>Emergency Crime Reports</h2>')
    else:  # power users
        put_buttons([
            {'label': 'Report a Crime', 'value': 'report_crime', 'color': 'success'}
        ], onclick=[report_crime]).style('float:right; margin-top: 12px;')
        put_html('<h2>My Police Reports</h2>')

    # initialise the crime table data
    crime_table_data = []
    seriesNum = 1  # for numbering the rows
    try:
        if valid_user is None:
            raise ValueError('You need to login to view police reports')
        elif valid_user is not None and valid_user.role_id not in [2, 3]:  # if not power user or police staff
            raise ValueError('You do not have permission to view police reports')
        elif valid_user.id == 3:  # police staff
            with Session() as sesh:
                if view == 'all':
                    crimes = sesh.query(CrimeReport).all()
                    crimeCount = len(crimes)
                    if crimeCount == 0:
                        put_html('<p class="lead text-center">There is no police reports</p>')
                        return
                elif view == 'emergency':
                    crimes = sesh.query(CrimeReport).filter(CrimeReport.is_emergency == True).all()
                    crimeCount = len(crimes)
                    if crimeCount == 0:
                        put_html('<p class="lead text-center">There is no emergency police reports</p>')
                        return
        else:  # power user
            with Session() as sesh:
                crimes = sesh.query(CrimeReport).filter_by(user_id=valid_user.id).all()
                crimeCount = len(crimes)
                if crimeCount == 0:
                    put_html('<p class="lead text-center">There is no police reports</p>')
                    return
    except SQLAlchemyError:
        toast('An error occurred', color='error')
    else:
        for crime in crimes:
            crimeDateTime = crime.date_time.strftime('%d %b, %Y')  # format the date
            row = [
                seriesNum,
                crime.id,
                crime.title,
                crime.location,
                crime.category,
                crimeDateTime,
                crime.status,
                put_buttons([
                    {'label': 'View', 'value': 'view', 'color': 'primary'},
                    {'label': 'Delete', 'value': 'delete', 'color': 'danger'}
                ], onclick=[partial(view_crime, crime.id), partial(delete_crime, crime.id)]).style(
                    'display: flex; justify-content: start; gap: 5px; flex-direction: column;')
            ]

            crime_table_data.append(row)
            seriesNum += 1

        header = [
            'No',
            'Ref ID',
            'Title',
            'Location',
            'Nature',
            'Date',
            'Status',
            'Action'
        ]

        put_table(crime_table_data, header=header)


def report_crime():
    """
    This is the screen for reporting a crime for Power Users through a form.
    """
    clear()
    global valid_user

    if valid_user is None or get_role_id() != 2:
        toast('You must be a Power User to report incidents', color='warning')
        main()
        return

    generate_header()
    generate_nav()
    put_html('<h2>Report a Crime</h2>')

    reportCrimeFields = [
        input('Title', name='title', required=True, maxlength=50),
        # this select field is made to show an "Other" option,
        # which will show an input field when selected by using input_update() function
        select('Nature of Crime', ['Theft', 'Assault', 'Vandalism', 'Other'
                                   ], name='category', required=True, value='Theft',
               onchange=lambda c: input_update('other', placeholder='Please specify', hidden=False,
                                               required=False) if c == 'Other' else input_update('other', hidden=True)),
        # if "Other" is selected, show an input field for specifying the nature of the crime
        input('', name='other', required=False, hidden=True, maxlength=20),
        select('Location', locations_list, name='location', required=True),
        textarea('Description', name='content', required=True, wrap='hard',
                 help_text='Please provide as much detail as possible including the exact location'),
        checkbox('Is this an emergency?', name='emergency', options=[{'label': 'Yes - Notify Police', 'value': True}]),
        actions('', [
            {'label': 'Report', 'value': 'report', 'type': 'submit'},
            {'label': 'Cancel', 'value': 'cancel', 'type': 'cancel', 'color': 'warning'}
        ], name='crime_actions')

    ]

    crime_data = input_group('Report a Crime', reportCrimeFields, cancelable=True)

    try:
        if crime_data is None or crime_data['crime_actions'] == 'cancel':
            clear()
            crime_report_feeds()
            raise ValueError('Crime report cancelled')  # raise an error if the user cancels the report
        if crime_data['crime_actions'] == 'report':
            with Session() as sesh:
                new_crime = CrimeReport(user_id=valid_user.id, title=crime_data['title'],
                                        category=crime_data['category'],
                                        location=crime_data['location'],
                                        description=crime_data['content'] if crime_data[
                                                                                 'category'] != 'Other' else "Crime Nature: " +
                                                                                                             crime_data[
                                                                                                                 'other'] + " - " +
                                                                                                             crime_data[
                                                                                                                 'content'],
                                        # to catch the "Other" category
                                        is_emergency=True if True in crime_data['emergency'] else False,
                                        date_time=datetime.now(), status='Pending')
                sesh.add(new_crime)
                sesh.commit()
    except ValueError as ve:
        toast(f'{str(ve)}', color='error')
    except SQLAlchemyError:
        toast('An error occurred', color='error')  # if there is an error in the database
    else:
        toast('Crime reported successfully', color='success')
    finally:
        crime_report_feeds()


@use_scope('ROOT', clear=True)
def view_crime(crime_id):
    """
    This function will display the details of a crime report.
    :param crime_id: The ID of the crime report to be viewed.
    """

    clear()

    current_crime_status = None  # to store the current status of the crime report

    def change_crime_status():
        """
        This function will allow the Police User to change the status of the crime report
        within individual crime report.
        """
        new_status = input_group('Change Status', [
            select('New Status', ["Pending", "Under Investigation", "Action Taken", "Closed"], name='status',
                   required=True, value=current_crime_status),
            actions('', [
                {'label': 'Change', 'value': 'change', 'type': 'submit'},
                {'label': 'Cancel', 'value': 'cancel', 'type': 'cancel', 'color': 'warning'}
            ], name='status_actions')
        ])

        if new_status is not None:
            if new_status['status_actions'] == 'change':
                new_status = new_status['status']
                with Session() as sesh:
                    selected_crime = sesh.query(CrimeReport).filter_by(id=crime_id).first()
                    selected_crime.status = new_status
                    sesh.add(selected_crime)
                    sesh.commit()
                toast(f'Crime report status has been changed to "{new_status}"', color='success')
                clear()
                view_crime(crime_id)
            elif new_status['status_actions'] == 'cancel':
                clear()  # clear the screen if the user cancels the status change so that the input field goes away
                view_crime(crime_id)

    generate_header()
    generate_nav()
    put_buttons(['Back to My Police Reports'], onclick=[crime_report_feeds]).style('float:right; margin-top: 12px;')
    put_html('<h2>Report Detail</h2>')

    with Session() as sesh:
        crime = sesh.query(CrimeReport).filter_by(id=crime_id).first()
        current_crime_status = crime.status  # store the current status of the crime report to be used outside the session
        crimeDateTime = crime.date_time.strftime('%I:%M%p – %d %b, %Y')
        put_table([
            ['Reference ID', crime.id],
            ['Date and Time', crimeDateTime],
            ['By', get_username(crime.user_id)['display_name']],
            ['Emergency',
             'Yes' if crime.is_emergency else 'No'],
            ['Description', crime.description],
            ['Location', crime.location],
            ['Nature of Crime', crime.category],
            ['Status', crime.status]
        ], header=[
            span(put_html(
                f'''<p class="h3">{crime.title} {f'<span class="fw-bolder badge bg-danger text-light"> EMERGENCY </span>' if crime.is_emergency else ''}</p>'''),
                col=2)])

        if get_role_id() == 3:  # if the user is a police staff, show the change status button
            put_buttons([
                {'label': 'Change Status', 'value': 'edit', 'color': 'primary'},
                {'label': 'Respond', 'value': 'delete', 'color': 'info'},
                {'label': 'Delete', 'value': 'delete', 'color': 'danger'}
            ], onclick=[change_crime_status, partial(respond_chat, crime_id), partial(delete_crime, crime.id)])


@use_scope('ROOT', clear=True)
def delete_crime(crime_id):
    """
    This function will delete the crime report of a given ID.
    :param crime_id: The ID of the crime report to be deleted.
    """
    clear()

    generate_header()

    def confirm_delete():
        with Session() as sesh:
            crime = sesh.query(CrimeReport).filter_by(id=crime_id).first()
            sesh.delete(crime)
            sesh.commit()
        toast(f'Crime report "{crime.title}" has been deleted', color='success')
        crime_report_feeds()

    put_warning(put_markdown(f'''## Warning!   
                             Are you sure you want to delete the crime report? This action cannot be undone.'''))
    put_buttons([
        {'label': 'Yes, confirm deletion', 'value': 'confirm', 'color': 'danger'},
        {'label': 'Cancel', 'value': 'cancel', 'color': 'secondary'}
    ], onclick=[confirm_delete, crime_report_feeds])


@use_scope('ROOT', clear=True)
def crime_stats(view='location'):
    """
    This function will display the statistics of the crime reports.
    """
    clear()
    global valid_user

    generate_header()
    generate_nav()
    if valid_user is None and valid_user.id not in [3, 4]:  # police and council staff
        toast('You do not have permission to view this page', color='warning')
        return
    if view == 'category':
        put_buttons([
            {'label': 'Reports by Crime Location', 'value': 'home', 'color': 'secondary'},
        ], onclick=[partial(crime_stats, 'location')]).style('float:right; margin-top: 12px;')
        put_html('<h2>Crime Statistics by Category</h2>')
    elif view == 'location':
        put_buttons([
            {'label': 'Reports by Crime Category', 'value': 'home', 'color': 'secondary'},
        ], onclick=[partial(crime_stats, 'category')]).style('float:right; margin-top: 12px;')
        put_html('<h2>Crime Statistics by Location</h2>')

    with Session() as sesh:
        crime_reports = sesh.query(CrimeReport).all()
        crimeCount = len(crime_reports)
        if crimeCount == 0:
            put_html('<p class="lead text-center">There is no crime reports</p>')
            return

        data_table = []

        if view == 'location':
            result = sesh.query(
                CrimeReport.location,
                func.count(CrimeReport.id),
                func.count(CrimeReport.id).filter(CrimeReport.status == "Pending"),
                func.count(CrimeReport.id).filter(CrimeReport.status == "Under Investigation"),
                func.count(CrimeReport.id).filter(CrimeReport.status == "Action Taken"),
                func.count(CrimeReport.id).filter(CrimeReport.status == "Closed")).group_by(
                CrimeReport.location).order_by((func.count(CrimeReport.id) - func.count(CrimeReport.id).filter(
                CrimeReport.status == "Closed")).desc()).all()
            for location, count, new_cases, investigation_cases, resolved_cases, closed_cases in result:
                data_table.append(
                    [location, count - closed_cases, new_cases, investigation_cases, resolved_cases,
                     closed_cases])

            put_table(data_table,
                      header=['Crime Location', 'Open Cases', 'New Cases', 'Under Investigation',
                              'Resolved Cases',
                              'Closed Cases'])

        elif view == 'category':
            result = sesh.query(
                CrimeReport.category, func.count(CrimeReport.id),
                func.count(CrimeReport.id).filter(CrimeReport.status == "Pending"),
                func.count(CrimeReport.id).filter(CrimeReport.status == "Under Investigation"),
                func.count(CrimeReport.id).filter(CrimeReport.status == "Action Taken"),
                func.count(CrimeReport.id).filter(CrimeReport.status == "Closed")).group_by(
                CrimeReport.category).order_by((func.count(CrimeReport.id) - func.count(CrimeReport.id).filter(
                CrimeReport.status == "Closed")).desc()).all()
            for category, count, new_cases, investigation_cases, resolved_cases, closed_cases in result:
                data_table.append(
                    [category, count - closed_cases, new_cases, investigation_cases, resolved_cases,
                     closed_cases])

            put_table(data_table,
                      header=['Crime Category', 'Open Cases', 'New Cases', 'Under Investigation',
                              'Resolved Cases',
                              'Closed Cases'])


#### NOTIFICATION FUNCTIONS by KT and MTK ####
@use_scope('ROOT', clear=True)
def notification_feeds():
    """
    This function will display the notifications feeds for the user.
    Only council member and police users will be able to create and manage their notifications.
    Council members will be able to see the name of council members who created council notifications / updates.
    Police users will be able to see the name of police members who created police notifications.
    """
    clear()
    global valid_user

    generate_header()
    generate_nav()
    if valid_user is not None and valid_user.role_id == 4:  # if the user is valid and is a council staff
        put_buttons([
            {'label': 'Announce an Update', 'value': 'create', 'color': 'primary'},
            {'label': 'My Announcements', 'value': 'manage', 'color': 'secondary'}
        ], onclick=[council_create_update, council_manage_updates]).style('float:right; margin-top: 12px;')
    elif valid_user is not None and valid_user.role_id == 3:  # if the user is valid and is a police staff
        put_buttons([
            {'label': 'Post a Notification', 'value': 'create', 'color': 'primary'},
            {'label': 'My Notifications', 'value': 'manage', 'color': 'secondary'}
        ], onclick=[police_create_notification, police_manage_notifications]).style('float:right; margin-top: 12px;')
    put_html('<h2>Notifications</h2>')

    with Session() as sesh:
        notifications = sesh.query(Notification).order_by(Notification.id.desc()).all()
        notificationCount = len(notifications)
        if notificationCount == 0:
            put_html('<p class="lead text-center">There is no notifications</p>')
            return
        for notification in notifications:
            notificationDateTime = notification.date_time.strftime('%I:%M%p – %d %b, %Y')  # format the date
            if valid_user is not None and valid_user.role_id == 3:  # police staff
                # use put_info to display the notification with a close button
                put_info(
                    put_html(f'''
                    <div class="card p-2">
                        <div class="card-body p-2">
                        <h4 class="card-title m-0">
                        {notification.category}: {notification.title} 
                        {f'<strong class="badge bg-primary text-light">Northumbria Police</strong>' if notification.by_role_id == 3 else f'<strong class="badge bg-info text-light">Gateshead Council</strong>'} 
                        </h4>
                        {f'<p class="mb-0">By Police Member: {get_username(notification.user_id)["display_name"]}</p>' if valid_user.role_id == 3 and notification.by_role_id == 3 else ''}
                        
                        <p class="card-subtitle mb-2"><small>{notificationDateTime}</small>
                        <p class="card-text">{notification.content}</p>
                        </div>
                    </div>
                    '''), closable=True
                ).style('margin-bottom: 10px;')
            elif valid_user is not None and valid_user.role_id == 4:  # council staff
                # use put_info to display the notification with a close button
                put_info(
                    put_html(f'''
                    <div class="card p-2">
                        <div class="card-body p-2">
                        <h4 class="card-title m-0">
                        {notification.category}: {notification.title} 
                        {f'<strong class="badge bg-primary text-light">Northumbria Police</strong>' if notification.by_role_id == 3 else f'<strong class="badge bg-info text-light">Gateshead Council</strong>'} 
                        </h4>
                        {f'<p class="mb-0">By Council Member: {get_username(notification.user_id)["display_name"]}</p>' if valid_user.role_id == 4 and notification.by_role_id == 4 else ''}
                        <p class="card-subtitle mb-2"><small>{notificationDateTime}</small>
                        <p class="card-text">{notification.content}</p>
                        </div>
                    </div>
                    '''), closable=True
                ).style('margin-bottom: 10px;')
            else:  # all other users
                put_info(
                    put_html(f'''
                                <div class="card p-2">
                                    <div class="card-body p-2">
                                    <h4 class="card-title m-0">
                                    {notification.category}: {notification.title} 
                                    {f'<strong class="badge bg-primary text-light">Northumbria Police</strong>' if notification.by_role_id == 3 else f'<strong class="badge bg-info text-light">Gateshead Council</strong>'} 
                                    </h4>

                                    <p class="card-subtitle mb-2"><small>{notificationDateTime}</small>
                                    <p class="card-text">{notification.content}</p>
                                    </div>
                                </div>
                                '''), closable=True
                ).style('margin-bottom: 10px;')


#### ACCESSIBILITY GUI FUNCTIONS by KT ####
def change_appearance():
    """
    This function toggles between dark and light mode
    by using the pywebio config function to change the theme.
    :return:
    """
    global appearance
    appearance += 1
    if appearance == 0:
        config(theme='default')
    elif appearance == 1:
        config(theme='dark')
    elif appearance == 2:
        config(theme='sketchy')
    elif appearance == 3:
        config(theme='yeti')
    else:
        appearance = 0
        config(theme='default')
    run_js('window.location.reload()')


def smaller_font():
    """
    This function decreases the font size of the text on the page
    by using the run_js function of pywebio.session module to run JavaScript code that decreases the font size.
    :return:
    """
    global smaller_font_clicks, bigger_font_clicks
    js_code = f'''
        let allElements = document.querySelectorAll('p,h2,h3,h4,h5,h6,label,input,table');
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
    # allow the user to decrease the font size only 5 times smaller than the original size
    if smaller_font_clicks < 5:
        smaller_font_clicks += 1
        bigger_font_clicks -= 1
    run_js(js_code)
    print(smaller_font_clicks, bigger_font_clicks)


def bigger_font():
    """
    This function increases the font size of the text on the page
    by using the run_js function of pywebio.session module to run JavaScript code that increases the font size.
    """
    global smaller_font_clicks, bigger_font_clicks
    js_code = f'''
            let allElements = document.querySelectorAll('p, h2, h3, h4, h5, h6,label,input,table');
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
    # allow the user to increase the font size only 6 times bigger than the original size
    if bigger_font_clicks < 6:
        bigger_font_clicks += 1
        smaller_font_clicks -= 1
    run_js(js_code)
    print(smaller_font_clicks, bigger_font_clicks)


#### GENERATIVE HEADERS AND NAVIGATIONS FUNCTIONS by KT ####
def generate_header():
    """
    This function generates the header of the page.
    The function can be used to structure a consistent header for every page.
    """
    global smaller_font_clicks, bigger_font_clicks
    smaller_font_clicks, bigger_font_clicks = 0, 0  # initialise the font size click counters
    put_buttons([
        {'label': 'Aa+', 'value': 'bigger', 'color': 'primary'},
        {'label': 'Aa-', 'value': 'smaller', 'color': 'info'},
        {'label': 'Switch Theme', 'value': 'switch_theme', 'color': 'dark'}
    ], onclick=[bigger_font, smaller_font, change_appearance], group=True).style(
        'float:right')
    put_html(f'''
        <h1>
        Welcome to Gateshead By Bike
        <p class="h5">A social platform for Gateshead bike users</p>
        </h1>
        ''')


def generate_nav():
    """
    This function generates the navigation bar of the page.
    Navigation bar will be different based on the role of the user.
    The function can be used to structure a consistent navigation bar for every page.
    """
    global valid_user
    if valid_user is None:  # if the user is not logged in (guest users)
        put_buttons([
            {'label': 'Login / Register', 'value': 'login', 'color': 'primary'},
        ], onclick=[user_login]).style("float:right; margin-left:20px; margin-top: -5px;")
        put_html(f'<p class="lead">Hello, <span class="font-weight-bold">Guest User</span></p>').style('float:right;')
    else:  # if the user is logged in (all registered users)
        put_buttons([
            {'label': 'Logout', 'value': 'login', 'color': 'danger'},
        ], onclick=[user_logout]).style("float:right; margin-left:20px;")
        put_html(
            f'''
            <p class="lead mb-n2">Hello, <span class="font-weight-bold">{valid_user.display_name}</span></p>
            {get_user_badge(valid_user.id)}
            ''').style(
            'float:right; text-align:right;')

    # global navigation buttons regardless of the user role
    globalNavBtns = [
        {'label': 'Home', 'value': 'home', 'color': 'primary'},
        {'label': 'Community Forum', 'value': 'admin', 'color': 'info'},
        {'label': f'🔔', 'value': 'view_notifications', 'color': 'success'}
    ]

    if valid_user is None or valid_user.role_id == 1:  # if the user registered (Standard User)
        put_buttons([
            globalNavBtns[0],
            globalNavBtns[1],
            globalNavBtns[2],
        ], onclick=[main, forum_feeds, notification_feeds])
    elif valid_user.role_id == 2:  # if the user is a Power User
        # TODO:  Attach navigation screens here
        put_buttons([
            globalNavBtns[0],
            globalNavBtns[1],
            {'label': 'My Police Reports', 'value': 'crime_reports', 'color': 'warning'},
            globalNavBtns[2]
        ], onclick=[main, forum_feeds, crime_report_feeds, notification_feeds])
    elif valid_user.role_id == 3:  # if the user is a Police Staff (Police User)
        put_buttons([
            globalNavBtns[0],
            globalNavBtns[1],
            {'label': 'Manage Crime Reports', 'value': 'manage_users', 'color': 'danger'},
            globalNavBtns[2]
        ], onclick=[main, forum_feeds, crime_report_feeds, notification_feeds])
    elif valid_user.role_id == 4:  # if the user is a Council Staff (Council User)
        put_buttons([
            globalNavBtns[0],
            globalNavBtns[1],
            {'label': 'Crime Statistics', 'value': 'content_reports', 'color': 'warning'},
            globalNavBtns[2]
        ], onclick=[main, forum_feeds, crime_stats, notification_feeds])


##############################################################################################################
"""
Below this line is for individual use-case parts implementations, create or move your functions down here.
Edit the functions as needed, but do not change the function names unless necessary.
"""


# KYI SIN LIN LATT'S IMPLEMENTATION STARTS HERE
def respond_chat(crime_id):
    clear()
    scroll_to('ROOT', position='top')
    put_html('<p class="lead center">This part can be found in Kyi Sin Lin Latt\'s Individual Implementation Code.</p>')


# all other code of KS should be placed here

# KYI SIN LIN LATT'S IMPLEMENTATION ENDS HERE

##############

# KHANT THURA'S IMPLEMENTATION STARTS HERE

def police_create_notification():
    clear()
    scroll_to('ROOT', position='top')
    put_html('<p class="lead center">This part can be found in Khant Thura\'s Individual Implementation Code.</p>')


def police_manage_notifications():
    clear()
    scroll_to('ROOT', position='top')
    put_html('<p class="lead center">This part can be found in Khant Thura\'s Individual Implementation Code.</p>')


# all other code of KT code should be placed here

# KHANT THURA'S IMPLEMENTATION ENDS HERE

##############

# MYAT THIRI KHANT'S IMPLEMENTATION STARTS HERE

def council_create_update():
    #this is the page for council staff site management
    clear()
    scroll_to('ROOT', position='top')
    global valid_user
    generate_header()
    generate_nav()
    if valid_user is not None and get_role_id(valid_user.id) == 4:
        put_buttons([
            {'label': 'Create an announcement', 'value': 'create_announcement', 'color': 'success'},
            {'label': 'My announcements', 'value': 'view_own_announcements', 'color': 'info'},
        ], onclick=[create_announcement, view_own_announcements]).style('float:right; margin-top: 12px;')
    else:
        '''if the user is not a council staff'''

    put_html('<h2>Announcements</h2>')
    get_announcements()


def create_announcement():
    #when a council staff wants to create an announcement
    clear()
    global valid_user

    generate_header()
    generate_nav()
    put_buttons(['Back to Announcements'], onclick=[council_create_update]).style('float:right; margin-top: 12px;')
    put_html('<h2>Post an Announcement</h2>')

    createAnnouncementForm = [
        input('Title', name='title', required=True),
        textarea('Detailed Description', name='content', required=True),
        select('Improvement Type',options=['Bike Parking Facilities', 'Cycling Routes',
        'Safety Enhancements', 'Maintenance'],name='improvementType', multiple=False),
        select('Status',options=['Active','Archived'],name='status', multiple=False),
        actions('', [
        {'label': 'Announce', 'value': 'announce', 'type': 'submit'},
        {'label': 'Cancel', 'value': 'cancel', 'type': 'cancel', 'color': 'warning'}
        ], name='announcement_actions')
    ]

    announcementData = input_group('Post an announcement', createAnnouncementForm, cancelable=True)
    try:
        if announcementData is None or announcementData['announcement_actions'] == 'cancel':
            clear()
            raise ValueError('Announcement creation cancelled')
        if announcementData['announcement_actions'] == 'announce':
            with Session as sesh:
                new_announcement = Notification(user_id=get_user_id(),
                                                by_role_id=get_role_id(),
                                                title=announcementData['title'],
                                                content=announcementData['content'],
                                                date_time=datetime.now(),
                                                category=announcementData['improvementType'],
                                                status=announcementData['status'],
                                                )
                sesh.add(new_announcement)
                sesh.commit()
    except ValueError as ve:
        toast(f'{str(ve)}', color='error')
    except SQLAlchemyError:
        toast('An error occurred', color='error')
    else:
        toast('Announcement posted successfully', color='success')
    finally:
        council_create_update()

def get_announcements(user_id=None):
    #to get all the announcements created
    global valid_user
    announcementModeration = None

    with Session as sesh:
        if valid_user is not None:
            announcements = sesh.query(Notification).filter_by(user_id=valid_user.id, parent_id=None).order_by(Notification.id.desc()).limit(20).all()
        else:
            announcements = sesh.query(Notification).filter_by(parent_id=None).order_by(Notification.id.desc()).limit(20).all()

        if len(announcements) == 0:
            put_html('<p>No announcements found</p>'.style('text-align:center;'))
            return

        for announcement in announcements:
            with use_scope(f'announcements-{announcement.id}'):
                if user_id is not None or (
                user_id is None and valid_user is not None and announcement.user_id == valid_user.id):
                    announcementModeration = put_buttons([
                        {'label': 'Edit', 'value': 'edit', 'color': 'primary'},
                        {'label': 'Delete', 'value': 'delete', 'color': 'danger'}
                    ], onclick=[partial(edit_announcement, announcement.id), partial(delete_announcement, announcement.id)], small=True)

                else:
                    announcementModeration = None

                # to show the date and time of announcement created
                announcementsDateTime = announcement.date_time.strftime('%I:%M%p – %d %b, %Y')
                put_html(f'''
                <div class="card">
                    <div class="card-header">
                    <h2 class="card-title" style = "margin: 8px 0;>{announcement.category}</h2>
                    <p class="card-subtitle mt-0"> By <strong> {get_username(announcement.user_id)["display_name"
                ]} </strong> on {get_user_badge(announcement.user_id) if get_role_id(announcement,user_id)
                != 1 else ''} at {announcementsDateTime}</p>
                </div>
                
                <div class="card-body">
                    <p style="white-space: pre-wrap;">Title: {announcement.title}</p>
                    <p style="white-space: pre-wrap;">Detailed Description: {announcement.content}</p>
                    <p style="white-space: pre-wrap;">Status: {announcement.status}</p>
                
                </div>
                ''').style('margin-bottom: 10px;')


def view_own_announcements():
    #this is the page for council staff to view their own announcements
    clear()
    global valid_user

    generate_header()
    generate_nav()
    put_html('<h2>My Announcements</h2>')
    get_announcements(valid_user.id)


def edit_announcement(announcement_id):
    #ONLY available to edit the announcement created by the owner
    clear()
    global valid_user
    generate_header()
    generate_nav()



def delete_announcement(announcement_id):
    #ONLY available to delete the announcement created by the owner
    clear()
    global valid_user
    generate_header()
    generate_nav()

def council_manage_updates():
    clear()
    scroll_to('ROOT', position='top')
    put_html('<p class="lead center">This part can be found in Myat Thiri Khant\'s Individual Implementation Code.</p>')


# all other code of MTK code should be placed here

# MYAT THIRI KHANT'S IMPLEMENTATION ENDS HERE


##############################################################################################################


@use_scope('ROOT', clear=True)
def main():
    clear()
    generate_header()
    generate_nav()

    put_html('<h2>Recent Parking Posts</h2>')
    post_feeds()


if __name__ == '__main__':
    start_server(main, port=8080, host='localhost', debug=True)
