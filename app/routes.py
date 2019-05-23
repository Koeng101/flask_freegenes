import json
from .models import *
from flask_restplus import Api, Resource, fields, Namespace, marshal, SchemaModel
from flask import Flask, abort, request, jsonify, g, url_for, redirect

from .config import PREFIX
from .config import LOGIN_KEY
from .config import SPACES
from .config import BUCKET        
#from dna_designer import moclo, codon

#from .sequence import sequence
from .schemas import schema_generator,collection_schema
from jsonschema import validate

###

import os
import jwt
from functools import wraps
from flask import make_response, jsonify
PUBLIC_KEY = os.environ['PUBLIC_KEY']
def requires_auth(roles):
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



def request_to_class(dbclass,json_request):
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
        elif k == 'derived_from' and v == "":
            pass
        elif k == 'fastqs' and v != []:
            dbclass.fastqs = []
            [dbclass.fastqs.append(Fastq.query.filter_by(uuid=uuid).first()) for uuid in v]
        else:
            setattr(dbclass,k,v)
    return dbclass

def crud_get_list(cls,full=None):
    return jsonify([obj.toJSON(full=full) for obj in cls.query.all()])

def crud_post(cls,post,database,uuid=None):
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

def crud_delete(cls,uuid,database):
    database.session.delete(cls.query.get(uuid))
    database.session.commit()
    return jsonify({'success':True})

def crud_put(cls,post,database,uuid=None):
    obj = cls.query.filter_by(uuid=uuid).first()
    updated_obj = request_to_class(obj,post)
    db.session.commit()
    return jsonify(obj.toJSON())

class CRUD():
    def __init__(self, namespace, cls, model, name, schema=None, security='token'):
        self.ns = namespace
        self.cls = cls
        self.model = model
        self.name = name

        def validate_json(obj, schema, output_type):
            try:
                validate(obj, schema=schema_generator(output_type,schema))
            except Exception as e:
                print(e)
                return make_response(jsonify({'message': 'schema validation failed'}), 400)
            return True

        def validate_request(obj, schema, output_type):
            result = validate_json(obj.json, schema, output_type)
            if result == True:
                return obj
            else:
                return make_response(jsonify({'message': 'schema validation failed'}), 400)

        def post_put(input_obj,schema,func, operation,uuid=None,cls=cls,db=db):
            if validate_json(input_obj,schema,operation) != True:
                return make_response(jsonify({'message': 'schema validation failed'}), 400)
            output_obj = func(cls,input_obj,db,uuid=uuid)
            return validate_request(output_obj,schema,'output_single')

        @self.ns.route('/')
        class ListRoute(Resource):
            @self.ns.doc('{}_list'.format(self.name))
            def get(self):
                return validate_request(crud_get_list(cls),schema,'output_list')

            @self.ns.doc('{}_create'.format(self.name),security=security)
            @self.ns.expect(model)
            @requires_auth(['moderator','admin'])
            def post(self):
                return post_put(requests.get_json(),schema,crud_post,'input')

        @self.ns.route('/<uuid>')
        class NormalRoute(Resource):
            @self.ns.doc('{}_get'.format(self.name))
            def get(self,uuid):
                return validate_request(crud_get(cls,uuid),schema,'output_single')

            @self.ns.doc('{}_delete'.format(self.name),security=security)
            @requires_auth(['moderator','admin'])
            def delete(self,uuid):
                return crud_delete(cls,uuid,db)

            @self.ns.doc('{}_put'.format(self.name),security=security)
            @self.ns.expect(self.model)
            @requires_auth(['moderator','admin'])
            def put(self,uuid):
                return post_put(requests.get_json(),schema,crud_put,'put',uuid=uuid)

        @self.ns.route('/full/')
        class FullListRoute(Resource):
            @self.ns.doc('{}_full'.format(self.name))
            def get(self):
                return validate_request(crud_get_list(cls,full='full'),schema,'output_list_full')

        @self.ns.route('/full/<uuid>')
        class FullRoute(Resource):
            @self.ns.doc('{}_full_single'.format(self.name))
            def get(self,uuid):
                return validate_request(crud_get(cls,uuid,full='full'),schema,'output_single_full')

#========#
# Routes #
#========#
        
###

ns_collection = Namespace('collections', description='Collections')
collection_model = ns_collection.schema_model("collection", schema_generator('input',collection_schema))

