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

from config import URL
from config import SECRET_KEY
from config import DEV
from config import LOGIN_KEY

# initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = URL
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# extensions
db = SQLAlchemy(app)
auth = HTTPBasicAuth()
api = Api(app, version='1.0', title='FreeGenes Collections',
            description='FreeGenes API',
            )
migrate = Migrate(app, db)
#######################
### User management ###
#######################

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True) 
    username = db.Column(db.String, index=True)
    password_hash = db.Column(db.String(150))

    def hash_password(self, password):
        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': str(self.id)})

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

ns_users = api.namespace('users', description='User login')
user_model = api.model("user", {
    "username": fields.String(),
    "password": fields.String(),
    "login_key": fields.String()
    })

@ns_users.route('/')
class UserPostRoute(Resource):
    @ns_users.doc('user_create')
    @api.expect(user_model)
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


#################
### FreeGenes ###
#################

tags_collection = db.Table('tags_collection',
    db.Column('tags_uuid', UUID(as_uuid=True), db.ForeignKey('tags.uuid'), primary_key=True),
    db.Column('collection_uuid', UUID(as_uuid=True), db.ForeignKey('collections.uuid'), primary_key=True, nullable=True),
)

tags_parts = db.Table('tags_parts',
    db.Column('tags_uuid', UUID(as_uuid=True), db.ForeignKey('tags.uuid'), primary_key=True),
    db.Column('part_uuid', UUID(as_uuid=True), db.ForeignKey('parts.uuid'),primary_key=True,nullable=True),
)

