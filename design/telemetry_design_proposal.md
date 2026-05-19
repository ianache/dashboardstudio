# Propuesta de Arquitectura: Telemetría y Visualización en Tiempo Real para CrewAI

Esta propuesta detalla el diseño y la integración de una consola interactiva premium de telemetría en tiempo real utilizando la librería `rich`. El sistema interceptará el ciclo de vida de los agentes y tareas de CrewAI para pintar un dashboard dinámico y libre de parpadeo (*flicker-free*) en la terminal.

---

## 1. Diseño Visual de la Terminal (Dashboard Premium)

En lugar de utilizar `os.system("clear")` clásico que genera parpadeo molesto y arruina la experiencia premium, proponemos utilizar `rich.live.Live`. Este componente mantiene un búfer virtual en consola y actualiza solo las partes que cambian, logrando una interfaz fluida e interactiva similar a una aplicación TUI (Terminal User Interface) profesional.

### Distribución de la Pantalla (Layout)
```
┌────────────────────────────────────────────────────────────────────────┐
│  🤖 AI AGENTS CREW - TELEMETRÍA DE EJECUCIÓN EN VIVO                   │
│  Meta Global: "Diseñar una User Story de Login con Keycloak en Angular"│
│  Estado: ⏳ EN EJECUCIÓN                                                │
├────────────────────────────────────────────────────────────────────────┤
│  ID      PASO / TAREA         AGENTE        SKILL / HERRAMIENTA  ESTADO│
│ ────────────────────────────────────────────────────────────────────── │
│  task_1  1. Analizar Requisitos  Researcher    SearchWebTool       ✅ OK  │
│  task_2  2. Diseñar Casos Prueba ScrumMaster   Pensando...         ⏳ ACT │
│  task_3  3. Validar Auditoría    Reporter      -                   💤 ESP │
├────────────────────────────────────────────────────────────────────────┤
│  Progreso Global: [████████████████░░░░░░░░░░░░░░░░] 33%                │
├────────────────────────────────────────────────────────────────────────┤
│  💬 FEED DE PENSAMIENTO EN VIVO (Últimos 4 logs):                     │
│  [10:04:12] Researcher: "Buscando documentación sobre Keycloak OIDC..."│
│  [10:04:15] Researcher: "Aplicando SearchWebTool con query..."        │
│  [10:04:18] ScrumMaster: "Analizando criterios de aceptación..."       │
│  [10:04:20] ScrumMaster: "Generando formato estructurado..."           │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Componente de Telemetría (`src/telemetry.py`)

La clase `CrewTelemetry` encapsulará todo el estado de la ejecución y proveerá métodos hilo-seguros para actualizar tareas, herramientas y logs.

```python
import time
from datetime import datetime
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.live import Live

