import os
import re
import requests
from typing import Dict, Any

# --- Placeholder for your AI/Claude API module ---
# from claude_api import get_conversational_response, answer_question_from_text

# --- Updated Import ---
from knowledge_base import get_shopify_page_by_handle, track_order_in_shopify, fetch_shopify_recommendations

# --- Configuration ---
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")

# --- Keyword Definitions ---
GREETING_KEYWORDS = {"hej", "hi", "hello", "hey", "tja", "good morning", "good evening"}
ORDER_TRACKING_KEYWORDS = {"track", "order", "spåra", "beställning", "where is my order", "status"}
POLICY_KEYWORDS = {"policy", "return", "retur", "shipping", "frakt", "policy", "terms", "rules", "villkor"}
RECOMMENDATION_KEYWORDS = {"recommend", "rekommendera", "suggest", "product", "produkt", "looking for"}


# ... (AI Placeholders and Utility functions remain the same) ...
async def get_conversational_response(query: str) -> str:
    print("DEBUG: Routing to general conversational AI.")
    if "how are you" in query:
        return "I'm doing great, thanks for asking! How can I help you find something amazing today?"
    return "That's an interesting question! While I ponder that, is there anything I can help you find in the store?"


async def answer_question_from_text(document_text: str, question: str) -> str:
    print(f"DEBUG: Using AI to answer '{question}' from a document.")
    summary = ". ".join(document_text.split('.')[:2])
    return f"According to our Policy, {summary}."


def clean_html(raw_html: str) -> str:
    clean_text = re.sub('<[^<]+?>', '', raw_html)
    return clean_text.strip()


async def scrape_product_image_url(product_url: str) -> str | None:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(product_url, headers=headers, timeout=10)
        response.raise_for_status()
        match = re.search(r'<meta property="og:image" content="([^"]+)"', response.text)
        if match:
            return match.group(1)
    except requests.RequestException as e:
        print(f"ERROR: Could not fetch product page {product_url}. Details: {e}")
    return None


# ==========================================================

async def handle_conversation(query: str, store_name: str) -> Dict[str, Any]:
    query_lower = query.lower().strip()

    # --- 1. Intent: Greeting ---
    if any(keyword in query_lower for keyword in GREETING_KEYWORDS):
        return {"text": "Hello! I'm V, your personal shopping assistant. What can I help you find today?",
                "products": []}

    # --- 2. Intent: Order Tracking ---
    if any(keyword in query_lower for keyword in ORDER_TRACKING_KEYWORDS):
        order_number_match = re.search(r'(\d{4,})', query)
        if order_number_match:
            order_id = order_number_match.group(1)
            status = await track_order_in_shopify(order_id)
            return {"text": status, "products": []}
        return {"text": "I can certainly help with that! What is your order number?", "products": []}

    # --- 3. Intent: Policy Question (UPDATED) ---
    if any(keyword in query_lower for keyword in POLICY_KEYWORDS):
        # Determine which topic to search for
        topic_to_find = "return"  # Default
        if "shipping" in query_lower or "frakt" in query_lower:
            topic_to_find = "shipping"

        # This now searches by topic title, not a fixed handle
        page_content_html = await get_shopify_page_by_handle(topic_to_find)
        if page_content_html:
            clean_text = clean_html(page_content_html)
            answer = await answer_question_from_text(clean_text, query)
            return {"text": answer, "products": []}
        else:
            return {"text": f"I couldn't find the specific details for our {topic_to_find} policy.", "products": []}

    # --- 4. Intent: Product Recommendation / Sales ---
    if any(keyword in query_lower for keyword in RECOMMENDATION_KEYWORDS):
        recommendations = await fetch_shopify_recommendations()
        if recommendations:
            product = recommendations[0]
            product_title = product.get("title")
            product_url = product.get("product_url")
            image_url = await scrape_product_image_url(product_url)

            response_text = f"I have a great suggestion for you! The {product_title} is very popular. It might be just what you're looking for."
            product_card = {"title": product_title, "product_url": product_url, "image_url": image_url or ""}
            return {"text": response_text, "products": [product_card]}

    # --- 5. Default: Fallback to General Conversation AI ---
    try:
        ai_response = await get_conversational_response(query)
        return {"text": ai_response, "products": []}
    except Exception as e:
        print(f"ERROR: General AI conversation failed. {e}")
        return {
            "text": "I'm sorry, I don't have information on that right now. Could I help with a product recommendation or a policy question instead?",
            "products": []}
