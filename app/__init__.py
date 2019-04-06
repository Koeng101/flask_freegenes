#!/usr/bin/env python
import os
from flask import Flask, abort, request, jsonify, g, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

from flask_expects_json import expects_json # Json schema

from flask_restplus import Api, Resource, fields
from flask.views import MethodView

from flask_migrate import Migrate

import json
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy
from sqlalchemy.sql import func

from .config import URL
from .config import SECRET_KEY
from .config import DEV
from .config import LOGIN_KEY
from .config import PREFIX

from .models import db

from .routes import api as collection

# initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = URL
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# extensions
db.init_app(app)
auth = HTTPBasicAuth()
api = Api(app, version='1.1', title='FreeGenes Collections',
            description='FreeGenes API',
            )

api.add_namespace(collection)
migrate = Migrate(app, db)

if DEV == True:
    app.run(debug=True)
elif DEV == False:
    app.run(host='0.0.0.0')
