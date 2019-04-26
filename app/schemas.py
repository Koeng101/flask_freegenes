from jsonschema import validate
import requests

# Shared
uuid_regex = '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
null = {'type': 'null'}

uuid = {'type': 'string','pattern': uuid_regex}
optional_uuid = {'oneOf': [uuid,null]}

generic_string = {'type': 'string'}
optional_string ={'oneOf': [generic_string,null]}

generic_date = {'type': 'string','format':'date-time'}
optional_date = {'oneOf': [generic_date,null]}

name = {'type': 'string','minLength': 3,'maxLength': 30}
tags = {'type': 'array', 'items': optional_string}
to_many = {'type': 'array', 'items': {'oneOf': [uuid,null]}}
#many_to_many = {'anyOf': [{'type': 'array','items': uuid},{'type': 'array','items': null}]}

def properties_generator(params,keys):
    return {key: params[key] for key in keys}

def object_generator(params,keys,required,additionalProperties=False):
    return {"$schema": "http://json-schema.org/schema#",
            "type": "object",
            "properties": properties_generator(params,keys),
            "required": required,
            "additionalProperties": additionalProperties}

def list_generator(name,params,keys,required):
    return {"type": "array",
            "definitions": {name: object_generator(params,keys,required)},
            "items": {"$ref": "#/definitions/{}".format(name)}}

def schema_generator(output_scheme, schema):
    def input_generator(inputs,schema,additionalProperties=False):
        return object_generator(schema['params'],list(set([item for sublist in [schema['input'][x] for x in inputs] for item in sublist])),schema['input']['required'],additionalProperties)
    # inputs
    if output_scheme == 'input_outward':
        return input_generator(['required','optional'],schema,additionalProperties=True)
    elif output_scheme == 'input_inward':
        return input_generator(['required','optional','optional_hidden'],schema)

    # ouputs
    elif output_scheme == 'output_single':
        outs = schema['output']['base']
        return object_generator(schema['params'],outs,outs)
    elif output_scheme == 'output_single_full':
        outs = schema['output']['base'] + schema['output']['full']
        return object_generator(schema['params'],outs,outs)

    elif output_scheme == 'output_all':
        outs = schema['output']['base']
        return list_generator(schema['name'],schema['params'],outs,outs)
    elif output_scheme == 'output_all_full':
        outs = schema['output']['base'] + schema['output']['full']
        return list_generator(schema['name'],schema['params'],outs,outs)
    
    raise ValueError('{} not a valid output_scheme')


collection_schema = {
        'name': 'collection',
        'params': {
            'uuid': uuid,
            'time_created': generic_date,
            'time_updated': optional_date,
            'parts': to_many,
            'parent_uuid': optional_string,
            'tags': tags,
            'name': name,
            'readme': generic_string,
            },
        'input': {
            'required': ['name','readme','tags'],
            'optional': ['parent_uuid'],
            'optional_hidden': ['uuid']
            },
        'output': {
            'base': ['uuid','time_created','time_updated','name','readme','tags','parent_uuid'],
            'full': ['parts']
            }
        }



###
collection_test = {
        'name': 'Test',
        'readme': 'foo bar!',
        'tags': ['woo', 'baz'],
        'parent_uuid': '89fbacae-c548-4a92-a370-3ffe81c80a70'
        }

#print(validate(requests.get('http://127.0.0.1:5000/collections/1c1976d1-6dbe-4f32-969c-fbf40bdd2640').json(),schema=schema_generator('output_single',collection_schema)))
#print(validate(requests.get('http://127.0.0.1:5000/collections/').json(),schema=schema_generator('output_all',collection_schema)))
#print(validate(requests.get('http://127.0.0.1:5000/collections/full/1c1976d1-6dbe-4f32-969c-fbf40bdd2640').json(),schema=schema_generator('output_single_full',collection_schema)))
#print(validate(requests.get('http://127.0.0.1:5000/collections/full').json(),schema=schema_generator('output_all_full',collection_schema)))
