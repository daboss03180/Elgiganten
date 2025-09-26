import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
import requests

# --- Simplified Imports ---
# We only need the main conversation handler.
from conversation_manager import handle_conversation


# --- Pydantic Model for POST Request Body ---
class ChatRequest(BaseModel):
    query: str


# --- App Initialization ---
app = FastAPI()

# --- State ---
STORE_NAME = "V's Store"

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
        store_url = os.getenv("SHOPIFY_STORE_URL")
        admin_token = os.getenv("SHOPIFY_ADMIN_API_TOKEN")
        api_version = "2023-10"

        if not all([store_url, admin_token]):
            raise ValueError("Shopify environment variables are not fully set.")

        url = f"https://{store_url}/admin/api/{api_version}/shop.json"
        headers = {
            "X-Shopify-Access-Token": admin_token,
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        shop_data = response.json().get("shop", {})
        STORE_NAME = shop_data.get("name", "V's Store")
        print(f"Successfully fetched store name: {STORE_NAME}")

    except Exception as e:
        print(f"CRITICAL: Failed to fetch store name on startup. Using fallback. Error: {repr(e)}")
        STORE_NAME = "V's Store"


# --- API Endpoints ---

@app.get("/")
async def root():
    """Root endpoint for health checks."""
    return {"message": f"Welcome to the chatbot API for {STORE_NAME}. I am V."}


@app.post("/chat")
async def chat_with_v(request: ChatRequest):
    """
    Main chat endpoint. All conversation logic is now handled here.
    """
    query = request.query
    if not query:
        raise HTTPException(status_code=400, detail="Query in request body cannot be empty.")
    try:
        response_data = await handle_conversation(query, STORE_NAME)
        return {"response": response_data}
    except Exception as e:
        import traceback
        print(f"ERROR in /chat endpoint: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# --- Obsolete endpoints from the old version have been removed ---

# --- Main Execution Block ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)