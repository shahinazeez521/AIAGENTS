# src/laptoper/main.py

import yaml
from pathlib import Path
import re

def slugify(text):
    return re.sub(r'\W+', '_', text.strip().lower())

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = BASE_DIR / "config"
AGENTS_YAML = CONFIG_PATH / "agents.yaml"
TASKS_YAML = CONFIG_PATH / "tasks.yaml"
TOOLS_PATH = Path(__file__).resolve().parent / "tools"
TOOL_FILE = TOOLS_PATH / "custom_tool.py"

def load_yaml(file_path):
    if not file_path.exists():
        return {}
    with open(file_path, 'r') as f:
        return yaml.safe_load(f) or {}

def save_yaml(data, file_path):
    with open(file_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)

def append_tool_function(tool_description: str, method_name: str):
    TOOLS_PATH.mkdir(parents=True, exist_ok=True)
    if not TOOL_FILE.exists():
        TOOL_FILE.write_text("# Custom tools module\n\n")

    existing_code = TOOL_FILE.read_text()
    if method_name in existing_code:
        print(f"⚠️ Tool `{method_name}` already exists.")
        return

    new_func = f"""
def {method_name}(input_data):
    \"\"\"
    {tool_description}
    TODO: Implement the logic to {tool_description.lower()} here.
    \"\"\"
    return "Tool response from {method_name}: " + str(input_data)
""".strip()

    with open(TOOL_FILE, "a") as f:
        f.write("\n\n" + new_func)

    print(f"✅ Tool function `{method_name}` appended to custom_tool.py")

def generate_agent_and_task(purpose: str, tool_description: str = None):
    CONFIG_PATH.mkdir(parents=True, exist_ok=True)

    agents_data = load_yaml(AGENTS_YAML)
    tasks_data = load_yaml(TASKS_YAML)

    agents_data.setdefault("agents", [])
    tasks_data.setdefault("tasks", [])

    agent_slug = slugify(purpose)
    tool_fn = f"run_{slugify(tool_description)}" if tool_description else "run_custom_tool"
    agent_name = f"{agent_slug}_agent"

    if any(agent["name"] == agent_name for agent in agents_data["agents"]):
        print(f"⚠️ Agent `{agent_name}` already exists. Skipping.")
        return

    if tool_description:
        append_tool_function(tool_description, tool_fn)

    new_agent = {
        "name": agent_name,
        "role": f"A specialized agent for: {purpose}",
        "goal": f"Perform the task: {purpose}",
        "backstory": "An intelligent AI agent capable of using tools for specific tasks.",
        "allow_delegation": False,
        "verbose": True
    }

    new_task = {
        "description": f"Use the tool `{tool_fn}` to accomplish: {purpose}",
        "expected_output": f"The completed result for {purpose}.",
        "agent": agent_name
    }

    agents_data["agents"].append(new_agent)
    tasks_data["tasks"].append(new_task)

    save_yaml(agents_data, AGENTS_YAML)
    save_yaml(tasks_data, TASKS_YAML)

    print("✅ New agent and task appended to agents.yaml and tasks.yaml.")

if __name__ == "__main__":
    print("🚀 Build a New Agent + Tool")
    purpose = input("Enter the agent purpose: ")
    tool_desc = input("Enter the tool description (optional): ")

    generate_agent_and_task(purpose, tool_desc or None)
