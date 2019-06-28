# Flask FreeGenes

Welcome to the Flask FreeGenes application. 

flask run --host=0.0.0.0

# bugs
- fastq file upload takes too long

## Notes
- You must upload file independently and first before applying it to a fastq or pileup
```
file_to_send = '/home/koeng/Downloads/MMSYN1_0003_1.pileup'
url= 'http://127.0.0.1:5000/files/upload'
payload = {"name": "MMSYN1_0003_1.pileup"}
files = {
     'json': ('json_file', json.dumps(payload), 'application/json'),
     'file': (os.path.basename(file_to_send), open(file_to_send, 'rb'), 'application/octet-stream')
}
r = requests.post(url, files=files,auth=())
```

`psql -d '' -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'`

Examples:
- pOpen_v3.0
`{GGAG-bbsi,GGAG-btgzi}.[].{bbsi-CGCT,btgzi-CGCT}_{AGAG-aari}.[BBF10K_003241].{aari-GTCA}`

- A part inserted into pOpen_v3.0
`{bsai-AATG}.[BBF10K_000003].{GCTT-bsai,TCC-sapi}_{AGAG-aari}.[pOpen_v3.0].{aari-GTCA}`

- A simple composite
`{bsmbi-GATG}.GGAG.[full_promoter].AATG.[cds].GCTT.[terminator].CGCT.{CAGT-bsmbi}_{AGAG-aari}.[pOpen_v3.0].{aari-GTCA}`


# reserved tags
- strain: [ccdB_res]
- marker: [gfp]
- resistance: [ampicillin]
- vector: [primitive, composite]
- target_organism: [yeast, ecoli]



