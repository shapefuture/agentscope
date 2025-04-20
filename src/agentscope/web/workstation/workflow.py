# -*- coding: utf-8 -*-
""" Workflow"""
import argparse
import json
import os

from loguru import logger
from agentscope.web.workstation.workflow_dag import build_dag
from agentscope.web.workstation.workflow_importer import load_workflow, convert_to_agentscope_workflow


def load_config(config_path: str) -> dict:
    """Load a workflow configuration file (JSON or XML).

    Args:
        config_path: A string path to the configuration file (JSON or XML).

    Returns:
        A dictionary containing the loaded configuration.
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

    Args:
        config: A dictionary containing the application configuration.

    This function will initialize and launch the application.
    """
    logger.info("Launching...")

    dag = build_dag(config)
    dag.run()

    logger.info("Finished.")


def compile_workflow(config: dict, compiled_filename: str = "main.py") -> None:
    """Generates Python code based on the given configuration.

    Args:
        config: A dictionary containing the application configuration.
        compiled_filename: complied file name.

    """
    logger.info("Compiling...")

    dag = build_dag(config)
    dag.compile(compiled_filename)

    logger.info("Finished.")


def main() -> None:
    """Parse command-line arguments and launch the application workflow.

    This function sets up command-line argument parsing and checks if a
    configuration file path is provided. If the configuration file is
    found, it proceeds to load it and start the workflow.

    If no configuration file is provided, a FileNotFoundError is raised.
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
