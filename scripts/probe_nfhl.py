import requests
from siteselect.refine import NFHL, H
for bb in [(-122.6, 46.75, -121.3, 47.65), (-122.1, 47.1, -121.8, 47.3)]:
    p = dict(where="SFHA_TF='T'", geometry=",".join(map(str, bb)), geometryType="esriGeometryEnvelope",
             inSR=4326, spatialRel="esriSpatialRelIntersects", f="json")
    r = requests.get(NFHL, params={**p, "returnIdsOnly": "true"}, headers=H, timeout=120)
    j = r.json()
    print(bb, r.status_code, list(j.keys()), len(j.get("objectIds") or []), str(j.get("error"))[:200])
    c = requests.get(NFHL, params={**p, "returnCountOnly": "true"}, headers=H, timeout=120).json()
    print("count", c)
