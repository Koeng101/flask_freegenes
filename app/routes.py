import json
from jsonschema import validate

from .models import *
from flask_restplus import Api, Resource, fields, Namespace 
from flask import Flask, abort, request, jsonify, g, url_for, redirect

from .config import PREFIX
from .config import LOGIN_KEY
from .config import SPACES
from .config import BUCKET        
#from dna_designer import moclo, codon

#from .sequence import sequence


###

import os
import jwt
from functools import wraps
from flask import make_response, jsonify
PUBLIC_KEY = os.environ['PUBLIC_KEY']
def requires_auth(roles): # Remove ability to send token as parameter in request
    def requires_auth_decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            def decode_token(token):
                return jwt.decode(token.encode("utf-8"), PUBLIC_KEY, algorithms='RS256')
            try:
                decoded = decode_token(str(request.headers['Token']))
            except Exception as e:
                post_token = False
                if request.json != None:
                    if 'token' in request.json:
                        try:
                            decoded = decode_token(request.json.get('token'))
                            post_token=True
                        except Exception as e:
                            return make_response(jsonify({'message': str(e)}),401)
                if not post_token:
                    return make_response(jsonify({'message': str(e)}), 401)
            if set(roles).isdisjoint(decoded['roles']):
                return make_response(jsonify({'message': 'Not authorized for this endpoint'}),401)
            return f(*args, **kwargs)
        return decorated
    return requires_auth_decorator
ns_token = Namespace('auth_test', description='Authorization_test')
@ns_token.route('/')
class ResourceRoute(Resource):
    @ns_token.doc('token_resource',security='token')
    @requires_auth(['user','moderator','admin'])
    def get(self):
        return jsonify({'message': 'Success'})
###



def request_to_class(dbclass,json_request): # Make classmethod
    tags = []
    for k,v in json_request.items():
        if k == 'tags' and v != []:
            dbclass.tags = []
            set_tags = list(set(v))
            for tag in set_tags:

                tags_in_db = Tag.query.filter_by(tag=tag).all()
                if len(tags_in_db) == 0:
                    tags.append(Tag(tag=tag))
                else:
                    tags.append(tags_in_db[0])
            for tag in tags:
                dbclass.tags.append(tag)
        elif k == 'files' and v != []:
            for file_uuid in v:
                files_in_db = File.query.filter_by(uuid=file_uuid).first()
                if len(files_in_db) == 0:
                    pass
                else: 
                    dbclass.files.append(files_in_db[0])
        elif k == 'plates' and v != []:
            dbclass.plates = []
            [dbclass.plates.append(Plate.query.filter_by(uuid=uuid).first()) for uuid in v]
        elif k == 'samples':
            if v != []:
                dbclass.samples = []
                [dbclass.samples.append(Sample.query.filter_by(uuid=uuid).first()) for uuid in v] # In order to sue
        elif k == 'wells' and v != []:
            dbclass.wells = []
            [dbclass.samples.append(Well.query.filter_by(uuid=uuid).first()) for uuid in v]
        elif k == 'platesets' and v != []:
            dbclass.platesets = []
            [dbclass.samples.append(PlateSet.query.filter_by(uuid=uuid).first()) for uuid in v]
        elif k == 'distributions' and v != []:
            dbclass.distributions = []
            [dbclass.samples.append(Distribution.query.filter_by(uuid=uuid).first()) for uuid in v]
        else:
            setattr(dbclass,k,v)
    return dbclass

def crud_get_list(cls,full=None):
    return jsonify([obj.toJSON(full=full) for obj in cls.query.all()])

def crud_post(cls,post,database):
    obj = request_to_class(cls(),post)
    database.session.add(obj)
    database.session.commit()
    return jsonify(obj.toJSON())

def crud_get(cls,uuid,full=None,jsonify_results=True):
    obj = cls.query.filter_by(uuid=uuid).first()
    if obj == None:
        return jsonify([])
    if jsonify_results == True:
        return jsonify(obj.toJSON(full=full))
    else:
        return obj

def crud_delete(cls,uuid,database,constraints={}):
    if constraints != {}:
        for constraint in constraints['delete']:
            if cls.query.filter_by(**{constraint: uuid}).first() != None:
                return make_response(jsonify({'message': 'UUID used elsewhere'}),501)
    database.session.delete(cls.query.get(uuid))
    database.session.commit()
    return jsonify({'success':True})

def crud_put(cls,uuid,post,database):
    obj = cls.query.filter_by(uuid=uuid).first()
    updated_obj = request_to_class(obj,post)
    db.session.commit()
    return jsonify(obj.toJSON())

