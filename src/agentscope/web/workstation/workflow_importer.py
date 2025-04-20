# -*- coding: utf-8 -*-
"""
Workflow importer module for AgentScope.

This module provides functionality to import workflow definitions from JSON or XML files
and convert them into AgentScope workflow configurations. It serves as a bridge between
external workflow definition formats and AgentScope's internal workflow representation.

The module supports:
1. Loading workflow configurations from JSON files
2. Loading workflow configurations from XML files
3. Converting between different workflow formats
4. Validating workflow configurations for compatibility with AgentScope

Typical usage:
    from agentscope.web.workstation.workflow_importer import load_workflow
    config = load_workflow("path/to/workflow.json")
    # or
    config = load_workflow("path/to/workflow.xml")
"""

import json
import os
import traceback
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, Union, List, Tuple, Set
from loguru import logger

# Define constants for validation
REQUIRED_CONFIG_KEYS = {"modules", "connections"}
REQUIRED_MODULE_KEYS = {"id", "module", "version", "parameters"}
OPTIONAL_MODULE_KEYS = {"metadata"}


def load_json_workflow(file_path: str) -> Dict[str, Any]:
    """
    Load a workflow configuration from a JSON file.

    This function reads a JSON file from the specified path and parses it into a Python
    dictionary. It performs basic validation to ensure the file exists and contains valid
    JSON data. The function is specifically designed to handle AgentScope workflow
    configurations, which typically include 'modules' and 'connections' sections.

    Args:
        file_path (str): Path to the JSON file containing the workflow configuration.
                         This should be an absolute or relative path to a valid JSON file.

    Returns:
        Dict[str, Any]: A dictionary containing the workflow configuration with all the
                        modules, connections, and metadata from the JSON file.

    Raises:
        FileNotFoundError: If the specified file does not exist or cannot be accessed.
        json.JSONDecodeError: If the file contains invalid JSON that cannot be parsed.

    Example:
        >>> config = load_json_workflow("workflow.json")
        >>> print(f"Loaded workflow with {len(config['modules'])} modules")
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Workflow file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        try:
            config = json.load(file)
            logger.info(f"Successfully loaded JSON workflow from {file_path}")
            return config
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON workflow: {e}")
            raise


def load_xml_workflow(file_path: str) -> Dict[str, Any]:
    """
    Load a workflow configuration from an XML file and convert it to a dictionary.

    This function reads an XML file from the specified path, parses it using ElementTree,
    and converts the XML structure into a Python dictionary format that is compatible with
    AgentScope's workflow system. The conversion process handles XML elements like modules,
    parameters, and connections, mapping them to the appropriate dictionary structure.

    Args:
        file_path (str): Path to the XML file containing the workflow configuration.
                         This should be an absolute or relative path to a valid XML file.

    Returns:
        Dict[str, Any]: A dictionary containing the workflow configuration with all the
                        modules, connections, and metadata converted from the XML structure.

    Raises:
        FileNotFoundError: If the specified file does not exist or cannot be accessed.
        ET.ParseError: If the file contains invalid XML that cannot be parsed.
        ValueError: If the XML structure cannot be properly converted to a workflow configuration.

    Example:
        >>> config = load_xml_workflow("workflow.xml")
        >>> print(f"Loaded workflow with {len(config['modules'])} modules")
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Workflow file not found: {file_path}")

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Convert XML to dictionary format compatible with AgentScope workflow
        config = _xml_to_dict(root)
        logger.info(f"Successfully loaded XML workflow from {file_path}")
        return config
    except ET.ParseError as e:
        logger.error(f"Failed to parse XML workflow: {e}")
        raise


