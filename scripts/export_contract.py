"""Export structural OpenAPI contracts without examples, URLs or credentials."""

import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path

import yaml


def export(source):
    raw = source.read_bytes()
    document = yaml.safe_load(raw)
    annotations = {"title", "description", "example", "examples", "externalDocs", "$comment"}
    mappings = {"properties", "patternProperties", "$defs", "definitions", "dependentSchemas"}
    subschemas = {"items", "additionalProperties", "unevaluatedProperties", "contains", "not", "if", "then", "else", "propertyNames", "unevaluatedItems"}

    def sensitive_name(name):
        return any(term in name.lower() for term in ("password", "secret", "token", "api_key"))

    def has_literal(value):
        if isinstance(value, dict):
            return any(value.get(key) is not None for key in ("default", "const", "enum")) or any(has_literal(child) for child in value.values())
        if isinstance(value, list):
            return any(has_literal(child) for child in value)
        return False

    def check_literal(value):
        if isinstance(value, dict):
            for name, child in value.items():
                if sensitive_name(name) and child is not None:
                    raise ValueError("Sensitive schema literal requires manual review; export stopped")
                check_literal(child)
        elif isinstance(value, list):
            for child in value:
                check_literal(child)

    def resolve(schema, seen=()):
        if not isinstance(schema, dict):
            return schema
        result = {}
        if "$ref" in schema:
            reference = schema["$ref"]
            if not reference.startswith("#/components/schemas/") or reference in seen:
                raise ValueError("Unsupported or cyclic schema reference")
            target = document
            for part in reference[2:].split("/"):
                target = target[part.replace("~1", "/").replace("~0", "~")]
            resolved = resolve(target, (*seen, reference))
            siblings = {key: value for key, value in schema.items() if key not in {"$ref", "nullable"} | annotations}
            result = {"allOf": [resolved, resolve(siblings, seen)]} if siblings else resolved
        else:
            for key, value in schema.items():
                if key in annotations or key == "nullable":
                    continue
                if key in mappings:
                    result[key] = {name: resolve(field, seen) for name, field in value.items()}
                elif key in subschemas:
                    result[key] = resolve(value, seen)
                elif key in {"anyOf", "oneOf", "allOf", "prefixItems"}:
                    result[key] = [resolve(field, seen) for field in value]
                else:
                    if key in {"default", "const", "enum"}:
                        check_literal(value)
                    result[key] = deepcopy(value)
            for name, field in result.get("properties", {}).items():
                if sensitive_name(name) and has_literal(field):
                    raise ValueError("Sensitive schema literal requires manual review; export stopped")
        if schema.get("nullable"):
            result = {"anyOf": [result, {"type": "null"}]}
        return result

    operations = []
    names = set()
    for route, methods in document["paths"].items():
        for method, operation in methods.items():
            if method not in {"get", "post", "put", "patch", "delete", "head", "options", "trace"}:
                continue
            name = operation["operationId"]
            if name in names:
                raise ValueError("Duplicate operationId")
            names.add(name)
            properties = {}
            required = []
            locations = {}
            metadata = {}
            parameters = {(parameter["in"], parameter["name"]): parameter for parameter in methods.get("parameters", []) + operation.get("parameters", [])}
            for parameter in parameters.values():
                if parameter["in"] not in {"path", "query"}:
                    raise ValueError("Unexpected parameter location: review before export")
                key = parameter["name"]
                if key in properties or key == "body":
                    raise ValueError("Ambiguous MCP parameter name")
                properties[key] = resolve(parameter["schema"])
                if sensitive_name(key) and has_literal(properties[key]):
                    raise ValueError("Sensitive parameter literal requires manual review; export stopped")
                locations[key] = parameter["in"]
                metadata[key] = {field: deepcopy(parameter[field]) for field in ("style", "explode", "allowReserved") if field in parameter}
                if parameter.get("required"):
                    required.append(key)
            if "requestBody" in operation:
                body = operation["requestBody"]
                properties["body"] = resolve(body["content"]["application/json"]["schema"])
                if body.get("required"):
                    required.append("body")
            responses = {
                str(status): resolve(response.get("content", {}).get("application/json", {}).get("schema", {}))
                for status, response in operation["responses"].items()
            }
            operations.append({
                "name": name, "method": method.upper(), "path": route,
                "input": {"type": "object", "properties": properties, "required": required},
                "parameter_locations": locations, "parameter_metadata": metadata, "responses": responses,
                "security": deepcopy(operation.get("security", document.get("security", []))),
                "authentication_verified": False,
            })
    security_schemes = {
        name: {key: deepcopy(scheme[key]) for key in ("type", "in", "name", "scheme") if key in scheme}
        for name, scheme in document.get("components", {}).get("securitySchemes", {}).items()
    }
    return {"source_sha256": hashlib.sha256(raw).hexdigest(), "security_schemes": security_schemes, "operations": operations}


if __name__ == "__main__":
    contract = export(Path(sys.argv[1]))
    destination = Path(__file__).resolve().parents[1] / "contracts" / "actions.json"
    if "--check" in sys.argv[2:]:
        if json.loads(destination.read_text()) != contract:
            raise SystemExit("Contract drift: review YAML changes before regenerating")
        print(f"Contract parity PASS: {len(contract['operations'])} operations match the local YAML")
    else:
        destination.parent.mkdir(exist_ok=True)
        destination.write_text(json.dumps(contract, indent=2, ensure_ascii=True) + "\n")
        print(f"Exported {len(contract['operations'])} operations; application defaults preserved, examples excluded")