class CrewTelemetry:
    def __init__(self, target_goal: str):
        self.target_goal = target_goal
        self.status = "RUNNING"  # RUNNING | COMPLETED | FAILED
        self.pipeline: List[Dict[str, Any]] = []
        self.logs: List[str] = []
        self.console = Console()
        self._live: Live | None = None

    def register_task(self, task_id: str, step_num: int, task_name: str, agent_role: str):
        """Inicializa una tarea en el pipeline con estado PENDING."""
        self.pipeline.append({
            "id": task_id,
            "step": step_num,
            "task_name": task_name,
            "agent": agent_role,
            "skill_applied": "-",
            "status": "PENDING",  # PENDING | RUNNING | COMPLETED | FAILED
            "started_at": None,
            "finished_at": None,
        })

    def start_task(self, task_id: str):
        for task in self.pipeline:
            if task["id"] == task_id:
                task["status"] = "RUNNING"
                task["started_at"] = time.time()
                self.add_log(f"Iniciando tarea: {task['task_name']}")
                break
        self.refresh()

    def complete_task(self, task_id: str, output: str = ""):
        for task in self.pipeline:
            if task["id"] == task_id:
                task["status"] = "COMPLETED"
                task["finished_at"] = time.time()
                self.add_log(f"Tarea completada: {task['task_name']}")
                break
        self.refresh()

    def fail_task(self, task_id: str, error: str):
        for task in self.pipeline:
            if task["id"] == task_id:
                task["status"] = "FAILED"
                task["finished_at"] = time.time()
                self.add_log(f"❌ Tarea falló: {task['task_name']} - Error: {error}")
                break
        self.status = "FAILED"
        self.refresh()

    def update_agent_step(self, task_id: str, skill: str, thought: str):
        """Actualiza el skill activo y añade el pensamiento del agente a los logs."""
        for task in self.pipeline:
            if task["id"] == task_id:
                task["skill_applied"] = skill
                break
        if thought:
            clean_thought = thought.strip().replace("\n", " ")[:80]
            self.add_log(f"{clean_thought}...")
        self.refresh()

    def add_log(self, text: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {text}")
        if len(self.logs) > 4:
            self.logs.pop(0)  # Mantener solo los últimos 4 logs

    def build_dashboard(self) -> Layout:
        """Construye la interfaz premium de Rich utilizando Layouts."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=4),
            Layout(name="body", minimum_size=8),
            Layout(name="progress", size=3),
            Layout(name="footer", size=7)
        )

        # 1. Cabecera (Header Panel)
        status_colors = {"RUNNING": "bold yellow", "COMPLETED": "bold green", "FAILED": "bold red"}
        status_emoji = {"RUNNING": "⏳ RUNNING", "COMPLETED": "✅ COMPLETED", "FAILED": "❌ FAILED"}
        header_text = (
            f"[bold cyan]🎯 Objetivo Global:[/bold cyan] {self.target_goal}\n"
            f"[bold cyan]📊 Estado General:[/bold cyan] [{status_colors[self.status]}]{status_emoji[self.status]}[/]"
        )
        layout["header"].update(Panel(header_text, title="🤖 CrewAI Execution Telemetry", border_style="blue"))

        # 2. Pipeline Table (Body)
        table = Table(expand=True, show_edge=False, box=None)
        table.add_column("ID", style="dim", width=8)
        table.add_column("Paso", width=6, justify="center")
        table.add_column("Tarea", ratio=2)
        table.add_column("Agente", style="magenta", ratio=1)
        table.add_column("Skill / Herramienta", style="green", ratio=1)
        table.add_column("Estado", justify="center", width=12)

        status_styles = {
            "PENDING": "[grey50]💤 PENDING[/]",
            "RUNNING": "[bold yellow]⏳ RUNNING[/]",
            "COMPLETED": "[bold green]✅ COMPLETED[/]",
            "FAILED": "[bold red]❌ FAILED[/]"
        }

        for task in self.pipeline:
            table.add_row(
                task["id"],
                str(task["step"]),
                task["task_name"],
                task["agent"],
                task["skill_applied"],
                status_styles[task["status"]]
            )
        layout["body"].update(Panel(table, title="📋 Pipeline de Ejecución", border_style="grey30"))

        # 3. Progress Bar
        completed = sum(1 for t in self.pipeline if t["status"] == "COMPLETED")
        total = len(self.pipeline) or 1
        pct = (completed / total) * 100

        progress = Progress(
            TextColumn("[bold cyan]Progreso Global:[/]"),
            BarColumn(bar_width=40, complete_style="green", finished_style="bold green"),
            TextColumn("[bold green]{task.percentage:>3.0f}%[/]"),
        )
        p_task = progress.add_task("tasks", total=total)
        progress.update(p_task, completed=completed)
        layout["progress"].update(Panel(progress, border_style="grey30"))

        # 4. Logs Feed (Footer)
        feed_content = "\n".join(self.logs) if self.logs else "[dim]Esperando eventos de agentes...[/dim]"
        layout["footer"].update(Panel(feed_content, title="💬 Pensamiento del Agente & Logs en Vivo", border_style="grey30"))

        return layout

    def start(self):
        """Inicia el renderizador en vivo de Rich."""
        self._live = Live(self.build_dashboard(), refresh_per_second=4, screen=True)
        self._live.start()

    def refresh(self):
        if self._live:
            self._live.update(self.build_dashboard())

    def stop(self):
        if self._live:
            self._live.stop()
            self._live = None
```

---

## 3. Integración Limpia con CrewAI (Callbacks y Wrappers)

CrewAI expone hooks clave que permiten enganchar nuestra telemetría de manera nativa sin contaminar la definición declarativa de la Crew.

### A. Intercepción de Tareas (`Task` Callbacks)
CrewAI expone una propiedad `callback` en cada tarea que se dispara cuando esta finaliza correctamente. Para registrar el inicio, el fin y los fallos, utilizaremos una fábrica de wrappers:

```python
def wrap_crew_task(telemetry: CrewTelemetry, task_id: str, step_num: int, task_name: str, agent_role: str, base_task_kwargs: dict) -> dict:
    """Prepara los argumentos para instanciar una Task de CrewAI con soporte de telemetría.
    
    Registra la tarea en la telemetría en estado PENDING y retorna los kwargs listos,
    incluyendo el callback de completitud.
    """
    telemetry.register_task(task_id, step_num, task_name, agent_role)
    
    # Callback que se ejecuta de forma nativa al finalizar con éxito
    def on_task_completed(output):
        telemetry.complete_task(task_id, str(output))
        
    base_task_kwargs["callback"] = on_task_completed
    return base_task_kwargs
```

### B. Intercepción del Pensamiento (`Agent` Step Callbacks)
Cada vez que un agente de CrewAI decide usar una herramienta o realiza un paso de razonamiento, ejecuta `step_callback`. Capturaremos esto para actualizar en tiempo real qué **skill** está aplicando y qué está **pensando**:

```python
def make_agent_step_callback(telemetry: CrewTelemetry, task_id: str, agent_role: str):
    """Fábrica de step_callback para agentes de CrewAI."""
    def step_callback(step):
        # step puede ser un objeto AgentStep o una lista de ellos
        tool_name = "Pensando..."
        thought = ""
        
        # CrewAI devuelve comúnmente un AgentStep o una lista que contiene el action (AgentAction)
        if hasattr(step, "action") and step.action:
            tool_name = getattr(step.action, "tool", "Pensando...")
            thought = getattr(step, "thought", "")
        elif isinstance(step, list) and len(step) > 0:
            last_step = step[-1]
            if hasattr(last_step, "action") and last_step.action:
                tool_name = getattr(last_step.action, "tool", "Pensando...")
                thought = getattr(last_step, "thought", "")
        elif hasattr(step, "thought"):
            thought = step.thought
            
        telemetry.update_agent_step(task_id, tool_name, f"{agent_role}: {thought}")
        
    return step_callback
```

### C. Captura de Errores e Inicio de Tareas
Dado que CrewAI ejecuta las tareas secuencialmente, podemos controlar el ciclo activo y capturar excepciones robustamente:

```python
def run_telemetry_crew(telemetry: CrewTelemetry, crew_factory):
    """Ejecuta una Crew bajo el contexto de telemetría en vivo, gestionando
    el inicio de cada paso y capturando excepciones.
    """
    telemetry.start()
    try:
        # 1. Instanciar la Crew
        crew = crew_factory()
        
        # 2. Iterar sobre las tareas para simular/gestionar su ejecución
        #    (CrewAI procesa las tareas en orden secuencial)
        for i, task in enumerate(crew.tasks):
            # Asumimos que podemos mapear cada task_id registrado
            task_id = f"task_{i+1:02d}"
            
            # En la ejecución secuencial, marcamos la tarea como RUNNING antes de iniciar
            telemetry.start_task(task_id)
            
            # Nota: CrewAI maneja su propio kickoff global, por lo que para 
            # interceptar el inicio exacto de cada paso secuencial en tiempo real,
            # podemos adjuntar pre-hooks o iniciar el pipeline de forma guiada.
        
        # Lanzamos el proceso global
        result = crew.kickoff()
        
        telemetry.status = "COMPLETED"
        telemetry.refresh()
        return result
        
    except Exception as e:
        # Captura de fallos globales o de cualquier tarea intermedia
        telemetry.status = "FAILED"
        telemetry.add_log(f"⚠️ Excepción crítica: {str(e)}")
        telemetry.refresh()
        raise e
    finally:
        # Esperar unos segundos para mostrar el dashboard final y luego detener la pantalla
        time.sleep(3)
        telemetry.stop()
```

---

## 4. Próximos Pasos de Iteración

1. **¿Qué te parece el diseño del Dashboard?** ¿Prefieres que utilicemos la librería `rich.live` para una pantalla TUI fluida, o deseas que implementemos el limpiado tradicional de pantalla por comandos `os.system`?
2. **Librerías de CrewAI**: Dado que en tu proyecto actual la orquestación multiagente es determinista y utiliza el motor nativo sobre la arquitectura del orquestador, ¿deseas que instalemos `crewai` como dependencia formal en tu `pyproject.toml` para crear esta demo integrada en el CLI principal?

Quedo atento a tus comentarios para proceder con la implementación exacta.
