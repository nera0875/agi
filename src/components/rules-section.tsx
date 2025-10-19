import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Switch } from "./ui/switch";
import { Badge } from "./ui/badge";

const automationRules = [
  {
    id: 'analytics',
    name: 'Analytics',
    description: 'Analyse et statistiques',
    badge: 'Autonome',
    enabled: true,
    examples: [
      'Génère un rapport de productivité',
      'Création de tâches / Je consulte ce mois ?',
      'Quel est mon temps moyen par tâche ?'
    ]
  },
  {
    id: 'create-memory',
    name: 'Create Memory',
    description: 'Stockage de mémoires et apprentissages',
    badge: 'Autonome',
    enabled: true,
    examples: [
      'Mémorise que je préfère React à Vue',
      'Note cette solution pour plus tard',
      'Retiens cette architecture'
    ]
  },
  {
    id: 'create-task',
    name: 'Create Task',
    description: 'Création de tâches depuis conversation',
    badge: 'Autonome',
    enabled: true,
    examples: [
      'Crée une tâche pour implémenter le login',
      'Ajoute ça à ma todo list',
      'Note que je dois faire X demain'
    ]
  },
  {
    id: 'read-tasks',
    name: 'Read Tasks',
    description: 'Lecture et recherche de tâches',
    badge: 'Autonome',
    enabled: true,
    examples: [
      'Liste mes tâches en cours',
      'Quelles sont mes priorités ?',
      'Montre-moi les tâches du projet X'
    ]
  }
];

export function RulesSection() {
  return (
    <div className="space-y-6">
      <div>
        <h2>AI Automation Rules</h2>
        <p className="text-muted-foreground">
          Configure what AI can do autonomously vs. with confirmation
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Actions Autonomes</CardTitle>
              <CardDescription>
                L'IA peut effectuer ces actions sans demander de confirmation. Idéal pour les opérations de lecture et création simples
              </CardDescription>
            </div>
            <Badge variant="secondary">{automationRules.length} règles</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {automationRules.map((rule) => (
            <div key={rule.id} className="space-y-3 pb-6 border-b last:border-b-0 last:pb-0">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <h4>{rule.name}</h4>
                    <Badge variant="outline" className="bg-chart-2/10 text-chart-2 border-chart-2/20">
                      {rule.badge}
                    </Badge>
                  </div>
                  <p className="text-muted-foreground text-sm">
                    {rule.description}
                  </p>
                </div>
                <Switch defaultChecked={rule.enabled} />
              </div>
              
              <div className="space-y-1.5 ml-0">
                <p className="text-sm text-muted-foreground">Exemples:</p>
                <ul className="space-y-1">
                  {rule.examples.map((example, idx) => (
                    <li key={idx} className="text-sm text-foreground/80 pl-4 relative before:content-['•'] before:absolute before:left-0">
                      "{example}"
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
