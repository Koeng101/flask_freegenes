from .models import *
from flask_restplus import Api, Resource, fields, Namespace
from flask import Flask, abort, request, jsonify, g, url_for

from .config import LOGIN_KEY

def request_to_class(dbclass,json_request):
    tags = []
    for k,v in json_request.items():
        if k == 'tags' and v != []:
            dbclass.tags = []
            for tag in v:
                tags_in_db = Tag.query.filter_by(tag=tag).all()
                if len(tags_in_db) == 0:
                    tags.append(Tag(tag=tag))
                else:
                    tags.append(tags_in_db[0])
        elif k == 'samples' and v != []:
            dbclass.samples = []
            [dbclass.samples.append(Sample.query.filter_by(uuid=uuid).first()) for uuid in v] # In order to sue 
        elif k == 'wells' and v != []:
            dbclass.wells = []
            [dbclass.samples.append(Well.query.filter_by(uuid=uuid).first()) for uuid in v]
        elif k == 'derived_from' and v == "":
            pass
        elif k == 'fastqs' and v != []:
            dbclass.fastqs = []
            [dbclass.fastqs.append(Fastq.query.filter_by(uuid=uuid).first()) for uuid in v]
        else:
            setattr(dbclass,k,v)
    for tag in tags:
        dbclass.tags.append(tag)
    return dbclass

def crud_get_list(cls,full=None):
    return jsonify([obj.toJSON(full=full) for obj in cls.query.all()])

def crud_post(cls,post,database):
    obj = request_to_class(cls(),post)
    database.session.add(obj)
    database.session.commit()
    return jsonify(obj.toJSON())

def crud_get(cls,uuid,full=None):
    return jsonify(cls.query.filter_by(uuid=uuid).first().toJSON(full=full))

def crud_delete(cls,uuid,database):
    database.session.delete(cls.query.get(uuid))
    database.session.commit()
    return jsonify({'success':True})

def crud_put(cls,uuid,post,database):
    obj = cls.query.filter_by(uuid=uuid).first()
    updated_obj = request_to_class(obj,post)
    db.session.commit()
    return jsonify(obj.toJSON())

class CRUD():
    def __init__(self, namespace, cls, model, name):
        self.ns = namespace
        self.cls = cls
        self.model = model
        self.name = name

        @self.ns.route('/')
        class ListRoute(Resource):
            @self.ns.doc('{}_list'.format(self.name))
            def get(self):
                return crud_get_list(cls)

            @self.ns.doc('{}_create'.format(self.name))
            @self.ns.expect(model)
            @auth.login_required
            def post(self):
                return crud_post(cls,request.get_json(),db)

        @self.ns.route('/<uuid>')
        class NormalRoute(Resource):
            @self.ns.doc('{}_get'.format(self.name))
            def get(self,uuid):
                return crud_get(cls,uuid)

            @self.ns.doc('{}_delete'.format(self.name))
            @auth.login_required
            def delete(self,uuid):
                return crud_delete(cls,uuid,db)

            @self.ns.doc('{}_put'.format(self.name))
            @self.ns.expect(self.model)
            @auth.login_required
            def put(self,uuid):
                return crud_put(cls,uuid,request.get_json(),db)

        @self.ns.route('/full')
        class FullListRoute(Resource):
            @self.ns.doc('{}_full'.format(self.name))
            def get(self):
                return crud_get_list(cls,full='full')

        @self.ns.route('/full/<uuid>')
        class FullRoute(Resource):
            @self.ns.doc('{}_full'.format(self.name))
            def get(self,uuid):
                return crud_get(cls,uuid,full='full')

#########
# Users #
#########

ns_users = Namespace('users', description='User login')
user_model = ns_users.model("user", {
    "username": fields.String(),
    "password": fields.String(),
    "login_key": fields.String()
    })

@ns_users.route('/')
class UserPostRoute(Resource):
    @ns_users.doc('user_create')
    @ns_users.expect(user_model)
    def post(self):
        '''Post new user. Checks for Login key'''
        username = request.json.get('username')
        password = request.json.get('password')
        login_key = request.json.get('login_key')
        if username is None or password is None:
            abort(400)    # missing arguments
        if User.query.filter_by(username=username).first() is not None:
            abort(400)    # existing user
        if login_key != LOGIN_KEY:
            abort(403)  # missing login key
        user = User(username=username)
        user.hash_password(password)
        db.session.add(user)
        db.session.commit()
        return jsonify({'username': user.username})

@ns_users.route('/token')
class TokenRoute(Resource):
    @ns_users.doc('user_token')
    @auth.login_required
    def get(self):
        token = g.user.generate_auth_token(600)
        return jsonify({'token': token.decode('ascii'), 'duration': 600})

@ns_users.route('/resource')
class ResourceRoute(Resource):
    @ns_users.doc('user_resource')
    @auth.login_required
    def get(self):
        return jsonify({'data': 'Success {}'.format(g.user.username)})

        

###############
# Collections #
###############

ns_collection = Namespace('collections', description='Collections')
collection_model = ns_collection.model("collection", {
    "name": fields.String(),
    "readme": fields.String(),
    "tags": fields.List(fields.String),
    "parent_uuid": fields.String()
    })

CRUD(ns_collection,Collection,collection_model,'collection')

@ns_collection.route('/recurse/<uuid>')
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

#########
# Parts #
#########

ns_part = Namespace('parts', description='Parts')
part_model = ns_part.model("part", {
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
    "translation": fields.String(),
    "collection_id": fields.String(),
    "parent_uuid": fields.String(),
    })
CRUD(ns_part,Part,part_model,'part')



