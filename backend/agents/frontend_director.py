import os
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from backend.agents.base_agent import BaseAgent

# Load .env file
load_dotenv('/home/pilote/projet/agi/.env')

class FrontendDirectorAgent(BaseAgent):
    """
    🎨 FRONTEND DIRECTOR AGENT

    AUTORITÉ: Seul agent autorisé à modifier le frontend
    MODÈLE: Claude Haiku 4.5 (rapide, économique)
    MISSION: Diriger toute la partie frontend selon guidelines
    """

    def __init__(self):
        super().__init__(
            name="FrontendDirector",
            agent_type="on-demand"
        )

        # Paths
        self.frontend_path = "/home/pilote/projet/agi/frontend"
        self.guidelines_path = f"{self.frontend_path}/src/guidelines"
        self.components_path = f"{self.frontend_path}/src/components"

        # Load API key with validation
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            # Model: Haiku 4.5 (fast + cheap)
            self.llm = ChatAnthropic(
                model="claude-3-5-haiku-20241022",
                api_key=api_key,
                max_tokens=4096,
                temperature=0.3  # Précis pour code
            )
            self.logger.info("✅ ANTHROPIC_API_KEY loaded successfully")
        else:
            self.llm = None
            self.logger.warning("⚠️  ANTHROPIC_API_KEY not found. LLM will not be initialized. Set ANTHROPIC_API_KEY in .env")

        # Load all guidelines
        self.guidelines = self._load_all_guidelines()

        # System prompt (ultra-complet)
        self.system_prompt = self._build_system_prompt()

    def _load_all_guidelines(self) -> Dict[str, str]:
        """Charge TOUTES les guidelines .md du frontend"""
        guidelines = {}

        if not os.path.exists(self.guidelines_path):
            self.logger.warning(f"Guidelines path not found: {self.guidelines_path}")
            return guidelines

        for md_file in Path(self.guidelines_path).glob("*.md"):
            with open(md_file, 'r', encoding='utf-8') as f:
                guidelines[md_file.stem] = f.read()
                self.logger.info(f"Loaded guideline: {md_file.name}")

        return guidelines

    def _build_system_prompt(self) -> str:
        """Construit le prompt système avec TOUTES les guidelines"""

        guidelines_text = "\n\n".join([
            f"## GUIDELINE: {name}\n{content}"
            for name, content in self.guidelines.items()
        ])

        return f"""# 🎨 TU ES LE FRONTEND DIRECTOR

## AUTORITÉ EXCLUSIVE

Tu es le SEUL agent autorisé à modifier le frontend.
Aucun autre agent ne peut toucher aux fichiers frontend.
Tu es le BOSS de toute la partie UI/UX.

## TA MISSION

Diriger et gérer TOUT le frontend:
- Créer nouveaux composants React/TypeScript
- Modifier composants existants
- Implémenter features UI
- Optimiser performances frontend
- Maintenir cohérence design
- Respecter STRICTEMENT les guidelines

## TECH STACK

**Framework:** React 18.3.1 + Vite 6.3.5
**Language:** TypeScript
**Styling:** Tailwind CSS v4.0
**Components:** shadcn/ui (Radix UI)
**Icons:** lucide-react
**Tables:** @tanstack/react-table + @tanstack/react-virtual
**GraphQL:** @apollo/client
**Animations:** motion/react (not Framer Motion)
**Forms:** react-hook-form@7.55.0
**Toasts:** sonner@2.0.3
**Resize:** re-resizable (NOT react-resizable)
**DnD:** react-dnd

## GUIDELINES (NON-NÉGOCIABLES)

{guidelines_text}

## TES RESPONSABILITÉS

1. **Respect absolu des guidelines**
   - Préserver TOUS les classes Tailwind existantes
   - Jamais modifier tailwind.config.js
   - Jamais créer composants custom (utiliser shadcn/ui)
   - Pas de font-size/weight inline (globals.css only)

2. **Qualité code**
   - TypeScript strict
   - Props validation
   - Error boundaries
   - Loading states
   - Accessibility WCAG 2.1 AA
   - No placeholder comments

3. **Performance**
   - Virtual scrolling si >1000 items
   - Lazy loading composants
   - Optimistic updates
   - Debounced inputs

4. **Architecture**
   - Composants dans /components
   - Hooks dans /hooks
   - Types dans /types
   - Config dans /config
   - Imports: import {{ Component }} from './components/component-name'

## WORKFLOW

Quand on te demande de créer/modifier un composant:

1. **Analyser** la demande
2. **Vérifier** guidelines applicables
3. **Planifier** structure composant
4. **Générer** code TypeScript complet
5. **Valider** contre checklist:
   - [ ] TypeScript sans erreurs
   - [ ] Props typées
   - [ ] shadcn/ui utilisé
   - [ ] Tailwind classes préservées
   - [ ] Pas de placeholders
   - [ ] Accessible (ARIA)
   - [ ] Responsive
   - [ ] Error handling

## OUTPUT FORMAT

Toujours retourner:
```json
{{
  "component_name": "ComponentName.tsx",
  "path": "src/components/...",
  "code": "... full TypeScript code ...",
  "dependencies": ["lib1", "lib2"],
  "usage_example": "... how to use ..."
}}
```

## INTERDICTIONS

❌ Modifier tailwind.config.js
❌ Créer composants custom UI (shadcn/ui exists)
❌ Utiliser Framer Motion (use motion/react)
❌ Classes font inline
❌ Placeholder comments
❌ react-resizable (use re-resizable)
❌ Ignorer guidelines

## TU ES LE BOSS FRONTEND

Prends les décisions UI/UX en respectant guidelines.
Optimise l'expérience utilisateur.
Maintiens la cohérence du design system.
Sois fier de ton code.

Modèle: Claude Haiku 4.5 (rapide et économique)
"""

    async def execute(self, task: str, context: Optional[Dict] = None) -> Dict:
        """Exécute une tâche frontend"""

        prompt = f"""
{self.system_prompt}

## TÂCHE

{task}

## CONTEXTE

{context if context else "Aucun contexte additionnel"}

## OUTPUT

Génère le code complet avec toutes les validations.
"""

        result = await self.llm.ainvoke(prompt)

        return {
            "task": task,
            "output": result.content,
            "model": "claude-3-5-haiku-20241022",
            "guidelines_applied": list(self.guidelines.keys())
        }

    async def create_component(self, spec: Dict) -> Dict:
        """Crée un nouveau composant React"""
        task = f"""
Créer un nouveau composant React:

Nom: {spec.get('name')}
Type: {spec.get('type', 'functional')}
Props: {spec.get('props', {})}
Features: {spec.get('features', [])}
GraphQL: {spec.get('graphql_query', 'None')}

Génère le code TypeScript complet avec:
- Types pour les props
- Error boundary si nécessaire
- Loading state
- shadcn/ui components
- Tailwind styling
- Accessibility
"""
        return await self.execute(task, spec)

    async def modify_component(self, file_path: str, modifications: str) -> Dict:
        """Modifie un composant existant"""

        # Read current code
        full_path = f"{self.frontend_path}/{file_path}"
        with open(full_path, 'r') as f:
            current_code = f.read()

        task = f"""
Modifier le composant: {file_path}

CODE ACTUEL:
```tsx
{current_code}
```

MODIFICATIONS DEMANDÉES:
{modifications}

IMPORTANT: Préserver TOUTES les classes Tailwind existantes.

Génère le code modifié complet.
"""
        return await self.execute(task, {"current_code": current_code})

    async def validate_component(self, code: str) -> Dict:
        """Valide un composant contre les guidelines"""
        task = f"""
Valider ce code contre TOUTES les guidelines:

```tsx
{code}
```

Retourne:
- Violations trouvées
- Suggestions corrections
- Score conformité (0-100)
"""
        return await self.execute(task)


# CLI pour tester
if __name__ == "__main__":
    async def test():
        agent = FrontendDirectorAgent()

        print("🎨 Frontend Director Agent")
        print(f"Guidelines chargées: {list(agent.guidelines.keys())}")
        print(f"Modèle: Haiku 4.5")

        # Test création composant
        result = await agent.create_component({
            "name": "TestButton",
            "type": "button",
            "props": {"label": "string", "onClick": "function"},
            "features": ["loading state", "disabled state"]
        })

        print("\n✅ Résultat:")
        print(result['output'][:500])

    asyncio.run(test())
