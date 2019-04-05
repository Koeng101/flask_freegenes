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
from config import PREFIX
# initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = URL
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# extensions
db = SQLAlchemy(app)
auth = HTTPBasicAuth()
api = Api(app, version='1.1', title='FreeGenes Collections',
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

# Think things
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
    translation = db.Column(db.String)

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

# Do things
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
    protocol_type = db.Column(db.String()) # human, opentrons

    def toJSON(self):
        return {'uuid': self.uuid, 'description': self.description, 'protocol': self.protocol, 'status': self.status, 'plates': [plate.uuid for plate in self.plates], 'protocol_type':self.protocol_type}


# Are things

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


    pileups = db.relationship('Pileup',backref='sample')
    wells = db.relationship('Well', secondary=samples_wells, lazy='subquery',
        backref=db.backref('samples', lazy=True))

    def toJSON(self, wells=True, part=False):
        return {'uuid':self.uuid,'derived_from':self.derived_from,'wells':[well.uuid for well in self.wells],'part_uuid':self.part_uuid,'pileups':[pileup.uuid for pileup in self.pileups]}

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


# Verify things
class Seqrun(db.Model):
    __tablename__ = 'seqruns'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    run_id = db.Column(db.String) # Sequencing provider id
    notes = db.Column(db.String)
    sequencing_type = db.Column(db.String) # illumina, nanopore, etc
    machine = db.Column(db.String) # minion, iseq, etc
    provider = db.Column(db.String) # in-house

    fastqs = db.relationship('Fastq',backref='seqrun')

    def toJSON(self):
        return {'uuid':self.uuid,'time_created':self.time_created,'time_updated':self.time_updated,'run_id':self.run_id,'notes':self.notes,'sequencing_type':self.sequencing_type,'machine':self.machine,'provider':self.provider, 'fastqs': [fastq.uuid for fastq in self.fastqs]}



pileup_fastq = db.Table('pileup_fastq',
    db.Column('pileup_uuid', UUID(as_uuid=True), db.ForeignKey('pileups.uuid'), primary_key=True),
    db.Column('fastq_uuid', UUID(as_uuid=True), db.ForeignKey('fastqs.uuid'),primary_key=True,nullable=True),
)

class Pileup(db.Model):
    __tablename__ = 'pileups'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    status = db.Column(db.String) # mutation,confirmed,etc
    full_search_sequence = db.Column(db.String)
    target_sequence = db.Column(db.String) 
    pileup_link = db.Column(db.String)

    sample_uuid = db.Column(UUID, db.ForeignKey('samples.uuid'),
            nullable=False)
    fastqs = db.relationship('Fastq', secondary=pileup_fastq, lazy='subquery',
        backref=db.backref('pileups', lazy=True))
    
    def toJSON(self):
        return {'uuid':self.uuid,'time_created':self.time_created,'time_updated':self.time_updated,'status':self.status,'full_search_sequence':self.full_search_sequence,'target_sequence':self.target_sequence,'pileup_link':self.pileup_link, 'sample_uuid': self.sample_uuid,'fastqs':[fastq.uuid for fastq in self.fastqs]}


class Fastq(db.Model):
    __tablename__ = 'fastqs'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    seqrun_uuid = db.Column(UUID, db.ForeignKey('seqruns.uuid'), nullable=False)
    fastq_link = db.Column(db.String)
    raw_link = db.Column(db.String) # gz zipped

    index_for = db.Column(db.String)
    index_rev = db.Column(db.String)
    
    def toJSON(self):
        return {'uuid':self.uuid,'time_created':self.time_created,'time_updated':self.time_updated,'seqrun_uuid':self.seqrun_uuid,'fastq_link':self.fastq_link,'index_for':self.index_for,'index_rev':self.index_rev,'pileups': [pileup.uuid for pileup in self.pileups]}


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

def next_gene_id():
    result = db.engine.execute("SELECT parts.gene_id FROM parts ORDER BY gene_id DESC LIMIT 1")
    for r in result:
        last_id = r
    last_num = int(last_id[0][-6:])
    new_id = PREFIX + str(last_num+1).zfill(6)
    return new_id

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
    @auth.login_required
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
    @auth.login_required
    def delete(self,uuid):
        '''Delete a single collection'''
        db.session.delete(Collection.query.get(uuid))
        db.session.commit()
        return jsonify({'success':True})

    @ns_collection.doc('collection_put')
    @api.expect(collection_model)
    @auth.login_required
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
    @auth.login_required
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
    @auth.login_required
    def delete(self,uuid):
        '''Delete a single part'''
        db.session.delete(Part.query.get(uuid))
        db.session.commit()
        return jsonify({'success':True})

    @ns_part.doc('part_put')
    @api.expect(part_model)
    @auth.login_required
    def put(self,uuid):
        '''Update a single part'''
        part = Part.query.filter_by(uuid=uuid).first()
        updated_part = request_to_class(part,request.get_json())
        db.session.commit()
        return jsonify(updated_part.toJSON())

@ns_part.route('/geneid/<gene_id>')
class PartGeneID(Resource):
    '''Shows a single part'''
    @ns_part.doc('part_geneid_get')
    def get(self,gene_id):
        '''Get a single part'''
        return jsonify(Part.query.filter_by(gene_id=gene_id).first().toJSON())

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
    @auth.login_required
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
    @auth.login_required
    def delete(self,uuid):
        '''Delete a single protocol'''
        db.session.delete(Protocol.query.get(uuid))
        db.session.commit()

    @ns_protocol.doc('protocol_put')
    @api.expect(protocol_model)
    @auth.login_required
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
    @auth.login_required
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
    @auth.login_required
    def delete(self,uuid):
        '''Delete a single plate'''
        db.session.delete(Plate.query.get(uuid))
        db.session.commit()
        return jsonify({'success':True})

    @ns_plate.doc('plate_put')
    @api.expect(plate_model)
    @auth.login_required
    def put(self,uuid):
        '''Update a single plate'''
        edit = Plate.query.filter_by(uuid=uuid).first()
        edit = request_to_class(edit,request.get_json())
        db.session.commit()
        return jsonify({'success':True})

@ns_plate.route('/full/<uuid>')
class PlateFullRoute(Resource):
    @ns_plate.doc('plate_full_get')
    def get(self,uuid):
        '''Get a single plate and down the tree'''

        plate = Plate.query.filter_by(uuid=uuid).first().toJSON()
        wells = []
        for well in plate['wells']:
            new_well = Well.query.filter_by(uuid=well).first().toJSON()
            new_well['samples'] = [Sample.query.filter_by(uuid=sample).first().toJSON() for sample in new_well['samples']]
            wells.append(new_well)
        plate['wells'] = wells
        return jsonify(plate)



        

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
    @auth.login_required
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
    @auth.login_required
    def delete(self,uuid):
        '''Delete a single sample'''
        db.session.delete(Sample.query.get(uuid))
        db.session.commit()
        return jsonify({'success':True})

    @ns_sample.doc('sample_put')
    @api.expect(sample_model)
    @auth.login_required
    def put(self,uuid):
        '''Update a single sample'''
        edit = Sample.query.filter_by(uuid=uuid).first()
        edit = request_to_class(edit,request.get_json())
        db.session.commit()
        return jsonify({'success':True})


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
    @auth.login_required
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
    @auth.login_required
    def delete(self,uuid):
        '''Delete a single well'''
        db.session.delete(Well.query.get(uuid))
        db.session.commit()
        return jsonify({'success':True})

    @ns_well.doc('well_put')
    @api.expect(well_model)
    @auth.login_required
    def put(self,uuid):
        '''Update a single well'''
        edit = Well.query.filter_by(uuid=uuid).first()
        edit = request_to_class(edit,request.get_json())
        db.session.commit()
        return jsonify({'success':True})


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
    @auth.login_required
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
        next_gene_id()
        return jsonify(Author.query.filter_by(uuid=uuid).first().toJSON())

    @ns_author.doc('author_delete')
    @auth.login_required
    def delete(self,uuid):
        '''Delete a single author'''
        db.session.delete(Author.query.get(uuid))
        db.session.commit()
        return jsonify({'success':True})

    @ns_author.doc('author_put')
    @api.expect(author_model)
    @auth.login_required
    def put(self,uuid):
        '''Update a single author'''
        # TODO add schema validator
        author = Author.query.filter_by(uuid=uuid).first()
        author.description = request.get_json().get('description')
        author.author = request.get_json().get('author')
        db.session.commit()
        return jsonify({'success':True})

###############
### PILEUPS ###
###############
ns_pileup = api.namespace('pileups', description='Pileups')
pileup_model = api.model("pileup", {
    "status": fields.String(),
    "full_search_sequence": fields.String(),
    "target_sequence": fields.String(),
    "pileup_link": fields.String(),
    "fastqs": fields.String(),
    "sample_uuid": fields.String()
    })

@ns_pileup.route('/')
class PileupListRoute(Resource):
    '''Shows all pileups and allows you to post new pileups'''
    @ns_pileup.doc('pileup_list')
    def get(self):
        '''Lists all pileups'''
        return jsonify([pileup.toJSON() for pileup in Pileup.query.all()])

    @ns_pileup.doc('pileup_create')
    @api.expect(pileup_model)
    @auth.login_required
    def post(self):
        '''Create new pileup'''
        # TODO add schema validator
        pileup = request_to_class(Pileup(),request.get_json())
        db.session.add(pileup)
        db.session.commit()
        return jsonify(pileup.toJSON())

@ns_pileup.route('/<uuid>')
class PileupRoute(Resource):
    '''Shows a single pileup and allows you to delete or update preexisting pileups'''
    @ns_pileup.doc('pileup_get')
    def get(self,uuid):
        '''Get a single pileup'''
        return jsonify(Pileup.query.filter_by(uuid=uuid).first().toJSON())

    @ns_pileup.doc('pileup_delete')
    @auth.login_required
    def delete(self,uuid):
        '''Delete a single pileup'''
        db.session.delete(Pileup.query.get(uuid))
        db.session.commit()
        return jsonify({'success':True})

    @ns_pileup.doc('pileup_put')
    @api.expect(pileup_model)
    @auth.login_required
    def put(self,uuid):
        '''Update a single pileup'''
        # TODO add schema validator
        pileup = Pileup.query.filter_by(uuid=uuid).first()
        pileup.description = request.get_json().get('description')
        pileup.pileup = request.get_json().get('pileup')
        db.session.commit()
        return jsonify({'success':True})

##############
### SEQRUN ###
##############
ns_seqrun = api.namespace('seqruns', description='Seqruns')
seqrun_model = api.model("seqrun", {
    "run_id": fields.String(),
    "notes": fields.String(),
    "sequencing_type": fields.String(),
    "machine": fields.String(),
    "provider": fields.String(),
    })

@ns_seqrun.route('/')
class SeqrunListRoute(Resource):
    '''Shows all seqruns and allows you to post new seqruns'''
    @ns_seqrun.doc('seqrun_list')
    def get(self):
        '''Lists all seqruns'''
        return jsonify([seqrun.toJSON() for seqrun in Seqrun.query.all()])

    @ns_seqrun.doc('seqrun_create')
    @api.expect(seqrun_model)
    @auth.login_required
    def post(self):
        '''Create new seqrun'''
        # TODO add schema validator
        seqrun = request_to_class(Seqrun(),request.get_json())
        db.session.add(seqrun)
        db.session.commit()
        return jsonify(seqrun.toJSON())

@ns_seqrun.route('/<uuid>')
class SeqrunRoute(Resource):
    '''Shows a single seqrun and allows you to delete or update preexisting seqruns'''
    @ns_seqrun.doc('seqrun_get')
    def get(self,uuid):
        '''Get a single seqrun'''
        return jsonify(Seqrun.query.filter_by(uuid=uuid).first().toJSON())

    @ns_seqrun.doc('seqrun_delete')
    @auth.login_required
    def delete(self,uuid):
        '''Delete a single seqrun'''
        db.session.delete(Seqrun.query.get(uuid))
        db.session.commit()
        return jsonify({'success':True})

    @ns_seqrun.doc('seqrun_put')
    @api.expect(seqrun_model)
    @auth.login_required
    def put(self,uuid):
        '''Update a single seqrun'''
        # TODO add schema validator
        seqrun = Seqrun.query.filter_by(uuid=uuid).first()
        seqrun.description = request.get_json().get('description')
        seqrun.seqrun = request.get_json().get('seqrun')
        db.session.commit()
        return jsonify({'success':True})

#############
### FASTQ ###
#############
ns_fastq = api.namespace('fastqs', description='Fastqs')
fastq_model = api.model("fastq", {
    "seqrun_uuid": fields.String(),
    "fastq_link": fields.String(),
    "raw_link": fields.String(),
    "index_for": fields.String(),
    "index_rev": fields.String(),
    })

@ns_fastq.route('/')
class FastqListRoute(Resource):
    '''Shows all fastqs and allows you to post new fastqs'''
    @ns_fastq.doc('fastq_list')
    def get(self):
        '''Lists all fastqs'''
        return jsonify([fastq.toJSON() for fastq in Fastq.query.all()])

    @ns_fastq.doc('fastq_create')
    @api.expect(fastq_model)
    @auth.login_required
    def post(self):
        '''Create new fastq'''
        # TODO add schema validator
        fastq = request_to_class(Fastq(),request.get_json())
        db.session.add(fastq)
        db.session.commit()
        return jsonify(fastq.toJSON())

@ns_fastq.route('/<uuid>')
class FastqRoute(Resource):
    '''Shows a single fastq and allows you to delete or update preexisting fastqs'''
    @ns_fastq.doc('fastq_get')
    def get(self,uuid):
        '''Get a single fastq'''
        return jsonify(Fastq.query.filter_by(uuid=uuid).first().toJSON())

    @ns_fastq.doc('fastq_delete')
    @auth.login_required
    def delete(self,uuid):
        '''Delete a single fastq'''
        db.session.delete(Fastq.query.get(uuid))
        db.session.commit()
        return jsonify({'success':True})

    @ns_fastq.doc('fastq_put')
    @api.expect(fastq_model)
    @auth.login_required
    def put(self,uuid):
        '''Update a single fastq'''
        # TODO add schema validator
        fastq = Fastq.query.filter_by(uuid=uuid).first()
        fastq.description = request.get_json().get('description')
        fastq.fastq = request.get_json().get('fastq')
        db.session.commit()
        return jsonify({'success':True})


if __name__ == '__main__' and DEV == True:
    app.run(debug=True)
elif __name__ == '__main__' and DEV == False:
    app.run(host='0.0.0.0')

