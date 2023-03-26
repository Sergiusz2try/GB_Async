from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, registry
from ..common.variables import *
import datetime


class ServerStorage:

    class AllUsers:

        def __init__(self, username):
            self.name = username
            self.last_login = datetime.datetime.now()
            self.id = None


    class ActiveUsers:

        def __init__(self, user_id, ip_address, port, login_time):
            self.user_id = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time
            self.id = None


    class LoginHistory:

        def __init__(self, name, date, ip, port):
            self.name = name
            self.date = date
            self.ip = ip
            self.port = port
            self.id = None


    def __init__(self):
        self.database_engine = create_engine(SERVER_DATABASE, echo=False, pool_recycle=7200)
        self.metadata = MetaData()

        users_table = Table(
            "Users", self.metadata,
            Column("id", Integer, primary_key=True),
            Column("username", String, unique=True),
            Column("last_login", DateTime)
        )

        active_users_table = Table(
            "ActiveUsers", self.metadata,
            Column("id", Integer, primary_key=True),
            Column("user_id", ForeignKey("Users.id")),
            Column("ip_address", String),
            Column("port", Integer),
            Column("login_time", DateTime)
        )

        users_login_history = Table(
            "Login_history", self.metadata,
            Column("id", Integer, primary_key=True),
            Column("user", ForeignKey("Users.id")),
            Column("datetime", DateTime),
            Column("ip", String),
            Column("port", Integer)
        )

        self.metadata.create_all(self.database_engine)

        registry.map_imperatively(self.AllUsers, users_table)
        registry.map_imperatively(self.ActiveUsers, active_users_table)
        registry.map_imperatively(self.LoginHistory, users_login_history)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session

    def user_login(self, username, ip, port):
        print(username, ip, port)
        rez = self.session.query(self.AllUsers).filter_by(name=username)

        if rez.count():
            user = rez.first()
            user.last_login = datetime.datetime.now()
        else:
            user = self.AllUsers(username)
            self.session.add(user)
            self.session.commit()

        new_active_user = self.ActiveUser(user.id, ip, port, datetime.datetime.now())
        self.session.add(new_active_user)

        history = self.LoginHistory(user.id, datetime.datetime.now(), ip, port)
        self.session.add(history)

        self.session.commit()

    def user_logout(self, username):
        user = self.session.query(self.AllUsers).filter_by(name=username)
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

    def users_list(self):
        query = self.session.query(
            self.AllUsers.name,
            self.ActiveUsers.ip_address,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time
        ).join(self.AllUsers)

        return query.all()
    
    def login_history(self, username=None):
        query = self.session.query(
            self.AllUsers.name,
            self.LoginHistory.date,
            self.LoginHistory.ip,
            self.LoginHistory.port
        ).join(self.AllUsers)

        if username:
            query = query.filter(self.AllUsers.name == username)
        return query.all()
