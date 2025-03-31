from typing import Dict, List, Any, Optional


class BaseAgent:
    """Base agent for determining browsing actions."""

    def __init__(self):
        pass

    def determine_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        pass


class BrowsingAgent(BaseAgent):
    """Agent specialized in web navigation decisions."""

    def __init__(self):
        super().__init__()

    def decide_navigation(
        self, current_page: Dict[str, Any], goal: str
    ) -> Dict[str, str]:
        pass

    def extract_relevant_info(self, page_content: str, query: str) -> Dict[str, Any]:
        pass

    def determine_search_query(self, goal: str) -> str:
        pass


class InteractionAgent(BaseAgent):
    """Agent specialized in determining page interactions."""

    def __init__(self):
        super().__init__()

    def decide_form_input(
        self, form_fields: List[Dict], context: Dict[str, Any]
    ) -> Dict[str, str]:
        pass

    def determine_click_action(
        self, page_elements: List[Dict], goal: str
    ) -> Optional[Dict[str, Any]]:
        pass

    def evaluate_interaction_success(
        self, before_state: Dict, after_state: Dict
    ) -> bool:
        pass
