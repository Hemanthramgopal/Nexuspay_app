from app.services.catalog_service import CatalogService
from app.agents.agent import BuyerAgent

print('CATALOG_CHECK', CatalogService().get_product('laptop').model_dump())

agent = BuyerAgent()
print('AGENT_TEST_START')
print(agent.process_user_intent('buy a laptop and include a charger').model_dump())
