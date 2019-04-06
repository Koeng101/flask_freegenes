from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy
from sqlalchemy.sql import func
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth

db = SQLAlchemy()
auth = HTTPBasicAuth()

#class User(db.Model):
#    __tablename__ = 'users'
#    id = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
#    username = db.Column(db.String, index=True)
#    password_hash = db.Column(db.String(150))
#
#    def hash_password(self, password):
#        self.password_hash = pwd_context.hash(password)
#
#    def verify_password(self, password):
#        return pwd_context.verify(password, self.password_hash)
#
#    def generate_auth_token(self, expiration=600):
#        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
#        return s.dumps({'id': str(self.id)})
#
#    @staticmethod
#    def verify_auth_token(token):
#        s = Serializer(app.config['SECRET_KEY'])
#        try:
#            data = s.loads(token)
#        except SignatureExpired:
#            return None    # valid token, but expired
#        except BadSignature:
#            return None    # invalid token
#        user = User.query.get(data['id'])
#        return user
#
#@auth.verify_password
#def verify_password(username_or_token, password):
#    # first try to authenticate by token
#    user = User.verify_auth_token(username_or_token)
#    if not user:
#        # try to authenticate with username/password
#        user = User.query.filter_by(username=username_or_token).first()
#        if not user or not user.verify_password(password):
#            return False
#    g.user = user
#    return True


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

class Organism(db.Model):
    __tablename__ = 'organisms'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    name = db.Column(db.String)
    description = db.Column(db.String)

    organism_id = db.Column(db.String)



class Part(db.Model):
    __tablename__ = 'parts'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    status = db.Column(db.String) # Status of the design, not physical 

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
        return {'uuid':self.uuid,'time_created':self.time_created,'time_updated':self.time_updated,'status':self.status,'tags':tags,'name':self.name,'description':self.description,'gene_id':self.gene_id,'part_type':self.part_type,'original_sequence':self.original_sequence,'optimized_sequence':self.optimized_sequence,'synthesized_sequence':self.synthesized_sequence,'full_sequence':self.full_sequence,'genbank':self.genbank,'vector':self.vector,'primer_for':self.primer_for,'primer_rev':self.primer_rev,'barcode':self.barcode,'vbd':self.vbd,'author_uuid':self.author_uuid, 'samples': [sample.uuid for sample in self.samples]}

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

class Plate(db.Model):
    __tablename__ = 'plates'
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False,default=sqlalchemy.text("uuid_generate_v4()"), primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    status = db.Column(db.String) # planned, processing, complete

    plate_name = db.Column(db.String(32))
    plate_form = db.Column(db.String(32))
    plate_type = db.Column(db.String(32)) # dna_plate, asssembly, transformation, agar_plate, deepwell, glycerol
    wells = db.relationship('Well',backref='plate')

    protocol_uuid = db.Column(UUID, db.ForeignKey('protocols.uuid'), nullable=True)
    location = db.Column(db.String)

    def toJSON(self):
        return {'uuid': self.uuid, 'plate_name': self.plate_name, 'plate_form': self.plate_form, 'plate_type': self.plate_type, 'status': self.status, 'protocol_uuid':self.protocol_uuid, 'wells':[well.uuid for well in self.wells]}



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


    pileups = db.relationship('Pileup',backref='sample')
    wells = db.relationship('Well', secondary=samples_wells, lazy='subquery',
        backref=db.backref('samples', lazy=True))

    def toJSON(self, wells=True, part=False):
        return {'uuid':self.uuid,'derived_from':self.derived_from,'part_uuid':self.part_uuid,'wells':[well.uuid for well in self.wells],'pileups':[pileup.uuid for pileup in self.pileups]}

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

