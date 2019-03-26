import requests
import uuid


# Setup a collection
r = requests.get('http://127.0.0.1:5000/samples')
print(r.text)
