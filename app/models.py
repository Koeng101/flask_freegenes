from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy
from sqlalchemy.sql import func
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from flask import Flask, abort, request, jsonify, g, url_for, Response
import uuid

from .config import SPACES
from .config import BUCKET

from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from passlib.apps import custom_app_context as pwd_context

db = SQLAlchemy()
auth = HTTPBasicAuth()

##################
### Validators ###
##################

from jsonschema import validate
import json
import string

# Shared
uuid_regex = '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
null = {'type': 'null'}

uuid_schema = {'type': 'string','pattern': uuid_regex}
optional_uuid = {'oneOf': [uuid_schema,null]}

generic_string = {'type': 'string'}
optional_string ={'oneOf': [generic_string,null]}

generic_num = { "type": "number" }
optional_num = {'oneOf': [generic_num,null]}

generic_date = {'type': 'string','format':'date-time'}
optional_date = {'oneOf': [generic_date,null]}

name = {'type': 'string','minLength': 3,'maxLength': 30}
tags = {'type': 'array', 'items': optional_string}
force_to_many = {'type': 'array', 'items': uuid_schema}
to_many = {'type': 'array', 'items': {'oneOf': [uuid_schema,null]}}
#many_to_many = {'anyOf': [{'type': 'array','items': uuid},{'type': 'array','items': null}]}

def schema_generator(properties,required,additionalProperties=False):
    return {"$schema": "http://json-schema.org/schema#",
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": additionalProperties}


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

tags_organisms = db.Table('tags_organisms',
        db.Column('tags_uuid', UUID(as_uuid=True), db.ForeignKey('tags.uuid'), primary_key=True),
    db.Column('organism_uuid', UUID(as_uuid=True), db.ForeignKey('organisms.uuid'),primary_key=True,nullable=True),
)

tags_authors = db.Table('tags_authors',
        db.Column('tags_uuid', UUID(as_uuid=True), db.ForeignKey('tags.uuid'), primary_key=True),
    db.Column('author_uuid', UUID(as_uuid=True), db.ForeignKey('authors.uuid'),primary_key=True,nullable=True),
)

class Tag(db.Model):
    __tablename__ = 'tags'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    tag = db.Column(db.String)

files_parts = db.Table('files_parts',
        db.Column('files_uuid', UUID(as_uuid=True), db.ForeignKey('files.uuid'), primary_key=True),
    db.Column('parts_uuid', UUID(as_uuid=True), db.ForeignKey('parts.uuid'),primary_key=True,nullable=True),
)

files_organisms = db.Table('files_organisms',
        db.Column('files_uuid', UUID(as_uuid=True), db.ForeignKey('files.uuid'), primary_key=True),
    db.Column('organisms_uuid', UUID(as_uuid=True), db.ForeignKey('organisms.uuid'),primary_key=True,nullable=True),
)

def get_total_bytes(s3, key):
    result = s3.list_objects(Bucket=BUCKET)
    for item in result['Contents']:
        if item['Key'] == key:
            return item['Size']

def get_object(s3, total_bytes,key):
    if total_bytes > 1000000:
        return get_object_range(s3, total_bytes, key)
    return s3.get_object(Bucket=BUCKET, Key=key)['Body'].read()

def get_object_range(s3, total_bytes, key):
    offset = 0
    while total_bytes > 0:
        end = offset + 999999 if total_bytes > 1000000 else ""
        total_bytes -= 1000000
        byte_range = 'bytes={offset}-{end}'.format(offset=offset, end=end)
        offset = end + 1 if not isinstance(end, str) else None
        yield s3.get_object(Bucket=BUCKET, Key=key, Range=byte_range)['Body'].read()

class Files(db.Model):
    def __init__(self,name,file):
        file_name = str(uuid.uuid4())
        def upload_file_to_spaces(file,file_name=file_name,bucket_name=BUCKET,spaces=SPACES):
            """
            Docs: http://boto3.readthedocs.io/en/latest/guide/s3.html
            http://zabana.me/notes/upload-files-amazon-s3-flask.html"""
            try:
                spaces.upload_fileobj(file,bucket_name,file_name)
            except Exception as e:
                print("Failed: {}".format(e))
                return False
            return True
        if upload_file_to_spaces(file,file_name=file_name) == True:
            self.name = name
            self.file_name = file_name
    __tablename__ = 'files'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())

    name = db.Column(db.String, nullable=False) # Name to be displayed to user
    file_name = db.Column(db.String, nullable=False) # Link to spaces

    def toJSON(self,full=None):
        return {'uuid':self.uuid,'name':self.name,'file_name':self.file_name}
    def download(self):
        s3 = SPACES
        key = self.file_name
        total_bytes = get_total_bytes(s3,key)
        return Response(
            get_object(s3, total_bytes, key),
            mimetype='text/plain',
            headers={"Content-Disposition": "attachment;filename={}".format(self.name)})



