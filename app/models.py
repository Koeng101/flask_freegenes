from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy
from sqlalchemy.sql import func
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from flask import Flask, abort, request, jsonify, g, url_for, Response
import uuid

from .config import SPACES
from .config import BUCKET

from .config import SECRET_KEY
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from passlib.apps import custom_app_context as pwd_context

db = SQLAlchemy()
auth = HTTPBasicAuth()

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
        s = Serializer(SECRET_KEY, expires_in=expiration)
        return s.dumps({'id': str(self.id)})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(SECRET_KEY)
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


# TODO fastq and pileup files
# TODO how to upload files?
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

distributions_plates = db.Table('distributions_plates',
        db.Column('distribution_uuid', UUID(as_uuid=True), db.ForeignKey('distributions.uuid'), primary_key=True),
    db.Column('plates_uuid', UUID(as_uuid=True), db.ForeignKey('plates.uuid'),primary_key=True,nullable=True),
)

class Distribution(db.Model):
    __tablename__ = 'distributions'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    
    plates = db.relationship('Plate', secondary=distributions_plates, lazy='subquery',
        backref=db.backref('distributions', lazy=True))
    collection_uuid = db.Column(UUID, db.ForeignKey('collections.uuid'),nullable=False)
    notes = db.Column(db.String)
    status = db.Column(db.String) # building,shipping,recreating

class Plan(db.Model):
    __tablename__ = 'plans'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    status = db.Column(db.String) # planned,executed
    notes = db.Column(db.String)
    plan = db.Column(db.JSON, nullable=False)

# Think things
class Collection(db.Model):
    __tablename__ = 'collections'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    
    status = db.Column(db.String) # planned, in-progress

    distributions = db.relationship('Distribution',backref='collections')
    parts = db.relationship('Part',backref='collections')
    parent_uuid = db.Column(UUID, db.ForeignKey('collections.uuid'),
            nullable=True)
    children = db.relationship('Collection')

    tags = db.relationship('Tag', secondary=tags_collection, lazy='subquery',
        backref=db.backref('collections', lazy=True))
 
    name = db.Column(db.String)
    readme = db.Column(db.String)

    def toJSON(self,full=None):
        dictionary = {'uuid':self.uuid,'time_created':self.time_created,'time_updated':self.time_updated,'status':self.status,'tags':[tag.tag for tag in self.tags],'name':self.name,'readme':self.readme,'parent_uuid':self.parent_uuid}
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
        dictionary = {'uuid':self.uuid,'time_created':self.time_created,'time_updated':self.time_updated,'status':self.status,'tags':[tag.tag for tag in self.tags],'name':self.name,'description':self.description,'gene_id':self.gene_id,'part_type':self.part_type,'original_sequence':self.original_sequence,'optimized_sequence':self.optimized_sequence,'synthesized_sequence':self.synthesized_sequence,'full_sequence':self.full_sequence,'genbank':self.genbank,'vector':self.vector,'primer_for':self.primer_for,'primer_rev':self.primer_rev,'barcode':self.barcode,'vbd':self.vbd,'author_uuid':self.author_uuid,'translation':self.translation}
        if full=='full':
            dictionary['samples'] = [sample.uuid for sample in self.samples]
        return dictionary

# Do things
class Robot(db.Model):
    __tablename__ = 'robots'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    name = db.Column(db.String)
    notes = db.Column(db.String)
    protocols = db.relationship('Protocol',backref='robot')
    pipettes = db.relationship('Pipette',backref='robot')

    def toJSON(self,full=None):
        dictionary = {'uuid':self.uuid,'right_300':self.right_300,'left_10':self.left_10,'robot_name':self.robot_name,'notes':self.notes}
        if full=='full':
            dictionary['protocols'] = [protocol.uuid for protocol in self.protocols]
        return dictionary

class Pipette(db.Model):
    __tablename__ = 'pipettes'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    pipette_type = db.Column(db.String) # TODO enum here
    mount_side = db.Column(db.String)
    robot_uuid = db.Column(UUID, db.ForeignKey('robots.uuid'),
            nullable=True)
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

    robot_uuid = db.Column(UUID, db.ForeignKey('robots.uuid'),
            nullable=True)

    def toJSON(self,full=None):
        dictionary= {'uuid': self.uuid, 'description': self.description, 'protocol': self.protocol, 'status': self.status, 'protocol_type':self.protocol_type}
        if full=='full':
            dictionary['plates'] = [plate.uuid for plate in self.plates]
        return dictionary

