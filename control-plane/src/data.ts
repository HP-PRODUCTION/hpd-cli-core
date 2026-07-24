// Data catalog representing the HPD CLI Core ecosystem, commands, maturity, and integration standards.

export interface Command {
  name: string;
  usage: string;
  description: string;
  module: "ai" | "system" | "infra" | "wp" | "lab";
  level: "Ready" | "In Progress" | "Roadmap";
  safetyFilter?: boolean;
}

export interface ProjectNode {
  id: string;
  name: string;
  type: string;
  dbName: string;
  dbUser: string;
  status: "Active" | "Configured" | "Design";
  description: string;
}

export const commandsCatalog: Command[] = [
  // hpd ai
  {
    name: "Doctor",
    usage: "hpd ai doctor",
    description: "Diagnostica la conectividad con proveedores de IA (Gemini, OpenAI, Ollama), latencia de la API y el estado del fallback chain en caso de fallos.",
    module: "ai",
    level: "Ready"
  },
  {
    name: "Ask (Contextual Repo)",
    usage: 'hpd ai ask "analiza este repo" --context repo',
    description: "Consulta al asistente inteligente de HPD enviando de manera automática el árbol de archivos relevantes de tu repositorio con filtrado de seguridad.",
    module: "ai",
    level: "Ready"
  },
  {
    name: "Ask (Local Filesystem)",
    usage: 'hpd ai ask --context fs --path /home/hpd "pregunta"',
    description: "Consulta a la IA con contexto mapeado del sistema de archivos local, escaneando directorios específicos y enlazando archivos.",
    module: "ai",
    level: "Ready"
  },
  {
    name: "AI List",
    usage: "hpd ai ls",
    description: "Lista todas las capacidades del asistente, modelos cargados en caliente y comandos disponibles locales-aware.",
    module: "ai",
    level: "Ready"
  },
  {
    name: "Repo Scan",
    usage: "hpd ai repo scan --path ~ --depth 2 --exclude node_modules --json",
    description: "Escanea la presencia de proyectos locales buscando marcadores técnicos para catalogarlos automáticamente de forma json.",
    module: "ai",
    level: "Ready"
  },
  {
    name: "Repo Analyze",
    usage: "hpd ai repo analyze --path ~ --depth 2 --cache",
    description: "Deduce cuáles repositorios son proclives a proyectos de Datos, Business Intelligence, backend o procesos ETL para preparar informes.",
    module: "ai",
    level: "Ready"
  },
  {
    name: "Patch",
    usage: 'hpd ai patch file.py "mejorar manejo de errores"',
    description: "Edición asistida por IA de un archivo con diferencias estructuradas (diff), backup automático de archivos (.bak) y confirmación manual interactiva previa.",
    module: "ai",
    level: "Ready",
    safetyFilter: true
  },
  {
    name: "Status",
    usage: "hpd ai status",
    description: "Muestra las métricas de uso acumuladas y la estabilidad de los proveedores configurados según cuotas y respuestas.",
    module: "ai",
    level: "Ready"
  },
  {
    name: "Compare",
    usage: 'hpd ai compare "pregunta"',
    description: "Envía una pregunta técnica en paralelo a múltiples proveedores activos (ej. Gemini vs OpenAI vs Local Ollama) para contrastar respuestas.",
    module: "ai",
    level: "Ready"
  },
  {
    name: "Generate Module",
    usage: "hpd ai generate module <name>",
    description: "Genera scaffolding automatizado de archivos y scripts según las plantillas de diseño y arquitectura HPD estándar.",
    module: "ai",
    level: "Ready"
  },
  {
    name: "AI Agent (Plan & Execute)",
    usage: "hpd ai plan / hpd ai fix",
    description: "Planeamiento autónomo de tareas complejas de múltiples etapas y corrección automática de incidentes del sistema detectados.",
    module: "ai",
    level: "In Progress"
  },

  // hpd system
  {
    name: "System Doctor",
    usage: "hpd system doctor [--history]",
    description: "Diagnóstico integral del host (CPU, RAM, Espacio en disco, Docker containers). Devuelve un Health Score (0-100) y lista de alertas con sugerencias.",
    module: "system",
    level: "Ready"
  },
  {
    name: "Trends",
    usage: "hpd system trends",
    description: "Análisis histórico de tendencias basado en los snapshots generados por el System Doctor para prever degradaciones tempranas.",
    module: "system",
    level: "Ready"
  },
  {
    name: "Clean Storage",
    usage: "hpd system clean --dry-run / --apply",
    description: "Mantenimiento proactivo. Identifica de manera segura logs obsoletos, caché del gestor del sistema APT, basuras de Docker, y los libera.",
    module: "system",
    level: "Ready"
  },
  {
    name: "Processes Tracker",
    usage: "hpd system processes",
    description: "Analizador de carga de nivel de procesos del sistema que señala aplicativos pesados y fugas de rendimiento con muestreo preciso.",
    module: "system",
    level: "Ready"
  },
  {
    name: "Services Monitor",
    usage: "hpd system services",
    description: "Controla y reporta el estado operativo de los servicios críticos de infraestructura local (como SSH, Docker local, Postgres SQL, Nginx).",
    module: "system",
    level: "Ready"
  },
  {
    name: "System Fix",
    usage: "hpd system fix docker --apply",
    description: "Reparaciones asistidas automatizadas no destructivas (reinicio de contenedores rotos, restablecer swap colapsado, reconstrucción de permisos de env).",
    module: "system",
    level: "Ready"
  },
  {
    name: "Serverize Precheck",
    usage: "hpd system serverize --precheck",
    description: "Valida si el host cumple con los requerimientos necesarios antes del despliegue final en producción (hardening técnico y puertos libres).",
    module: "system",
    level: "Ready"
  },
  {
    name: "Serverize Profile Auto-config",
    usage: "hpd system serverize --profile <web|docker|basic>",
    description: "Configura automáticamente los puertos, firewalls y estructuras de aislamiento para el tipo de servidor seleccionado.",
    module: "system",
    level: "In Progress"
  },

  // hpd infra / core
  {
    name: "Project Init",
    usage: "hpd init <project_name>",
    description: "Inicializa un proyecto HPD montando el archivo de orquestación hpd.config.json y creando las carpetas estructuradas estándar.",
    module: "infra",
    level: "Ready"
  },
  {
    name: "Integration Pipeline",
    usage: "hpd integrate <source> <target>",
    description: "Orquestador de transferencia e integración. Ejecuta las migraciones o sincronización de pipelines (ej: de Anaconda a WordPress).",
    module: "infra",
    level: "Ready"
  },
  {
    name: "DB Provision",
    usage: "hpd db provision <project_name>",
    description: "Crea automáticamente la base de datos lógica y un usuario de acceso asilado con contraseña aleatoria robusta, bajo las leyes del RFC-002.",
    module: "infra",
    level: "Ready"
  },
  {
    name: "DB Isolated Backup",
    usage: "hpd db backup <project_name>",
    description: "Ejecuta un backup exclusivo de la base de datos lógica del proyecto usando pg_dump aislado para evitar volcados masivos acoplados.",
    module: "infra",
    level: "Ready"
  },

  // wordpress ecosistema
  {
    name: "WordPress Doctor",
    usage: "hpd wordpress doctor [--json]",
    description: "Diagnóstico personalizado de los plugins de HPD (Publicador Automático v2.14, Módulo Económico con feeds financieros) y conectividad a WP-CLI.",
    module: "wp",
    level: "Ready"
  },
  {
    name: "WP Stabilize CLI",
    usage: "hpd wordpress stabilize",
    description: "Valida el estado del núcleo de WordPress Docker y ejecuta pruebas de humo de publicación editorial.",
    module: "wp",
    level: "In Progress"
  },

  // hpd lab
  {
    name: "Lab Status",
    usage: "hpd lab status",
    description: "Muestra la métrica de uso de la carpeta de investigación y desarrollo (I+D) y los archivos archivados en legacy/.",
    module: "lab",
    level: "Ready"
  },
  {
    name: "Lab Sandbox Init",
    usage: "hpd lab sandbox init",
    description: "Monta un sandbox limpio y aislado con fixtures para validar de manera segura parches sintácticos de hpd ai patch.",
    module: "lab",
    level: "Ready"
  },
  {
    name: "AI Benchmarks",
    usage: "hpd lab benchmark ollama",
    description: "Prueba comparativa de velocidad de tokenización y calidad de razonamiento por segundo de modelos pesados vs livianos locales.",
    module: "lab",
    level: "Ready"
  }
];

