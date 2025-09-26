import os
import httpx
from dotenv import load_dotenv

# --- Load Environment Variables & API Configuration ---
load_dotenv()

SHOPIFY_ADMIN_API_TOKEN = os.getenv("SHOPIFY_ADMIN_API_TOKEN")
SHOPIFY_STOREFRONT_API_TOKEN = os.getenv("SHOPIFY_STOREFRONT_API_TOKEN")
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")
API_VERSION = "2024-07"  # Using a fixed API version for stability

# --- Validate Environment Variables ---
if not all([SHOPIFY_ADMIN_API_TOKEN, SHOPIFY_STOREFRONT_API_TOKEN, SHOPIFY_STORE_URL]):
    raise ValueError("A required Shopify environment variable is missing. Check your .env file.")

# --- API Headers ---
ADMIN_API_HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_ADMIN_API_TOKEN,
    "Content-Type": "application/json"
}
STOREFRONT_API_HEADERS = {
    "X-Shopify-Storefront-Access-Token": SHOPIFY_STOREFRONT_API_TOKEN,
    "Content-Type": "application/json"
}


# --- Internal Helper Functions ---

def _format_product_data(node: dict) -> dict:
    """Creates a consistent product object for the frontend."""
    image_edge = node.get('images', {}).get('edges', [{}])[0]
    image = image_edge.get('node', {})

    # Safely access nested price data
    price = "N/A"
    if 'priceRange' in node and 'minVariantPrice' in node['priceRange']:
        price_info = node['priceRange']['minVariantPrice']
        price = f"{price_info.get('amount', '0.0')} {price_info.get('currencyCode', '')}"

    return {
        "id": node.get('id'),
        "title": node.get('title'),
        "price": price,
        "image": image.get('originalSrc'),
        "url": f"{SHOPIFY_STORE_URL}/products/{node.get('handle')}"
    }


# --- Admin API Functions ---

async def get_store_name_admin() -> str:
    """Fetches the store's name using the Admin API."""
    api_url = f"{SHOPIFY_STORE_URL}/admin/api/{API_VERSION}/shop.json"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(api_url, headers=ADMIN_API_HEADERS)
            response.raise_for_status()
            shop_data = response.json().get('shop', {})
            return shop_data.get('name', "Unknown Store")
        except httpx.HTTPStatusError as e:
            # Using repr() for safe error logging
            print(f"ERROR: Failed to fetch store name from Admin API. Status: {repr(e)}")
            return "Fallback Store Name"
        except Exception as e:
            print(f"ERROR: An unexpected error occurred fetching store name: {repr(e)}")
            return "Fallback Store Name"


async def track_order_admin(order_id: str) -> dict:
    """
    Fetches order status for a given order ID/name using the Admin API.
    Returns a dictionary with status information.
    """
    clean_order_id = order_id.lstrip('#')
    api_url = f"{SHOPIFY_STORE_URL}/admin/api/{API_VERSION}/orders.json?name={clean_order_id}&status=any"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(api_url, headers=ADMIN_API_HEADERS)
            response.raise_for_status()
            orders = response.json().get('orders', [])

            if not orders:
                return {"error": f"Order {order_id} not found."}

            order = orders[0]
            status = order.get('fulfillment_status') or 'unfulfilled'

            return {
                "order_number": order.get('name'),
                "fulfillment_status": status,
                "tracking_url": order.get('fulfillments', [{}])[0].get(
                    'tracking_url') if status == 'fulfilled' else None
            }
        except httpx.HTTPStatusError as e:
            # Using repr() for safe error logging
            print(f"ERROR: Failed to track order from Admin API. Status: {repr(e)}")
            return {"error": "Could not connect to the order system."}
        except Exception as e:
            # Using repr() for safe error logging
            print(f"ERROR: An unexpected error occurred tracking order: {repr(e)}")
            return {"error": "An unexpected error occurred."}


# --- Storefront API Functions ---

async def search_products_storefront(query: str) -> list:
    """
    Searches for products using the Storefront API (GraphQL) and limits to 3 results.
    """
    api_url = f"{SHOPIFY_STORE_URL}/api/{API_VERSION}/graphql.json"

    graphql_query = {
        "query": """
        query searchProducts($query: String!) {
          products(first: 3, query: $query) {
            edges {
              node {
                id
                title
                handle
                priceRange {
                  minVariantPrice {
                    amount
                    currencyCode
                  }
                }
                images(first: 1) {
                  edges {
                    node {
                      originalSrc
                      altText
                    }
                  }
                }
              }
            }
          }
        }
        """,
        "variables": {"query": query}
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(api_url, headers=STOREFRONT_API_HEADERS, json=graphql_query)
            response.raise_for_status()
            data = response.json()

            products = []
            for edge in data.get('data', {}).get('products', {}).get('edges', []):
                node = edge.get('node', {})
                products.append(_format_product_data(node))
            return products
        except httpx.HTTPStatusError as e:
            # Using repr() for safe error logging
            print(f"ERROR: Failed to search products from Storefront API. Status: {repr(e)}")
            return []
        except Exception as e:
            # Using repr() for safe error logging
            print(f"ERROR: An unexpected error occurred searching products: {repr(e)}")
            return []