CRUD(ns_collection,Collection,collection_model,'collection',schema=collection_schema)

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
    def get(self,key,uuid):
        sql = "SELECT parts.{}, parts.status FROM parts WHERE parts.collection_id='{}'".format(key,uuid)
        result = db.engine.execute(sql)
        dictionary = {}
        for r in result:
            dictionary[str(r[0])] = r[1]
        return jsonify(dictionary)

@ns_collection.route('/part_status/<uuid>/<key>/<status>')
class CollectionPartStatus(Resource):
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

#def modify_part(uuid, function,from_attribute,to_attribute,cls=Part,part_type='cds',status=None):
#    obj = cls.query.filter_by(uuid=uuid).first()
#    if part_type=='cds':
#        if obj.part_type != 'cds' or obj.translation == '' or obj.translation == None:
#            return {'message': 'Not CDS or no translation'}
#    elif obj.status not in [None,'optimized','fixed','checked','twist_checked']:
#        return {'message': 'Checkpoint passed, changing sequence failed'}
#    result = function(getattr(obj, from_attribute))
#    if type(result) == dict:
#        return result
#    if type(result) == str:
#        setattr(obj,to_attribute,result)
#        obj.status = status
#        db.session.commit()
#        return obj.toJSON()
#
#@ns_part_modifiers.route('/optimize/<uuid>')
#class Optimize(Resource):
#    @requires_auth(['moderator','admin'])
#    def put(self,uuid):
#        return jsonify(modify_part(uuid, codon.optimize_protein, 'translation', 'optimized_sequence', status='optimized'))
#
#@ns_part_modifiers.route('/fix/<uuid>')
#class FixCds(Resource):
#    @requires_auth(['moderator','admin'])
#    def put(self,uuid):
#        return jsonify(modify_part(uuid, moclo.fix_cds, 'optimized_sequence', 'optimized_sequence', status='fixed'))
#
#@ns_part_modifiers.route('/optimize_fix/<uuid>')
#class OptimizeFix(Resource):
#    @requires_auth(['moderator','admin'])
#    def put(self,uuid):
#        return jsonify(modify_part(uuid, moclo.optimize_fix, 'translation', 'optimized_sequence', status='fixed'))
#
#@ns_part_modifiers.route('/apply_sites/<uuid>')
#class ApplySites(Resource):
#    @requires_auth(['moderator','admin'])
#    def put(self,uuid):
#        obj = Part.query.filter_by(uuid=uuid).first()
#        obj.synthesized_sequence = moclo.part_type_preparer(obj.part_type,obj.optimized_sequence)
#        obj.status = 'sites_applied'
#        db.session.commit()
#        return jsonify(obj.toJSON())
#
#@ns_part_modifiers.route('/fg_check/<uuid>')
#class FgCheck(Resource):
#    @requires_auth(['moderator','admin'])
#    def put(self,uuid):
#        obj = Part.query.filter_by(uuid=uuid).first()
#        try:
#            result = moclo.input_checker(obj.name,obj.synthesized_sequence,re=False)
#        except Exception as e:
#            print(e)
#            obj.status = 'syn_check_failed'
#            return jsonify({'message': e})
#        if result == 'fg_checked':
#            obj.status = 'syn_checked'
#            db.session.commit()
#            return jsonify(obj.toJSON())
#
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

ns_robot = Namespace('robots', description='Robots')
robot_model = ns_robot.model('robot', {
    "name": fields.String(),
    "description": fields.String(),
    "tags": fields.List(fields.String),
    "genotype": fields.String(),
    })
CRUD(ns_robot,Robot,robot_model,'robot')

###

ns_pipette = Namespace('pipettes', description='Pipettes')
pipette_model = ns_pipette.model('pipette', {
    "pipette_type": fields.String(),
    "mount_side": fields.String(),
    "robot_uuid": fields.String(),
    "notes": fields.String(),
    })
CRUD(ns_pipette,Pipette,pipette_model,'pipette')

###

ns_protocol = Namespace('protocols', description='Protocols')
protocol_model = ns_protocol.model('protocol', {
    "description": fields.String(),
    "protocol": fields.Raw,
    "status": fields.String(),
    "protocol_type": fields.String(),
    "robot_uuid": fields.String(),
    })
CRUD(ns_protocol,Protocol,protocol_model,'protocol')

###

