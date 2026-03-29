import json
from src.config import METADATA_FILE
from .CRUD_operations import create_operation, read_operation, update_operation, delete_operation

def query_parser(query_dict: dict) -> dict:
    """Parse a query dictionary and interpret its meaning."""
    if not query_dict:
        print("There is no query to execute")
        return None
        
    # Extract basic fields from query
    operation = query_dict.get("operation")  # READ, UPDATE, DELETE
    entity = query_dict.get("entity")        # main_records, etc.
    filters = query_dict.get("filters")      # WHERE clause conditions
    payload = query_dict.get("payload")      # Data to update (if UPDATE/CREATE)
    
    print(f"\n--- PARSED QUERY ---")
    print(f"Operation: {operation}")
    print(f"Entity: {entity}")
    print(f"Filters: {filters}")
    if payload:
        print(f"Payload: {payload}")
    
    return {
        "operation": operation,
        "entity": entity,
        "filters": filters,
        "payload": payload
    }

def get_field_locations() -> dict:
    """Read metadata.json and create a map of field -> database location."""
    try:
        with open(METADATA_FILE, 'r') as f:
            metadata = json.load(f)
        
        field_map = {}
        for field in metadata.get("fields", []):
            field_name = field.get("field_name")
            decision = field.get("decision")
            field_map[field_name] = decision
        return field_map
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading metadata: {e}")
        return {}

def analyze_query_databases(parsed_query: dict) -> dict:
    """
    Analyze which databases we need based on operation type and fields.
    """
    operation = parsed_query.get("operation")
    field_map = get_field_locations()
    
    fields_to_analyze = {}
    field_source_type = {}
    
    if operation == "CREATE":
        payload = parsed_query.get("payload", {})
        fields_to_analyze = payload
        field_source_type = {k: "payload" for k in payload.keys()}
        print(f"\n[ANALYZE] Operation: {operation}")
        print(f"[ANALYZE] Analyzing PAYLOAD fields ({len(payload)} fields)")
        
    elif operation == "UPDATE":
        filters = parsed_query.get("filters", {})
        payload = parsed_query.get("payload", {})
        fields_to_analyze = {**filters, **payload}
        field_source_type = {k: "filter" for k in filters.keys()}
        field_source_type.update({k: "payload" for k in payload.keys()})
        print(f"\n[ANALYZE] Operation: {operation}")
        print(f"[ANALYZE] Analyzing FILTER + PAYLOAD fields")
        
    else:  # READ or DELETE
        filters = parsed_query.get("filters", {})
        fields_to_analyze = filters
        field_source_type = {k: "filter" for k in filters.keys()}
        print(f"\n[ANALYZE] Operation: {operation}")
        print(f"[ANALYZE] Analyzing FILTER fields ({len(filters)} fields)")
    
    if not fields_to_analyze:
        print(f"No fields specified - querying all databases for safety")
        return {
            "field_locations": {},
            "databases_needed": ["SQL", "MONGO", "Unknown"]
        }
    
    field_locations = {}
    for field_name in fields_to_analyze.keys():
        location = field_map.get(field_name, "Unknown")
        field_locations[field_name] = location
    
    databases_needed = list(set(field_locations.values()))
    
    print(f"\n--- FIELD LOCATIONS ---")
    for field, location in field_locations.items():
        source = field_source_type.get(field, "unknown")
        print(f"{field} ({source}): {location}")
    print(f"Databases: {', '.join(databases_needed)}")
    
    return {
        "field_locations": field_locations,
        "databases_needed": databases_needed
    }
    
def query_runner(query_dict: dict) -> dict:
    """
    Execute a CRUD query passed explicitly as a dictionary.
    No file I/O operations are performed here anymore.
    """
    parsed_query = query_parser(query_dict)
    
    if parsed_query:
        db_analysis = analyze_query_databases(parsed_query)
        print(f"\nAnalysis Result: {db_analysis}")
        
        operation = parsed_query.get("operation")
        result = None
        
        if operation == "CREATE":
            result = create_operation(parsed_query, db_analysis)
        elif operation == "READ":
            result = read_operation(parsed_query, db_analysis)
        elif operation == "UPDATE":
            result = update_operation(parsed_query, db_analysis)
        elif operation == "DELETE":
            result = delete_operation(parsed_query, db_analysis)
        
        if result:
            print(f"\n{'='*60}")
            print("[FINAL RESULT]")
            print(f"{'='*60}")
            print(json.dumps(result, indent=2, default=str))
            print(f"{'='*60}\n")
            
        return result
    return None