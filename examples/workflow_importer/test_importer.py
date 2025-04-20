# -*- coding: utf-8 -*-
"""
Test script for the workflow importer.

This script tests the workflow importer by loading both JSON and XML workflow files
and verifying that they are correctly converted to AgentScope-compatible format.

The tests verify:
1. Loading workflow configurations from JSON files
2. Loading workflow configurations from XML files
3. Converting configurations to AgentScope-compatible format
4. Comparing JSON and XML workflow configurations for consistency

This script serves as both a test suite for the workflow importer functionality
and a demonstration of how to use the importer in different scenarios.

Usage:
    python test_importer.py

The script will output detailed logs of the test process and results.
If all tests pass, it will exit with a success message.
If any test fails, it will exit with an error message and a non-zero exit code.
"""

import os
import sys
import json
from loguru import logger

# Add the parent directory to the path so we can import agentscope
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agentscope.web.workstation.workflow_importer import load_workflow, convert_to_agentscope_workflow


def test_json_workflow():
    """
    Test loading a JSON workflow file and converting it to AgentScope format.

    This function tests the workflow importer's ability to load a JSON workflow file
    and convert it to an AgentScope-compatible format. It verifies that the loaded
    configuration has the expected structure and components.

    The test checks:
    - That the configuration contains modules and connections
    - That the expected number of modules are present
    - That the expected connections between modules are present

    Returns:
        dict: The loaded and converted workflow configuration for further testing.

    Raises:
        AssertionError: If any of the verification checks fail.
        Exception: If any other error occurs during loading or conversion.
    """
    json_file = os.path.join(os.path.dirname(__file__), 'workflow_example.json')

    logger.info(f"Testing JSON workflow import from {json_file}")

    # Load the JSON workflow
    config = load_workflow(json_file)

    # Convert to AgentScope format
    config = convert_to_agentscope_workflow(config)

    # Verify the configuration
    assert "modules" in config, "Modules not found in configuration"
    assert "connections" in config, "Connections not found in configuration"

    # Verify modules
    assert len(config["modules"]) == 4, f"Expected 4 modules, got {len(config['modules'])}"

    # Verify connections
    assert "1" in config["connections"], "Connection from module 1 not found"
    assert "2" in config["connections"], "Connection from module 2 not found"
    assert "3" in config["connections"], "Connection from module 3 not found"

    logger.info("JSON workflow import test passed")
    return config


def test_xml_workflow():
    """
    Test loading an XML workflow file and converting it to AgentScope format.

    This function tests the workflow importer's ability to load an XML workflow file,
    parse its structure, and convert it to an AgentScope-compatible format. It verifies
    that the loaded configuration has the expected structure and components.

    The test checks:
    - That the configuration contains modules and connections
    - That the expected number of modules are present
    - That the expected number of connections are present

    Returns:
        dict: The loaded and converted workflow configuration for further testing.

    Raises:
        AssertionError: If any of the verification checks fail.
        Exception: If any other error occurs during loading or conversion.
    """
    xml_file = os.path.join(os.path.dirname(__file__), 'workflow_example.xml')

    logger.info(f"Testing XML workflow import from {xml_file}")

    # Load the XML workflow
    config = load_workflow(xml_file)

    # Convert to AgentScope format
    config = convert_to_agentscope_workflow(config)

    # Verify the configuration
    assert "modules" in config, "Modules not found in configuration"
    assert "connections" in config, "Connections not found in configuration"

    # Verify modules
    assert len(config["modules"]) == 4, f"Expected 4 modules, got {len(config['modules'])}"

    # Verify connections
    assert len(config["connections"]) == 3, f"Expected 3 connections, got {len(config['connections'])}"

    logger.info("XML workflow import test passed")
    return config


def compare_workflows(json_config, xml_config):
    """
    Compare the JSON and XML workflow configurations for consistency.

    This function verifies that workflow configurations loaded from different file formats
    (JSON and XML) are consistent with each other. It checks that both configurations have
    the same number of modules and connections, ensuring that the workflow importer
    produces equivalent results regardless of the input format.

    Args:
        json_config (dict): The workflow configuration loaded from a JSON file.
        xml_config (dict): The workflow configuration loaded from an XML file.

    Raises:
        AssertionError: If the configurations are not consistent with each other.

    Note:
        This function only checks for structural consistency (number of modules and connections).
        It does not perform a deep comparison of the configuration contents.
    """
    logger.info("Comparing JSON and XML workflow configurations")

    # Compare the number of modules
    assert len(json_config["modules"]) == len(xml_config["modules"]), \
        f"Different number of modules: JSON={len(json_config['modules'])}, XML={len(xml_config['modules'])}"

    # Compare the number of connections
    assert len(json_config["connections"]) == len(xml_config["connections"]), \
        f"Different number of connections: JSON={len(json_config['connections'])}, XML={len(xml_config['connections'])}"

    logger.info("Workflow comparison passed")


def main():
    """
    Run all tests for the workflow importer.

    This function orchestrates the execution of all test functions in this script.
    It runs each test in sequence, collects the results, and reports the overall
    test status. If any test fails, the function will exit with a non-zero status code.

    The function includes error handling to provide clear error messages when tests fail,
    making it easier to diagnose and fix issues with the workflow importer.

    Returns:
        None: This function does not return a value, but exits with a status code
              indicating success (0) or failure (1).

    Raises:
        SystemExit: If any test fails, the function will exit with a non-zero status code.
    """
    try:
        # Test JSON workflow
        json_config = test_json_workflow()

        # Test XML workflow
        xml_config = test_xml_workflow()

        # Compare the workflows
        compare_workflows(json_config, xml_config)

        logger.info("All tests passed!")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
