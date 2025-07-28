import json
from typing import List
from langchain_openai import ChatOpenAI
from config.settings import settings
from tools import ALL_TOOLS
from models.api_models import VerifyConfigurationResponse, WaypointNode, WaypointConnection
from config.settings import get_logger

logger = get_logger(__name__)

class WaypointService():
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4", 
            temperature=0.1, 
            api_key=settings.OPENAI_API_KEY
        ).bind_tools(ALL_TOOLS)
    
    def verify_configuration(self, nodes: List[WaypointNode], connections: List[WaypointConnection]) -> VerifyConfigurationResponse:
        logger.info(nodes)
        logger.info(connections)
        
        if self._has_cycle(nodes, connections):
            return VerifyConfigurationResponse (
                success=False,
                message="Cycle detected in configuration"
            )
        
        try:
            llm_validation = self._validate_workflow_with_llm(nodes, connections)
            return llm_validation
        except Exception as e:
            return VerifyConfigurationResponse(
                success=False,
                message=f"LLM validation failed: {str(e)}"
            )
    
    def _has_cycle(self, nodes: List[WaypointNode], connections: List[WaypointConnection]) -> bool:
        """
        Detect cycles in the workflow graph using DFS.
        Returns True if a cycle is detected, False otherwise.
        """
        graph = {}
        node_ids = {node.id for node in nodes}
        
        for node in nodes:
            graph[node.id] = []
        
        for conn in connections:
            if conn.source_id in node_ids and conn.target_id in node_ids:
                graph[conn.source_id].append(conn.target_id)
        
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for neighbor in graph[node_id]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node in nodes:
            if node.id not in visited:
                if dfs(node.id):
                    return True
        
        return False
    
    def _validate_workflow_with_llm(self, nodes: List[WaypointNode], connections: List[WaypointConnection]) -> VerifyConfigurationResponse:        
        workflow_nodes = [f"- {node.tool_name}" for node in nodes]
        workflow_connections = [f"- {conn.source_tool_name} → {conn.target_tool_name}" for conn in connections]
        
        prompt = f"""
        You are a workflow validation expert with access to all available analysis tools. 

        Analyze this software analysis workflow configuration and determine if it makes logical sense based on your knowledge of the bound tools.

        USER'S WORKFLOW:
        Tools in workflow:
        {chr(10).join(workflow_nodes)}

        Connections (data flow):
        {chr(10).join(workflow_connections) if workflow_connections else "- No connections (isolated tools)"}

        Please evaluate based on the tool schemas you have access to:
        1. Do the tools flow in a logical order considering their inputs/outputs?
        2. Are there missing prerequisites (e.g., trying to create a pull request before performing analysis or applying fixes)?
        3. Does the workflow accomplish a coherent goal?
        4. Are there any incompatible tool sequences?
        5. Are tools being used appropriately for their intended purpose?

        DO NOT execute any tools - only analyze the workflow configuration.

        Respond with ONLY a JSON object in this format:
        {{
            "valid": true/false,
            "message": "User-friendly message about the workflow validity"
        }}
        """
        
        response = self.llm.invoke(prompt)
        response_text = response.content
        logger.info(response_text)
        
        try:
            result = json.loads(response_text)
            is_valid = result.get("valid", True)
            message = result.get("message", "Workflow validation completed")
            
            return VerifyConfigurationResponse(
                success=is_valid,
                message=message
            )
        except json.JSONDecodeError:
            return VerifyConfigurationResponse(
                success=False,
                message="LLM response parsing failed. Please try again"
            )

waypoint_service = WaypointService()
