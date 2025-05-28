# Metaschema Parsing

## Metaschema Tree
The metaschema tree is a recursive dictionary representing a fully resolved metaschema definition.  
Each assembly, flag and field is represented by a metaschema node. The node structure is identical with some fields unused in certain scenarios.

The hierarchy of nodes is built with the top metaschema node representing the OSCAL model's root element. 
Each flag is represented by its own metaschema node and stored in the `flags` array. 
Each child field or assembly is represented by its own metaschema node and stored in the `children` array. 
The pattern repeats as needed until the entire model is represented.

```
assembly (root level metaschema node)
|
+- flags: (array of metaschema nodes. One for each flag.)
|  |
|  + flag (metaschema node)
|  + flag (metaschema node)
|
+- children: (array of metaschema nodes epresenting fields and assemblies)
   |
   + assembly [metaschema node - repeat assembly pattern from top]
   | 
   +- field (metaschema node)
      |
      +- flags
         |
         + flag
         + flag

```


`flags` and `children` 

| Name                  | Type     | Values / Example Values                                  | Default      | Description |
|-----------------------|----------|----------------------------------------------------------|--------------|-------------|
| path                  | string   | Example: "/model_name/x/y/z"                             |              |             |
| use-name              | string   |                                                          |              |             |
| name                  | string   |                                                          |              |             |
| structure-type        | string   | "assembly", "field", "flag"                              |              |             |
| datatype              | string   |                                                          |              |             |
| min-occurs            | string   | "0", "1"                                                 |              |             |
| max-occurs            | string   | "1", "unbounded"                                         |              |             |

| default               | variant  |                                                          |              |             |
| formal-name           | string   |                                                          |              |             |

| wrapped-in-xml        | string   | "WRAPPED", "UNWRAPPED", "WITH_WRAPPER"                   |              |             |
| group-as              | string   |                                                          |              |             |
| group-as-in-json      | string   | "ARRAY", "SINGLETON_OR_ARRAY", "BY_KEY"                  |              |             |
| group-as-in-xml       | string   | "GROUPED", "UNGROUPED"                                   |              |             |
| json-array-name       | string   | "json_key"                                               |              |             |
| json-value-key        | string   |                                                          |              |             |
| json-value-key-flag   | string   |                                                          |              |             |
| json-collapsaible     | boolean  | True, False                                              |              |             |
| depreciated           | boolean  | True                                                     |              |             |
| sunsetting            | string   | version                                                  |              |             |
| sequence              | integer  |                                                          |              |             |
| source                | array    | [string, ...]                                            |              |             |
| props                 | array    | [{"name": {"value": "string", "namespace": "uri"}} ]     |              |             |

| description           | array    | [string, ...]                                            |              |             |
| remarks               | array    | [string, ...]                                            |              |             |
| example               | array    | [string, ...]                                            |              |             |

| flags                 | array    | [dict, ...]                                              |              |             |
| children              | array    | [dict, ...]                                              |              |             |
| rules                 | array    | ["rule_id", ...] or [dict, ...]                          |              |             |

```json
metaschema = "model-name" : [{
            "sequence": integer, # identifies the order in which the JSON structure was created from the metadata
            "name": defined_name (identifier),     @name
            "use-name" : [string] element_name,
            "datatype": [string],   @as-type or via constraint
            "path": [string: path syntax], # Example: "/model_name/x/y/z",
            "min-occurs": [string: "0" | "1" ],
            "max-occurs": [string: "1" | "unbounded" ],
            "structure-type": [ string: "assembly" | "field" | "flag":],
            "default": variant ,

            "formal-name": [ string ],
            "description": [ string ],
            "remarks": [ string ],
            "example": [ string ],

            "in-xml" : [string: "WRAPPED" | "UNWRAPPED" | "WITH_WRAPPER" ],
            "group-as" : string,
            "group-as-in-json" : ["ARRAY" | "SINGLETON_OR_ARRAY" | "BY_KEY"],
            "group-as-in-xml" : ["GROUPED", "UNGROUPED"],
            "json-array-name": "json_key",
            "json-value-key": "string",
            "json-value-key-flag": "string",
            "json-collapsaible" : [ True | False],
            "depreciated": True, (If metaschema @depreciated is present and this verison is >= the depreciated version, this is set to True.)
            "sunsetting": "version", (If metaschema @depreciated is present, but this versiion is still valid, use the sunsetting version.)

            "source": [], # array of strings representing source metaschema file
            "flags": [ { repeat_this_dict }, {} ], (if required: min-occurs=1, max-occurs=1, if not-required: min-occurs=0, max-occurs=1)
            "children": [ { repeat this dict }, {} ],
            "allowed_values": [ {"value": "value2", "text": "string"}, {} ],
            "rules": ["rule_id", "rule_id", "rule_id"],  (if the rule context matches this path location)
            "props": ["name": {"value": "string", "namespace": "string"}, {}],
            "rules": [ {rule-object-see-below} ],
            "rule-references": ["rule_id", "rule_id", "rule_id"], (for rules that apply in more than one place)
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
                "default" : "string, # a default value for the flag or field
                "pattern": "string", (regex pattern)
                "allowed-values": [ {"value": "value2", "text": "string"}, {} ],
                "allow-others": [ True | False ],
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
