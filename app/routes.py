from .models import *
from flask_restplus import Api, Resource, fields, Namespace
from flask import Flask, abort, request, jsonify, g, url_for

# Abstractions
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

def crud_get_list(cls):
    return jsonify([obj.toJSON() for obj in cls.query.all()])
def crud_post(cls,post,database):
    obj = request_to_class(cls(),post)
    database.session.add(obj)
    database.session.commit()
    return jsonify(obj.toJSON())
def crud_get(cls,uuid):
    return jsonify(cls.query.filter_by(uuid=uuid).first().toJSON())
def crud_delete(cls,uuid,database):
    database.session.delete(cls.query.get(uuid))
    database.session.commit()
    return jsonify({'success':True})
def crud_put(cls,uuid,post,database):
    obj = cls.query.filter_by(uuid=uuid).first()
    updated_obj = request_to_class(obj,post)
    db.session.commit()
    return jsonify(obj.toJSON())

###################
### COLLECTIONS ###
###################

api = Namespace('collections', description='Collections')
collection_model = api.model("collection", {
    "name": fields.String(),
    "readme": fields.String(),
    "tags": fields.List(fields.String),
    "parent_uuid": fields.String()
    })

@api.route('/')
class CollectionListRoute(Resource):
    @api.doc('collection_list')
    def get(self):
        return crud_get_list(Collection)

    @api.doc('collection_create')
    @api.expect(collection_model)
    @auth.login_required
    def post(self):
        return crud_post(Collection,request.get_json(),db)

@api.route('/<uuid>')
class CollectionRoute(Resource):
    @api.doc('collection_get')
    def get(self,uuid):
        return crud_get(Collection,uuid)

    @api.doc('collection_delete')
    @auth.login_required
    def delete(self,uuid):
        return crud_delete(Collection,uuid,db)

    @api.doc('collection_put')
    @api.expect(collection_model)
    @auth.login_required
    def put(self,uuid):
        return crud_put(Collection,uuid,request.get_json(),db)

@api.route('/full/<uuid>')
class CollectionAllRoute(Resource):
    '''Shows a collection all the way down to the root'''
    @api.doc('collection_get_all')
    def get(self,uuid):
        '''Get a single collection and everything down the tree'''
        def recursive_down(collection):
            dictionary = collection.toJSON()
            dictionary['parts'] = [part.toJSON() for part in collection.parts]
            if len(collection.children) > 0:
                dictionary['subcollections'] = [recursive_down(subcollection) for subcollection in collection.children]
            return dictionary
        return jsonify(recursive_down(Collection.query.filter_by(uuid=uuid).first()))

