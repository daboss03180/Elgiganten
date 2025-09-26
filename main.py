import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup

# --- Load Environment Variables ---
load_dotenv()

# --- Import Actual Functions from Your Modules ---
# These replace the placeholder functions.
# We assume handle_conversation will now be updated to return a dict
# and use the new scraping function.
from shopify_api import get_store_name_admin, search_products_storefront, track_order_admin
from knowledge_base import lookup_policy, lookup_faq, fetch_recommendations
from conversation_manager import handle_conversation


# --- Pydantic Model for POST Request Body ---
class ChatRequest(BaseModel):
    query: str


# --- App Initialization ---
app = FastAPI()

# --- State and Constants ---
STORE_NAME = "V's Store"
CONVERSATIONAL_KEYWORDS = ["retur", "öppettider", "return", "hours", "policy", "fråga"]

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- NEW: Web Scraping Function ---
def scrape_product_image_url(product_url: str) -> str | None:
    """
    Scrapes a product page to find the main product image URL.
    It specifically looks for the 'og:image' meta tag which is reliable.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(product_url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the 'og:image' meta tag, which is a standard for sharing images
        image_tag = soup.find('meta', property='og:image')

        if image_tag and image_tag.get('content'):
            return image_tag['content']

    except requests.RequestException as e:
        print(f"Error fetching product page {product_url}: {e}")
    except Exception as e:
        print(f"Error parsing page {product_url}: {e}")

    return None


# --- Startup Event ---
@app.on_event("startup")
async def startup_event():
    """On startup, fetch the store name from the Shopify Admin API."""
    global STORE_NAME
    try:
        STORE_NAME = await get_store_name_admin()
        print(f"Successfully fetched store name: {STORE_NAME}")
    except Exception as e:
        print(f"CRITICAL: Failed to fetch store name on startup. Error: {repr(e)}")
        STORE_NAME = "V's Store"  # Fallback name


# --- API Endpoints ---

@app.get("/")
async def root():
    """Root endpoint for health checks."""
    return {"message": f"Welcome to the chatbot API for {STORE_NAME}. I am V."}


# --- UPDATED CHAT ENDPOINT ---
@app.post("/chat")
async def chat_with_v(request: ChatRequest):
    """
    Main chat endpoint. Handles conversation and now expects a structured response
    that might include product data.
    """
    query = request.query
    if not query:
        raise HTTPException(status_code=400, detail="Query in request body cannot be empty.")
    try:
        # We now expect handle_conversation to return a dictionary.
        # It should be responsible for calling scrape_product_image_url when needed.
        response_data = await handle_conversation(query, STORE_NAME)

        # --- IMPORTANT ---
        # Your `handle_conversation` function must now be modified to do something like this:
        # if is_product_recommendation:
        #     # ... find product_title and product_url ...
        #     image_url = scrape_product_image_url(product_url)
        #     return {
        #         "text": f"Absolut! Jag kan rekommendera {product_title}. Ta en titt här: {product_url}",
        #         "products": [{
        #             "title": product_title,
        #             "product_url": product_url,
        #             "image_url": image_url
        #         }]
        #     }
        # else:
        #     # ... handle other questions ...
        #     return {"text": "Some other answer", "products": []}

        return {"response": response_data}

    except Exception as e:
        # Log the full error for debugging
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# --- Other endpoints remain the same ---

@app.get("/search")
async def search(query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")
    if any(keyword in query.lower() for keyword in CONVERSATIONAL_KEYWORDS):
        return {
            "message": "It looks like you're asking a question. Try using the /chat endpoint for general conversation or policy questions!",
            "results": []
        }
    try:
        products = await search_products_storefront(query)
        if not products:
            return {"message": "No products found matching your search.", "results": []}
        return {"results": products}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search for products: {str(e)}")


@app.get("/track_order")
async def track_order(order_id: str):
    if not order_id:
        raise HTTPException(status_code=400, detail="Order ID cannot be empty.")
    try:
        order_status = await track_order_admin(order_id)
        return {"status": order_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track order: {str(e)}")


@app.get("/policy")
async def get_policy(topic: str):
    if not topic:
        raise HTTPException(status_code=400, detail="Policy topic cannot be empty.")
    try:
        policy_info = await lookup_policy(topic)
        return {"topic": topic, "details": policy_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get policy: {str(e)}")


@app.get("/faq")
async def get_faq(question: str):
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    try:
        faq_answer = await lookup_faq(question)
        return {"question": question, "answer": faq_answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get FAQ: {str(e)}")


@app.get("/recommendations")
async def get_recommendations():
    try:
        recommendations = await fetch_recommendations()
        return {"recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch recommendations: {str(e)}")


# --- Main Execution Block ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)