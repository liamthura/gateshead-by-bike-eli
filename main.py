import sqlalchemy as sa
from pywebio import *
from pywebio.input import *
from pywebio.output import *
from sqlalchemy import Integer, ForeignKey
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker, declarative_base, relationship

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

    # Structuring output of Role object for better readability
    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"


# Defining the Post class with table name 'posts'
# class ParkingPost(Base):
#     pass
#
#
# class ParkingRating(Base):
#     pass
#
#
# class Thread(Base):
#     pass
#
#
# class ContentReport(Base):
#     pass
#
#
# class CrimeReport(Base):
#     pass
#
#
# class PoliceNotification(Base):
#     pass
#
#
# class SiteNotification(Base):
#     pass

# Base.metadata.create_all(db)

@use_scope('ROOT')
def main():
    clear()
    put_html(f'''
    <h1>
    Welcome to GBB-ELI
    <small class="text-body-secondary">A parking lot management system for Gateshead Bike Users</small>
    </h1>
    <h4>
    Khant Thura
    <small class="text-body-secondary">2022-03-12</small>
    </h4>
    ''')
    # put_buttons(['Login', 'Register'], onclick=[login, register])


if __name__ == '__main__':
    start_server(main, port=8080, host='localhost', debug=True)
