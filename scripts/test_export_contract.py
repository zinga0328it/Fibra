import json
import tempfile
import unittest
from pathlib import Path

from export_contract import export


class ExportTests(unittest.TestCase):
    def export_schema(self, body, components=None, path_parameters=None, operation_parameters=None):
        document = {"openapi": "3.1.0", "paths": {"/test": {"post": {
            "operationId": "testAction", "requestBody": {"required": True, "content": {"application/json": {"schema": body}}},
            "responses": {"200": {"content": {"application/json": {"schema": body}}}},
        }}}}
        document["components"] = components or {}
        document["paths"]["/test"]["parameters"] = path_parameters or []
        document["paths"]["/test"]["post"]["parameters"] = operation_parameters or []
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "synthetic.json"
            source.write_text(json.dumps(document))
            return export(source)["operations"][0]

    def test_defaults_application_keys_and_optional_nulls_survive(self):
        body = {"type": "object", "properties": {
            "description": {"type": "string", "default": "value"},
            "settings": {"type": "object", "default": {"description": "application-data"}},
            "note": {"type": "string", "nullable": True},
        }}
        result = self.export_schema(body)
        schema = result["input"]["properties"]["body"]
        self.assertEqual(schema["properties"]["description"]["default"], "value")
        self.assertEqual(schema["properties"]["settings"]["default"], {"description": "application-data"})
        self.assertEqual(schema["properties"]["note"]["anyOf"][-1], {"type": "null"})
        self.assertNotIn("additionalProperties", schema)
        self.assertNotIn("additionalProperties", result["input"])

    def test_explicit_restrictions_and_response_schema_survive(self):
        body = {"type": "object", "additionalProperties": False, "required": ["value"], "properties": {
            "value": {"type": "integer", "default": 5, "minimum": 1, "maximum": 9},
        }}
        result = self.export_schema(body)
        self.assertEqual(result["input"]["properties"]["body"], body)
        self.assertEqual(result["responses"]["200"], body)

    def test_sensitive_literals_stop_export_instead_of_changing_contract(self):
        with self.assertRaises(ValueError):
            self.export_schema({"properties": {"api_key": {"default": "synthetic-do-not-export"}}})

    def test_examples_removed_not_application_properties(self):
        result = self.export_schema({"type": "object", "description": "annotation", "examples": [{}], "properties": {"examples": {"type": "array"}}})
        schema = result["responses"]["200"]
        self.assertNotIn("description", schema)
        self.assertNotIn("examples", schema)
        self.assertIn("examples", schema["properties"])

    def test_local_reference_siblings_and_nullable_survive(self):
        result = self.export_schema({"$ref": "#/components/schemas/Value~1Type", "maximum": 9, "nullable": True},
                                    {"schemas": {"Value/Type": {"type": "integer", "minimum": 1, "default": 5}}})
        self.assertEqual(result["responses"]["200"], {"anyOf": [
            {"allOf": [{"type": "integer", "minimum": 1, "default": 5}, {"maximum": 9}]}, {"type": "null"},
        ]})

    def test_sensitive_defaults_through_refs_and_nested_literal_are_blocked(self):
        with self.assertRaises(ValueError):
            self.export_schema({"properties": {"api_key": {"$ref": "#/components/schemas/Key"}}},
                               {"schemas": {"Key": {"default": "synthetic-only"}}})
        with self.assertRaises(ValueError):
            self.export_schema({"default": {"settings": {"api_key": "synthetic-only"}}})

    def test_external_and_cyclic_refs_fail_closed(self):
        with self.assertRaises(ValueError):
            self.export_schema({"$ref": "https://example.invalid/schema"})
        with self.assertRaises(ValueError):
            self.export_schema({"$ref": "#/components/schemas/Loop"},
                               {"schemas": {"Loop": {"$ref": "#/components/schemas/Loop"}}})

    def test_operation_parameter_override_keeps_default_and_serialization(self):
        result = self.export_schema({}, path_parameters=[
            {"in": "query", "name": "limit", "required": True, "schema": {"type": "integer", "default": 10}},
        ], operation_parameters=[
            {"in": "query", "name": "limit", "schema": {"type": "integer", "default": 20}, "style": "form", "explode": False},
        ])
        self.assertEqual(result["input"]["properties"]["limit"]["default"], 20)
        self.assertNotIn("limit", result["input"]["required"])
        self.assertEqual(result["parameter_metadata"]["limit"], {"style": "form", "explode": False})


if __name__ == "__main__":
    unittest.main()