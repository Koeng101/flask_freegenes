import pandas as pd
import itertools
from constraint import *
import os
from .models import uuid_schema, generic_num,schema_generator

con = os.environ['URL']

# Robot side
class Part():
    def __init__(self,uuid,address,volume,quantity,plate_uuid):
        self.uuid = uuid
        self.address = address
        self.volume = volume
        self.quantity = quantity
        self.plate_uuid = plate_uuid
        
        self.volume_used = 0
    
    def export(self):
        return {'uuid':self.uuid,'address':self.address,'plate_uuid':self.plate_uuid}
            
class Plate():
    def __init__(self,uuid,parts_list,thaw_weight,container_uuid):
        self.uuid = uuid
        self.parts_list = parts_list
        self.thaw_weight = thaw_weight
        self.container_uuid = container_uuid
        
    def contains_part(self,part_uuid):
        for part in self.parts_list:
            if part_uuid == part.uuid:
                return True
        return False
    
        
class PlateList():
    def __init__(self,plate_list):
        self.plates = plate_list
        
    def contains_part_sublist(self,part_uuid_list): # Does a list of part UUIDs exist in one plate in this list?
        part_found=False
        for part_uuid in part_uuid_list:
            for plate in self.plates:
                if plate.contains_part(part_uuid):
                    part_found=True
                    break
            if part_found !=True:
                return False
        return True
    
    def contains_part_list(self,parts):
        for part_uuid_list in parts:
            if not self.contains_part_sublist(part_uuid_list):
                return False
            
        return True
    
    def get_part(self,part,volume_min=15):
        for plate in self.plates:
            for part in plate.parts_list:
                if part.uuid == part and part.volume-part.volume_used > 15:
                    return part
        return False
    
    def reset_used_volume(self):
        for plate in self.plates:
            for part in plate.parts_list:
                part.volume_used=0
        return True
    
    def thaw_weight(self):
        return sum([x.thaw_weight for x in self.plates])
    
    def containers(self):
        return [x.container_uuid for x in self.plates]
    
    def export_part_dict(self):
        parts_dict = {}
        for plate in self.plates:
            for part in plate.parts_list:
                parts_dict[part.uuid] = part.export()
        return parts_dict

    
