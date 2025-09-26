import os
import re
import random
import httpx
import anthropic
from dotenv import load_dotenv
from knowledge_base import lookup_policy, fetch_recommendations, POLICY_KEYWORD_TO_TITLE_MAP

# --- Load Environment Variables & API Clients ---
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SHOPIFY_ADMIN_API_TOKEN = os.getenv("SHOPIFY_ADMIN_API_TOKEN")
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")

if not all([ANTHROPIC_API_KEY, SHOPIFY_ADMIN_API_TOKEN, SHOPIFY_STORE_URL]):
    raise ValueError("CRITICAL: One or more environment variables are missing.")

claude_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
shopify_admin_headers = {
    "X-Shopify-Access-Token": SHOPIFY_ADMIN_API_TOKEN,
    "Content-Type": "application/json"
}


# --- Functions for specific intents ---

async def answer_question_from_text(question: str, policy_text: str) -> str:
    """
    Uses Claude to read a policy text and extract the answer to a specific question,
    with custom phrasing.
    """
    cleaned_text = re.sub('<[^<]+?>', ' ', policy_text).strip()

    # --- MODIFIED SYSTEM PROMPT ---
    # This new prompt instructs the AI to use your desired phrasing.
    system_prompt = """
    You are a helpful customer service agent. You have been given a store policy document to answer a user's question.
    Your task is to answer the user's question based *only* on the provided text.
    - Start your answer with the phrase "According to our policy,".
    - Be concise and directly answer the question.
    - If the information is not in the text, respond with "I couldn't find specific information about that in our policy document."
    """

    user_prompt = f"Here is the policy text:\n---\n{cleaned_text}\n---\nNow, please answer this question: \"{question}\""

    try:
        response = await claude_client.messages.create(
            model="claude-3-haiku-20240307", max_tokens=300, system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        return response.content[0].text
    except Exception as e:
        print(f"ERROR (answer_question_from_text): {repr(e)}")
        return "I encountered an error while trying to understand the policy text."


async def track_order_on_shopify(order_number: str) -> str:
    clean_order_number = order_number.lstrip('#')
    api_url = f"{SHOPIFY_STORE_URL}/admin/api/2024-07/orders.json?name={clean_order_number}&status=any"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, headers=shopify_admin_headers)
            response.raise_for_status()
            orders = response.json().get('orders', [])
            if not orders: return f"Jag kunde inte hitta någon order med nummer {order_number}."
            order = orders[0]
            status = order.get('fulfillment_status', 'unfulfilled') or 'unfulfilled'
            if status == 'fulfilled':
                tracking_url = order.get('fulfillments', [{}])[0].get('tracking_url')
                return f"Din order #{clean_order_number} har skickats! Spåra den här: {tracking_url}" if tracking_url else f"Din order #{clean_order_number} har skickats, men spårningsinformation saknas."
            return f"Din order #{clean_order_number} har tagits emot och behandlas."
    except Exception as e:
        print(f"ERROR (track_order_on_shopify): {repr(e)}")
        return "Ett fel uppstod vid spårning av din order."


# --- Main Conversation Handler (with Recommendation Logic) ---
async def handle_conversation(query: str, store_name: str) -> dict:
    query_lower = query.lower()

    # Intent 1: Order Tracking
    order_match = re.search(r'#?(\d{4,})', query)
    if order_match and any(kw in query_lower for kw in ["order", "beställning", "spåra", "track"]):
        return {"text": await track_order_on_shopify(order_match.group(0)), "products": []}

    # Intent 2: Policy Question
    policy_keywords = POLICY_KEYWORD_TO_TITLE_MAP.keys()
    if any(kw in query_lower for kw in policy_keywords):
        policy_html = await lookup_policy(query_lower)
        if policy_html:
            return {"text": await answer_question_from_text(query, policy_html), "products": []}

    # Intent 3: Product Recommendation
    recommendation_keywords = ["recommend", "rekommendera", "product", "produkt", "suggest", "föreslå", "popular",
                               "populär"]
    if any(kw in query_lower for kw in recommendation_keywords):
        all_products = await fetch_recommendations()
        if all_products:
            recommended_product = random.choice(all_products)
            product_name = recommended_product['name']
            product_url = recommended_product['url']
            text_response = f"Absolut! Jag kan rekommendera {product_name}. Ta en titt här: {product_url}"
            return {"text": text_response, "products": [recommended_product]}
        else:
            return {"text": "Jag kunde tyvärr inte hitta några produkter att rekommendera just nu.", "products": []}

    # Fallback: General Conversation
    try:
        system_prompt = f"Du är 'V', en AI-assistent för butiken '{store_name}'. Svara kort och hjälpsamt."
        response = await claude_client.messages.create(model="claude-3-haiku-20240307", max_tokens=250,
                                                       system=system_prompt,
                                                       messages=[{"role": "user", "content": query}])
        return {"text": response.content[0].text, "products": []}
    except Exception as e:
        print(f"ERROR (Claude API): {repr(e)}")
        return {"text": "Jag har lite tekniska problem just nu, men vårt team jobbar på det.", "products": []}
