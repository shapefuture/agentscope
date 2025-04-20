# Function Outline

## src/agentscope/serialize.py

- **_default_serialize(obj: Any) -> Any**  
  Serialize the object when `json.dumps` cannot handle it. Special-cases `Msg` objects in `agentscope.message.msg` by converting to dict, otherwise returns the object as-is.

- **_deserialize_hook(data: dict) -> Any**  
  Used as a hook in `json.loads` to reconstruct Python objects (notably Msg objects) from dicts with `__module__` and `__name__` attributes by dynamically importing the class and calling `from_dict` if available.

- **serialize(obj: Any) -> str**  
  Serializes an object (currently focusing on `Msg` objects) to a JSON string using the default fallback `_default_serialize`.

- **deserialize(s: str) -> Any**  
  Deserializes a JSON string back to an object, supporting special Msg-object handling with `_deserialize_hook`.

- **is_serializable(obj: Any) -> bool**  
  Checks if the object is serializable by attempting to serialize it with `serialize`. Returns `True` if successful, `False` otherwise.