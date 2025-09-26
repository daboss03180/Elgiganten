import os
import random
import httpx
from dotenv import load_dotenv

# --- Load Environment Variables & API Configuration ---
load_dotenv()
SHOPIFY_ADMIN_API_TOKEN = os.getenv("SHOPIFY_ADMIN_API_TOKEN")
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")
API_VERSION = "2024-07"

if not all([SHOPIFY_ADMIN_API_TOKEN, SHOPIFY_STORE_URL]):
    raise ValueError("A required Shopify environment variable is missing.")

ADMIN_API_HEADERS = {"X-Shopify-Access-Token": SHOPIFY_ADMIN_API_TOKEN, "Content-Type": "application/json"}

# --- Keyword Mapping for Policies ---
POLICY_KEYWORD_TO_TITLE_MAP = {
    "return": "Refund policy", "refund": "Refund policy", "privacy": "Privacy policy",
    "shipping": "Shipping", "delivery": "Shipping", "terms": "Terms of service", "contact": "Contact",
    "retur": "Refund policy", "återbetalning": "Refund policy", "integritet": "Privacy policy",
    "frakt": "Shipping", "leverans": "Shipping", "villkor": "Terms of service", "kontakt": "Contact",
}


# --- Core Functions ---
async def lookup_policy(query: str) -> str | None:
    api_url = f"{SHOPIFY_STORE_URL}/admin/api/{API_VERSION}/policies.json"
    target_title = next((title for keyword, title in POLICY_KEYWORD_TO_TITLE_MAP.items() if keyword in query.lower()),
                        None)
    if not target_title:
        return None
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, headers=ADMIN_API_HEADERS)
            response.raise_for_status()
            policies = response.json().get('policies', [])
            for policy in policies:
                if policy.get('title') == target_title:
                    return policy.get('body')
            return None
    except Exception as e:
        print(f"ERROR (lookup_policy): Failed to process Shopify policies: {repr(e)}")
        return None


# --- UPGRADED: Function to fetch product recommendations ---
async def fetch_recommendations() -> list:
    """
    Fetches active products from the Shopify store to use as recommendations.
    """
    api_url = f"{SHOPIFY_STORE_URL}/admin/api/{API_VERSION}/products.json?status=active&limit=10"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, headers=ADMIN_API_HEADERS)
            response.raise_for_status()
            products = response.json().get('products', [])

            recommendations = []
            for product in products:
                # Construct the product URL and get the image
                product_url = f"{SHOPIFY_STORE_URL}/products/{product.get('handle')}"
                image_url = product.get('image', {}).get('src') if product.get('image') else ""

                recommendations.append({
                    "name": product.get('title'),
                    "url": product_url,
                    "image_url": image_url
                })

            return recommendations
    except Exception as e:
        print(f"ERROR (fetch_recommendations): Failed to fetch Shopify products: {repr(e)}")
        return []


# --- Placeholder for FAQ ---
async def lookup_faq(question: str) -> str | None:
    return "This is a placeholder FAQ answer."