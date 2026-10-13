from app.tools import list_meals, get_meal_by_id, add_meal, PROJECT_ID

def test_hardcoded_project_id():
    assert PROJECT_ID == "qwiklabs-gcp-04-58a387086d87"

def test_list_and_get_meals():
    meals = list_meals()
    assert isinstance(meals, list)
    assert len(meals) >= 5
    
    first_id = meals[0]["id"]
    meal = get_meal_by_id(first_id)
    assert meal["id"] == first_id
    assert "calories" in meal
    assert "protein_g" in meal
    assert "name" in meal

def test_add_meal():
    res = add_meal(
        name="Greek Yogurt Protein Parfait",
        category="Breakfast",
        calories=310,
        protein_g=28.0,
        carbs_g=32.0,
        fats_g=4.0,
        diet_type="Vegetarian",
        description="Nonfat Greek yogurt layered with raw honey, walnuts, and strawberries."
    )
    assert res["status"] == "success"
    meal = get_meal_by_id(res["meal_id"])
    assert meal["name"] == "Greek Yogurt Protein Parfait"
    assert meal["calories"] == 310

from app.tools import lookup_barcode

def test_lookup_barcode():
    result = lookup_barcode("3017620422003")
    assert result.get("found") is True
    assert "Nutella" in result.get("product_name")
    nutrition = result.get("nutrition_per_100g")
    assert nutrition.get("calories_kcal") is not None
    assert nutrition.get("protein_g") is not None

from app.agent import root_agent
from google.adk.code_executors import AgentEngineSandboxCodeExecutor

def test_code_executor_configured():
    assert root_agent.code_executor is not None
    assert isinstance(root_agent.code_executor, AgentEngineSandboxCodeExecutor)
    assert root_agent.code_executor.agent_engine_resource_name == "projects/747232054876/locations/us-central1/reasoningEngines/7976376592253321216"

from app.app_utils import services
from google.adk.tools import preload_memory, load_memory

def test_memory_setup():
    assert preload_memory in root_agent.tools
    assert load_memory in root_agent.tools
    assert root_agent.after_agent_callback is not None
    assert "allerg" in root_agent.instruction.lower()
    mem_svc = services.get_memory_service()
    assert mem_svc is not None

