# -*- coding: utf-8 -*-
"""
AgentScope Workflow Module

This module provides functionality for loading, running, and compiling AgentScope workflows.
It serves as the main entry point for working with workflow configurations, supporting both
JSON and XML workflow definition formats through the workflow_importer module.

The module includes functions for:
1. Loading workflow configurations from files
2. Starting workflow execution
3. Compiling workflows to standalone Python scripts
4. Command-line interface for workflow operations

Typical usage:
    # Load and run a workflow
    config = load_config("workflow.json")
    start_workflow(config)

    # Or compile a workflow to a Python script
    compile_workflow(config, "output.py")
"""
import argparse
import json
import os

from loguru import logger
from agentscope.web.workstation.workflow_dag import build_dag
from agentscope.web.workstation.workflow_importer import load_workflow, convert_to_agentscope_workflow


def load_config(config_path: str) -> dict:
    """Load a workflow configuration file (JSON or XML).

    This function serves as a wrapper around the workflow importer functionality,
    providing a simple interface for loading workflow configurations from files.
    It handles both JSON and XML formats through the workflow_importer module,
    and ensures the loaded configuration is compatible with AgentScope's workflow system.

    The function includes error handling to provide clear error messages when loading fails.

    Args:
        config_path (str): A string path to the configuration file (JSON or XML).
                          This should be an absolute or relative path to a valid workflow file.

    Returns:
        dict: A dictionary containing the loaded configuration, structured according to
              AgentScope's workflow format with modules, connections, and optional metadata.

    Raises:
        FileNotFoundError: If the specified file does not exist or cannot be accessed.
        ValueError: If the file extension is not supported or the configuration is invalid.
        Exception: Any other exceptions that might occur during loading or conversion.

    Example:
        >>> config = load_config("workflow.json")
        >>> # Now use the config with start_workflow or compile_workflow
    """
    try:
        # Use the workflow importer to load the file based on its extension
        config = load_workflow(config_path)

        # Convert the configuration to AgentScope format if needed
        config = convert_to_agentscope_workflow(config)

        return config
    except Exception as e:
        logger.error(f"Failed to load configuration file: {e}")
        raise


def start_workflow(config: dict) -> None:
    """Start the application workflow based on the given configuration.

    This function takes a workflow configuration dictionary and executes the workflow
    by building a directed acyclic graph (DAG) and running it. The DAG represents the
    workflow structure, with nodes for modules and edges for connections between modules.

    The function logs the start and completion of the workflow execution, providing
    feedback on the workflow's progress.

    Args:
        config (dict): A dictionary containing the workflow configuration, with modules,
                      connections, and optional metadata. This should be a configuration
                      that has been loaded and validated, typically by the load_config function.

    Returns:
        None: This function does not return a value, but executes the workflow defined
              by the configuration.

    Raises:
        ValueError: If the configuration is invalid or cannot be used to build a DAG.
        Exception: Any exceptions that might occur during workflow execution.

    Example:
        >>> config = load_config("workflow.json")
        >>> start_workflow(config)  # Execute the workflow
    """
    logger.info("Launching...")

    dag = build_dag(config)
    dag.run()

    logger.info("Finished.")


def compile_workflow(config: dict, compiled_filename: str = "main.py") -> None:
    """Generates a standalone Python script based on the given workflow configuration.

    This function takes a workflow configuration dictionary and compiles it into a Python
    script that can be executed independently. The compiled script includes all necessary
    imports, initialization code, and the workflow execution logic.

    The function logs the start and completion of the compilation process, providing
    feedback on the compilation's progress.

    Args:
        config (dict): A dictionary containing the workflow configuration, with modules,
                      connections, and optional metadata. This should be a configuration
                      that has been loaded and validated, typically by the load_config function.
        compiled_filename (str, optional): The name of the output Python file. Defaults to "main.py".
                                          This should be a valid filename with a .py extension.

    Returns:
        None: This function does not return a value, but writes the compiled Python script
              to the specified file.

    Raises:
        ValueError: If the configuration is invalid or cannot be used to build a DAG.
        IOError: If the output file cannot be written.
        Exception: Any exceptions that might occur during compilation.

    Example:
        >>> config = load_config("workflow.json")
        >>> compile_workflow(config, "my_workflow.py")  # Compile to a Python script
    """
    logger.info("Compiling...")

    dag = build_dag(config)
    dag.compile(compiled_filename)

    logger.info("Finished.")


def main() -> None:
    """Parse command-line arguments and launch the application workflow.

    This function provides a command-line interface for working with AgentScope workflows.
    It sets up argument parsing to handle workflow file paths and compilation options,
    then loads and processes the workflow according to the provided arguments.

    The function supports two main operations:
    1. Running a workflow directly from a configuration file
    2. Compiling a workflow to a standalone Python script

    When compiling a workflow, the function checks if the output file already exists
    and prompts the user for confirmation before overwriting it.

    Args:
        None: This function does not take any arguments, but reads from command-line arguments.

    Returns:
        None: This function does not return a value, but either runs a workflow or
              compiles it to a Python script based on the command-line arguments.

    Raises:
        FileNotFoundError: If no configuration file path is provided or the specified file
                          does not exist.
        FileExistsError: If the output file for compilation already exists and the user
                        chooses not to overwrite it.
        Exception: Any exceptions that might occur during loading, running, or compiling.

    Command-line Usage:
        # Run a workflow
        python workflow.py path/to/workflow.json

        # Compile a workflow to a Python script
        python workflow.py path/to/workflow.json --compile output.py
    """
    parser = argparse.ArgumentParser(description="AgentScope Launcher")
    parser.add_argument(
        "cfg",
        type=str,
        help="Path to the config file (JSON or XML).",
        nargs="?",
    )
    parser.add_argument(
        "--compile",
        type=str,
        help="Compile the workflow to a Python file, e.g. main.py",
        default=False,
        nargs="?",
        const="",
    )
    args = parser.parse_args()
    cfg_path = args.cfg
    compiled_filename = args.compile

    if cfg_path:
        config = load_config(cfg_path)
        if not compiled_filename:
            start_workflow(config)
        else:
            if os.path.exists(compiled_filename):
                while True:
                    user_input = input(
                        f"File 【{compiled_filename}】already exists, are you "
                        f"sure to overwrite? (yes/no)",
                    )
                    if user_input.lower() in ["no", "n", "false"]:
                        raise FileExistsError(compiled_filename)

                    if user_input.lower() in ["", "yes", "y", "true"]:
                        logger.warning(f"Overwrite 【{compiled_filename}】!")
                        break

                    logger.info("Invalid input.")
            compile_workflow(config, compiled_filename)
    else:
        raise FileNotFoundError("Please provide config file.")


if __name__ == "__main__":
    main()
