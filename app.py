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


# initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://jfoiyrnh:rbdDeE-lTR1FdAOQMiRW_H3Ht1Zt5BLW@isilo.db.elephantsql.com:5432/jfoiyrnh'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# extensions
db = SQLAlchemy(app)
auth = HTTPBasicAuth()
api = Api(app, version='1.0', title='FreeGenes Collections',
            description='FreeGenes API',
            )
migrate = Migrate(app, db)
db.UUID = UUID
#######################
### User management ###
#######################

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.UUID, primary_key=True)
    username = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(64))

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        user = User.query.get(data['id'])
        return user

@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


@app.route('/api/users', methods=['POST'])
def new_user():
    username = request.json.get('username')
    password = request.json.get('password')
    if username is None or password is None:
        abort(400)    # missing arguments
    if User.query.filter_by(username=username).first() is not None:
        abort(400)    # existing user
    user = User(username=username)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return (jsonify({'username': user.username}), 201,
            {'Location': url_for('get_user', id=user.id, _external=True)})


@app.route('/api/users/<int:id>')
def get_user(id):
    user = User.query.get(id)
    if not user:
        abort(400)
    return jsonify({'username': user.username})


@app.route('/api/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})


@app.route('/api/resource')
@auth.login_required
def get_resource():
    return jsonify({'data': 'Hello, %s!' % g.user.username})



#################
### FreeGenes ###
#################

tags_collection = db.Table('tags_collection',
    db.Column('tags_uuid', db.UUID(as_uuid=True), db.ForeignKey('tags.uuid'), primary_key=True),
    db.Column('collection_uuid', db.UUID(as_uuid=True), db.ForeignKey('collections.uuid'), primary_key=True, nullable=True),
)

tags_parts = db.Table('tags_parts',
    db.Column('tags_uuid', db.UUID(as_uuid=True), db.ForeignKey('tags.uuid'), primary_key=True),
    db.Column('part_uuid', db.UUID(as_uuid=True), db.ForeignKey('parts.uuid'),primary_key=True,nullable=True),
)


class Collection(db.Model):
    __tablename__ = 'collections'
    uuid = db.Column(db.UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    
    status = db.Column(db.String) # planned, in-progress

    parts = db.relationship('Part',backref='collections')
    parent_uuid = db.Column(db.UUID, db.ForeignKey('collections.uuid'),
            nullable=True)
    children = db.relationship('Collection')

    tags = db.relationship('Tag', secondary=tags_collection, lazy='subquery',
        backref=db.backref('collections', lazy=True))
 
    name = db.Column(db.String)
    readme = db.Column(db.String)

    def toJSON(self):
        tags = []
        for tag in self.tags:
            tags.append(tag.tag)
        return {'uuid':self.uuid,'time_created':self.time_created,'time_updated':self.time_updated,'status':self.status,'tags':tags,'name':self.name,'readme':self.readme,'parent_uuid':self.parent_uuid}


class Part(db.Model):
    __tablename__ = 'parts'
    uuid = db.Column(db.UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    status = db.Column(db.String)

    name = db.Column(db.String)
    description = db.Column(db.String)

    gene_id = db.Column(db.String)
    part_type = db.Column(db.String)
    original_sequence = db.Column(db.String)
    optimized_sequence = db.Column(db.String)
    synthesized_sequence = db.Column(db.String)
    full_sequence = db.Column(db.String)
    genbank = db.Column(db.JSON, nullable=True)

    vector = db.Column(db.String)
    primer_for = db.Column(db.String)
    primer_rev = db.Column(db.String)
    barcode = db.Column(db.String)

    vbd = db.Column(db.String)
    resistance = db.Column(db.String) # amp,kan,cam

    tags = db.relationship('Tag', secondary=tags_parts, lazy='subquery',
        backref=db.backref('parts', lazy=True))

    collection_id = db.Column(db.UUID, db.ForeignKey('collections.uuid'),
            nullable=False)


    def toJSON(self):
        tags = []
        for tag in self.tags:
            tags.append(tag.tag)
        # Return collection ID as well
        return {'uuid':self.uuid,'time_created':self.time_created,'time_updated':self.time_updated,'status':self.status,'tags':tags,'name':self.name,'description':self.description,'gene_id':self.gene_id,'part_type':self.part_type,'original_sequence':self.original_sequence,'optimized_sequence':self.optimized_sequence,'synthesized_sequence':self.synthesized_sequence,'full_sequence':self.full_sequence,'genbank':self.genbank,'vector':self.vector,'primer_for':self.primer_for,'primer_rev':self.primer_rev,'barcode':self.barcode,'vbd':self.vbd,'resistance':self.resistance}

class Tag(db.Model):
    __tablename__ = 'tags'
    uuid = db.Column(db.UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    tag = db.Column(db.String)

    def toJSON(self):
        return {'tag':tag}


def request_to_class(dbclass,json_request):
    tags = []
    for k,v in json_request.items():
        if k != 'tags':
            setattr(dbclass, k, v)
        if k == 'tags' and v != []:
            for tag in v:
                tags_in_db = Tag.query.filter_by(tag=tag).all()
                if len(tags_in_db) == 0:
                    tags.append(Tag(tag=tag))
                else:
                    tags.append(tags_in_db[0])
    dbclass.tags = []
    for tag in tags:
        dbclass.tags.append(tag)
    return dbclass

###################
### Collections ###
###################
ns_collection = api.namespace('collections', description='Collection collection definitions')
collection_model = api.model("collection", {
    "name": fields.String(),
    "readme": fields.String(),
    "tags": fields.List(fields.String),
    "parent_uuid": fields.String()
    })

@ns_collection.route('/')
class CollectionListRoute(Resource): 
    '''Shows all collections and allows you to post new collections'''
    @ns_collection.doc('collection_list')
    def get(self):
        '''Lists all collections'''
        return jsonify([collection.toJSON() for collection in Collection.query.all()])

    @ns_collection.doc('collection_create')
    @api.expect(collection_model)
    def post(self):
        '''Create new collection'''
        collection = request_to_class(Collection(), request.get_json())
        if 'uuid' in request.get_json():
            collection.uuid=request.get_json().get('uuid')
        db.session.add(collection)
        db.session.commit()
        return jsonify(collection.toJSON())

@ns_collection.route('/<uuid>')
class CollectionRoute(Resource):
    '''Shows a single collection and allows you to delete or update preexisting collections'''
    @ns_collection.doc('collection_get')
    def get(self,uuid):
        '''Get a single collection'''
        return jsonify(Collection.query.filter_by(uuid=uuid).first().toJSON())
    
    @ns_collection.doc('collection_delete')
    def delete(self,uuid):
        '''Delete a single collection'''
        db.session.delete(Collection.query.get(uuid))
        db.session.commit()
        return jsonify({'success':True})

    @ns_collection.doc('collection_put')
    @api.expect(collection_model)
    def put(self,uuid):
        '''Update a single collection'''
        # TODO add schema validator
        collection = Collection.query.filter_by(uuid=uuid).first()
        updated_collection = request_to_class(collection,request.get_json())
        db.session.commit()
        return jsonify(updated_collection.toJSON())

@ns_collection.route('/full/<uuid>')
class CollectionAllRoute(Resource):
    '''Shows a collection all the way down to the root'''
    @ns_collection.doc('collection_get_all')
    def get(self,uuid):
        '''Get a single collection and everything down the tree'''
        def recursive_down(collection):
            dictionary = collection.toJSON()
            dictionary['parts'] = [part.toJSON() for part in collection.parts]
            if len(collection.children) > 0:
                dictionary['subcollections'] = [recursive_down(subcollection) for subcollection in collection.children]
            return dictionary
        return jsonify(recursive_down(Collection.query.filter_by(uuid=uuid).first()))


        

#############
### Parts ###
#############

# TODO self insert dat gene_id
# {'uuid':self.uuid,'time_created':self.time_created,'time_updated':self.time_updated,'status':self.status,'tags':tags,'name':self.name,'description':self.description,'gene_id':self.gene_id,'part_type':self.part_type,'original_sequence':self.original_sequence,'optimized_sequence':self.optimized_sequence,'synthesized_sequence':self.synthesized_sequence,'full_sequence':self.full_sequence,'genbank':self.genbank,'vector':self.vector,'primer_for':self.primer_for,'primer_rev':self.primer_rev,'barcode':self.barcode,'vbd':self.vbd,'resistance':self.resistance}
ns_part = api.namespace('parts', description='Part part definitions')
part_model = api.model("part", {
    "name": fields.String(),
    "description": fields.String(),
    "tags": fields.List(fields.String),
    "gene_id": fields.String(),
    "part_type": fields.String(), # TODO enum
    "original_sequence": fields.String(),
    "optimized_sequence": fields.String(),
    "synthesized_sequence": fields.String(),
    "full_sequence": fields.String(),
    "genbank": fields.Raw(),
    "vector": fields.String(),
    "primer_for": fields.String(),
    "primer_rev": fields.String(),
    "barcode": fields.String(),
    "vbd": fields.String(),
    "resistance": fields.String(),
    "collection_id": fields.String()
    })

@ns_part.route('/')
class PartListRoute(Resource):
    '''Shows all parts and allows you to post new parts'''
    @ns_part.doc('part_list')
    def get(self):
        '''Lists all parts'''
        return jsonify([part.toJSON() for part in Part.query.all()])

    @ns_part.doc('part_create')
    @api.expect(part_model)
    def post(self):
        '''Create new part'''
        part = request_to_class(Part(), request.get_json())
        if 'uuid' in request.get_json():
            part.uuid=request.get_json().get('uuid')
        db.session.add(part)
        db.session.commit()
        return jsonify(part.toJSON())

@ns_part.route('/<uuid>')
class PartRoute(Resource):
    '''Shows a single part and allows you to delete or update preexisting parts'''
    @ns_part.doc('part_get')
    def get(self,uuid):
        '''Get a single part'''
        return jsonify(Part.query.filter_by(uuid=uuid).first().toJSON())

    @ns_part.doc('part_delete')
    def delete(self,uuid):
        '''Delete a single part'''
        db.session.delete(Part.query.get(uuid))
        db.session.commit()
        return jsonify({'success':True})

    @ns_part.doc('part_put')
    @api.expect(part_model)
    def put(self,uuid):
        '''Update a single part'''
        # Remember, tags are always reset.  
        part = Part.query.filter_by(uuid=uuid).first()
        updated_part = request_to_class(part,request.get_json())
        db.session.commit()
        return jsonify(updated_part.toJSON())




if __name__ == '__main__':
    app.run(debug=True)

