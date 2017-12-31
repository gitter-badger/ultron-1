# -*-coding: utf-8 -*-

"""
Author          : Arijit Basu
Email           : sayanarijit@gmail.com
"""

from pymongo import MongoClient
from ultron.config import DB_URL


client = MongoClient(DB_URL)
db = client.ultronstorage
db_config = db['config']
db_reports =db['reports']
db_inventory = db['inventory']
db_admins = db['admins']


class BaseModel:
    """
    Base class for all models
    """
    def __init__(self, collection):
        self.collection = collection

    def get(self, admin, name, attr=None, default=None):
        """
        Returns the requested value if found else the specified value
        """
        found = self.collection.find_one({'name': name, 'admin': admin})
        if attr is None and found is not None:
            return found
        return found.get(attr, default) if found else default

    def set(self, admin, name, attr, value):
        """
        Updates/Inserts key-value pair and returns True
        If no change is made, returns False
        """
        result = self.collection.update_one({'name': name, 'admin': admin},
                                            {'$set': {attr: value}},
                                            upsert=True)
        return False if result.modified_count == 0 else True

    def unset(self, admin, name, attr=None):
        """
        Deletes document or key-value pair and returns True
        If no change is made, returns False
        """
        if attr is None:
            result = self.collection.find_one_and_delete({
                'name': name,
                'admin': admin
            })
            return False if result is None else True

        result = self.collection.update_one({'name': name, 'admin': admin},
                                            {'$unset': {attr: 1}})
        return False if result.modified_count == 0 else True

    def list(self, admin, attr=None, unique=False):
        """
        Returns all values / unique values
        """
        if attr is None: attr = 'name'
        found = self.collection.find({'admin': admin})
        result = list(map(lambda x: x[attr], found))
        return list(set(result)) if unique else result


class Config(BaseModel):
    """
    To manipulate all configurations
    """
    def __init__(self):
        BaseModel.__init__(self, db_config)


class Inventory(BaseModel):
    """
    To manipulate inventory
    """
    def __init__(self):
        BaseModel.__init__(self, db_inventory)


class Reports(BaseModel):
    """
    To manipulate reports
    """
    def __init__(self):
        BaseModel.__init__(self, db_reports)

    def save(self, client):
        """
        Save client into DB
        """
        data = client.dict()
        del data['reportname']
        del data['name']
        result = self.collection.update_one(
            {'name': client.reportname,
             'clientname': client.name},
            {'$set': data}, upsert=True)
        return False if result.modified_count == 0 else True

    def load(self, client):
        """
        Load client from DB
        """
        found = self.collection.find_one({'name':client.reportname,
                                     'clientname': client.name,
                                     'admin': client.admin},
                                    {'_id': 0})
        if found is not None:
            data = dict(found)
            data['name'] = found['clientname']
            data['reportname'] = found['name']
            client.__dict__.update(data)
            return True
        return False

    def cleanup(self, client):
        """
        Removes client from report
        """
        result = self.collection.delete_one({'name': client.reportname,
            'clientname': client.name, 'admin': client.admin})
        return False if result is None else True


class Admins(object):
    """
    To authorize admins to run this app
    """
    def __init__(self):
        self.collection = db_admins

    def get(self, name, attr=None, default=None):
        """
        Returns the requested value if found else the specified value
        """
        found = self.collection.find_one({'name': name})
        if attr is None and found is not None:
            return found
        return found.get(attr, default) if found else default

    def set(self, name, attr, value):
        """
        Updates/Inserts key-value pair and returns True
        If no change is made, returns False
        """
        result = self.collection.update_one({'name': name},
                                            {'$set': {attr: value}},
                                            upsert=True)
        return False if result.modified_count == 0 else True

    def unset(self, name, attr=None):
        """
        Deletes document or key-value pair and returns True
        If no change is made, returns False
        """
        if attr is None:
            result = self.collection.find_one_and_delete({'name': name})
            return False if result is None else True

        result = self.collection.update_one({'name': name},
                                            {'$unset': {attr: 1}})
        return False if result.modified_count == 0 else True

    def list(self, attr=None, unique=False):
        """
        Returns all values / unique values
        """
        if attr is None: attr = 'name'
        found = self.collection.find()
        result = list(map(lambda x: x[attr], found))
        return list(set(result)) if unique else result

    def save(self, admin):
        """
        Saves admin into DB
        """
        data = admin.dict()
        result = self.collection.update_one(
            {'name': admin.name},
            {'$set': data},
            upsert=True
        )
        return False if result.modified_count == 0 else True

    def load(self, admin):
        """
        Loads admin from DB
        """
        found = self.collection.find_one({'name': admin.name}, {'_id': 0})
        if found is not None:
            data = dict(found)
            admin.__dict__.update(data)
            return True
        return False

    def cleanup(self, admin):
        """
        Removes admin from DB
        """
        result = self.collection.delete_one({'name': admin.name})
        return False if result is None else True
