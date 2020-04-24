import json

from snapshot_generation.snapshot_generator import SnapshotGenerator
from snapshot_generation.helper import *


with open("fhir_bundles/profiles.json", "r") as profile_file:
    profiles = json.load(profile_file)


def find_profile_by_id(id_):
    return next(p["resource"] for p in profiles["entry"] if p["resource"]["id"] == id_)


profile = find_profile_by_id("servicerequest-genetics")
profile_diff = profile["differential"]
base_snap = fetch_structure_definition(url=profile["baseDefinition"])["items"][0]["snapshot"]

generator = SnapshotGenerator()
result_snap = generator.augment_with_snapshot(profile)


with open("/Users/jason/Desktop/test.json", "w") as fp:
    json.dump(result_snap, fp)

for el_result, el_ref in zip(result_snap["element"], profile_snap["element"]):
    if el_result != el_ref:
        print(el_result["id"], el_result["path"])
        print("diff from")
        print(el_ref["id"], el_ref["path"])
        print()
        for k, v in el_ref.items():
            try:
                if el_result[k] != v:
                    print(el_ref["id"])
                    print(k)
                    print(v)
                    print(el_result[k])
                    print()
            except:
                print("absent in result")
                print(k, "\t", v)
                print()
        for k, v in el_result.items():
            if k not in el_ref:
                print("absent in ref")
                print(k, "\t", v)
                print()
