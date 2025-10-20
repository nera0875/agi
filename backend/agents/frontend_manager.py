"""
FrontendManagerAgent - Autonomous frontend development agent

Manages frontend development according to design guidelines:
- Generate React components (shadcn/ui compliant)
- Modify existing components
- Integrate backend API routes
- Validate design consistency
- Auto-fix styling issues

Rules enforced:
- Preserve all Tailwind classes (no modification)
- Use shadcn/ui components exclusively
- Typography via globals.css (no inline font classes)
- lucide-react for icons
- motion/react for animations
- Responsive design always
- No placeholder comments
"""

import os
import json
import re
import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from datetime import datetime

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class ComponentSpec:
    """Component specification for generation"""
    name: str
    purpose: str
    props: Dict[str, Any]
    path: Optional[str] = None
    api_endpoint: Optional[str] = None
    ui_components: List[str] = None

    def __post_init__(self):
        if self.ui_components is None:
            self.ui_components = []


@dataclass
class ValidationResult:
    """Result of design validation"""
    is_valid: bool
    violations: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]


class FrontendManagerAgent:
    """Autonomous agent for frontend development management"""

    # Design rules embedded
    FIGMA_RULES = {
        "component_library": "shadcn/ui",
        "css_framework": "tailwind-v4.0",
        "icon_library": "lucide-react",
        "animation_library": "motion/react",
        "typography_source": "globals.css",
        "strict_rules": [
            "Preserve all Tailwind classes - never modify or rename",
            "Use shadcn/ui components exclusively - no custom components",
            "Typography defined in globals.css only - no inline font classes",
            "Icons from lucide-react package - no custom icons",
            "Animations via motion/react - no raw CSS animations",
            "Responsive design mandatory - mobile-first approach",
            "No placeholder comments - production-ready code only",
            "Props validation required - TypeScript types",
            "Accessibility compliance - WCAG 2.1 AA minimum",
            "Performance optimization - React.memo for expensive components"
        ],
        "tailwind_utilities": [
            "spacing (p-, m-, gap-)",
            "sizing (w-, h-)",
            "colors (text-, bg-, border-)",
            "typography (text-sm, text-base, font-bold)",
            "layout (flex, grid, absolute)",
            "responsive (sm:, md:, lg:, xl:)",
            "hover/focus states (hover:, focus:)",
            "dark mode (dark:)"
        ],
        "forbidden_patterns": [
            r"style=\{.*\}",  # Inline styles
            r"<style>",  # Style tags
            r"className=\"[^\"]*font-",  # Inline font classes
            r"<Component\s*/>",  # Custom components
            r"TODO|FIXME|XXX|HACK",  # Placeholder comments
            r"<div[^>]*class=\"\">",  # Empty classes
        ]
    }

    def __init__(self):
        """Initialize FrontendManagerAgent"""
        self.llm_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.llm_model = "claude-3-5-sonnet-20241022"
        self.llm_base_url = "https://api.anthropic.com/v1"
        self.frontend_path = Path("/home/pilote/projet/agi/frontend")
        self.guidelines_path = self.frontend_path / "src" / "guidelines"
        self.components_path = self.frontend_path / "app" / "components"
        self.http_client = httpx.AsyncClient(timeout=60.0)
        self.base_path = "/home/pilote/projet/agi/backend/agents"

        # Ensure directories exist
        self.guidelines_path.mkdir(parents=True, exist_ok=True)
        self.components_path.mkdir(parents=True, exist_ok=True)

        self.logger_events: List[Dict[str, Any]] = []

    async def initialize(self):
        """Initialize agent and verify setup"""
        init_result = {
            "status": "initialized",
            "timestamp": datetime.now().isoformat(),
            "api_key_present": bool(self.llm_api_key),
            "frontend_path": str(self.frontend_path),
            "figma_rules_count": len(self.FIGMA_RULES["strict_rules"])
        }
        self._log_event("agent_init", init_result)
        return init_result

    def _load_specialist_prompt(self, specialist: str) -> str:
        """Load specialist prompt from prompts/ directory"""
        path = f"{self.base_path}/prompts/{specialist}.md"
        if os.path.exists(path):
            with open(path, 'r') as f:
                return f.read()
        return ""

    def _log_event(self, event_type: str, data: Any):
        """Log internal events"""
        self.logger_events.append({
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data if isinstance(data, dict) else str(data)
        })

    async def generate_database_ui(self, table_name: str) -> str:
        """Generate professional database UI using specialist prompt"""
        specialist_prompt = self._load_specialist_prompt("database_ui_specialist")

        prompt = f"""{specialist_prompt}

TASK: Create complete Database UI for table: {table_name}

Generate all 9 components listed in the specialist prompt.
Follow TanStack Table best practices.
Implement all features: sort, filter, pagination, inline edit, insert.
Use GraphQL queries for data fetching.

OUTPUT: Complete React components ready to use.
"""

        result = await self._call_llm(self._build_system_prompt(), prompt)
        return result.content if hasattr(result, 'content') else result

    async def generate_component(self, spec: ComponentSpec) -> Dict[str, Any]:
        """
        Generate React component following figma.md rules

        Args:
            spec: ComponentSpec with name, purpose, props

        Returns:
            Dict with generated_code, path, validation_result
        """
        try:
            # Build system prompt with strict rules
            system_prompt = self._build_system_prompt()

            # Build user prompt
            user_prompt = self._build_generation_prompt(spec)

            # Call LLM
            component_code = await self._call_llm(system_prompt, user_prompt)

            # Validate generated code
            validation = await self.validate_design(component_code, is_file=False)

            # If validation fails, attempt fix
            if not validation.is_valid:
                component_code = await self._fix_violations(component_code, validation.violations)
                validation = await self.validate_design(component_code, is_file=False)

            # Write to file
            output_path = self._resolve_component_path(spec)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(component_code)

            self._log_event("component_generated", {
                "name": spec.name,
                "path": str(output_path),
                "valid": validation.is_valid,
                "violations": validation.violations
            })

            return {
                "success": True,
                "component_name": spec.name,
                "path": str(output_path),
                "code_lines": len(component_code.split('\n')),
                "validation": asdict(validation),
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "component_name": spec.name,
                "timestamp": datetime.now().isoformat()
            }
            self._log_event("generation_error", error_result)
            return error_result

    async def integrate_api_route(self,
                                 component_path: str,
                                 api_route: str,
                                 method: str = "GET") -> Dict[str, Any]:
        """
        Integrate backend API route into component

        Args:
            component_path: Path to component file
            api_route: Backend API endpoint (e.g., /api/data)
            method: HTTP method (GET, POST, etc.)

        Returns:
            Dict with integration_result
        """
        try:
            component_file = Path(component_path)

            if not component_file.exists():
                return {
                    "success": False,
                    "error": f"Component file not found: {component_path}"
                }

            component_code = component_file.read_text()

            # Build integration prompt
            integration_prompt = f"""
You are integrating a backend API route into an existing React component.

RULES:
- Preserve all existing Tailwind classes
- Use proper React hooks (useState, useEffect, useCallback)
- Add proper error handling and loading states
- Add TypeScript types for API response
- Use fetch API with proper headers
- Add abort controller for cleanup
{self.FIGMA_RULES['strict_rules'][0]}

Component file: {component_path}
API endpoint: {api_route}
HTTP method: {method}

Current component:
```tsx
{component_code}
```

Generate updated component with API integration:
1. Add useState for data, loading, error
2. Add useEffect with fetch
3. Add loading and error UI states
4. Maintain all existing styling
5. Return complete .tsx file
"""

            integrated_code = await self._call_llm(
                self._build_system_prompt(),
                integration_prompt
            )

            # Validate integration
            validation = await self.validate_design(integrated_code, is_file=False)

            if not validation.is_valid:
                integrated_code = await self._fix_violations(integrated_code, validation.violations)

            # Write updated component
            component_file.write_text(integrated_code)

            self._log_event("api_integration", {
                "component": component_path,
                "api_route": api_route,
                "method": method,
                "success": True
            })

            return {
                "success": True,
                "component": component_path,
                "api_route": api_route,
                "integration_complete": True,
                "validation": asdict(validation),
                "updated_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "component": component_path,
                "timestamp": datetime.now().isoformat()
            }

    async def validate_design(self,
                             file_path_or_code: str,
                             is_file: bool = True) -> ValidationResult:
        """
        Validate component against design rules

        Args:
            file_path_or_code: Path to file or code string
            is_file: Whether input is file path or code

        Returns:
            ValidationResult with violations and warnings
        """
        try:
            if is_file:
                code = Path(file_path_or_code).read_text()
            else:
                code = file_path_or_code

            violations = []
            warnings = []

            # Check forbidden patterns
            for pattern in self.FIGMA_RULES["forbidden_patterns"]:
                if re.search(pattern, code):
                    violations.append(f"Forbidden pattern detected: {pattern}")

            # Check required imports
            required_imports = {
                "react": "React",
                "shadcn/ui": "shadcn component",
                "lucide-react": "lucide icon"
            }

            if "import React" not in code and "React" in code:
                warnings.append("Missing React import")

            if "from '@/components/ui" in code or "from 'shadcn" in code:
                pass  # Has shadcn imports
            else:
                warnings.append("No shadcn/ui components detected")

            # Check Tailwind class structure
            if not re.search(r'className="[^"]*[a-z]+-', code):
                warnings.append("No Tailwind utilities detected")

            # Check for inline styles
            if "style=" in code:
                violations.append("Inline styles detected - use Tailwind only")

            # Check for custom CSS
            if "<style" in code or "css`" in code:
                violations.append("Custom CSS detected - use Tailwind only")

            # Check TypeScript types (if TypeScript)
            if code.strip().startswith("import") or ".tsx" in code:
                if "interface" not in code and "type" not in code and "Props" not in code:
                    warnings.append("No TypeScript props interface detected")

            # Check for accessibility
            if "<button" in code and 'aria-' not in code:
                warnings.append("Button missing ARIA attributes")

            if "<img" in code and 'alt=' not in code:
                violations.append("Image missing alt text")

            is_valid = len(violations) == 0

            return ValidationResult(
                is_valid=is_valid,
                violations=violations,
                warnings=warnings,
                metadata={
                    "code_length": len(code),
                    "lines": len(code.split('\n')),
                    "has_jsx": "return" in code or "JSX" in code,
                    "has_typescript": ".tsx" in code or "interface" in code
                }
            )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                violations=[str(e)],
                warnings=[],
                metadata={"error": str(e)}
            )

    async def _fix_violations(self,
                             code: str,
                             violations: List[str]) -> str:
        """
        Auto-fix styling violations

        Args:
            code: Component code with violations
            violations: List of violations to fix

        Returns:
            Fixed component code
        """
        try:
            fix_prompt = f"""
You are fixing styling violations in a React component while preserving all functionality.

VIOLATIONS TO FIX:
{chr(10).join(f'- {v}' for v in violations)}

RULES:
- Remove inline styles
- Remove custom CSS
- Use Tailwind utilities only
- Preserve all component logic
- Maintain all Tailwind classes
- Keep all props and callbacks

Component:
```tsx
{code}
```

Return fixed component - complete .tsx file with ALL violations resolved.
"""

            fixed_code = await self._call_llm(
                self._build_system_prompt(),
                fix_prompt
            )

            self._log_event("violations_fixed", {
                "violations_count": len(violations),
                "fixed_code_length": len(fixed_code)
            })

            return fixed_code

        except Exception as e:
            self._log_event("fix_error", {"error": str(e)})
            return code  # Return original if fix fails

    async def _call_llm(self, system: str, user: str) -> str:
        """
        Call Claude LLM API

        Args:
            system: System prompt
            user: User prompt

        Returns:
            Generated text from LLM
        """
        try:
            headers = {
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
                "x-api-key": self.llm_api_key
            }

            payload = {
                "model": self.llm_model,
                "max_tokens": 4096,
                "system": system,
                "messages": [
                    {
                        "role": "user",
                        "content": user
                    }
                ]
            }

            response = await self.http_client.post(
                f"{self.llm_base_url}/messages",
                json=payload,
                headers=headers
            )

            response.raise_for_status()
            result = response.json()

            if "content" in result and len(result["content"]) > 0:
                return result["content"][0]["text"]
            else:
                raise ValueError(f"Unexpected LLM response: {result}")

        except Exception as e:
            self._log_event("llm_error", {"error": str(e)})
            raise

    def _build_system_prompt(self) -> str:
        """Build system prompt with design rules"""
        rules_text = "\n".join(
            f"- {rule}" for rule in self.FIGMA_RULES["strict_rules"]
        )

        return f"""You are a frontend development expert specializing in React and Tailwind CSS.

Your PRIMARY RESPONSIBILITIES:
1. Generate production-ready React components
2. Enforce design system consistency
3. Ensure accessibility compliance
4. Optimize performance

CRITICAL DESIGN RULES (MUST FOLLOW):
{rules_text}

COMPONENT LIBRARIES:
- UI Framework: {self.FIGMA_RULES['component_library']}
- CSS: {self.FIGMA_RULES['css_framework']}
- Icons: {self.FIGMA_RULES['icon_library']}
- Animations: {self.FIGMA_RULES['animation_library']}

TAILWIND UTILITIES YOU CAN USE:
{chr(10).join(f"- {util}" for util in self.FIGMA_RULES['tailwind_utilities'])}

FORBIDDEN:
- Inline styles (style={{}})
- Custom CSS or <style> tags
- Placeholder comments (TODO, FIXME, XXX)
- Non-shadcn/ui components
- Font classes in className (use globals.css)

OUTPUT:
- Complete, production-ready code
- Full TypeScript types
- Proper error handling
- No placeholders or comments marked with TODO
- All components fully functional
"""

    def _build_generation_prompt(self, spec: ComponentSpec) -> str:
        """Build component generation prompt"""
        props_desc = json.dumps(spec.props, indent=2)

        api_section = ""
        if spec.api_endpoint:
            api_section = f"\nAPI Integration: {spec.api_endpoint}"

        ui_section = ""
        if spec.ui_components:
            ui_section = f"\nRequired shadcn/ui components: {', '.join(spec.ui_components)}"

        return f"""Generate a React component with these specifications:

Component Name: {spec.name}
Purpose: {spec.purpose}

Props Structure:
{props_desc}
{api_section}
{ui_section}

Requirements:
1. Generate complete .tsx file (with TypeScript types)
2. Use shadcn/ui components exclusively
3. Use Tailwind v4.0 for all styling
4. Include proper error boundaries if needed
5. Add loading states for async operations
6. Make responsive (mobile-first)
7. Include proper TypeScript interfaces for props
8. No placeholder comments
9. Export default component

Return the complete component file content ready for production.
"""

    def _resolve_component_path(self, spec: ComponentSpec) -> Path:
        """Resolve output path for component"""
        if spec.path:
            return Path(spec.path)

        # Convert component name to kebab-case filename
        filename = re.sub(r'(?<!^)(?=[A-Z])', '-', spec.name).lower()
        return self.components_path / f"{filename}.tsx"

    async def cleanup(self):
        """Cleanup resources"""
        await self.http_client.aclose()
        self._log_event("cleanup", {"events_logged": len(self.logger_events)})

    def get_logs(self) -> List[Dict[str, Any]]:
        """Get agent event logs"""
        return self.logger_events.copy()


