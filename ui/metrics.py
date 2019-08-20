
ex={}
ex['ExAc']={'label': 'Access', 'color':'#311B92'
                ,'description':'Does the meta data contain access information for the resources?'}
ex['ExCo']={'label': 'Contact', 'color':'#4527A0'
                ,'description':'Does the meta data contain information to contact the data provider or publisher?'}
ex['ExDa']={'label': 'Date', 'color':'#512DA8'
                ,'description':'Does the meta data contain information about creation and modification date of metadata and resources respectively?'}
ex['ExDi']={'label': 'Discovery', 'color':'#5E35B1'
                ,'description':'Does the meta data contain information that can help to discover/search datasets?'}
ex['ExPr']={'label': 'Preservation', 'color':'#673AB7'
                ,'description':'Does the meta data contain information about format, size or update frequency of the resources?'}
ex['ExRi']={'label': 'Rights', 'color':'#7E57C2'
                ,'description':'Does the meta data contain information about the license of the dataset or resource.?'}
ex['ExSp']={'label': 'Spatial', 'color':'#9575CD'
                ,'description':'Does the meta data contain spatial information?'}
ex['ExTe']={'label': 'Temporal', 'color':'#B39DDB'
                ,'description':'Does the meta data contain temporal information?'}
existence={'dimension':'Existence','metrics':ex, 'color':'#B39DDB'}

ac={}
ac['AcFo']={'label': 'Format', 'color':'#00838F'
    ,'description':'Does the meta data contain information that can help to discover/search datasets?'}
ac['AcSi']={'label': 'Size', 'color':'#0097A7'
    ,'description':'Does the meta data contain information that can help to discover/search datasets?'}
accuracy={'dimension':'Accurracy', 'metrics':ac, 'color':'#0097A7'}

co={}
co['CoAc']={'label': 'AccessURL', 'color':'#388E3C'
    ,'description':'Are the available values of access properties valid HTTP URLs?'}
co['CoCE']={'label': 'ContactEmail', 'color':'#1B5E20'
    ,'description':'Are the available values of contact properties valid emails?'}

co['CoCU']={'label': 'ContactURL', 'color':'#43A047'
    ,'description':'Are the available values of contact properties valid HTTP URLs?'}
co['CoDa']={'label': 'DateFormat', 'color':'#66BB6A'
    ,'description':'Is date information specified in a valid date format?'}
co['CoFo']={'label': 'FileFormat', 'color':'#A5D6A7'
    ,'description':'Is the specified file format or media type registered by IANA?'}
co['CoLi']={'label': 'License', 'color':'#C8E6C9'
    ,'description':'Can the license be mapped to the list of licenses reviewed by opendefinition.org?'}
conformance={'dimension':'Conformance', 'metrics':co, 'color':'#C8E6C9'}

op={}
op['OpFo']={'label': 'Format Openness', 'color':'#F4511E'
    ,'description':'Is the file format based on an open standard?'}
op['OpLi']={'label': 'License Openneness', 'color':'#FF8A65'
    ,'description':'s the used license conform to the open definition?'}
op['OpMa']={'label': 'Format machine readability', 'color':'#E64A19'
    ,'description':'Can the file format be considered as machine readable?'}
opendata={'dimension':'Open Data', 'metrics':op, 'color':'#E64A19'}

re={}
re['ReDa']={'label': 'Datasets', 'color':'#FF9800'}
re['ReRe']={'label': 'Resources', 'color':'#FFA726'}
retrievability={'dimension':'Retrievability', 'metrics':re, 'color':'#FFA726'}

qa=[existence, conformance, opendata]#, retrievability, accuracy]
