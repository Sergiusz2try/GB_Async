from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, registry
from corelib.common.variables import *
import datetime

mapper_registry = registry()

class ServerStorage:

    class AllUsers:
        def __init__(self, username):
            self.id = None
            self.name = username
            self.last_login = datetime.datetime.now()
            

    class ActiveUsers:
        def __init__(self, user_id, ip_address, port, login_time):
            self.id = None
            self.user_id = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time
            

    class LoginHistory:
        def __init__(self, name, date, ip, port):
            self.id = None
            self.name = name
            self.date = date
            self.ip = ip
            self.port = port
            

    class UsersContacts:
        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact


    class UsersHistory:
        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0


    def __init__(self, path):
        self.database_engine = create_engine(f"sqlite:///databases/server_db/{path}", echo=False, pool_recycle=7200,
                                                connect_args={"check_same_thread": False})
        self.metadata = MetaData()

        users_table = Table(
            "Users", self.metadata,
            Column("id", Integer, primary_key=True),
            Column("name", String, unique=True),
            Column("last_login", DateTime)
        )

        active_users_table = Table(
            "Active_users", self.metadata,
            Column("id", Integer, primary_key=True),
            Column("user", ForeignKey("Users.id"), unique=True),
            Column("ip_address", String),
            Column("port", Integer),
            Column("login_time", DateTime)
        )

        users_login_history = Table(
            "Login_history", self.metadata,
            Column("id", Integer, primary_key=True),
            Column("name", ForeignKey("Users.id")),
            Column("date_time", DateTime),
            Column("ip", String),
            Column("port", Integer)
        )

        contacts = Table(
            "Contacts", self.metadata,
            Column("id", Integer, primary_key=True),
            Column("user", ForeignKey("Users.id")),
            Column("contact", ForeignKey("Users.id"))
        )

        users_history_table = Table(
            "History", self.metadata,
            Column("id", Integer, primary_key=True),
            Column("user", ForeignKey("Users.id")),
            Column("sent", Integer),
            Column("accepted", Integer)
        )

        # Create tables
        self.metadata.create_all(self.database_engine)

        # Create display
        mapper_registry.map_imperatively(self.AllUsers, users_table)
        mapper_registry.map_imperatively(self.ActiveUsers, active_users_table)
        mapper_registry.map_imperatively(self.LoginHistory, users_login_history)
        mapper_registry.map_imperatively(self.UsersContacts, contacts)
        mapper_registry.map_imperatively(self.UsersHistory, users_history_table)

        # Create session
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        # If in active users table exists notes, delete it
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, username, ip, port):
        # Query to database about existing user with name
        rez = self.session.query(self.AllUsers).filter_by(name=username)

        if rez.count():
            user = rez.first()
            user.last_login = datetime.datetime.now()
        else:
            user = self.AllUsers(username)
            self.session.add(user)
            self.session.commit()
            user_in_history = self.UsersHistory(user.id)
            self.session.add(user_in_history)
            self.session.commit()

        new_active_user = self.ActiveUsers(user.id, ip, port, datetime.datetime.now())
        self.session.add(new_active_user)

        history = self.LoginHistory(user.id, datetime.datetime.now(), ip, port)
        self.session.add(history)

        self.session.commit()

    def user_logout(self, username):
        user = self.session.query(self.AllUsers).filter_by(name=username).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

    def process_message(self, sender, recipient):
        # Get id sender and receiver
        sender = self.session.query(self.AllUsers).filter_by(name=sender).first().id
        recipient = self.session.query(self.AllUsers).filter_by(name=recipient).first().id
        # Requests strings on history and improve count
        sender_row = self.session.query(self.UsersHistory).filter_by(user=sender).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.UsersHistory).filter_by(user=recipient).first()
        recipient_row.accepted += 1

        self.session.commit()

    def add_contact(self, user, contact):
        # Get user ID
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(name=contact).first()

        if not contact or self.session.query(self.UsersContacts).filter_by(user=user.id,
                                                                            contact=contact.id).count():
            return

        contact_row = self.UsersContacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    def remove_contact(self, user, contact):
        # Get user ID
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(name=contact).first()

        if not contact:
            return

        # Delete contact
        print(self.session.query(self.UsersContacts).filter(
            self.UsersContacts.user == user.id,
            self.UsersContacts.contact == contact.id
        ).delete())
        self.session.commit()

    def users_list(self):
        query = self.session.query(
            self.AllUsers.name,
            self.AllUsers.last_login
        )

        return query.all()

    def active_users_list(self):
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
    
    def get_contacts(self, username):
        # Requests user
        user = self.session.query(self.AllUsers).filter_by(name=username).one()

        # Requests users contact list
        query = self.session.query(self.UsersContacts, self.AllUsers.name). \
            filter_by(user=user.id). \
            join(self.AllUsers, self.UsersContacts.contact == self.AllUsers.id)

        return [contact[1] for contact in query.all()]

    def message_history(self):
        query = self.session.query(
            self.AllUsers.name,
            self.AllUsers.last_login,
            self.UsersHistory.sent,
            self.UsersHistory.accepted
        ).join(self.AllUsers)

        return query.all()
    
# Отладка
if __name__ == '__main__':
    test_db = ServerStorage("server_base.sqlite")
    test_db.user_login('1111', '192.168.1.113', 8080)
    test_db.user_login('McG2', '192.168.1.113', 8081)
    print(test_db.users_list())
    # print(test_db.active_users_list())
    # test_db.user_logout('McG')
    # print(test_db.login_history('re'))
    # test_db.add_contact('test2', 'test1')
    # test_db.add_contact('test1', 'test3')
    # test_db.add_contact('test1', 'test6')
    # test_db.remove_contact('test1', 'test3')
    test_db.process_message('McG2', '1111')
    print(test_db.message_history())