# Virtuals
class Collection(db.Model):
    __tablename__ = 'collections'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    
    status = db.Column(db.String) # planned, in-progress

    parts = db.relationship('Part',backref='collections')
    parent_uuid = db.Column(UUID, db.ForeignKey('collections.uuid'),
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
        return {'uuid':self.uuid,'time_created':self.time_created,'time_updated':self.time_updated,'status':self.status,'tags':tags,'name':self.name,'readme':self.readme,'parent_uuid':self.parent_uuid,'parts': [part.uuid for part in self.parts]}


class Author(db.Model):
    __tablename__ = 'authors'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    name = db.Column(db.String)
    email = db.Column(db.String)
    affiliation = db.Column(db.String)
    orcid = db.Column(db.String)
    parts = db.relationship('Part',backref='author')

    def toJSON(self):
        return {'uuid':self.uuid,'name':self.name,'email':self.email,'affiliation':self.affiliation,'orcid':self.orcid,'parts':[part.uuid for part in self.parts]}

class Part(db.Model):
    __tablename__ = 'parts'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    status = db.Column(db.String) # NOT NORMALIZED WITH SEQ. NOT GOOD... but convenient.

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

    collection_id = db.Column(UUID, db.ForeignKey('collections.uuid'),
            nullable=False)
    author_uuid = db.Column(UUID, db.ForeignKey('authors.uuid'),
            nullable=False)

    samples = db.relationship('Sample',backref='part')

    def toJSON(self):
        tags = []
        for tag in self.tags:
            tags.append(tag.tag)
        # Return collection ID as well
        return {'uuid':self.uuid,'time_created':self.time_created,'time_updated':self.time_updated,'status':self.status,'tags':tags,'name':self.name,'description':self.description,'gene_id':self.gene_id,'part_type':self.part_type,'original_sequence':self.original_sequence,'optimized_sequence':self.optimized_sequence,'synthesized_sequence':self.synthesized_sequence,'full_sequence':self.full_sequence,'genbank':self.genbank,'vector':self.vector,'primer_for':self.primer_for,'primer_rev':self.primer_rev,'barcode':self.barcode,'vbd':self.vbd,'resistance':self.resistance,'samples':[sample.uuid for sample in self.samples],'author_uuid':self.author_uuid}

class Tag(db.Model):
    __tablename__ = 'tags'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    tag = db.Column(db.String)

    def toJSON(self):
        return {'tag':tag}

# Robot 
class Robot(db.Model):
    __tablename__ = 'robots'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    right_300 = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"))
    left_10 = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"))
    robot_name = db.Column(db.String)
    notes = db.Column(db.String)

class Protocol(db.Model):
    __tablename__ = 'protocols'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    description = db.Column(db.String())
    protocol = db.Column(db.JSON, nullable=False)

    status = db.Column(db.String(), default='planned') # planned, executed 
    plates = db.relationship('Plate',backref='protocol') # TODO ADD plates in toJSON

    def toJSON(self):
        return {'uuid': self.uuid, 'description': self.description, 'protocol': self.protocol, 'status': self.status, 'plates': [plate.uuid for plate in self.plates]}


# Plates, wells, samples

samples_wells = db.Table('samples_wells',
    db.Column('samples_uuid', UUID(as_uuid=True), db.ForeignKey('samples.uuid'), primary_key=True),
    db.Column('wells_uuid', UUID(as_uuid=True), db.ForeignKey('wells.uuid'), primary_key=True, nullable=True),
)

class Plate(db.Model):
    __tablename__ = 'plates'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    status = db.Column(db.String) # planned, processing, complete

    breadcrumb = db.Column(db.String)
    plate_name = db.Column(db.String(32))
    plate_form = db.Column(db.String(32))
    plate_type = db.Column(db.String(32)) # dna_plate, asssembly, transformation, agar_plate, deepwell, glycerol
    wells = db.relationship('Well',backref='plate')

    protocol_uuid = db.Column(UUID, db.ForeignKey('protocols.uuid'), nullable=True)

    def toJSON(self):
        return {'uuid': self.uuid, 'breadcrumb':self.breadcrumb,'plate_name': self.plate_name, 'plate_form': self.plate_form, 'plate_type': self.plate_type, 'status': self.status, 'protocol_uuid':self.protocol_uuid, 'wells':[well.uuid for well in self.wells]}

class Sample(db.Model):
    __tablename__ = 'samples'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    part_uuid = db.Column(UUID, db.ForeignKey('parts.uuid'), nullable=False)
    derived_from = db.Column(UUID, db.ForeignKey('samples.uuid'), nullable=True)


    sequencing= db.relationship('Sequencing',backref='samples')
    wells = db.relationship('Well', secondary=samples_wells, lazy='subquery',
        backref=db.backref('samples', lazy=True))

    def toJSON(self, wells=True, part=False):
        return {'uuid':self.uuid,'derived_from':self.derived_from,'wells':[well.uuid for well in self.wells],'part_uuid':self.part_uuid}

class Well(db.Model): # Constrain Wells to being unique to each plate
    __tablename__ = 'wells'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    address = db.Column(db.String(32), nullable=False)
    volume = db.Column(db.Float, nullable=True) # ul - if null, dry

    quantity = db.Column(db.Float, nullable=True) # fmol - if null, unknown
    media = db.Column(db.String(32)) # Liquid
    well_type = db.Column(db.String(32)) # glycerol,grown,purified_dna,pcr,gdna,etc
    organism = db.Column(db.String)

    plate_uuid = db.Column(UUID, db.ForeignKey('plates.uuid'),
            nullable=False)

    def toJSON(self):
        return {'uuid':self.uuid,'address':self.address,'volume':self.volume,'quantity':self.quantity,'media':self.media,'well_type':self.well_type,'organism':self.organism,'plate_uuid':self.plate_uuid,'samples':[sample.uuid for sample in self.samples]} 


# Sequencing

class Sequencing(db.Model):
    __tablename__ = 'sequencing'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    sequencing_id = db.Column(db.String) # Sequencing provider id
    sequencing_notes = db.Column(db.String)

    sequencing_type = db.Column(db.String) # illumina, nanopore, etc
    machine = db.Column(db.String) # Minion, iseq, etc
    sequencing_provider = db.Column(db.String)
    status = db.Column(db.String) # mutation,confirmed,etc
    sequence = db.Column(db.String) 

    pileups= db.relationship('Pileup',backref='sequencing')

    sample_uuid = db.Column(UUID, db.ForeignKey('samples.uuid'),
            nullable=False)

    def toJSON(self):
        return {'uuid':self.uuid,'time_created':self.time_created,'time_updated':self.time_updated,'status':self.status,'sequencing_id':self.sequencing_id,'sequencing_notes':self.sequencing_notes,'sequencing_type':self.sequencing_type,'machine':self.machine,'sequencing_provider':self.sequencing_provider,'sequence':self.sequence, 'sample_uuid':self.sample_uuid, 'pileups':[pileup.toJSON() for pileup in self.pileups]}

class Pileup(db.Model):
    __tablename__ = 'pileups'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    sequence = db.Column(db.String) # geneid. Yes, not normalized: but makes everything more simple
    position = db.Column(db.Integer) # Integer position
    reference_base = db.Column(db.String) # A,T,G,C
    read_count = db.Column(db.Integer) # 24
    read_results = db.Column(db.String) # ,.$.....,,.,.,...,,,.,..^+.	
    quality = db.Column(db.String) # <<<+;<<<<<<<<<<<=<;<;7<&

    sequencing_uuid = db.Column(UUID, db.ForeignKey('sequencing.uuid'),
            nullable=True)

    def toJSON(self):
        return {'sequence':self.sequence,'position':self.position,'reference_base':self.reference_base,'read_count':self.read_count,'read_results':self.read_results,'quality':self.quality}

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
        elif k == 'pileups' and v != []:
            dbclass.pileups = []
            for pileup in v:
                new_pileup = request_to_class(Pileup,pileup)
                dbclass.pileups.append(new_pileup)
        else:
            setattr(dbclass,k,v)
    for tag in tags:
        dbclass.tags.append(tag)
    return dbclass

###################
### COLLECTIONS ###
###################
ns_collection = api.namespace('collections', description='Collections')
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
### PARTS ###
#############

# TODO self insert dat gene_id
ns_part = api.namespace('parts', description='Parts')
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
    "collection_id": fields.String(),
    "parent_uuid": fields.String(),
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
        part = Part.query.filter_by(uuid=uuid).first()
        updated_part = request_to_class(part,request.get_json())
        db.session.commit()
        return jsonify(updated_part.toJSON())



#################
### PROTOCOLS ###
#################
ns_protocol = api.namespace('protocols', description='OpenFoundry Protocols')
protocol_model = api.model("protocol", {
    "description": fields.String("A description of what the protocol was used for"),
    "protocol": fields.Raw("The Protocol json protocol itself")
    })

@ns_protocol.route('/')
class ProtocolListRoute(Resource): 
    '''Shows all protocols and allows you to post new protocols'''
    @ns_protocol.doc('protocol_list')
    def get(self):
        '''Lists all protocols'''
        return jsonify([protocol.toJSON() for protocol in Protocol.query.all()])

    @ns_protocol.doc('protocol_create')
    @api.expect(protocol_model)
    def post(self):
        '''Create new protocol'''
        # TODO add schema validator
        protocol = request_to_class(Protocol(),request.get_json())
        db.session.add(protocol)
        db.session.commit()
        return jsonify(protocol.toJSON())

@ns_protocol.route('/<uuid>')
class ProtocolRoute(Resource):
    '''Shows a single protocol and allows you to delete or update preexisting protocols'''
    @ns_protocol.doc('protocol_get')
    def get(self,uuid):
        '''Get a single protocol'''
        return jsonify(Protocol.query.filter_by(uuid=uuid).first().toJSON())
    
    @ns_protocol.doc('protocol_delete')
    def delete(self,uuid):
        '''Delete a single protocol'''
        db.session.delete(Protocol.query.get(uuid))
        db.session.commit()

    @ns_protocol.doc('protocol_put')
    def put(self,uuid):
        '''Update a single protocol'''
        # TODO add schema validator
        protocol = Protocol.query.filter_by(uuid=uuid).first()
        protocol.description = request.get_json().get('description')
        protocol.protocol = request.get_json().get('protocol')
        db.session.commit()


#############
### PLATE ###
#############
ns_plate = api.namespace('plates', description='OpenFoundry Plates')
plate_model = api.model("plate", {
    "breadcrumb": fields.String(),
    "plate_name": fields.String("The human readable plate name"),
    "plate_form": fields.String("The physical form of the plate: 96standard, 96deepwell, 384standard"),
    "plate_type": fields.String("The sample types contained within a plate: raw_dna,miniprep,pcr,glycerol_stock,culture,agar"),
    "status": fields.String("The status of the plate as it transfers through the system: planned,processing,used,trashed,stored"),
    "protocol_uuid": fields.String(),
    })

@ns_plate.route('/')
class PlateListRoute(Resource): 
    '''Shows all plates and allows you to post new plates'''
    @ns_plate.doc('plates_list')
    def get(self):
        '''Lists all plates'''
        return jsonify([db_object.toJSON() for db_object in Plate.query.all()])

    @ns_plate.doc('plates_create')
    @api.expect(plate_model)
    def post(self):
        '''Create new plate'''
        # TODO add schema validator
        plate = request_to_class(Plate(),request.get_json())
        db.session.add(plate)
        db.session.commit()
        return jsonify(plate.toJSON())

@ns_plate.route('/<uuid>')
class PlateRoute(Resource):
    '''Shows a single plate and allows you to delete or update preexisting plates'''
    @ns_plate.doc('plate_get')
    def get(self,uuid):
        '''Get a single plate'''
        return jsonify(Plate.query.filter_by(uuid=uuid).first().toJSON())
    
    @ns_plate.doc('plate_delete')
    def delete(self,uuid):
        '''Delete a single plate'''
        db.session.delete(Plate.query.get(uuid))
        db.session.commit()

    @ns_plate.doc('plate_put')
    @api.expect(plate_model)
    def put(self,uuid):
        '''Update a single plate'''
        edit = Plate.query.filter_by(uuid=uuid).first()
        edit = request_to_class(edit,request.get_json())
        db.session.commit()

#@ns_plate.route('/all/<uuid>')
#class PlateWellsRoute(Resource):
#    '''Gets all information associated with a plate except historical information'''
#    @ns_plate.doc('plate_wells_get')
#    def get(self,uuid):
#        '''Get all information associated with a plate'''
#        plate = Plate.query.filter_by(uuid=uuid).first().toJSON()
#        wells = []
#        for well in Well.query.filter_by(plate_id=uuid):
#            target_well = well.toJSON()
#            target_well['sample'] = Sample.query.filter_by(uuid=target_well['sample_id']).first().toJSON()
#            target_well['sample']['virtual'] = Virtual.query.filter_by(uuid=target_well['sample']['dna_id']).first().toJSON()
#            wells.append(target_well)
#        plate['wells'] = wells
#        return jsonify(plate)


###############
### Sample ####
###############
ns_sample = api.namespace('samples', description='OpenFoundry Samples')
sample_model = api.model("sample", {
    "part_uuid": fields.String("The DNA sample that this sample represented"), # TODO add required where necessary
    "derived_from": fields.String(default=None), #TODO RULES FOR DERIVED FROM
    "wells": fields.List(fields.String),
    })

@ns_sample.route('/')
class SampleListRoute(Resource):
    '''Shows all samples and allows you to post new samples'''
    @ns_sample.doc('samples_list')
    def get(self):
        '''Lists all samples'''
        return jsonify([db_object.toJSON() for db_object in Sample.query.all()])

    @ns_sample.doc('samples_create')
    @api.expect(sample_model)
    def post(self):
        '''Create new sample'''
        # TODO add schema validator
        sample = request_to_class(Sample(),request.get_json())
        db.session.add(sample)
        db.session.commit()
        return jsonify(sample.toJSON())

@ns_sample.route('/<uuid>')
class SampleRoute(Resource):
    '''Shows a single sample and allows you to delete or update preexisting samples'''
    @ns_sample.doc('sample_get')
    def get(self,uuid):
        '''Get a single sample'''
        return jsonify(Sample.query.filter_by(uuid=uuid).first().toJSON())

    @ns_sample.doc('sample_delete')
    def delete(self,uuid):
        '''Delete a single sample'''
        db.session.delete(Sample.query.get(uuid))
        db.session.commit()

    @ns_sample.doc('sample_put')
    @api.expect(sample_model)
    def put(self,uuid):
        '''Update a single sample'''
        edit = Sample.query.filter_by(uuid=uuid).first()
        edit = request_to_class(edit,request.get_json())
        db.session.commit()


#############
### Well ####
#############
#        return {'uuid':self.uuid,'address':self.address,'volume':self.volume,'plate_id':self.plate_id,'sample_id':self.sample_id}

ns_well = api.namespace('wells', description='OpenFoundry Wells')
well_model = api.model("well", {
    "address": fields.String("Plate address of well"),
    "volume": fields.Float("Volume of sample"),
    "plate_uuid": fields.String("UUID of plate that well exists in"),
    "samples": fields.List(fields.String),
    ###    
    "quantity": fields.Float("The quantity of the DNA in fmol. Null if in organism or unknown"),
    "media": fields.String("The solvent or media that the sample is in"),
    "sample_type": fields.String("The physical type of sample (glycerol_stock,miniprepped_sample,synthetic_dna)"),
    "organism": fields.String("The organism the DNA is in if not a raw DNA sample")

    })

@ns_well.route('/')
class WellListRoute(Resource):
    '''Shows all wells and allows you to post new wells'''
    @ns_well.doc('wells_list')
    def get(self):
        '''Lists all wells'''
        return jsonify([db_object.toJSON() for db_object in Well.query.all()])

    @ns_well.doc('wells_create')
    @api.expect(well_model)
    def post(self):
        '''Create new well'''
        # TODO add schema validator
        well = request_to_class(Well(),request.get_json())
        db.session.add(well)
        db.session.commit()
        return jsonify(well.toJSON())

@ns_well.route('/<uuid>')
class WellRoute(Resource):
    '''Shows a single well and allows you to delete or update preexisting wells'''
    @ns_well.doc('well_get')
    def get(self,uuid):
        '''Get a single well'''
        return jsonify(Well.query.filter_by(uuid=uuid).first().toJSON())

    @ns_well.doc('well_delete')
    def delete(self,uuid):
        '''Delete a single well'''
        db.session.delete(Well.query.get(uuid))
        db.session.commit()

    @ns_well.doc('well_put')
    @api.expect(well_model)
    def put(self,uuid):
        '''Update a single well'''
        edit = Well.query.filter_by(uuid=uuid).first()
        edit = request_to_class(edit,request.get_json())
        db.session.commit()

##################
### SEQUENCING ###
##################

ns_sequencing = api.namespace('sequencing', description='OpenFoundry Sequencing')
sequencing_model = api.model("sequencing", {
    "status": fields.String(),
    "sequencing_id": fields.Raw(),
    "sequencing_notes": fields.String(),
    "sequencing_type": fields.String(), # nanopore, illumina
    "machine": fields.String(),
    "sequencing_provider": fields.String(),
    "sample_uuid": fields.String(),
    "pileups": fields.List(fields.Raw),
    })

@ns_sequencing.route('/')
class SequencingListRoute(Resource):
    '''Shows all sequencings and allows you to post new sequencings'''
    @ns_sequencing.doc('sequencing_list')
    def get(self):
        '''Lists all sequencings'''
        return jsonify([sequencing.toJSON() for sequencing in Sequencing.query.all()])

    @ns_sequencing.doc('sequencing_create')
    @api.expect(sequencing_model)
    def post(self):
        '''Create new sequencing'''
        # TODO add schema validator
        sequencing = request_to_class(Sequencing(),request.get_json())
        db.session.add(sequencing)
        db.session.commit()
        return jsonify(sequencing.toJSON())

@ns_sequencing.route('/<uuid>')
class SequencingRoute(Resource):
    '''Shows a single sequencing and allows you to delete or update preexisting sequencings'''
    @ns_sequencing.doc('sequencing_get')
    def get(self,uuid):
        '''Get a single sequencing'''
        return jsonify(Sequencing.query.filter_by(uuid=uuid).first().toJSON())

    @ns_sequencing.doc('sequencing_delete')
    def delete(self,uuid):
        '''Delete a single sequencing'''
        db.session.delete(Sequencing.query.get(uuid))
        db.session.commit()

    @ns_sequencing.doc('sequencing_put')
    def put(self,uuid):
        '''Update a single sequencing'''
        # TODO add schema validator
        sequencing = Sequencing.query.filter_by(uuid=uuid).first()
        sequencing.description = request.get_json().get('description')
        sequencing.sequencing = request.get_json().get('sequencing')
        db.session.commit()

###############
### AUTHORS ###
###############
ns_author = api.namespace('authors', description='Authors')
author_model = api.model("author", {
    "name": fields.String(),
    "email": fields.String(),
    "affiliation": fields.String(),
    "orcid": fields.String(),
    })

@ns_author.route('/')
class AuthorListRoute(Resource):
    '''Shows all authors and allows you to post new authors'''
    @ns_author.doc('author_list')
    def get(self):
        '''Lists all authors'''
        return jsonify([author.toJSON() for author in Author.query.all()])

    @ns_author.doc('author_create')
    @api.expect(author_model)
    def post(self):
        '''Create new author'''
        # TODO add schema validator
        author = request_to_class(Author(),request.get_json())
        db.session.add(author)
        db.session.commit()
        return jsonify(author.toJSON())

@ns_author.route('/<uuid>')
class AuthorRoute(Resource):
    '''Shows a single author and allows you to delete or update preexisting authors'''
    @ns_author.doc('author_get')
    def get(self,uuid):
        '''Get a single author'''
        return jsonify(Author.query.filter_by(uuid=uuid).first().toJSON())

    @ns_author.doc('author_delete')
    def delete(self,uuid):
        '''Delete a single author'''
        db.session.delete(Author.query.get(uuid))
        db.session.commit()

    @ns_author.doc('author_put')
    def put(self,uuid):
        '''Update a single author'''
        # TODO add schema validator
        author = Author.query.filter_by(uuid=uuid).first()
        author.description = request.get_json().get('description')
        author.author = request.get_json().get('author')
        db.session.commit()


if __name__ == '__main__' and DEV == True:
    app.run(debug=True)
elif __name__ == '__main__' and DEV == False:
    app.run(host='0.0.0.0')