class CRUD():
    def __init__(self, namespace, cls, model, name, constraints={}, security='token',validate_json=False, custom_post=False):
        self.ns = namespace
        self.cls = cls
        self.model = model
        self.name = name
        self.constraints = constraints

        @self.ns.route('/')
        class ListRoute(Resource):
            @self.ns.doc('{}_list'.format(self.name))
            def get(self):
                return crud_get_list(cls)
            
            if custom_post == False:
                @self.ns.doc('{}_create'.format(self.name),security=security)
                @self.ns.expect(model)
                @requires_auth(['moderator','admin'])
                def post(self):
                    if validate_json == True:
                        try:
                            validate(instance=request.get_json(),schema=cls.validator)
                        except Exception as e:
                            return make_response(jsonify({'message': 'Schema validation failed: {}'.format(e)}),400)
                    if 'uuid' in request.get_json():
                        if cls.query.filter_by(uuid=request.get_json()['uuid']).first() == None:
                            return crud_post(cls,request.get_json(),db)
                        else:
                            return make_response(jsonify({'message': 'UUID taken'}),501)
                    return crud_post(cls,request.get_json(),db)
            else:
                print('Custom post for {}'.format(name))

        @self.ns.route('/<uuid>')
        class NormalRoute(Resource):
            @self.ns.doc('{}_get'.format(self.name))
            def get(self,uuid):
                return crud_get(cls,uuid)

            @self.ns.doc('{}_delete'.format(self.name),security=security)
            @requires_auth(['moderator','admin'])
            def delete(self,uuid):
                return crud_delete(cls,uuid,db,constraints)

            @self.ns.doc('{}_put'.format(self.name),security=security)
            @self.ns.expect(self.model)
            @requires_auth(['moderator','admin'])
            def put(self,uuid):
                return crud_put(cls,uuid,request.get_json(),db)

        @self.ns.route('/full/')
        class FullListRoute(Resource):
            @self.ns.doc('{}_full'.format(self.name))
            def get(self):
                return crud_get_list(cls,full='full')

        @self.ns.route('/full/<uuid>')
        class FullRoute(Resource):
            @self.ns.doc('{}_full_single'.format(self.name))
            def get(self,uuid):
                return crud_get(cls,uuid,full='full')

        @self.ns.route('/validator')
        class ValidatorRoute(Resource):
            @self.ns.doc('{}_validator'.format(self.name))
            def get(self):
                if validate_json==True:
                    return make_response(jsonify(cls.validator),200)
                return make_response(jsonify({'message': 'No validator for object'}),404)


#========#
# Routes #
#========#
        
###

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
            dictionary['parts'] = [part.toJSON(full='full') for part in collection.parts]
            if len(collection.children) > 0:
                dictionary['subcollections'] = [recursive_down(subcollection) for subcollection in collection.children]
            return dictionary
        return jsonify(recursive_down(Collection.query.filter_by(uuid=uuid).first()))

@ns_collection.route('/part_status/<uuid>/<key>')
class CollectionPartStatus(Resource):
    @ns_collection.doc('collection_get_part_status')
    def get(self,key,uuid):
        sql = "SELECT parts.{}, parts.status FROM parts WHERE parts.collection_id='{}'".format(key,uuid)
        result = db.engine.execute(sql)
        dictionary = {}
        for r in result:
            dictionary[str(r[0])] = r[1]
        return jsonify(dictionary)

@ns_collection.route('/part_status/search/<uuid>/<key>/<status>')
class CollectionPartStatus(Resource):
    @ns_collection.doc('collection_get_part_status_search')
    def get(self,key,uuid,status):
        sql = "SELECT parts.{}, parts.status FROM parts WHERE parts.collection_id='{}' AND parts.status='{}'".format(key,uuid,status)
        result = db.engine.execute(sql)
        dictionary = {}
        for r in result:
            dictionary[str(r[0])] = r[1]
        return jsonify(dictionary)

###

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
    "author_uuid": fields.String(),
    "ip_check": fields.String(),
    "ip_check_date": fields.DateTime(),
    "ip_check_ref": fields.String()
    })
CRUD(ns_part,Part,part_model,'part')
@ns_part.route('/get/<key>/<value>')
class PartGeneId(Resource):
    def get(self,key,value):
        kwargs = {key:value}
        parts = Part.query.filter_by(**kwargs)
        if parts.count() == 0:
            return jsonify([])
        else:
            return jsonify([part.toJSON() for part in parts])

@ns_part.route('/collection/<uuid>')
class PartCollection(Resource):
    def get(self,uuid):
        return jsonify([obj.toJSON() for obj in Part.query.filter_by(collection_id=uuid)])

@ns_part.route('/locations/<uuid>')
class PartLocations(Resource):
    def get(self,uuid):
        obj = Part.query.filter_by(uuid=uuid).first()
        results = []
        for sample in obj.samples:
            for well in sample.wells:
                plate = well.plate.toJSON()
                plate['wells'] = well.toJSON()
                results.append(plate)
        return jsonify(results)

###

ns_part_modifiers = Namespace('part_modification', description='Modify parts')