build_schema = build_schema = {
    'parts': {'type':'array', 'items': {'type': 'array', 'items': uuid_schema}},
    'volume': generic_num,
    'sample_status': {'type': 'array', 'items': {'type': 'string', 'enum': ['Confirmed', 'Mutated']}},
    'sample_evidence': {'type': 'array', 'items': {'type': 'string', 'enum': ['NGS','Twist_Confirmed']}},
    'plate_type': {'type': 'array', 'items': {'type': 'string', 'enum': ['glycerol_stock','distro']}}, 
    'sort_method': {'type': 'array', 'items': {'type': 'string', 'enum': ['fewest_plates','fewest_retrieval','highest_thaw_count','lowest_thaw_count']}}
}
build_required = ['parts','volume']
# Request side
class Build():
    def __init__(self,transfer_groups:list,sample_status:list=['Confirmed'],sample_evidence:list=['NGS','Twist_Confirmed'],plate_type:list=['glycerol_stock']):
        self.transfer_groups = transfer_groups
        self.sample_status = sample_status
        self.sample_evidence = sample_evidence
        self.plate_type = plate_type
        self.plate_list = 'Not Generated'
    validator = schema_generator(build_schema,build_required)
        
    def transfer_groups_as_part(self,parts,volume):
        transfer_groups = []
        for g in parts:
            transfers=[]
            for part in g:
                transfers.append(Transfer(part,volume))
            transfer_groups.append(TransferGroup(transfers))
        self.transfer_groups = transfer_groups
        return transfer_groups



    def flatten(self,lst):
        return [item for sublist in lst for item in sublist]
    
    def export_part_list(self):
        lst = []
        for transfer_group in self.transfer_groups:
            sublst = []
            for transfer in transfer_group.transfers:
                sublst.append(transfer.part)
            lst.append(sublst)
        return lst
    
    def export_flat_part_list(self):
        return self.flatten(self.export_part_list())
    
    def generate_PlateList(self,con):
        def generate_part_sql(uuid_list:list,
                      sample_status:list,
                      sample_evidence:list,
                      plate_type:list):
            def sqlval(lst):
                return "'{}'".format('\' , \''.join(lst))
            def lst_to_sql(field,lst):
                if None in lst:
                    return "AND ({} IN ({}) OR {} IS NULL)".format(field,sqlval([x for x in lst if x!=None]),field)
                else:
                    return "AND {} IN ({})".format(field,sqlval(lst))
            sql_query = """SELECT DISTINCT p.uuid AS part_uuid, pl.uuid AS plate_uuid, w.address, w.volume, (pl.thaw_count + 1) * t.count AS thaw_weight, pl.container_uuid AS container_uuid
        FROM parts AS p 
        JOIN samples AS s ON s.part_uuid=p.uuid
        JOIN samples_wells AS sw ON sw.samples_uuid=s.uuid
        JOIN wells AS w ON w.uuid=sw.wells_uuid
        JOIN plates AS pl ON pl.uuid=w.plate_uuid
        JOIN (SELECT plate_uuid, COUNT(*) FROM wells GROUP BY plate_uuid) as t on t.plate_uuid=pl.uuid
        WHERE p.uuid in ({}) 
        AND pl.status = 'Stocked'
        {}
        {}
        {}
        """.format(sqlval(uuid_list),
                   lst_to_sql("s.status",sample_status),
                   lst_to_sql("s.evidence",sample_evidence),
                   lst_to_sql("pl.plate_type",plate_type))
            return sql_query
    
        df = pd.read_sql(generate_part_sql(self.export_flat_part_list(),self.sample_status,self.sample_evidence,self.plate_type),con)
        plate_dict = {}
        thaw_dict = {}
        container_dict = {}
        for index, row in df.iterrows():
            plate_dict.setdefault(str(row[1]),[]).append({"part_uuid":str(row[0]), "address":row[2], "volume":row[3], "quantity":row[4]})
            thaw_dict.setdefault(str(row[1]),row[4])
            container_dict.setdefault(str(row[1]),str(row[5]))

        plates = []
        for k,v in plate_dict.items():
            plates.append(Plate(k,[Part(x['part_uuid'],x['address'],x['volume'],x['quantity'],k) for x in v],thaw_dict[k],container_dict[k]))

        plates = PlateList(plates)
        self.plate_list = plates
        return plates

    def plate_possibilities(self):
        def sub_lists(lst): 
            sublist = [[]] 
            for i in range(len(lst) + 1):   
                for j in range(i + 1, len(lst) + 1): 
                    sub = lst[i:j] 
                    sublist.append(sub) 
            return sublist  

        def combine_lists(a,b):
            return list(itertools.product(a, b))
        
        return sub_lists(self.plate_list.plates)
        

    ### IMPORTANT STUFF ###
    def solutions(self):
        solutions = [PlateList(x) for x in self.plate_possibilities() if PlateList(x).contains_part_list(self.export_part_list())]
        return solutions
    
    def sorted_solutions(self,sort_methods):
        solutions = self.solutions()
        if 'fewest_plates' in sort_methods:
            minimal_plate_num = min([len(x.plates) for x in solutions])
            solutions = [x for x in solutions if len(x.plates) == minimal_plate_num]
            
        if 'fewest_retrieval' in sort_methods:
            minimal_location_num = min([len(x.containers()) for x in solutions])
            solutions = [x for x in solutions if len(x.containers()) == minimal_location_num]
        
        if 'highest_thaw_count' in sort_methods:
            max_thaw = max([x.thaw_weight() for x in solutions])
            solutions = [x for x in solutions if x.thaw_weight() == max_thaw]
            
        if 'lowest_thaw_count' in sort_methods:
            min_thaw = min([x.thaw_weight() for x in solutions])
            solutions = [x for x in solutions if x.thaw_weight() == min_thaw]
        return solutions
    
    def export_solution(self,sort_methods=['fewest_plates','fewest_retrieval']):
        solutions = self.sorted_solutions(sort_methods)
        solution = solutions[0] # Pick first solution, might as well
        parts_dict = solution.export_part_dict()
        transfer_groups = []
        for tg in self.transfer_groups:
            transfers = []
            for t in tg.transfers:
                transfers.append({'part':t.part,'volume':t.volume,'address':parts_dict[t.part]['address'],'plate_uuid':parts_dict[t.part]['plate_uuid']})
            transfer_groups.append(transfers)
        return {'plates':[x.uuid for x in solution.plates], 'transfers':transfer_groups}
    
    
class TransferGroup():
    def __init__(self,transfers):
        self.transfers = transfers

class Transfer():
    def __init__(self,part,volume,quantity=0):
        self.part = part
        self.volume = volume
        self.quantity = quantity
        self.address = None
        self.plate_uuid = None
        
    def export_dict(self):
        if self.quantity == 0:
            return {'part_uuid':self.part,'volume':self.volume}
        
    def set_well(self,plate_uuid,address):
        self.plate_uuid = plate_uuid
        self.address = address
        return True