ns_plate = Namespace('plates', description='Plates')
plate_model = ns_plate.model('plate', {
    "plate_vendor_id": fields.String(),
    "breadcrumb": fields.String(),
    "plate_name": fields.String(),
    "plate_form": fields.String(),
    "plate_type": fields.String(),
    "notes": fields.String(),
    "protocol_uuid": fields.String(),
    })
CRUD(ns_plate,Plate,plate_model,'plate')

@ns_plate.route('/recurse/<uuid>')
class PlateSamples(Resource):
    def get(self,uuid):
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
        return jsonify(plate)
###

ns_sample = Namespace('samples', description='Samples')
sample_model = ns_sample.model('sample', {
    "part_uuid": fields.String(),
    "derived_from": fields.String(),
    "status": fields.String(),
    "evidence": fields.String(),
    "wells": fields.String()
    })
CRUD(ns_sample,Sample,sample_model,'sample')

@ns_sample.route('/validation/<uuid>')
class SeqDownloadFile(Resource):
    def get(self,uuid):
        obj = Sample.query.filter_by(uuid=uuid).first()
        pileup = [pileup.uuid for pileup in obj.pileups]
        if len(pileup) > 1:
            return {'message': 'too many pileup'}
        elif len(pileup) == 0:
            return {'message': 'no pileup found'}
        else:
            target = Pileup.query.filter_by(uuid=pileup[0]).first()
            return redirect('/files/download/{}'.format(target.file_uuid))


###

ns_well = Namespace('wells', description='Wells')
well_model = ns_well.model('well', {
    "address": fields.String(),
    "volume": fields.Float(),
    "quantity": fields.Float(),
    "media": fields.String(),
    "well_type": fields.String(),
    "plate_uuid": fields.String()
    })
CRUD(ns_well,Well,well_model,'well')

###

ns_seqrun = Namespace('seqrun', description='Seqrun')
seqrun_model = ns_seqrun.model('seqrun', {
    "name": fields.String(),
    "run_id": fields.String(),
    "machine_id": fields.String(),
    "notes": fields.String(),
    "sequencing_type": fields.String(),
    "machine": fields.String(),
    "provider": fields.String(),
    })
CRUD(ns_seqrun,Seqrun,seqrun_model,'seqrun')


#@ns_seqrun.route('/seq_verify/<uuid>')
#class SeqDownloadFile(Resource):
#    @requires_auth(['moderator','admin'])
#    def put(self,uuid):
#        obj = Seqrun.query.filter_by(uuid=uuid).first()
#        indexs = []
#        fastqs = [fastq for fastq in obj.fastqs]
#        for fastq in fastqs:
#            for_rev = '{}_{}'.format(fastq.index_for,fastq.index_rev)
#            indexs.append(for_rev)
#        indexs = list(set(indexs))
#        index_dict = {}
#        for index in indexs:
#            index_fastqs = []
#            pileups = []
#            for fastq in fastqs:
#                for_rev = '{}_{}'.format(fastq.index_for,fastq.index_rev)
#                if for_rev == index:
#                    index_fastqs.append(fastq.toJSON())
#                    for pileup in fastq.pileups:
#                        pileups.append(pileup.toJSON())
#            pileups = list(dict((v['uuid'],v) for v in pileups).values())
#            index_dict[index] = {'fastqs': index_fastqs, 'pileups':pileups}
#
#        seqrun = obj.toJSON()
#        seqrun['indexes'] = index_dict
#
#        job = q.enqueue_call(func=sequence, args=(seqrun,))
#        obj.job = job.get_id
#        db.session.commit()
#        return jsonify(seqrun)
#            
            


###

ns_pileup = Namespace('pileup', description='Pileup')
pileup_model = ns_pileup.model('pileup', {
    "sample_uuid": fields.String(),
    "status": fields.String(),
    "full_sequence_search": fields.String(),
    "target_sequence": fields.String(),
    "fastqs": fields.List(fields.String()),
    "file_uuid": fields.String()
    })
CRUD(ns_pileup,Pileup,pileup_model,'pileup')

###

ns_fastq = Namespace('fastq', description='Fastq')
fastq_model = ns_fastq.model('fastq', {
    "name": fields.String(),
    "seqrun_uuid": fields.String(),
    "file_uuid": fields.String(),
    "index_for": fields.String(),
    "index_rev": fields.String(),
    })
CRUD(ns_fastq,Fastq,fastq_model,'fastq')




