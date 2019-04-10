# Flask FreeGenes

Welcome to the Flask FreeGenes application. 

flask run --host=0.0.0.0

## Examples
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

## Notes
- You must upload file independently and first before applying it to a fastq or pileup
