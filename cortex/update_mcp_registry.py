#!/usr/bin/env python3
"""
Script helper pour mettre à jour dynamiquement le registry MCP

Usage:
  python3 update_mcp_registry.py "@openai/mcp" --creds '{"OPENAI_API_KEY": "sk-xxx"}' --category ai
  python3 update_mcp_registry.py "https://api.example.com/mcp" --registry /path/to/registry.json
  python3 update_mcp_registry.py --add-batch mcps.json
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
from mcp_detector import detect_and_config


def load_registry(registry_path: str) -> Dict[str, Any]:
    """Charger le registry JSON"""
    with open(registry_path, "r") as f:
        return json.load(f)


def save_registry(registry_path: str, registry: Dict[str, Any]) -> None:
    """Sauvegarder le registry JSON"""
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)
    print(f"Registry saved to {registry_path}")


def add_mcp_to_registry(
    registry_path: str,
    mcp_input: str,
    credentials: Optional[Dict[str, str]] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    tools: Optional[list] = None,
    category: Optional[str] = None,
    force: bool = False,
) -> bool:
    """Ajouter un MCP au registry"""

    # Charger registry
    registry = load_registry(registry_path)

    # Générer config
    config = detect_and_config(
        mcp_input,
        credentials=credentials,
        name=name,
        description=description,
        tools=tools,
        category=category,
    )

    # Récupérer le nom du provider
    provider_name = list(config.keys())[0]

    # Vérifier si le provider existe déjà
    if provider_name in registry and not force:
        print(f"Error: '{provider_name}' already exists in registry")
        print("Use --force to overwrite")
        return False

    # Ajouter au registry
    registry.update(config)

    # Sauvegarder
    save_registry(registry_path, registry)

    print(f"Added '{provider_name}' to registry")
    print(f"Config: {json.dumps(config, indent=2)}")

    return True


def remove_mcp_from_registry(registry_path: str, provider_name: str) -> bool:
    """Retirer un MCP du registry"""

    registry = load_registry(registry_path)

    if provider_name not in registry:
        print(f"Error: '{provider_name}' not found in registry")
        return False

    del registry[provider_name]
    save_registry(registry_path, registry)

    print(f"Removed '{provider_name}' from registry")
    return True


def list_mcps(registry_path: str, category: Optional[str] = None) -> None:
    """Lister les MCPs du registry"""

    registry = load_registry(registry_path)

    print(f"\nMCPs in registry ({registry_path}):\n")

    for provider_name, config in sorted(registry.items()):
        cat = config.get("category", "unknown")

        if category and cat != category:
            continue

        desc = config.get("description", "No description")
        command = config.get("command", "unknown")

        print(f"  {provider_name:<20} | {cat:<15} | {command:<20} | {desc}")

    print()


def batch_add_mcps(batch_file: str, registry_path: str, force: bool = False) -> int:
    """Ajouter plusieurs MCPs à partir d'un fichier"""

    with open(batch_file, "r") as f:
        batch_data = json.load(f)

    if not isinstance(batch_data, list):
        print("Error: Batch file must contain a JSON array")
        return 1

    added = 0
    for entry in batch_data:
        if not isinstance(entry, dict):
            print(f"Warning: Skipping invalid entry: {entry}")
            continue

        mcp_input = entry.get("input")
        if not mcp_input:
            print("Warning: Entry missing 'input' field")
            continue

        result = add_mcp_to_registry(
            registry_path,
            mcp_input,
            credentials=entry.get("credentials"),
            name=entry.get("name"),
            description=entry.get("description"),
            tools=entry.get("tools"),
            category=entry.get("category"),
            force=force,
        )

        if result:
            added += 1

    print(f"\nAdded {added} MCPs from {batch_file}")
    return 0


