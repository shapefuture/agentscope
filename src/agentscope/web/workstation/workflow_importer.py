# -*- coding: utf-8 -*-
"""
Workflow importer module for AgentScope.

This module provides functionality to import workflow definitions from JSON or XML files
and convert them into AgentScope workflow configurations.
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

    Args:
        file_path (str): Path to the JSON file containing the workflow configuration.

    Returns:
        Dict[str, Any]: A dictionary containing the workflow configuration.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
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

    Args:
        file_path (str): Path to the XML file containing the workflow configuration.

    Returns:
        Dict[str, Any]: A dictionary containing the workflow configuration.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ET.ParseError: If the file contains invalid XML.
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
    Convert an XML element to a dictionary.

    Args:
        element (ET.Element): The XML element to convert.

    Returns:
        Dict[str, Any]: A dictionary representation of the XML element.
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

    Args:
        file_path (str): Path to the file containing the workflow configuration.

    Returns:
        Dict[str, Any]: A dictionary containing the workflow configuration.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file extension is not supported.
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

    This function handles any necessary transformations to make the imported workflow
    compatible with AgentScope's workflow system.

    Args:
        config (Dict[str, Any]): The workflow configuration to convert.

    Returns:
        Dict[str, Any]: An AgentScope-compatible workflow configuration.
    """
    # Check if the configuration is already in the expected format
    if "modules" in config and "connections" in config:
        return config

    # If the configuration is in a different format, convert it
    # This is a placeholder for future conversion logic
    logger.warning("The workflow configuration may not be in the expected format for AgentScope.")

    return config
