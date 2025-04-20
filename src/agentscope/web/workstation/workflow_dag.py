# -*- coding: utf-8 -*-
"""
AgentScope Workstation DAG (Directed Acyclic Graph) Running Engine.

This module provides the core functionality for building, running, and compiling
workflow DAGs in AgentScope. It defines the ASDiGraph class, which extends NetworkX's
DiGraph to support AgentScope-specific workflow operations.

The module handles:
1. Building DAGs from workflow configurations
2. Executing workflow DAGs by running nodes in topological order
3. Compiling workflow DAGs to standalone Python scripts
4. Managing dependencies between workflow nodes

The workflow DAG represents the structure of a workflow, with nodes for modules
and edges for connections between modules. Each node in the DAG corresponds to
a specific operation or component in the workflow, such as a model, agent, or service.

Typical usage:
    config = load_workflow("workflow.json")
    dag = build_dag(config)
    dag.run()  # Execute the workflow
    # or
    dag.compile("output.py")  # Compile to a Python script
"""
import copy
from typing import Any
from loguru import logger

import agentscope
from agentscope.web.workstation.workflow_node import (
    NODE_NAME_MAPPING,
    WorkflowNodeType,
    DEFAULT_FLOW_VAR,
)
from agentscope.web.workstation.workflow_utils import (
    is_callable_expression,
    kwarg_converter,
)

try:
    import networkx as nx
except ImportError:
    nx = None


def remove_duplicates_from_end(lst: list) -> list:
    """
    Remove duplicate elements from a list while preserving the order of first occurrence.

    This function processes the list in reverse order, keeping track of seen elements
    to remove duplicates. The result is a list with only the first occurrence of each
    element preserved, which is useful for removing duplicate import statements while
    maintaining their original order.

    Args:
        lst (list): The input list that may contain duplicate elements.

    Returns:
        list: A new list with duplicates removed, preserving the order of first occurrence.

    Example:
        >>> remove_duplicates_from_end(['import a', 'import b', 'import a'])
        ['import a', 'import b']
    """
    seen = set()
    result = []
    for item in reversed(lst):
        if item not in seen:
            seen.add(item)
            result.append(item)
    result.reverse()
    return result


