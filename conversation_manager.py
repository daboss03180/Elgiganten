import os
import re
import requests
from typing import Dict, Any

# --- Placeholder for your AI/Claude API module ---
# You will need to create this file and function.
# It's responsible for general chitchat.
# from claude_api import get_conversational_response, answer_question_from_text

# --- Placeholder for your Knowledge Base (now an API wrapper) ---
# This file should now contain the functions that call the Shopify API.
from knowledge_base import get_shopify_page_by_handle, track_order_in_shopify, fetch_shopify_recommendations

# --- Configuration from Environment Variables ---
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")
SHOPIFY_ADMIN_API_TOKEN = os.getenv("SHOPIFY_ADMIN_API_TOKEN")

# --- Keyword Definitions for Intent Routing ---
GREETING_KEYWORDS = {"hej", "hi", "hello", "hey", "tja", "good morning", "good evening"}
ORDER_TRACKING_KEYWORDS = {"track", "order", "spåra", "beställning", "where is my order", "status"}
POLICY_KEYWORDS = {"policy", "return", "retur", "shipping", "frakt", "policy", "terms", "rules", "villkor"}
RECOMMENDATION_KEYWORDS = {"recommend", "rekommendera", "suggest", "product", "produkt", "looking for"}


# ==============================================================================
# AI-Powered Helper Functions (Placeholders - YOU MUST IMPLEMENT THESE)
# ==============================================================================

async def get_conversational_response(query: str) -> str:
    """
    Placeholder: Calls an AI like Claude for general, friendly conversation.
    This should NOT be used for store-specific information.
    """
    # Example: return await claude_api.get_chat_response(query)
    print("DEBUG: Routing to general conversational AI.")
    # This is a temporary, friendly fallback until you connect a real AI
    if "how are you" in query:
        return "I'm doing great, thanks for asking! How can I help you find something amazing today?"
    return "That's an interesting question! While I ponder that, is there anything I can help you find in the store?"


async def answer_question_from_text(document_text: str, question: str) -> str:
    """
    Placeholder: Uses an AI to read a long document and extract a precise answer.
    """
    # Example: return await claude_api.answer_from_context(document_text, question)
    print(f"DEBUG: Using AI to answer '{question}' from a document.")
    # This is a temporary, simple fallback. A real AI would be much more powerful.
    # For now, we return the first few sentences as a "summary".
    summary = ". ".join(document_text.split('.')[:2])
    return f"According to our Policy, {summary}."


# ==============================================================================
# Utility Functions
# ==============================================================================

def clean_html(raw_html: str) -> str:
    """A simple regex to strip HTML tags from text."""
    clean_text = re.sub('<[^<]+?>', '', raw_html)
    return clean_text.strip()


async def scrape_product_image_url(product_url: str) -> str | None:
    """Scrapes a product page to find the main product image URL."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(product_url, headers=headers, timeout=10)
        response.raise_for_status()
        # Using regex for simplicity, but BeautifulSoup is more robust
        match = re.search(r'<meta property="og:image" content="([^"]+)"', response.text)
        if match:
            return match.group(1)
    except requests.RequestException as e:
        print(f"ERROR: Could not fetch product page {product_url}. Details: {e}")
    return None


# ==============================================================================
# Main Conversation Handler
# ==============================================================================

async def handle_conversation(query: str, store_name: str) -> Dict[str, Any]:
    """
    The new, smart, and human-like conversation brain.
    It identifies user intent and delegates to the appropriate function.
    """
    query_lower = query.lower().strip()

    # --- 1. Intent: Greeting ---
    if any(keyword in query_lower for keyword in GREETING_KEYWORDS):
        return {"text": "Hello! I'm V, your personal shopping assistant. What can I help you find today?",
                "products": []}

    # --- 2. Intent: Order Tracking ---
    if any(keyword in query_lower for keyword in ORDER_TRACKING_KEYWORDS):
        # A real implementation would extract the order number from the query
        order_number_match = re.search(r'(\d{4,})', query)  # Simple regex for a number
        if order_number_match:
            order_id = order_number_match.group(1)
            status = await track_order_in_shopify(order_id)
            return {"text": status, "products": []}
        return {"text": "I can certainly help with that! What is your order number?", "products": []}

    # --- 3. Intent: Policy Question ---
    if any(keyword in query_lower for keyword in POLICY_KEYWORDS):
        # Determine which policy page to fetch (e.g., 'return-policy')
        handle = "return-policy"  # Default or determined from keywords
        if "shipping" in query_lower or "frakt" in query_lower:
            handle = "shipping-policy"

        page_content_html = await get_shopify_page_by_handle(handle)
        if page_content_html:
            clean_text = clean_html(page_content_html)
            # Use AI to read the text and find the specific answer
            answer = await answer_question_from_text(clean_text, query)
            return {"text": answer, "products": []}
        else:
            return {"text": f"I couldn't find the specific details for our {handle.replace('-', ' ')}.", "products": []}

    # --- 4. Intent: Product Recommendation / Sales ---
    if any(keyword in query_lower for keyword in RECOMMENDATION_KEYWORDS):
        recommendations = await fetch_shopify_recommendations()  # This should call the Shopify API
        if recommendations:
            product = recommendations[0]  # Pick the first one
            product_title = product.get("title")
            product_url = product.get("product_url")
            image_url = await scrape_product_image_url(product_url)

            response_text = f"I have a great suggestion for you! The {product_title} is very popular. It might be just what you're looking for."
            product_card = {
                "title": product_title,
                "product_url": product_url,
                "image_url": image_url or ""
            }
            return {"text": response_text, "products": [product_card]}

    # --- 5. Default: Fallback to General Conversation AI ---
    # If no other intent is matched, let the conversational AI handle it
    try:
        ai_response = await get_conversational_response(query)
        return {"text": ai_response, "products": []}
    except Exception as e:
        print(f"ERROR: General AI conversation failed. {e}")
        return {
            "text": "I'm sorry, I don't have information on that right now. Could I help with a product recommendation or a policy question instead?",
            "products": []}
