import sqlalchemy as sa
from pywebio import *
from pywebio.input import *
from pywebio.output import *
from pywebio.session import run_js
from sqlalchemy import Integer, ForeignKey
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker, declarative_base, relationship
from datetime import datetime

# Creating a SQL Database 'gbb-eli.db' with SQLAlchemy
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
    users: Mapped[list["User"]] = relationship("User", back_populates="role_id")
    avatar_url: Mapped[str]

    # Structuring output of Role object for better readability
    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"


# Defining the Post class with table name 'posts'
class ParkingPost(Base):
    __tablename__ = 'posts'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date_time: Mapped[datetime] = mapped_column(default=datetime.now())
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    location: Mapped[str]
    content: Mapped[str]
    amt_slots: Mapped[int]
    ratings: Mapped[list["ParkingRating"]] = relationship("Rating", back_populates="post_id")

    def __repr__(self):
        return f"<ParkingPost(id={self.id}, user_id={self.user_id}, location={self.location})>"

    pass


class ParkingRating(Base):
    __tablename__ = 'ratings'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    rating: Mapped[int]
    comment: Mapped[str]

    def __repr__(self):
        return f"<ParkingRating(id={self.id}, post_id={self.post_id}, user_id={self.user_id}, rating={self.rating})>"


class Thread(Base):
    __tablename__ = 'threads'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str]
    content: Mapped[str]
    parent_id: Mapped[int] = mapped_column(ForeignKey("threads.id"))
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

smaller_font_clicks = 0
bigger_font_clicks = 0
dark_mode = False
dark_mode_css = """
            <div style="display: none">
                <style>
                    body, .footer {background-color: #333; color: white;}
                    footer {margin-top: auto;}
                    div {background-color: #444; color: white}
                    #input-cards, #input-container  {background-color: #444; white}
                    .card-header, .card-footer {background-color: #4a4a4a;}
                </style>
            </div>
"""


@use_scope('ROOT')
def main():
    clear()
    generate_header()
    user_data = {'username': 'khantthura',
                 'date': '12-05-2024',
                 'display_name': 'Khant Thura',
                 'content': 'This is a test content to see if the function is working'}

    generate_card(user_data)

    # put_buttons(['Login', 'Register'], onclick=[login, register])


def edit_content():
    clear()
    generate_header()
    user_data = input_group('Edit Content', [
        textarea('Content', name='content', value='This is a test content to see if the function is working')
    ], cancelable=True)

    if user_data is None:
        run_js('window.location.href = "/"')


# function that switches between dark and light mode
def toggle_dark_mode():
    global dark_mode
    dark_mode = not dark_mode
    print(dark_mode)
    run_js('window.location.reload()')


def smaller_font():
    global smaller_font_clicks, bigger_font_clicks
    js_code = f'''
        let allElements = document.querySelectorAll('p,h2,h3,h4,h5,h6');
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
            let allElements = document.querySelectorAll('p, h2, h3, h4, h5, h6');
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
    if dark_mode:
        put_html(dark_mode_css)
    global smaller_font_clicks, bigger_font_clicks
    smaller_font_clicks, bigger_font_clicks = 0, 0
    put_buttons([
        {'label': '+', 'value': 'bigger', 'color': 'primary'},
        {'label': '-', 'value': 'smaller', 'color': 'info'},
        {'label': 'Dark Mode', 'value': 'dark_mode', 'color': 'dark'}
    ], onclick=[bigger_font, smaller_font, toggle_dark_mode]).style(
        'float:right')
    put_html(f'''
        <h1>
        Welcome to GBB-ELI
        <p class="h5">A parking lot management system for Gateshead Bike Users</p>
        </h1>
        ''')


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
                <a href="/?app=edit"><button class="btn btn-primary">Edit</button></a>
                <button class="btn btn-danger">Delete</button>
            </div>
        </div>
        ''')


if __name__ == '__main__':
    # Defining routes for the server so that it is navigable through html buttons and links
    routes = {
        'index': main,
        'edit': edit_content
    }
    start_server(routes, port=8080, host='localhost', debug=True)
