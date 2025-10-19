#!/usr/bin/env python3
"""Test GraphQL schema introspection"""
import asyncio
import sys
sys.path.insert(0, '/home/pilote/projet/agi/backend')

from api.schema import Query
import strawberry

# Check if get_all_knowledge exists
query_obj = Query()
print("Query class methods:")
for attr in dir(query_obj):
    if not attr.startswith('_'):
        print(f"  - {attr}")

print("\nChecking if get_all_knowledge exists:")
print(f"  hasattr: {hasattr(query_obj, 'get_all_knowledge')}")

# Try to create schema
try:
    schema = strawberry.Schema(query=Query)
    print("\n✓ Schema created successfully")

    # Introspect query fields
    print("\nQuery fields in schema:")
    for field_name in schema.query_type.__strawberry_definition__.fields:
        print(f"  - {field_name}")

except Exception as e:
    print(f"\n✗ Schema creation failed: {e}")
    import traceback
    traceback.print_exc()
