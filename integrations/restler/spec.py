"""Document the measured existing-resource domain, without fault/variant labels."""
import json
from pathlib import Path
from integrations.salon.model import RESOURCES

RESTLER_COMMIT = "6d984deedbc54aad957fa3da0c7e9e5df23a2aee"


def specification():
    paths = {}
    for operation, method, path in [("list_bookings", "get", "/bookings"),
                                    ("read_booking", "get", "/bookings/{identifier}")]+[
            (op, "post", "/bookings/{identifier}/"+op)
            for op in ("reserve", "pay", "confirm", "cancel", "refund")]:
        parameters = [{"name": "authorization", "in": "header", "required": True,
                       "schema": {"type": "string"}}]
        if "{identifier}" in path:
            parameters.append({"name": "identifier", "in": "path", "required": True,
                               "schema": {"type": "string"}})
        paths[path] = {method: {"operationId": operation, "parameters": parameters,
                               "responses": {"200": {"description": "Business response"},
                                             "401": {"description": "Authentication denial"},
                                             "403": {"description": "Role denial"},
                                             "404": {"description": "Missing or inaccessible booking"},
                                             "409": {"description": "Business state denial"}}}}
    return {"openapi": "3.0.3", "info": {"title": "TurnoSalon finite existing-resource domain", "version": "0.1.0"},
            "servers": [{"url": "http://127.0.0.1:8765"}], "paths": paths}


def write_inputs(output, headers):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    spec, dictionary = output/"openapi.json", output/"dictionary.json"
    spec.write_text(json.dumps(specification(), indent=2)+"\n")
    dictionary.write_text(json.dumps({"restler_custom_payload": {"identifier": list(RESOURCES)},
        "restler_custom_payload_header": {"authorization": [headers[a].get("Authorization", "")
                  for a in ("alice", "bob", "staff_a", "staff_b", "anonymous")]},
        "restler_fuzzable_string": [], "restler_fuzzable_int": [], "restler_fuzzable_bool": [],
        "restler_fuzzable_number": [], "restler_fuzzable_object": [], "restler_fuzzable_uuid4": [],
        "restler_fuzzable_datetime": [], "restler_fuzzable_date": []}, indent=2)+"\n")
    config = {"SwaggerSpecFilePath": [str(spec)], "CustomDictionaryFilePath": str(dictionary),
              "ResolveHeaderDependencies": True, "UseHeaderExamples": False, "UsePathExamples": False,
              "IncludeOptionalParameters": False}
    (output/"compiler.json").write_text(json.dumps(config, indent=2)+"\n")
    return output/"compiler.json"