def validate_registry(registry_path: str) -> bool:
    """Valider l'intégrité du registry"""

    try:
        registry = load_registry(registry_path)

        errors = []

        for provider_name, config in registry.items():
            if not isinstance(config, dict):
                errors.append(f"  - {provider_name}: config is not a dict")

            required_fields = ["command", "args", "transport"]
            for field in required_fields:
                if field not in config:
                    errors.append(f"  - {provider_name}: missing '{field}'")

        if errors:
            print("Validation errors:")
            for error in errors:
                print(error)
            return False

        print(f"Registry is valid ({len(registry)} MCPs)")
        return True

    except Exception as e:
        print(f"Error validating registry: {e}")
        return False


def export_registry(registry_path: str, output_format: str = "json") -> None:
    """Exporter le registry dans différents formats"""

    registry = load_registry(registry_path)

    if output_format == "json":
        print(json.dumps(registry, indent=2))

    elif output_format == "csv":
        print("name,command,transport,category,description")
        for name, config in sorted(registry.items()):
            cat = config.get("category", "")
            desc = config.get("description", "").replace(",", ";")
            cmd = config.get("command", "")
            transport = config.get("transport", "")
            print(f"{name},{cmd},{transport},{cat},{desc}")

    elif output_format == "table":
        print(f"\n{'Name':<20} {'Command':<15} {'Transport':<10} {'Category':<15}")
        print("-" * 60)
        for name, config in sorted(registry.items()):
            cmd = config.get("command", "")[:15]
            transport = config.get("transport", "")
            cat = config.get("category", "")
            print(f"{name:<20} {cmd:<15} {transport:<10} {cat:<15}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Update MCP registry dynamically",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add single MCP
  %(prog)s "@openai/mcp" --creds '{"OPENAI_API_KEY": "sk-xxx"}' --category ai

  # Add from batch file
  %(prog)s --add-batch mcps.json

  # List all MCPs
  %(prog)s --list

  # List by category
  %(prog)s --list --category ai

  # Remove MCP
  %(prog)s --remove openai

  # Validate registry
  %(prog)s --validate

  # Export to CSV
  %(prog)s --export csv
        """,
    )

    # Registry path
    parser.add_argument(
        "--registry",
        default="/home/pilote/projet/agi/cortex/mcp-registry.json",
        help="Path to MCP registry (default: /home/pilote/projet/agi/cortex/mcp-registry.json)",
    )

    # Actions
    action_group = parser.add_mutually_exclusive_group(required=True)

    action_group.add_argument(
        "mcp_input",
        nargs="?",
        help="MCP input (@package, URL, or path)",
    )

    action_group.add_argument(
        "--list",
        action="store_true",
        help="List all MCPs in registry",
    )

    action_group.add_argument(
        "--remove",
        metavar="PROVIDER",
        help="Remove MCP from registry",
    )

    action_group.add_argument(
        "--add-batch",
        metavar="FILE",
        help="Add multiple MCPs from batch JSON file",
    )

    action_group.add_argument(
        "--validate",
        action="store_true",
        help="Validate registry integrity",
    )

    action_group.add_argument(
        "--export",
        metavar="FORMAT",
        choices=["json", "csv", "table"],
        help="Export registry in format",
    )

    # Add options
    parser.add_argument(
        "--creds",
        type=json.loads,
        help="Credentials as JSON",
    )

    parser.add_argument(
        "--name",
        help="Custom provider name",
    )

    parser.add_argument(
        "--description",
        help="MCP description",
    )

    parser.add_argument(
        "--tools",
        type=json.loads,
        help="Tools list as JSON",
    )

    parser.add_argument(
        "--category",
        help="MCP category",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite if exists",
    )

    args = parser.parse_args()

    # Exécuter les actions
    if args.list:
        list_mcps(args.registry, category=args.category)

    elif args.remove:
        remove_mcp_from_registry(args.registry, args.remove)

    elif args.add_batch:
        sys.exit(batch_add_mcps(args.add_batch, args.registry, force=args.force))

    elif args.validate:
        sys.exit(0 if validate_registry(args.registry) else 1)

    elif args.export:
        export_registry(args.registry, output_format=args.export)

    elif args.mcp_input:
        success = add_mcp_to_registry(
            args.registry,
            args.mcp_input,
            credentials=args.creds,
            name=args.name,
            description=args.description,
            tools=args.tools,
            category=args.category,
            force=args.force,
        )
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
