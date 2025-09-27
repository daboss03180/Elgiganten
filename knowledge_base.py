import os
import requests
from typing import List, Dict, Any, Optional

# --- Configuration from Environment Variables ---
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")
SHOPIFY_ADMIN_API_TOKEN = os.getenv("SHOPIFY_ADMIN_API_TOKEN")
API_VERSION = "2023-10"


# --- Helper to build headers for Shopify Admin API requests ---
def _get_admin_api_headers():
    """Returns the required headers for Shopify Admin API calls."""
    if not SHOPIFY_ADMIN_API_TOKEN:
        raise ValueError("SHOPIFY_ADMIN_API_TOKEN is not set in the environment.")
    return {
        "X-Shopify-Access-Token": SHOPIFY_ADMIN_API_TOKEN,
        "Content-Type": "application/json"
    }


# ==============================================================================
# UPDATED API-DRIVEN FUNCTIONS
# ==============================================================================

async def get_shopify_page_by_handle(topic: str) -> Optional[str]:
    """
    Fetches a policy page from Shopify.
    Instead of a fixed handle, it now searches for a page with the topic in its title.
    """
    if not SHOPIFY_STORE_URL:
        print("ERROR: SHOPIFY_STORE_URL is not set.")
        return None

    url = f"https://{SHOPIFY_STORE_URL}/admin/api/{API_VERSION}/pages.json"

    try:
        headers = _get_admin_api_headers()
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        pages = response.json().get("pages", [])

        # --- NEW: More robust search logic ---
        print(f"DEBUG: Searching for a page with '{topic}' in the title...")

        # Log all found page titles for easier debugging
        all_titles = [page.get('title', '').lower() for page in pages]
        print(f"DEBUG: Available page titles: {all_titles}")

        for page in pages:
            page_title = page.get("title", "").lower()
            if topic in page_title:
                print(f"DEBUG: Match found! Using page titled '{page.get('title')}'.")
                return page.get("body_html", "")

        print(f"WARN: No page found with '{topic}' in the title.")
        return None

    except requests.RequestException as e:
        print(f"ERROR: Failed to fetch Shopify pages. Details: {e}")
        return None
    except Exception as e:
        print(f"ERROR: An unexpected error occurred while fetching pages. {e}")
        return None


async def track_order_in_shopify(order_number: str) -> str:
    """
    Looks up an order in Shopify by its number and returns its fulfillment status.
    """
    if not SHOPIFY_STORE_URL:
        return "I'm sorry, my connection to the store is currently unavailable."

    url = f"https://{SHOPIFY_STORE_URL}/admin/api/{API_VERSION}/orders.json?name=#{order_number}&status=any"

    try:
        headers = _get_admin_api_headers()
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        orders = response.json().get("orders", [])
        if not orders:
            return f"I couldn't find any order with the number #{order_number}. Please double-check the number."

        order = orders[0]
        fulfillment_status = order.get("fulfillment_status")

        if fulfillment_status is None:
            return f"Order #{order_number} has been placed, but is not yet fulfilled."
        elif fulfillment_status == "fulfilled":
            return f"Great news! Order #{order_number} has been fulfilled and is on its way."
        elif fulfillment_status == "partial":
            return f"Good news! Part of your order #{order_number} has been shipped."
        else:
            return f"The current status for order #{order_number} is: {fulfillment_status}."

    except requests.RequestException as e:
        print(f"ERROR: Failed to track order in Shopify. Details: {e}")
        return "I'm having trouble accessing order information right now. Please try again in a moment."


async def fetch_shopify_recommendations() -> List[Dict[str, Any]]:
    """
    Fetches a few published products from Shopify to use as recommendations.
    """
    if not SHOPIFY_STORE_URL:
        print("ERROR: SHOPIFY_STORE_URL is not set.")
        return []

    url = f"https://{SHOPIFY_STORE_URL}/admin/api/{API_VERSION}/products.json?status=active&limit=3"

    try:
        headers = _get_admin_api_headers()
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        products_data = response.json().get("products", [])

        recommendations = []
        for prod in products_data:
            recommendations.append({
                "title": prod.get("title"),
                "product_url": f"https://{SHOPIFY_STORE_URL}/products/{prod.get('handle')}"
            })

        print(f"DEBUG: Fetched {len(recommendations)} products for recommendation.")
        return recommendations

    except requests.RequestException as e:
        print(f"ERROR: Failed to fetch Shopify products. Details: {e}")
        return []