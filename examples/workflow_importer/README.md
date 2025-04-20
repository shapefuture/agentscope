# Workflow Importer for AgentScope

This example demonstrates how to use the new workflow importer feature in AgentScope to create agent workflows from JSON or XML files.

## Features

- Import workflow configurations from JSON or XML files
- Convert imported workflows to AgentScope-compatible format
- Run or compile the imported workflows

## Background

AgentScope provides a powerful workflow system that allows you to create complex agent interactions. With the new workflow importer, you can now define these workflows in JSON or XML format, making it easier to create, share, and modify agent workflows.

This is particularly useful for:
- Creating reusable workflow templates
- Sharing workflows between projects
- Integrating with other systems that generate workflow definitions
- Visually designing workflows in external tools and importing them into AgentScope

## Usage

### Importing a Workflow

You can import a workflow using the provided example script:

```bash
python import_workflow_example.py path/to/your/workflow.json --run
```

Or for XML files:

```bash
python import_workflow_example.py path/to/your/workflow.xml --run
```

### Compiling a Workflow

You can also compile the workflow to a Python file:

```bash
python import_workflow_example.py path/to/your/workflow.json --compile output.py
```

### Using the API in Your Code

```python
from agentscope.web.workstation.workflow_importer import load_workflow, convert_to_agentscope_workflow
from agentscope.web.workstation.workflow import start_workflow

# Load the workflow configuration
config = load_workflow("path/to/your/workflow.json")  # or .xml

# Convert the configuration to AgentScope format if needed
config = convert_to_agentscope_workflow(config)

# Run the workflow
start_workflow(config)
```

## Example Workflow Files

This example includes:

1. A JSON workflow file (`workflow_example.json`) - This is the same as the original plan.json file
2. An XML workflow file (`workflow_example.xml`) - This is an XML version of the same workflow

## File Format

### JSON Format

The JSON format follows the structure used by AgentScope's workflow system:

```json
{
  "metadata": {
    "version": 2
  },
  "modules": [
    {
      "id": 1,
      "module": "module.type",
      "version": 1,
      "parameters": {
        "param1": "value1",
        "param2": "value2"
      },
      "metadata": {
        "designer": {
          "x": 0,
          "y": 0
        }
      }
    }
  ],
  "connections": {
    "1": { "2": [0] },
    "2": { "3": [0] }
  }
}
```

### XML Format

The XML format is a structured representation of the same information:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<workflow>
  <metadata>
    <version>2</version>
  </metadata>
  <modules>
    <module id="1" type="module.type" version="1">
      <parameters>
        <param1>value1</param1>
        <param2>value2</param2>
      </parameters>
      <position x="0" y="0"/>
    </module>
  </modules>
  <connections>
    <connection from="1" to="2"/>
  </connections>
</workflow>
```

## Requirements

- AgentScope
- Python 3.8 or higher