def next_gene_id():
    result = db.engine.execute("SELECT parts.gene_id FROM parts WHERE gene_id IS NOT NULL ORDER BY gene_id DESC LIMIT 1")
    for r in result:
        last_id = r
    last_num = int(last_id[0][-6:])
    print(last_num)
    new_id = PREFIX + str(last_num+1).zfill(6)
    return new_id

@ns_part.route('/next_gene_id')
class NextGeneId(Resource):
    def get(self):
        return jsonify({'gene_id': next_gene_id()})

@ns_part_modifiers.route('/gene_id/<uuid>')
class NewGeneID(Resource):
    @ns_part.doc('new_gene_id',security='token')
    @requires_auth(['moderator','admin'])
    def put(self,uuid):
        obj = Part.query.filter_by(uuid=uuid).first()
        obj.gene_id = next_gene_id()
        db.session.commit()
        return jsonify(obj.toJSON())

###

ns_file = Namespace('files', description='Files')

@ns_file.route('/')
class AllFiles(Resource):
    def get(self):
        return crud_get_list(Files)

@ns_file.route('/<uuid>')
class SingleFile(Resource):
    def get(self,uuid):
        return crud_get(Files,uuid)
    @ns_file.doc('delete_file',security='token')
    @requires_auth(['moderator','admin'])
    def delete(self,uuid):
        file = Files.query.get(uuid)
        print(type(SPACES))
        SPACES.delete_object(Bucket=BUCKET,Key=file.file_name)
        db.session.delete(file)
        db.session.commit()
        return jsonify({'success':True})


@ns_file.route('/upload')
class NewFile(Resource):
    @ns_file.doc('new_file',security='token')
    @requires_auth(['moderator','admin'])
    def post(self):
        json_file = json.loads(request.files['json'].read())
        file = request.files['file']
        new_file = Files(json_file['name'],file)
        db.session.add(new_file)
        db.session.commit()
        return jsonify(new_file.toJSON())

@ns_file.route('/download/<uuid>')
class DownloadFile(Resource):
    def get(self,uuid):
        obj = Files.query.filter_by(uuid=uuid).first()
        return obj.download()




###

ns_author = Namespace('authors', description='Authors')
author_model = ns_part.model("author", {
    "name": fields.String(),
    "email": fields.String(),
    "tags": fields.List(fields.String),
    "affiliation": fields.String(),
    "orcid": fields.String(), # TODO enum
    })
CRUD(ns_author,Author,author_model,'author')

###

ns_organism = Namespace('organisms', description='Organisms')
organism_model = ns_organism.model("organism", {
    "name": fields.String(),
    "description": fields.String(),
    "tags": fields.List(fields.String),
    "genotype": fields.String(),
    })
CRUD(ns_organism,Organism,organism_model,'organism')

###
###
###

ns_protocol = Namespace('protocols', description='Protocols')
protocol_model = ns_protocol.schema_model('protocol', Protocol.validator)
CRUD(ns_protocol,Protocol,protocol_model,'protocol',validate_json=True)

###

ns_plate = Namespace('plates', description='Plates')
plate_model = ns_plate.schema_model('plate', Plate.validator)
CRUD(ns_plate,Plate,plate_model,'plate',validate_json=True)

def plate_recurse(uuid):
    obj = Plate.query.filter_by(uuid=uuid).first()
    wells = []
    for well in obj.wells:
        samples = []
        for sample in well.samples:
            to_add = sample.toJSON()
            to_add['part'] = sample.part.toJSON()
            samples.append(to_add)
        to_add = well.toJSON()
        to_add['samples'] = samples
        wells.append(to_add)
    plate = obj.toJSON()
    plate['wells'] = wells
    return plate

@ns_plate.route('/recurse/<uuid>')
class PlateSamples(Resource):
    def get(self,uuid):
        return jsonify(plate_recurse(uuid))

###

ns_sample = Namespace('samples', description='Samples')
sample_model = ns_sample.schema_model('sample', Sample.validator)
CRUD(ns_sample,Sample,sample_model,'sample',constraints={'delete': ['derived_from']},validate_json=True)

###

ns_well = Namespace('wells', description='Wells')
well_model = ns_well.schema_model('well', Well.validator)
CRUD(ns_well,Well,well_model,'well',validate_json=True)

@ns_well.route('/plate_recurse/<uuid>')
class WellToPlate(Resource):
    def get(self,uuid):
        plate_uuid = Well.query.filter_by(uuid=uuid).first().toJSON()['plate_uuid']
        return jsonify(plate_recurse(plate_uuid))

###
###
###

ns_operator = Namespace('operators', description='Operators')
operator_model = ns_operator.schema_model('operator', Operator.validator)
CRUD(ns_operator,Operator,operator_model,'operator',validate_json=True)

###

ns_plan = Namespace('plans',description='Plans')
plan_model = ns_plan.schema_model('plan', Plan.validator)
CRUD(ns_plan,Plan,plan_model,'plan',validate_json=True)

###
