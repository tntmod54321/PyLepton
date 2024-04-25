# install
  `python -m pip install -r requirements.txt`

# usage
```
import lepton
with open('./test.jpg', 'rb') as fh:
    jpeg = fh.read()

lep = lepton.encode(jpeg)
_ = lepton.decode(lep)

# encode_verify will decode the lepton file and verify the hash (xxhash3 128)
# the hash is accessible as lep.jpeghash
lep = lepton.encode_verify(jpeg)

with open('./test.lep', 'wb') as fh:
    fh.write(lep.data)
```