export const projectNodes: ProjectNode[] = [
  {
    id: "anaconda",
    name: "Proyecto Anaconda",
    type: "Data Platform / ETL Pipeline",
    dbName: "anaconda_db",
    dbUser: "anaconda_user",
    status: "Active",
    description: "Plataforma de datos principales encargada de flujos ETL de backend y análisis BI central."
  },
  {
    id: "wordpress",
    name: "HPD WordPress El Matutino",
    type: "WordPress Docker Editorial",
    dbName: "wordpress_db",
    dbUser: "wordpress_user",
    status: "Active",
    description: "Ecosistema editorial autogestionado con hpd-auto-publicador y calculadora de tasas financieras dominicanas."
  },
  {
    id: "dropshipping",
    name: "Dropshipping eBay Bridge",
    type: "eCommerce Integration Bridge",
    dbName: "dropshipping_db",
    dbUser: "dropshipping_user",
    status: "Configured",
    description: "Pasarela comercial capaz de recopilar precios, reviews de dropshipping y publicarlos en lotes."
  },
  {
    id: "deportiva",
    name: "Plataforma Deportiva",
    type: "Sports Metrics Engine",
    dbName: "deportiva_db",
    dbUser: "deportiva_user",
    status: "Configured",
    description: "Procesador analítico de estadísticas e información deportiva con base de datos en PostgreSQL."
  },
  {
    id: "metabase",
    name: "Metabase OSS Suite",
    type: "Business Intelligence Hub",
    dbName: "metabase_db",
    dbUser: "metabase_user",
    status: "Active",
    description: "Visualizador unificado de base de datos e incidencias bajo dashboards para visualización ejecutiva."
  }
];