# Event-driven handlers

async def on_backend_route_created(route_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Triggered when new backend route created

    Args:
        route_spec: Dict with name, purpose, path, props

    Returns:
        Generation result
    """
    agent = FrontendManagerAgent()
    await agent.initialize()

    try:
        spec = ComponentSpec(
            name=f"{route_spec.get('name', 'Page')}",
            purpose=f"Display {route_spec.get('purpose', 'content')}",
            props=route_spec.get('props', {}),
            path=route_spec.get('path'),
            api_endpoint=route_spec.get('api_endpoint'),
            ui_components=route_spec.get('ui_components', [])
        )

        result = await agent.generate_component(spec)

        # If API endpoint provided, integrate it
        if route_spec.get('api_endpoint') and result.get('success'):
            api_result = await agent.integrate_api_route(
                result['path'],
                route_spec['api_endpoint'],
                route_spec.get('method', 'GET')
            )
            result['api_integration'] = api_result

        result['logs'] = agent.get_logs()
        await agent.cleanup()

        return result

    except Exception as e:
        await agent.cleanup()
        return {
            "success": False,
            "error": str(e),
            "logs": agent.get_logs(),
            "timestamp": datetime.now().isoformat()
        }


async def on_component_validate(component_path: str) -> Dict[str, Any]:
    """
    Validate existing component against design rules

    Args:
        component_path: Path to component file

    Returns:
        Validation result with violations
    """
    agent = FrontendManagerAgent()
    await agent.initialize()

    try:
        validation = await agent.validate_design(component_path, is_file=True)

        result = {
            "success": True,
            "component": component_path,
            "is_valid": validation.is_valid,
            "violations": validation.violations,
            "warnings": validation.warnings,
            "metadata": validation.metadata,
            "timestamp": datetime.now().isoformat()
        }

        # Auto-fix if violations found
        if validation.violations:
            code = Path(component_path).read_text()
            fixed_code = await agent._fix_violations(code, validation.violations)
            Path(component_path).write_text(fixed_code)

            # Re-validate
            fixed_validation = await agent.validate_design(component_path, is_file=True)
            result['auto_fixed'] = True
            result['after_fix'] = {
                "is_valid": fixed_validation.is_valid,
                "violations": fixed_validation.violations
            }

        result['logs'] = agent.get_logs()
        await agent.cleanup()

        return result

    except Exception as e:
        await agent.cleanup()
        return {
            "success": False,
            "error": str(e),
            "component": component_path,
            "logs": agent.get_logs(),
            "timestamp": datetime.now().isoformat()
        }


# Test/Demo functions

async def demo_component_generation():
    """Demo: Generate sample component"""
    agent = FrontendManagerAgent()
    await agent.initialize()

    spec = ComponentSpec(
        name="DashboardPanel",
        purpose="Display system metrics",
        props={
            "title": "string",
            "metrics": "MetricItem[]",
            "onRefresh": "() => Promise<void>"
        },
        ui_components=["Card", "Button", "Badge"],
        api_endpoint="/api/metrics"
    )

    result = await agent.generate_component(spec)
    await agent.cleanup()

    return result


async def demo_validation():
    """Demo: Validate component"""
    agent = FrontendManagerAgent()
    await agent.initialize()

    # Test code with violations
    test_code = """
export default function TestComponent() {
  return (
    <div style={{color: 'red'}}>
      <button>Click me</button>
      TODO: Add functionality
    </div>
  )
}
"""

    result = await agent.validate_design(test_code, is_file=False)
    await agent.cleanup()

    return {
        "is_valid": result.is_valid,
        "violations": result.violations,
        "warnings": result.warnings
    }


if __name__ == "__main__":
    # Run demo
    print("FrontendManagerAgent - Demo Mode")
    print("=" * 50)

    # Test validation
    print("\nTesting validation...")
    validation_result = asyncio.run(demo_validation())
    print(json.dumps(validation_result, indent=2))

    print("\nAgent ready for integration")