# Think things
class Collection(db.Model):
    __tablename__ = 'collections'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    
    parts = db.relationship('Part',backref='collections')
    parent_uuid = db.Column(UUID, db.ForeignKey('collections.uuid'),
            nullable=True)
    children = db.relationship('Collection')

    tags = db.relationship('Tag', secondary=tags_collection, lazy='subquery',
        backref=db.backref('collections', lazy=True))
 
    name = db.Column(db.String)
    readme = db.Column(db.String)

    def toJSON(self,full=None):
        dictionary = {'uuid':self.uuid,'time_created':self.time_created,'time_updated':self.time_updated,'tags':[tag.tag for tag in self.tags],'name':self.name,'readme':self.readme,'parent_uuid':self.parent_uuid}
        if full=='full':
            dictionary['parts'] = [part.uuid for part in self.parts]
        return dictionary

class Author(db.Model):
    __tablename__ = 'authors'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    name = db.Column(db.String)
    email = db.Column(db.String)
    affiliation = db.Column(db.String)
    orcid = db.Column(db.String)
    parts = db.relationship('Part',backref='author')
    tags = db.relationship('Tag', secondary=tags_authors, lazy='subquery',
        backref=db.backref('authors', lazy=True))

    def toJSON(self,full=None): # TODO add tagging options
        dictionary = {'uuid':self.uuid,'name':self.name,'email':self.email,'affiliation':self.affiliation,'orcid':self.orcid, 'tags':[tag.tag for tag in self.tags]}
        if full=='full':
            dictionary['parts'] = [part.uuid for part in self.parts]
        return dictionary

class Organism(db.Model):
    __tablename__ = 'organisms'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    name = db.Column(db.String)
    description = db.Column(db.String)
    genotype = db.Column(db.String)
    tags = db.relationship('Tag', secondary=tags_organisms, lazy='subquery',
        backref=db.backref('organisms', lazy=True))
    files = db.relationship('Files', secondary=files_organisms, lazy='subquery', backref=db.backref('organisms', lazy=True))

    def toJSON(self,full=None):
        dictionary = {'uuid':self.uuid,'time_created':self.time_created,'time_updated':self.time_updated,'name':self.name,'description':self.description,'genotype':self.genotype,'tags':[tag.tag for tag in self.tags]}
        return dictionary

class Part(db.Model):
    __tablename__ = 'parts'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    status = db.Column(db.String) # null, optimized, fixed, sites_applied, syn_checked (syn_check_failed),   

    name = db.Column(db.String)
    description = db.Column(db.String)

    gene_id = db.Column(db.String)
    part_type = db.Column(db.String) # full_promoter, promoter, rbs, cds, terminator
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

    ip_check = db.Column(db.String(), default='Not_Checked')
    ip_check_date = db.Column(db.DateTime(timezone=True))
    ip_check_ref = db.Column(db.String())


    tags = db.relationship('Tag', secondary=tags_parts, lazy='subquery',
        backref=db.backref('parts', lazy=True))
    files = db.relationship('Files', secondary=files_parts, lazy='subquery', backref=db.backref('parts', lazy=True))

    collection_id = db.Column(UUID, db.ForeignKey('collections.uuid'),
            nullable=False)
    author_uuid = db.Column(UUID, db.ForeignKey('authors.uuid'),
            nullable=False)

    samples = db.relationship('Sample',backref='part')


    def toJSON(self,full=None):
        # Return collection ID as well
        dictionary = {'uuid':self.uuid,'time_created':self.time_created,'time_updated':self.time_updated,'status':self.status,'tags':[tag.tag for tag in self.tags],'name':self.name,'description':self.description,'gene_id':self.gene_id,'part_type':self.part_type,'original_sequence':self.original_sequence,'optimized_sequence':self.optimized_sequence,'synthesized_sequence':self.synthesized_sequence,'full_sequence':self.full_sequence,'genbank':self.genbank,'vector':self.vector,'primer_for':self.primer_for,'primer_rev':self.primer_rev,'barcode':self.barcode,'vbd':self.vbd,'author_uuid':self.author_uuid,'collection_id':self.collection_id,'translation':self.translation,'ip_check':self.ip_check,'ip_check_date':self.ip_check_date,'ip_check_ref':self.ip_check_ref}
        if full=='full':
            dictionary['samples'] = [sample.uuid for sample in self.samples]
        return dictionary


# Are things

