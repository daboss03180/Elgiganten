import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel

# --- Load Environment Variables ---
load_dotenv()

# --- Import Actual Functions from Your Modules ---
# These replace the placeholder functions.
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
        STORE_NAME = "V's Store" # Fallback name

# --- API Endpoints ---

@app.get("/")
async def root():
    """Root endpoint for health checks."""
    return {"message": f"Welcome to the chatbot API for {STORE_NAME}. I am V."}

# --- FIXED ENDPOINT ---
@app.post("/chat")
async def chat_with_v(request: ChatRequest):
    """
    Main chat endpoint. Accepts POST requests with a JSON body.
    e.g., {"query": "Hello world"}
    """
    query = request.query
    if not query:
        raise HTTPException(status_code=400, detail="Query in request body cannot be empty.")
    try:
        response = await handle_conversation(query, STORE_NAME)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/search")
async def search(query: str):
    """Searches for products using the Shopify Storefront API."""
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
    """Tracks an order using the Shopify Admin API."""
    if not order_id:
        raise HTTPException(status_code=400, detail="Order ID cannot be empty.")
    try:
        order_status = await track_order_admin(order_id)
        return {"status": order_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track order: {str(e)}")


@app.get("/policy")
async def get_policy(topic: str):
    """Retrieves information about a specific store policy."""
    if not topic:
        raise HTTPException(status_code=400, detail="Policy topic cannot be empty.")
    try:
        policy_info = await lookup_policy(topic)
        return {"topic": topic, "details": policy_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get policy: {str(e)}")


@app.get("/faq")
async def get_faq(question: str):
    """Retrieves an answer from the FAQ knowledge base."""
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    try:
        faq_answer = await lookup_faq(question)
        return {"question": question, "answer": faq_answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get FAQ: {str(e)}")


@app.get("/recommendations")
async def get_recommendations():
    """Provides product recommendations."""
    try:
        recommendations = await fetch_recommendations()
        return {"recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch recommendations: {str(e)}")


# --- Main Execution Block ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)