class ASDiGraph(nx.DiGraph):
    """
    A directed acyclic graph (DAG) class for AgentScope workflows.

    This class extends NetworkX's DiGraph to provide specialized functionality for
    AgentScope workflows. It supports building, running, and compiling workflow DAGs,
    with nodes representing workflow components (models, agents, services, etc.) and
    edges representing connections between components.

    The class manages the execution of workflow nodes in topological order, ensuring
    that dependencies are satisfied before a node is executed. It also provides
    functionality for compiling workflows to standalone Python scripts.

    Attributes:
        nodes_not_in_graph (set): A set of node IDs that are excluded from the computation
                                 graph, typically nodes that are part of a group or
                                 are otherwise handled separately.
        imports (list): A list of import statements needed for the compiled Python script.
        inits (list): A list of initialization statements for the compiled Python script.
        execs (list): A list of execution statements for the compiled Python script.
    """

    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        """
        Initialize the ASDiGraph instance.

        This constructor initializes the ASDiGraph by calling the parent class constructor
        and setting up the necessary attributes for workflow management. It prepares lists
        for imports, initializations, and execution statements that will be used when
        compiling the workflow to a Python script.

        Args:
            *args: Variable length argument list passed to the parent class constructor.
            **kwargs: Arbitrary keyword arguments passed to the parent class constructor.
        """
        super().__init__(*args, **kwargs)
        self.nodes_not_in_graph = set()

        # Prepare the header of the file with necessary imports and any
        # global definitions
        self.imports = [
            "import agentscope",
        ]

        self.inits = [
            'agentscope.init(logger_level="DEBUG")',
            f"{DEFAULT_FLOW_VAR} = None",
        ]

        self.execs = ["\n"]

    def run(self) -> None:
        """
        Execute the workflow by running each node in topological order.

        This method executes the workflow represented by the DAG. It first initializes
        AgentScope, then performs a topological sort of the nodes to determine the
        execution order. Each node is executed in sequence, with the outputs from its
        predecessors passed as inputs.

        The method handles the flow of data between nodes, ensuring that each node
        receives the appropriate inputs from its predecessors. Currently, the method
        only supports passing the output of the first predecessor as input to a node.

        Returns:
            None: This method does not return a value, but executes the workflow.

        Raises:
            ValueError: If a node has too many predecessors or if there are other issues
                      with the workflow execution.
            Exception: Any exceptions that might occur during workflow execution.
        """
        agentscope.init(logger_level="DEBUG")
        sorted_nodes = list(nx.topological_sort(self))
        sorted_nodes = [
            node_id
            for node_id in sorted_nodes
            if node_id not in self.nodes_not_in_graph
        ]
        logger.info(f"sorted_nodes: {sorted_nodes}")
        logger.info(f"nodes_not_in_graph: {self.nodes_not_in_graph}")

        # Cache output
        values = {}

        # Run with predecessors outputs
        for node_id in sorted_nodes:
            inputs = [
                values[predecessor]
                for predecessor in self.predecessors(node_id)
            ]
            if not inputs:
                values[node_id] = self.exec_node(node_id)
            elif len(inputs):
                # Note: only support exec with the first predecessor now
                values[node_id] = self.exec_node(node_id, inputs[0])
            else:
                raise ValueError("Too many predecessors!")

    def compile(  # type: ignore[no-untyped-def]
        self,
        compiled_filename: str = "",
        **kwargs,
    ) -> str:
        """
        Compile the workflow DAG to a standalone Python script.

        This method generates a Python script that can execute the workflow represented
        by the DAG. The script includes all necessary imports, initialization code, and
        the workflow execution logic. The generated code can be saved to a file and run
        independently of AgentScope.

        The method performs a topological sort of the nodes to determine the execution
        order, then generates code for each node in sequence. It also attempts to format
        the generated code using the 'black' code formatter if available.

        Args:
            compiled_filename (str, optional): The name of the output Python file.
                                             If empty, the code is returned but not saved.
                                             Defaults to "".
            **kwargs: Additional keyword arguments to pass to AgentScope initialization
                     in the generated code.

        Returns:
            str: The generated Python code as a string.

        Raises:
            IOError: If the output file cannot be written.
            Exception: Any exceptions that might occur during compilation.
        """

        def format_python_code(code: str) -> str:
            try:
                from black import FileMode, format_str

                logger.debug("Formatting Code with black...")
                return format_str(code, mode=FileMode())
            except Exception:
                return code

        self.inits[
            0
        ] = f'agentscope.init(logger_level="DEBUG", {kwarg_converter(kwargs)})'

        sorted_nodes = list(nx.topological_sort(self))
        sorted_nodes = [
            node_id
            for node_id in sorted_nodes
            if node_id not in self.nodes_not_in_graph
        ]

        for node_id in sorted_nodes:
            node = self.nodes[node_id]
            self.execs.append(node["compile_dict"]["execs"])

        header = "\n".join(self.imports)

        # Remove duplicate import
        new_imports = remove_duplicates_from_end(header.split("\n"))
        header = "\n".join(new_imports)
        body = "\n    ".join(self.inits + self.execs)

        main_body = f"def main():\n    {body}"

        # Combine header and body to form the full script
        script = (
            "# -*- coding: utf-8 -*-\n"
            f"{header}\n\n\n{main_body}\n\nif __name__ == "
            f"'__main__':\n    main()\n"
        )

        formatted_code = format_python_code(script)

        if len(compiled_filename) > 0:
            # Write the script to file
            with open(compiled_filename, "w", encoding="utf-8") as file:
                file.write(formatted_code)
        return formatted_code

    # pylint: disable=R0912
    def add_as_node(
        self,
        node_id: str,
        node_info: dict,
        config: dict,
    ) -> Any:
        """
        Add a node to the graph based on provided node information and configuration.

        This method creates and adds a node to the DAG based on the provided information.
        It handles the creation of the appropriate node type (model, agent, message, etc.),
        initializes the node with the specified parameters, and adds it to the graph.

        The method also handles dependencies between nodes, ensuring that dependent nodes
        are added to the graph before the current node. It recursively adds any dependent
        nodes that are not already in the graph.

        For nodes that are part of a group (e.g., nodes within a pipeline), the method
        excludes them from the main DAG execution by adding them to the nodes_not_in_graph set.

        Args:
            node_id (str): The identifier for the node being added. This should be a unique
                          string that identifies the node within the workflow.
            node_info (dict): A dictionary containing information about the node, including
                            its type, parameters, and other metadata.
            config (dict): Configuration information for the entire workflow, used to resolve
                         dependencies between nodes.

        Returns:
            Any: The computation object associated with the added node, which can be called
                to execute the node's computation.

        Raises:
            NotImplementedError: If the node type is not supported.
            ValueError: If there are issues with the node configuration or dependencies.
            Exception: Any other exceptions that might occur during node creation.
        """
        node_cls = NODE_NAME_MAPPING[node_info.get("name", "")]
        if node_cls.node_type not in [
            WorkflowNodeType.MODEL,
            WorkflowNodeType.AGENT,
            WorkflowNodeType.MESSAGE,
            WorkflowNodeType.PIPELINE,
            WorkflowNodeType.COPY,
            WorkflowNodeType.SERVICE,
        ]:
            raise NotImplementedError(node_cls)

        if self.has_node(node_id):
            return self.nodes[node_id]["opt"]

        # Init dep nodes
        deps = [str(n) for n in node_info.get("data", {}).get("elements", [])]

        # Exclude for dag when in a Group
        if node_cls.node_type != WorkflowNodeType.COPY:
            self.nodes_not_in_graph = self.nodes_not_in_graph.union(set(deps))

        dep_opts = []
        for dep_node_id in deps:
            if not self.has_node(dep_node_id):
                dep_node_info = config[dep_node_id]
                self.add_as_node(dep_node_id, dep_node_info, config)
            dep_opts.append(self.nodes[dep_node_id]["opt"])

        node_opt = node_cls(
            node_id=node_id,
            opt_kwargs=node_info["data"].get("args", {}),
            source_kwargs=node_info["data"].get("source", {}),
            dep_opts=dep_opts,
        )

        # Add build compiled python code
        compile_dict = node_opt.compile()

        self.add_node(
            node_id,
            opt=node_opt,
            compile_dict=compile_dict,
            **node_info,
        )

        # Insert compile information to imports and inits
        self.imports.append(compile_dict["imports"])

        if node_cls.node_type == WorkflowNodeType.MODEL:
            self.inits.insert(1, compile_dict["inits"])
        else:
            self.inits.append(compile_dict["inits"])
        return node_opt

    def exec_node(self, node_id: str, x_in: Any = None) -> Any:
        """
        Execute the computation associated with a given node in the graph.

        This method executes the computation for a specific node in the workflow DAG.
        It retrieves the node's computation object from the graph and calls it with
        the provided input. The method logs the input and output values for debugging
        purposes.

        The node's computation is expected to be a callable object that takes an input
        and returns an output. The specific behavior depends on the type of node being
        executed (model, agent, message, etc.).

        Args:
            node_id (str): The identifier of the node whose computation is to be executed.
                          This should be a valid node ID in the graph.
            x_in (Any, optional): The input to the node's computation. This is typically
                                the output from a predecessor node. Defaults to None.

        Returns:
            Any: The output of the node's computation, which can be passed as input to
                successor nodes.

        Raises:
            KeyError: If the specified node_id is not found in the graph.
            Exception: Any exceptions that might occur during the node's computation.
        """
        logger.debug(
            f"\nnode_id: {node_id}\nin_values:{x_in}",
        )
        opt = self.nodes[node_id]["opt"]
        out_values = opt(x_in)
        logger.debug(
            f"\nnode_id: {node_id}\nout_values:{out_values}",
        )
        return out_values


