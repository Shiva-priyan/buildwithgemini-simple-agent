#!/usr/bin/env python3
"""
Seed script to populate Firestore collection with wholesome meals and exercises.
Hardcoded project ID: 'qwiklabs-gcp-04-58a387086d87'
"""

import sys
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-58a387086d87"

SAMPLE_MEALS = [
    {
        "id": "quinoa-veggie-bowl",
        "name": "Mediterranean Quinoa & Veggie Bowl",
        "category": "Lunch",
        "calories": 450,
        "protein_g": 16.0,
        "carbs_g": 62.0,
        "fats_g": 14.0,
        "diet_type": "Vegetarian",
        "prep_time_minutes": 20,
        "description": "Fluffy quinoa tossed with cherry tomatoes, cucumbers, kalamata olives, feta, and extra virgin olive oil."
    },
    {
        "id": "grilled-salmon-asparagus",
        "name": "Grilled Wild Salmon with Asparagus",
        "category": "Dinner",
        "calories": 520,
        "protein_g": 42.0,
        "carbs_g": 12.0,
        "fats_g": 32.0,
        "diet_type": "Non-Vegetarian",
        "prep_time_minutes": 25,
        "description": "Wild-caught salmon fillet seasoned with lemon, garlic, and fresh herbs paired with roasted tender asparagus."
    },
    {
        "id": "paneer-tikka-salad",
        "name": "Spiced Paneer Tikka Salad",
        "category": "Lunch",
        "calories": 380,
        "protein_g": 22.0,
        "carbs_g": 18.0,
        "fats_g": 24.0,
        "diet_type": "Vegetarian",
        "prep_time_minutes": 15,
        "description": "Tandoori-spiced grilled cottage cheese cubes served over mixed greens with mint-yogurt dressing."
    },
    {
        "id": "overnight-protein-oats",
        "name": "Overnight Chia & Protein Berry Oats",
        "category": "Breakfast",
        "calories": 390,
        "protein_g": 25.0,
        "carbs_g": 48.0,
        "fats_g": 9.0,
        "diet_type": "Vegetarian",
        "prep_time_minutes": 5,
        "description": "Rolled oats soaked in almond milk, mixed with whey or plant protein, chia seeds, and topped with fresh blueberries."
    },
    {
        "id": "tofu-stir-fry",
        "name": "Ginger Sesame Tofu & Edamame Stir-Fry",
        "category": "Dinner",
        "calories": 420,
        "protein_g": 26.0,
        "carbs_g": 35.0,
        "fats_g": 18.0,
        "diet_type": "Vegan",
        "prep_time_minutes": 20,
        "description": "Crispy pan-seared firm tofu and shelled edamame wok-tossed with broccoli, bell peppers, and low-sodium tamari."
    }
]

def seed():
    print(f"Connecting to Firestore for project: {PROJECT_ID}...")
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection("meals")

    for meal in SAMPLE_MEALS:
        meal_id = meal["id"]
        doc_data = {k: v for k, v in meal.items() if k != "id"}
        collection_ref.document(meal_id).set(doc_data)
        print(f"✓ Seeded meal: {meal['name']} ({meal_id})")

    print(f"Successfully seeded {len(SAMPLE_MEALS)} items into 'meals' collection.")

if __name__ == "__main__":
    seed()
