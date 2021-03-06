import requests

from .errors import GenerationError


def fetch_structure_definition(api_url, id_=None, url=None):
    if not (id_ is None) ^ (url is None):
        raise ValueError("should provide id or url")

    try:
        if id_ is not None:
            response = requests.get(f"{api_url}/StructureDefinition/{id_}")
        else:
            response = requests.get(f"{api_url}/StructureDefinition?url={url}")
    except requests.exceptions.ConnectionError as e:
        raise ConnectionError(f"Could not connect to the fhir-api service: {e}")
    if response.status_code != 200:
        raise Exception(f"Error while fetching structure definition: {response.text}.")

    if id_ is not None:
        return response.json()
    else:
        return response.json()["entry"][0]["resource"]


def get_root_element(structure_definition):
    for element in structure_definition["snapshot"]["element"]:
        if "." not in element["id"]:
            return element
    raise GenerationError("root element not found in structure definition.")


def prepend_root(root, val):
    """
    Helper function to build slice element definition paths and ids.

    Examples:
        - prepend_root("Observation.category:VSCat", "CodeableConcept.id")
        will return "Observation.category:VSCat.id"
        - prepend_root("Observation.category:VSCat", "CodeableConcept")
        will return "Observation.category:VSCat"
    """
    split = val.split(".", 1)
    if len(split) == 1:
        # Root case
        return root
    return f"{root}.{split[1]}"


def uppercase_first_letter(string):
    return string[0].upper() + string[1:]
