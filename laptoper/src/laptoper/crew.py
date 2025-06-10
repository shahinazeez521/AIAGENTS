# src/laptoper/crew.py

from crewai import Agent, Task, Crew
from pathlib import Path
import yaml
import importlib.util
import inspect

def load_yaml(file_path):
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

def import_all_tool_functions():
    tool_path = Path(__file__).resolve().parent / "tools" / "custom_tool.py"
    if not tool_path.exists():
        return []

    spec = importlib.util.spec_from_file_location("custom_tool", tool_path)
    custom_tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(custom_tool)

    functions = [getattr(custom_tool, fn) for fn in dir(custom_tool)
                 if callable(getattr(custom_tool, fn)) and fn.startswith("run_")]
    return functions

def build_crew():
    config_dir = Path(__file__).resolve().parent.parent / "config"

    agents_config = load_yaml(config_dir / "agents.yaml")["agents"]
    tasks_config = load_yaml(config_dir / "tasks.yaml")["tasks"]

    tools = import_all_tool_functions()

    agents = [Agent(**agent, tools=tools) for agent in agents_config]
    tasks = [Task(agent=next(a for a in agents if a.name == task["agent"]), **task) for task in tasks_config]

    return Crew(agents=agents, tasks=tasks, verbose=True)
