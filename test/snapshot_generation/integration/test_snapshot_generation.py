import json

from snapshot_generation.snapshot_generator import SnapshotGenerator
from snapshot_generation.helper import *

API_URL = "https://pyrog.staging.arkhn.com/api"

with open("fhir_bundles/profiles.json", "r") as profile_file:
    profiles = json.load(profile_file)


# Known to have weird snapshot/differential pairs I don't agree with
profiles_to_skip = [
    "bp",  # Add .code on a BackboneElement?
    "catalog",  # One element is missing in snapshot...
    "clinicaldocument",
    "diagnosticreport-genetics",
    "elementdefinition-de",  # Extensions are expanded in snap but not in diff
    "familymemberhistory-genetic",
    "hlaresult",  # Default slicing absent from some extensions in snap
    "observation-genetics",  # Default slicing absent from some extensions in snap
    "provenance-relevant-history",
    "servicerequest-genetics",
]

# Some fields that are sometimes slightly different between diff or base and snapshot.
# For instance, some words are modified in descriptions.
fields_to_skip = [
    "alias",
    "base",
    "comment",
    # TODO check what this is in fhir and why it sometimes change
    # when profiling without being noticed in differential
    "condition",
    "constraint",
    "definition",
    # TODO check what this is in fhir and why it sometimes change
    # when profiling without being noticed in differential
    "mapping",
    "requirements",
    "short",
    # Sometimes, type is restricted in ref slice root but I don't think they should
    # maybe we should anyway check that the ref type is in the result types.
    "type",
]

# TODO investigate on these. Maybe some of them can be added/removed easily in
# generated snapshot
can_be_absent_in_result = ["alias", "comment", "mapping", "slicing"]
can_be_absent_in_ref = ["alias", "comment", "mapping", "isSummary"]


def test_snapshot_generation():
    generator = SnapshotGenerator(api_url=API_URL)

    for profile_definition in profiles["entry"]:
        profile = profile_definition["resource"]
        profile_snapshot = profile["snapshot"]
        profile_diff = profile["differential"]

        if profile["id"] in profiles_to_skip:
            continue

        augmented_profile = generator.augment_with_snapshot(profile)

        for el_result, el_ref in zip(
            augmented_profile["snapshot"]["element"], profile_snapshot["element"]
        ):
            if el_result != el_ref:
                for k, v in el_ref.items():
                    if k in el_result:
                        if el_result[k] != v:
                            assert k in fields_to_skip, f"{profile['id']}, {k}, {v}"
                    else:
                        assert k in can_be_absent_in_result, f"{profile['id']}, {k}, {v}"
                for k, v in el_result.items():
                    if k not in el_ref:
                        assert k in can_be_absent_in_ref, f"{profile['id']}, {k}, {v}"