# Plates #
plate_schema = {
    "uuid": uuid_schema,
    "status": {'type': 'string', 'enum': ['Planned','Stocked','Trashed']},
  "plate_vendor_id": generic_string,
  "breadcrumb": generic_string,
  "plate_name": generic_string,
  "plate_form": {'type': 'string', 'enum': ['standard96,deep96,standard384,deep384']},
  "plate_type": {'type': 'string', 'enum': ['archive_glycerol_stock','glycerol_stock','culture','distro']},
  "notes": generic_string,
  "protocol_uuid": uuid_schema
}
plate_required = ['status','breadcrumb','plate_name','plate_form','plate_type']

class Plate(db.Model):
    validator = schema_generator(plate_schema,plate_required)
    put_validator = schema_generator(plate_schema,[])

    __tablename__ = 'plates'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    status = db.Column(db.String) # planned, processing, complete

    plate_vendor_id = db.Column(db.String)
    breadcrumb = db.Column(db.String)
    plate_name = db.Column(db.String(32))
    plate_form = db.Column(db.String(32))
    plate_type = db.Column(db.String(32)) # dna_plate, asssembly, transformation, agar_plate, deepwell, glycerol
    wells = db.relationship('Well',backref='plate')

    notes = db.Column(db.String)
    protocol_uuid = db.Column(UUID, db.ForeignKey('protocols.uuid'), nullable=True)

    def toJSON(self,full=None):
        dictionary= {'uuid': self.uuid, 'plate_vendor_id':self.plate_vendor_id, 'breadcrumb':self.breadcrumb, 'plate_name': self.plate_name, 'plate_form': self.plate_form, 'plate_type': self.plate_type, 'status': self.status, 'protocol_uuid':self.protocol_uuid}
        if full=='full':
            dictionary['wells'] = [well.uuid for well in self.wells]
        return dictionary

# Samples #

sample_schema = {
    "uuid": uuid_schema,
    "part_uuid": uuid_schema,
    "status": {'type': 'string', 'enum': ['Confirmed', 'Mutated']},
    "derived_from": uuid_schema,
    "evidence": {'type': 'string', 'enum': ['Twist_Confirmed','NGS','Sanger','Nanopore']},
    "wells": force_to_many,
}
sample_required = ['part_uuid','status','evidence']

samples_wells = db.Table('samples_wells',
    db.Column('samples_uuid', UUID(as_uuid=True), db.ForeignKey('samples.uuid'), primary_key=True),
    db.Column('wells_uuid', UUID(as_uuid=True), db.ForeignKey('wells.uuid'), primary_key=True, nullable=True),
)
class Sample(db.Model):
    validator = schema_generator(sample_schema,sample_required)
    put_validator = schema_generator(sample_schema,[])

    __tablename__ = 'samples'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    part_uuid = db.Column(UUID, db.ForeignKey('parts.uuid'), nullable=False)
    derived_from = db.Column(UUID, db.ForeignKey('samples.uuid'), nullable=True)
    
    status = db.Column(db.String)
    evidence = db.Column(db.String) # ngs, sanger, TWIST - capitals denote outside folks

    pileups = db.relationship('Pileup',backref='sample')
    wells = db.relationship('Well', secondary=samples_wells, lazy='subquery',
        backref=db.backref('samples', lazy=True))

    def toJSON(self, full=None):
        dictionary= {'uuid':self.uuid,'derived_from':self.derived_from,'part_uuid':self.part_uuid, 'status':self.status, 'evidence':self.evidence}
        if full=='full':
            dictionary['wells'] = [well.uuid for well in self.wells]
            dictionary['pileups'] = [pileup.uuid for pileup in self.pileups]
        return dictionary

# Wells #
class Plate_loc():
    def __init__(self, height:int=8, length:int=12,locations:list=[]) -> None:
        positions = []
        for letter in list(string.ascii_uppercase[0:height]):
            for number in range(length):
                positions.append((letter, number+1))
        self.height = height
        self.length = length
        if locations==[]:
            self.locations = [x[0]+str(x[1]) for x in positions]
        else:
            self.locations = locations