export const securityRuleList = [
  {
    title: "Sanitización del AI Context (Denylist)",
    description: "Una estricta lista de exclusión en `build_context` e `ia patch` protege inmediatamente todos tus archivos sensibles (como `.env`, `/secrets`, claves SSH, y base de datos local) de ser leídos por la IA.",
    icon: "ShieldAlert"
  },
  {
    title: "Aislamiento de Conexiones de DB",
    description: "Bajo las pautas del RFC-002, queda prohibido que los proyectos usen el superusuario `postgres` o que se unifiquen en una única base de datos gigante. Cada rol y esquema es independiente.",
    icon: "KeyRound"
  },
  {
    title: "Backups Resilientes Separados",
    description: "Las tareas automáticas ejecutan backups aislados. El colapso del volcado o restauración de un sistema nunca compromete a la base de datos de los otros entornos.",
    icon: "RefreshCcw"
  },
  {
    title: "Manejo Tipado de Errores",
    description: "HPD ha erradicado por completo los bloques inestables `bare except:`. Captura de fallos de forma refinada, registrando de forma rotativa en archivos compactos legibles por máquinas.",
    icon: "Bug"
  }
];

export const integrationQA = [
  {
    q: "¿Qué nivel de madurez o preparación tiene hpd-cli-core hoy?",
    a: "HPD CLI Core está en nivel VERDE / ESTABLE de grado de producción local (Hardened). Posee una suite de cobertura automatizada impecable con 47 de 47 pruebas pasando en pytest y una canalización de GitHub Actions activa en .github/workflows/tests.yml que mantiene el código blindado en cada push."
  },
  {
    q: "¿Cómo se integra hpd-cli-core con mi sistema operativo local?",
    a: "Se integra interactuando vía el CLI global `hpd` una vez instalado con `pip install -e '.[dev]'`. Sus módulos interactúan directamente con tu host mediante la lectura de métricas de rendimiento del sistema host en `hpd system doctor` y automatiza tareas con scripts nativos estructurados."
  },
  {
    q: "¿Cómo interactúa hpd-cli-core con los diferentes proyectos locales?",
    a: "A través del orquestador unificado. Los comandos de infraestructura como `hpd db provision` o `hpd db backup` permiten dar de alta esquemas, aislar accesos, preparar automatizaciones y validar con precisión prechequeos en servidores con `hpd system serverize`."
  },
  {
    q: "¿Es seguro dar acceso al router de IA para el desarrollo?",
    a: "Completamente. Posee una Denylist (lista negra) robusta y un Singleton AIRouter para prevenir sobrefacturación o latencia excesiva, con un sistema de fallback inteligente en caso de desconexión."
  }
];