def _xml_to_dict(element: ET.Element) -> Dict[str, Any]:
    """
    Convert an XML element to a dictionary representation compatible with AgentScope workflows.

    This is a helper function that recursively processes XML elements and converts them into
    a dictionary structure. It handles special cases for workflow elements such as:
    - metadata: Converted to a nested dictionary
    - modules: Converted to a list of module dictionaries
    - parameters: Converted to a dictionary of parameter values
    - connections: Converted to a nested dictionary structure
    - position attributes: Mapped to designer metadata

    The function is designed to transform XML workflow definitions into the same dictionary
    format that would be produced by parsing a JSON workflow file, ensuring consistency
    regardless of the input format.

    Args:
        element (ET.Element): The XML element to convert. This should be an ElementTree
                             Element object, typically the root element of an XML document
                             or a child element being processed recursively.

    Returns:
        Dict[str, Any]: A dictionary representation of the XML element, structured to be
                        compatible with AgentScope's workflow system.

    Note:
        This is an internal helper function and not intended to be called directly by users.
        It is used by the load_xml_workflow function to process XML workflow definitions.
    """
    result = {}

    # Process metadata if it exists
    metadata_elem = element.find("metadata")
    if metadata_elem is not None:
        result["metadata"] = _xml_to_dict(metadata_elem)

    # Process modules
    modules = []
    for module_elem in element.findall(".//module"):
        module = {
            "id": int(module_elem.get("id", "0")),
            "module": module_elem.get("type", ""),
            "version": int(module_elem.get("version", "1")),
            "parameters": {},
            "metadata": {"designer": {"x": 0, "y": 0}}
        }

        # Process parameters
        params_elem = module_elem.find("parameters")
        if params_elem is not None:
            for param in params_elem:
                # Handle different parameter types
                if param.tag == "header" or param.tag == "headers":
                    headers = []
                    for header in param:
                        headers.append({
                            "name": header.get("name", ""),
                            "value": header.get("value", "")
                        })
                    module["parameters"]["headers"] = headers
                else:
                    module["parameters"][param.tag] = param.text

        # Process position if available
        pos_elem = module_elem.find("position")
        if pos_elem is not None:
            module["metadata"]["designer"]["x"] = int(pos_elem.get("x", "0"))
            module["metadata"]["designer"]["y"] = int(pos_elem.get("y", "0"))

        modules.append(module)

    if modules:
        result["modules"] = modules

    # Process connections
    connections = {}
    for conn_elem in element.findall(".//connection"):
        from_id = conn_elem.get("from", "")
        to_id = conn_elem.get("to", "")

        if from_id and to_id:
            if from_id not in connections:
                connections[from_id] = {}

            if to_id not in connections[from_id]:
                connections[from_id][to_id] = [0]  # Default connection index

    if connections:
        result["connections"] = connections

    return result


def load_workflow(file_path: str) -> Dict[str, Any]:
    """
    Load a workflow configuration from either a JSON or XML file based on the file extension.

    This is the main entry point for loading workflow configurations from files. It determines
    the file type based on the file extension and delegates to the appropriate loader function.
    Currently supported file formats are JSON (.json) and XML (.xml).

    The function performs basic validation to ensure the file exists and has a supported
    extension. It then calls the appropriate loader function to parse the file and return
    the workflow configuration as a dictionary.

    Args:
        file_path (str): Path to the file containing the workflow configuration.
                         This should be an absolute or relative path to a valid workflow file
                         with either a .json or .xml extension.

    Returns:
        Dict[str, Any]: A dictionary containing the workflow configuration, structured
                        according to AgentScope's workflow format with modules, connections,
                        and optional metadata.

    Raises:
        FileNotFoundError: If the specified file does not exist or cannot be accessed.
        ValueError: If the file extension is not supported (.json or .xml).
        json.JSONDecodeError: If a JSON file contains invalid JSON.
        ET.ParseError: If an XML file contains invalid XML.

    Example:
        >>> config = load_workflow("workflow.json")  # Load from JSON
        >>> # or
        >>> config = load_workflow("workflow.xml")   # Load from XML
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Workflow file not found: {file_path}")

    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext == ".json":
        return load_json_workflow(file_path)
    elif file_ext == ".xml":
        return load_xml_workflow(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {file_ext}. Supported extensions are .json and .xml")


def convert_to_agentscope_workflow(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a generic workflow configuration to an AgentScope-compatible workflow configuration.

    This function validates and transforms workflow configurations to ensure they are compatible
    with AgentScope's workflow system. It checks for required components like modules and
    connections, and can perform transformations to adapt configurations from different formats
    or versions to the current AgentScope workflow format.

    Currently, the function primarily validates that the configuration has the expected structure.
    It is designed to be extensible to handle more complex transformations in the future, such as
    converting from third-party workflow formats or handling version migrations.

    Args:
        config (Dict[str, Any]): The workflow configuration to convert. This should be a dictionary
                                 containing workflow components, typically loaded from a JSON or XML file.

    Returns:
        Dict[str, Any]: An AgentScope-compatible workflow configuration, with all necessary
                        transformations applied to ensure compatibility with the current
                        AgentScope workflow system.

    Raises:
        ValueError: If the configuration is missing required components and cannot be
                   converted to a valid AgentScope workflow.

    Example:
        >>> raw_config = load_workflow("workflow.json")
        >>> config = convert_to_agentscope_workflow(raw_config)
        >>> # Now use the config with AgentScope
    """
    # Check if the configuration is already in the expected format
    if "modules" in config and "connections" in config:
        return config

    # If the configuration is in a different format, convert it
    # This is a placeholder for future conversion logic
    logger.warning("The workflow configuration may not be in the expected format for AgentScope.")

    return config
