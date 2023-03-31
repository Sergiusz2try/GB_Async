from sqlalchemy import create_engine, Table, Column, Integer, String, Text, MetaData, DateTime
from sqlalchemy.orm import registry, sessionmaker
from ..common.variables import *
import datetime

mapper_registry = registry()

class ClientDatabase:

    class KnownUsers:
        def __init__(self, user):
            self.id = None
            self.username = user

    
    class MessageHistory:
        def __init__(self, from_user,to_user, message):
            self.id = None
            self.from_user = from_user
            self.to_user = to_user
            self.message = message
            self.date = datetime.datetime.now()


    class Contacts:
        def __init__(self, contact):
            self.id = None
            self.name = contact


    def __init__(self, name):
        self.database_engine = create_engine(f"sqlite:///databases/clients_db/client_{name}.sqlite", echo=False,
                                            connect_args={"check_same_thread": False})
        
        self.metadata = MetaData()

        users = Table(
            "known_users", self.metadata,
            Column("id", Integer, primary_key=True),
            Column("username", String)
        )

        history = Table(
            "message_history", self.metadata,
            Column("id", Integer, primary_key=True),
            Column("from_user", String),
            Column("to_user", String),
            Column("message", Text),
            Column("date", DateTime)
        )

        contacts = Table(
            "contacts", self.metadata,
            Column("id", Integer, primary_key=True),
            Column("name", String, unique=True)
        )

        self.metadata.create_all(self.database_engine)

        mapper_registry.map_imperatively(self.KnownUsers, users)
        mapper_registry.map_imperatively(self.MessageHistory, history)
        mapper_registry.map_imperatively(self.Contacts, contacts)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_contact(self, contact):
        if not self.session.query(self.Contacts).filter_by(name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    def del_contact(self, contact):
        self.session.query(self.Contacts).filter_by(name=contact).delete()

    def add_user(self, users_list):
        self.session.query(self.KnownUsers).delete()
        for user in users_list:
            user_row = self.KnownUsers(user)
            self.session.add(user_row)
        self.session.commit()

    def save_message(self, from_user, to_user, message):
        message_row = self.MessageHistory(from_user, to_user, message)
        self.session.add(message_row)
        self.session.commit()

    def get_contacts(self):
        return [contact[0] for contact in self.session.query(self.Contacts.name).all()]
    
    def get_users(self):
        return [user[0] for user in self.session.query(self.KnownUsers.username).all()]
    
    def check_user(self, user):
        if self.session.query(self.KnownUsers).filter_by(username=user).count():
            return True
        else:
            return False
        
    def check_contact(self, contact):
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        else:
            return False
        
    def get_history(self, from_who=None, to_who=None):
        query = self.session.query(self.MessageHistory)
        if from_who:
            query = query.filter_by(from_user=from_who)
        if to_who:
            query = query.filter_by(to_user=to_who)
        return [(history_row.form_user, history_row.to_user, history_row.message, history_row.date)
                for history_row in query.all()]