def sanitize_node_data(raw_info: dict) -> dict:
    """
    Clean and validate node data, evaluating callable expressions where necessary.

    This function processes raw node information from a workflow configuration,
    performing several transformations to prepare it for use in building a workflow DAG:

    1. It creates a deep copy of the original data to avoid modifying the input
    2. It preserves the original arguments in a 'source' field for reference
    3. It removes empty arguments that might cause issues during execution
    4. It evaluates any callable expressions provided as string literals

    Callable expressions are strings that represent Python functions or objects that
    can be called. These are evaluated using eval() to convert them from strings to
    actual callable objects.

    Args:
        raw_info (dict): The raw node information dictionary from the workflow configuration.
                        This may contain callable expressions as strings and empty arguments.

    Returns:
        dict: The sanitized node information with empty arguments removed and callable
             expressions evaluated. The original arguments are preserved in the 'source' field.

    Raises:
        Exception: Any exceptions that might occur during evaluation of callable expressions.
    """

    copied_info = copy.deepcopy(raw_info)
    raw_info["data"]["source"] = copy.deepcopy(
        copied_info["data"].get(
            "args",
            {},
        ),
    )
    for key, value in copied_info["data"].get("args", {}).items():
        if value == "":
            raw_info["data"]["args"].pop(key)
            raw_info["data"]["source"].pop(key)
        elif is_callable_expression(value):
            raw_info["data"]["args"][key] = eval(value)
    return raw_info


