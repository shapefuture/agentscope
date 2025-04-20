# -*- coding: utf-8 -*-
"""
Test script for the workflow importer.

This script tests the workflow importer by loading both JSON and XML workflow files
and verifying that they are correctly converted to AgentScope-compatible format.
"""

import os
import sys
import json
from loguru import logger

# Add the parent directory to the path so we can import agentscope
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agentscope.web.workstation.workflow_importer import load_workflow, convert_to_agentscope_workflow


def test_json_workflow():
    """Test loading a JSON workflow file."""
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
    """Test loading an XML workflow file."""
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
    """Compare the JSON and XML workflow configurations."""
    logger.info("Comparing JSON and XML workflow configurations")
    
    # Compare the number of modules
    assert len(json_config["modules"]) == len(xml_config["modules"]), \
        f"Different number of modules: JSON={len(json_config['modules'])}, XML={len(xml_config['modules'])}"
    
    # Compare the number of connections
    assert len(json_config["connections"]) == len(xml_config["connections"]), \
        f"Different number of connections: JSON={len(json_config['connections'])}, XML={len(xml_config['connections'])}"
    
    logger.info("Workflow comparison passed")


def main():
    """Run the tests."""
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
