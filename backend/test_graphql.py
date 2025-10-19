#!/usr/bin/env python3
"""Test GraphQL queries to verify schema"""
import requests
import json

GRAPHQL_ENDPOINT = "http://localhost:8000/graphql"

# Test get_all_knowledge query
query_knowledge = """
{
  get_all_knowledge {
    id
    section
    content
    tags
    priority
  }
}
"""

print("Testing get_all_knowledge query...")
response = requests.post(
    GRAPHQL_ENDPOINT,
    json={"query": query_knowledge},
    headers={"Content-Type": "application/json"}
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
