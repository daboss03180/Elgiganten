import requests
from bs4 import BeautifulSoup

# --- We assume these functions exist in your other files ---
# You might need to adjust the import paths if your file structure is different.
from knowledge_base import lookup_policy, lookup_faq, fetch_recommendations


# --- Web Scraper Function ---
# Moved here from main.py to be used by the conversation manager.
def scrape_product_image_url(product_url: str) -> str | None:
    """
    Scrapes a product page to find the main product image URL.
    It looks for the 'og:image' meta tag which is standard and reliable.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(product_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        image_tag = soup.find('meta', property='og:image')

        if image_tag and image_tag.get('content'):
            return image_tag['content']

    except requests.RequestException as e:
        print(f"ERROR: Could not fetch product page {product_url}. Details: {e}")
    except Exception as e:
        print(f"ERROR: Could not parse page {product_url}. Details: {e}")

    return None


# --- Main Conversation Handler ---

async def handle_conversation(query: str, store_name: str) -> dict:
    """
    Processes the user's query and returns a structured response.
    This is the new "brain" of the chatbot.
    """
    query_lower = query.lower()

    # 1. Intent: Handle "Return" Policy
    if "return" in query_lower or "retur" in query_lower:
        print("Intent identified: Return Policy")
        policy_text = await lookup_policy("return")
        return {"text": policy_text, "products": []}

    # 2. Intent: Handle "Connect to Human"
    if "human" in query_lower or "agent" in query_lower or "person" in query_lower:
        print("Intent identified: Connect to Human")
        return {
            "text": "I understand. I am connecting you to a live agent now. Please wait a moment.",
            "products": []
        }

    # 3. Intent: Handle Product Recommendations
    if "recommend" in query_lower or "rekommendera" in query_lower or "product" in query_lower or "produkt" in query_lower:
        print("Intent identified: Product Recommendation")
        recommendations = await fetch_recommendations()  # Assumes this returns a list of product dicts

        if recommendations:
            # For simplicity, we'll just use the first recommendation
            product = recommendations[0]
            product_title = product.get("title")
            product_url = product.get("product_url")

            if product_title and product_url:
                # Scrape the product page for an image
                image_url = scrape_product_image_url(product_url)

                response_text = f"Absolut! Jag kan rekommendera {product_title}. Ta en titt här: {product_url}"

                product_card_data = {
                    "title": product_title,
                    "product_url": product_url,
                    "image_url": image_url if image_url else ""  # Send empty string if no image found
                }

                return {"text": response_text, "products": [product_card_data]}

        # Fallback if no recommendations are found
        return {"text": "I'm sorry, I couldn't find any specific recommendations for you at the moment.",
                "products": []}

    # 4. Default: Fallback to General FAQ
    print("Intent identified: General FAQ")
    faq_answer = await lookup_faq(query)
    return {"text": faq_answer, "products": []}