def build_dag(config: dict) -> ASDiGraph:
    """
    Construct a Directed Acyclic Graph (DAG) from a workflow configuration.

    This function is the main entry point for building a workflow DAG from a configuration
    dictionary. It processes the configuration, creates nodes for each component, and
    establishes connections between them according to the workflow structure.

    The function follows these steps:
    1. Handle special cases for configurations from different sources (e.g., HTML JSON files)
    2. Sanitize node data to prepare it for use in the DAG
    3. Add model nodes first, as they may be dependencies for other nodes
    4. Add non-model nodes (agents, messages, pipelines, etc.)
    5. Add edges between nodes based on the connections in the configuration
    6. Verify that the resulting graph is acyclic

    Args:
        config (dict): The workflow configuration to build the graph from. This should
                      contain information about nodes (modules) and their connections.
                      The format should match the AgentScope workflow configuration format,
                      which can be loaded from JSON or XML files.

    Returns:
        ASDiGraph: The constructed directed acyclic graph representing the workflow.
                  This graph can be executed using its run() method or compiled to a
                  Python script using its compile() method.

    Raises:
        ValueError: If the resulting graph is not acyclic, indicating that there are
                  circular dependencies in the workflow.
        KeyError: If required keys are missing from the configuration.
        NotImplementedError: If unsupported node types are encountered.
        Exception: Any other exceptions that might occur during DAG construction.
    """
    dag = ASDiGraph()

    # for html json file,
    # retrieve the contents of config["drawflow"]["Home"]["data"],
    # and remove the node whose class is "welcome"
    if (
        "drawflow" in config
        and "Home" in config["drawflow"]
        and "data" in config["drawflow"]["Home"]
    ):
        config = config["drawflow"]["Home"]["data"]

        config = {
            k: v
            for k, v in config.items()
            if not ("class" in v and v["class"] == "welcome")
        }

    for node_id, node_info in config.items():
        config[node_id] = sanitize_node_data(node_info)

    # Add and init model nodes first
    for node_id, node_info in config.items():
        if (
            NODE_NAME_MAPPING[node_info["name"]].node_type
            == WorkflowNodeType.MODEL
        ):
            dag.add_as_node(node_id, node_info, config)

    # Add and init non-model nodes
    for node_id, node_info in config.items():
        if (
            NODE_NAME_MAPPING[node_info["name"]].node_type
            != WorkflowNodeType.MODEL
        ):
            dag.add_as_node(node_id, node_info, config)

    # Add edges
    for node_id, node_info in config.items():
        outputs = node_info.get("outputs", {})
        for output_key, output_val in outputs.items():
            connections = output_val.get("connections", [])
            for conn in connections:
                target_node_id = conn.get("node")
                # Here it is assumed that the output of the connection is
                # only connected to one of the inputs. If there are more
                # complex connections, modify the logic accordingly
                dag.add_edge(node_id, target_node_id, output_key=output_key)

    # Check if the graph is a DAG
    if not nx.is_directed_acyclic_graph(dag):
        raise ValueError("The provided configuration does not form a DAG.")

    return dag
