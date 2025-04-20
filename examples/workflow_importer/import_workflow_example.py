# -*- coding: utf-8 -*-
"""
Example script demonstrating how to import workflows from JSON or XML files.

This script shows how to use the workflow importer to load workflow configurations
from either JSON or XML files and run them in AgentScope.
"""

import os
import sys
import argparse
from loguru import logger

# Add the parent directory to the path so we can import agentscope
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentscope.web.workstation.workflow_importer import load_workflow, convert_to_agentscope_workflow
from agentscope.web.workstation.workflow import start_workflow, compile_workflow


def main():
    """
    Parse command-line arguments and import the specified workflow file.
    """
    parser = argparse.ArgumentParser(description="AgentScope Workflow Importer Example")
    parser.add_argument(
        "workflow_file",
        type=str,
        help="Path to the workflow file (JSON or XML).",
    )
    parser.add_argument(
        "--compile",
        type=str,
        help="Compile the workflow to a Python file, e.g. main.py",
        default=None,
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run the workflow after importing",
        default=False,
    )
    
    args = parser.parse_args()
    workflow_file = args.workflow_file
    compile_file = args.compile
    run_workflow = args.run
    
    try:
        # Load the workflow configuration
        logger.info(f"Loading workflow from {workflow_file}")
        config = load_workflow(workflow_file)
        
        # Convert the configuration to AgentScope format if needed
        config = convert_to_agentscope_workflow(config)
        
        # Compile the workflow if requested
        if compile_file:
            logger.info(f"Compiling workflow to {compile_file}")
            compile_workflow(config, compile_file)
        
        # Run the workflow if requested
        if run_workflow:
            logger.info("Running workflow")
            start_workflow(config)
            
        logger.info("Workflow import completed successfully")
        
    except Exception as e:
        logger.error(f"Error importing workflow: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
