"""
Firestore Tools for FitFuel Agent.
Hardcoded project ID: 'qwiklabs-gcp-04-58a387086d87'
"""

from typing import List, Dict, Any, Optional
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

PROJECT_ID = "qwiklabs-gcp-04-58a387086d87"

def _get_firestore_client() -> firestore.Client:
    """Returns a Firestore client initialized with hardcoded project ID."""
    return firestore.Client(project=PROJECT_ID)

def list_meals(category: Optional[str] = None, diet_type: Optional[str] = None, max_calories: Optional[int] = None) -> List[Dict[str, Any]]:
    """List and filter meals from the Firestore meals collection.

    Args:
        category: Optional category filter, e.g. 'Breakfast', 'Lunch', 'Dinner'.
        diet_type: Optional diet filter, e.g. 'Vegetarian', 'Vegan', 'Non-Vegetarian'.
        max_calories: Optional maximum calories threshold in kcal.

    Returns:
        A list of meal dictionaries with nutritional data and descriptions.
    """
    db = _get_firestore_client()
    query = db.collection("meals")
    
    if category:
        query = query.where(filter=FieldFilter("category", "==", category))
    if diet_type:
        query = query.where(filter=FieldFilter("diet_type", "==", diet_type))

    results = []
    for doc in query.stream():
        data = doc.to_dict()
        data["id"] = doc.id
        if max_calories is not None:
            if data.get("calories", 0) > max_calories:
                continue
        results.append(data)
    
    return results

def get_meal_by_id(meal_id: str) -> Dict[str, Any]:
    """Retrieve detailed nutritional and recipe info for a specific meal by ID.

    Args:
        meal_id: The document ID of the meal, e.g. 'quinoa-veggie-bowl'.

    Returns:
        The meal dictionary if found, or an error dictionary.
    """
    db = _get_firestore_client()
    doc_ref = db.collection("meals").document(meal_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        return {"error": f"Meal with id '{meal_id}' not found."}
    
    data = doc.to_dict()
    data["id"] = doc.id
    return data

def add_meal(
    name: str,
    category: str,
    calories: int,
    protein_g: float,
    carbs_g: float,
    fats_g: float,
    diet_type: str,
    description: str,
    prep_time_minutes: int = 15,
    meal_id: Optional[str] = None
) -> Dict[str, Any]:
    """Add a new wholesome meal or recipe to the Firestore meals catalog.

    Args:
        name: Name of the meal.
        category: 'Breakfast', 'Lunch', 'Dinner', or 'Snack'.
        calories: Total calorie count in kcal.
        protein_g: Protein in grams.
        carbs_g: Carbohydrates in grams.
        fats_g: Fats in grams.
        diet_type: 'Vegetarian', 'Vegan', 'Non-Vegetarian', etc.
        description: Short description or recipe instructions.
        prep_time_minutes: Preparation time in minutes.
        meal_id: Optional custom identifier. If not provided, one is generated from name.

    Returns:
        A dictionary with the creation status and document ID.
    """
    db = _get_firestore_client()
    if not meal_id:
        meal_id = name.lower().replace(" ", "-").replace("&", "and")
        meal_id = "".join(c for c in meal_id if c.isalnum() or c == "-")

    doc_data = {
        "name": name,
        "category": category,
        "calories": calories,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fats_g": fats_g,
        "diet_type": diet_type,
        "description": description,
        "prep_time_minutes": prep_time_minutes
    }

    doc_ref = db.collection("meals").document(meal_id)
    doc_ref.set(doc_data)
    
    return {
        "status": "success",
        "message": f"Successfully created meal '{name}' in Firestore.",
        "meal_id": meal_id,
        "data": doc_data
    }

import os
import urllib.request
import json

def lookup_barcode(barcode: str) -> Dict[str, Any]:
    """Look up nutrition facts for a packaged food item by its barcode using Open Food Facts.

    Args:
        barcode: The product barcode string, e.g. '3017620422003' (Nutella).

    Returns:
        A dictionary containing product name, brand, serving size, and nutrition facts per 100g.
    """
    clean_barcode = barcode.strip().replace(" ", "")
    url = f"https://world.openfoodfacts.org/api/v2/product/{clean_barcode}.json"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "FitFuelApp - Agent - Version 1.0"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            if response.status != 200:
                return {"error": f"Failed to fetch barcode {clean_barcode}. Status code: {response.status}"}
            raw_bytes = response.read()
            if response.info().get("Content-Encoding") == "gzip" or raw_bytes[:2] == b"\x1f\x8b":
                import gzip
                raw_bytes = gzip.decompress(raw_bytes)
            payload = json.loads(raw_bytes.decode("utf-8"))
            
        if payload.get("status") != 1:
            return {
                "error": f"Product with barcode '{clean_barcode}' not found in Open Food Facts database.",
                "found": False
            }
            
        product = payload.get("product", {})
        nutriments = product.get("nutriments", {})
        
        return {
            "found": True,
            "barcode": clean_barcode,
            "product_name": product.get("product_name") or product.get("product_name_en") or "Unknown Product",
            "brands": product.get("brands", "Generic"),
            "serving_size": product.get("serving_size", "100g"),
            "nutrition_per_100g": {
                "calories_kcal": nutriments.get("energy-kcal_100g") or nutriments.get("energy-kcal"),
                "protein_g": nutriments.get("proteins_100g"),
                "carbs_g": nutriments.get("carbohydrates_100g"),
                "fats_g": nutriments.get("fat_100g"),
                "sugars_g": nutriments.get("sugars_100g"),
                "fiber_g": nutriments.get("fiber_100g"),
                "sodium_mg": nutriments.get("sodium_100g", 0) * 1000 if nutriments.get("sodium_100g") is not None else None
            }
        }
    except Exception as e:
        return {"error": f"Failed to retrieve barcode data: {str(e)}"}
