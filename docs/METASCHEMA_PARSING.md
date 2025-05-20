# Metaschema Parsing

## Metaschema Structure
```json
metaschema = "model-name" : [{"name": element_name,
                    "type": [ "assembly" | "field" | "flag" ],
                    "path": "/model_name/x/y/z",
                    "source": "name-of-metaschema-file",
                    "scope": ["global" | "local"], (default: global)
                    "formal-name": "formal_name",
                    "description": "description",
                    "datatype": "string",
                    "min-occurs": [ "0" | "1" ],
                    "max-occurs": [ "1" | "unbounded" ],
                    "value-type": "OSCAL_value_type",
                    "json-array-name": "json_array_name",
                    "json-value-key": "string"
                    "attributes": [ { repeat_this_dict }, {} ], (required: min-occurs=1, max-occurs=1, not-required: min-occurs=0, max-occurs=1)
                    "children": [ { repeat this dict }, {} ],
                    "allowed_values": [ {"value": "value2", "text": "string"}, {} ],
                    "rules": ["rule_id", "rule_id", "rule_id"],  (if the rule context matches this path location)
                    "props": ["name": {"value": "string", "namespace": "string"}, {}],
                    "remarks": "string",
                    "rules": [ {rule-object-see-below} ],
                    "rule-references": ["rule_id", "rule_id", "rule_id"], (for rules that apply in more than one place)
                    "value" : _as_appropriate_for_this_context_,
                    }]
```

### Properties and Values

identifier-persistence: per-subject
identifier-scope: cross-instance
identifier-type: human-oriented, machine-oriented
identifier-uniqueness: instance
value-type: identifier, identifier-reference

## Rules Structure

```json
        rules = {"id": "rule_id", (if no ID present, assign a UUID)
                "level": ["CRITICAL", "ERROR", "WARNING", "INFORMATIONAL", "DEBUG"], (when not specified, default to ERROR)
                "name": "rule_name",
                "formal-name": "formal_name",
                "description": "description",
                "rule-type": ["let", "allowed-values", "expect", "has-cardinality", "index", "index-has-key", "is-unique", "matches"], (array: one or more)
                "data-type": "string",
                "pattern": "string", (regex pattern)
                "allowed-values": [ {"value": "value2", "text": "string"}, {} ],
                "allow-others": True,
                "extensible": ["none", "model", "external"],  (default: model)
                "test": "metapath-string",
                "index-key": {"target": "string", "pattern": "string", "remarks": "string"}, (target is xapth, pattern is a regex pattern)
                "message": "string",
                "source": {"organization": "string", "url": "string", "version": "string"},
                "context": ["/model_name/x/y/z", "/model_name/a/b/c"],
                "target": "./p/d/q",
                "help-url": ["uri", "uri"],
                "help-text": ["string", "string"],
                "min-occurs": "0",
                "max-occurs": "unbounded",
                "depreciated": True, (If metaschema @depreciated is present and this verison is >= the depreciated version, this is set to True.)
                "sunsetting": "version", (If metaschema @depreciated is present, but this versiion is still valid, use the sunsetting version.)
                "let": ["var-name": "expressioon-value", "var-name": "expressioon-value"], (as defined by the let statements for this context.)
                "props": ["name": {"value": "string", "namespace": "string"}, {}],
                "remarks": "string"
                }
```

## Data Structure

```json
document = {"model" : "name",
            "tree" :  {
                "path" : "",
                "data" : [oscal_data_type | ]
            }
}

```
- `path` links back to metaschema_tree
  - Used to identify:
    - field, flag or assembly
    - data type (if field or flag)
    - array (JSON name if appropriate)
    - cardinality
    - rules/constraints
  - Ordinal values are unnecessary
    - Path is only used to tie into metaschema info
