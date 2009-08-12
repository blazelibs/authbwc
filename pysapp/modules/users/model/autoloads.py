from sqlalchemy import Table
from pysmvt import db

vuserperms = Table('v_users_permissions', db.meta, autoload=True, autoload_with=db.engine)