well_schema = {
    "uuid": uuid_schema,
  "address": {"type": "string", "enum": Plate_loc(height=16,length=24).locations},
  "volume": { "type": "number" },
  "quantity": optional_num,
  "media": generic_string,
  "plate_uuid": uuid_schema,
    "samples": force_to_many
}
well_required = ['address','volume','media','plate_uuid','samples']
class Well(db.Model): # Constrain Wells to being unique to each plate
    validator = schema_generator(well_schema,well_required)
    put_validator = schema_generator(well_schema,[])

    __tablename__ = 'wells'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    address = db.Column(db.String(32), nullable=False)
    volume = db.Column(db.Float, nullable=True) # ul - if null, dry

    quantity = db.Column(db.Float, nullable=True) # fmol - if null, unknown
    media = db.Column(db.String(32)) # Liquid
    organism = db.Column(db.String) # IMPLEMENT ORGANISM CONTROL

    plate_uuid = db.Column(UUID, db.ForeignKey('plates.uuid'),
            nullable=False)

    def toJSON(self,full=None):
        dictionary={'uuid':self.uuid,'address':self.address,'volume':self.volume,'quantity':self.quantity,'media':self.media,'well_type':self.well_type,'organism':self.organism,'plate_uuid':self.plate_uuid} 
        if full=='full':
            dictionary['samples'] = [sample.uuid for sample in self.samples]
        return dictionary

# Protocol things

protocolschema_schema = {
    "uuid": uuid_schema,
    "name": generic_string,
    "description": generic_string,
    "schema": {'type': 'object'}
}
protocolschema_required = ['name','description','schema']
class ProtocolSchema(db.Model):
    validator = schema_generator(protocolschema_schema,protocolschema_required)
    put_validator = schema_generator(protocolschema_schema,[])

    __tablename__ = 'protocolschema'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    name = db.Column(db.String())
    description = db.Column(db.String())

    schema = db.Column(db.JSON, nullable=False)



protocol_schema = {
    "uuid": uuid_schema,
    "description": generic_string,
    "protocol": {'type': 'object'},
    "status": {'type': 'string', 'enum':['Executed','Planned']},
    "protocolschema": uuid_schema,
}
protocol_required = ['protocol','protocolschema']
class Protocol(db.Model):
    validator = schema_generator(protocol_schema,protocol_required)
    put_validator = schema_generator(protocol_schema,[])

    __tablename__ = 'protocols'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    description = db.Column(db.String())
    protocol = db.Column(db.JSON, nullable=False)

    plates = db.relationship('Plate',backref='protocol') # TODO ADD plates in toJSON

    def toJSON(self,full=None):
        dictionary= {'uuid': self.uuid, 'description': self.description, 'protocol': self.protocol, 'status': self.status, 'protocol_type':self.protocol_type}
        if full=='full':
            dictionary['plates'] = [plate.uuid for plate in self.plates]
        return dictionary

###

operator_schema = {
        "uuid": uuid_schema,
        "name": generic_string,
        "role": {"type": "string", "enum": ['PI','Admin','Technician']},
        "description": generic_string
        }
operator_required = ['name','role']
class Operator(db.Model):
    validator = schema_generator(operator_schema,operator_required)
    put_validator = schema_generator(operator_schema,[])

    __tablename__ = 'operators'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    name = db.Column(db.String())
    role = db.Column(db.String())
    description = db.Column(db.String())

    def toJSON(self,full=None):
        dictionary = {'uuid': self.uuid, 'name': self.name, 'role': self.role, 'description': self.description}
        return dictionary

plan_schema = {
        "uuid": uuid_schema,
        "name": generic_string,
        "description": generic_string,
        "requested_by" : uuid_schema,
        "executed_by": uuid_schema,
        "depends_on": uuid_schema,
        "status": {"type": "string", "enum": ['Planned','Trashed','Executed']},
        "plan_data": {"type": "object", "properties": {
            "protocols": {'oneOf': [null,{"type": "array", "items": schema_generator(protocol_schema,protocol_required)}]},
            "plates": {'oneOf': [null,{"type": "array", "items": schema_generator(plate_schema,plate_required)}]},
            "samples": {'oneOf': [null,{"type": "array", "items": schema_generator(sample_schema,sample_required)}]},
            "wells": {'oneOf': [null,{"type": "array", "items": schema_generator(well_schema,well_required)}]}
            }, 
            "additionalProperties": False},
        }    
plan_required = ['name','requested_by','status','plan_data']
class Plan(db.Model):
    validator = schema_generator(plan_schema,plan_required)
    put_validator = schema_generator(plan_schema,[])

    __tablename__ = 'plans'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String())
    status = db.Column(db.String())

    requested_by = db.Column(UUID, db.ForeignKey('operators.uuid'),nullable=False)
    executed_by = db.Column(UUID, db.ForeignKey('operators.uuid'),nullable=True)
    depends_on = db.Column(UUID, db.ForeignKey('plans.uuid'),nullable=True)

    plan_data = db.Column(db.JSON, nullable=False)

    def toJSON(self,full=None):
        dictionary = {'uuid': self.uuid, 'name': self.name, 'description': self.description, 'status': self.status, 'requested_by': self.requested_by, 'executed_by': self.executed_by, 'depends_on': self.depends_on, 'protocol': self.plan_data}
        return dictionary