# Are things

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

    notes = db.Column(db.String)
    protocol_uuid = db.Column(UUID, db.ForeignKey('protocols.uuid'), nullable=True)

    def toJSON(self,full=None):
        dictionary= {'uuid': self.uuid, 'breadcrumb':self.breadcrumb, 'plate_name': self.plate_name, 'plate_form': self.plate_form, 'plate_type': self.plate_type, 'status': self.status, 'protocol_uuid':self.protocol_uuid}
        if full=='full':
            dictionary['wells'] = [well.uuid for well in self.wells]
        return dictionary



samples_wells = db.Table('samples_wells',
    db.Column('samples_uuid', UUID(as_uuid=True), db.ForeignKey('samples.uuid'), primary_key=True),
    db.Column('wells_uuid', UUID(as_uuid=True), db.ForeignKey('wells.uuid'), primary_key=True, nullable=True),
)

class Sample(db.Model):
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
        dictionary= {'uuid':self.uuid,'derived_from':self.derived_from,'part_uuid':self.part_uuid, 'status':self.status, 'evidence':self.status}
        if full=='full':
            dictionary['wells'] = [well.uuid for well in self.wells]
            dictionary['pileups'] = [pileup.uuid for pileup in self.pileups]
        return dictionary

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
    organism = db.Column(db.String) # IMPLEMENT ORGANISM CONTROL

    plate_uuid = db.Column(UUID, db.ForeignKey('plates.uuid'),
            nullable=False)

    def toJSON(self,full=None):
        dictionary={'uuid':self.uuid,'address':self.address,'volume':self.volume,'quantity':self.quantity,'media':self.media,'well_type':self.well_type,'organism':self.organism,'plate_uuid':self.plate_uuid} 
        if full=='full':
            dictionary['samples'] = [sample.uuid for sample in self.samples]
        return dictionary


# Verify things
class Seqrun(db.Model):
    __tablename__ = 'seqruns'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    name = db.Column(db.String) # run name
    run_id = db.Column(db.String) # Sequencing provider id
    machine_id = db.Column(db.String)
    notes = db.Column(db.String)
    sequencing_type = db.Column(db.String) # illumina, nanopore, etc
    machine = db.Column(db.String) # minion, iseq, etc
    provider = db.Column(db.String) # in-house

    job = db.Column(db.String) # the job id of the redis job

    fastqs = db.relationship('Fastq',backref='seqrun')

    def toJSON(self,full=None):
        dictionary= {'uuid':self.uuid,'time_created':self.time_created,'time_updated':self.time_updated,'name':self.name,'run_id':self.run_id,'machine_id':self.machine_id,'notes':self.notes,'sequencing_type':self.sequencing_type,'machine':self.machine,'provider':self.provider, 'job':self.job}
        if full=='full':
            dictionary['fastqs'] = [fastq.uuid for fastq in self.fastqs]
        return dictionary

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

    sample_uuid = db.Column(UUID, db.ForeignKey('samples.uuid'),
            nullable=False)
    fastqs = db.relationship('Fastq', secondary=pileup_fastq, lazy='subquery',
        backref=db.backref('pileups', lazy=True))

    file_uuid = db.Column(UUID, db.ForeignKey('files.uuid'),nullable=True)
    
    def toJSON(self,full=None):
        dictionary= {'uuid':self.uuid,'time_created':self.time_created,'time_updated':self.time_updated,'status':self.status,'full_search_sequence':self.full_search_sequence,'target_sequence':self.target_sequence,'file_uuid':self.file_uuid, 'sample_uuid': self.sample_uuid}
        if full=='full':
            dictionary['fastqs'] = [fastq.uuid for fastq in self.fastqs]
        return dictionary

class Fastq(db.Model):
    __tablename__ = 'fastqs'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    seqrun_uuid = db.Column(UUID, db.ForeignKey('seqruns.uuid'), nullable=False)
    name = db.Column(db.String)

    file_uuid = db.Column(UUID, db.ForeignKey('files.uuid'),nullable=True)

    index_for = db.Column(db.String)
    index_rev = db.Column(db.String)
    
    def toJSON(self,full=None):
        dictionary= {'uuid':self.uuid,'time_created':self.time_created,'time_updated':self.time_updated,'seqrun_uuid':self.seqrun_uuid,'file_uuid':self.file_uuid,'index_for':self.index_for,'index_rev':self.index_rev}
        if full=='full':
            dictionary['pileups'] = [pileup.uuid for pileup in self.pileups]
        return dictionary

