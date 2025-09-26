# This file contains the "knowledge" for the chatbot.
# For a real-world application, this might connect to a database,
# a CMS, or a more advanced knowledge retrieval system.

async def lookup_policy(topic: str) -> str:
    """
    Looks up a store policy. Instead of returning raw HTML,
    it now returns a clean, concise summary.
    """
    topic_lower = topic.lower()

    if topic_lower == "return":
        # This is the new, short and clean summary.
        return (
            "You have 30 days from the date you received your item to request a return. "
            "To be eligible, the item must be in the same condition you received it, "
            "unworn or unused, with tags, and in its original packaging. "
            "You will also need the receipt or proof of purchase."
        )
    else:
        return "I can't find information on that specific policy. I can help with the 'return' policy."


async def lookup_faq(question: str) -> str:
    """
    Looks up a frequent question. This is a simplified fallback.
    """
    question_lower = question.lower()

    if "shipping" in question_lower or "leverans" in question_lower:
        return "We ship to all of Scandinavia. Standard shipping usually takes 3-5 business days."
    elif "hours" in question_lower or "öppettider" in question_lower:
        return "Our online store is always open! Customer service is available from 9 AM to 5 PM, Monday to Friday."
    else:
        return "I'm not sure how to answer that. Could you try rephrasing? You can also ask to 'connect to a human agent'."


async def fetch_recommendations() -> list:
    """
    Provides a list of products to recommend.
    In a real application, this could be based on user data or best-sellers.
    """
    # This is a placeholder list.
    return [
        {
            "title": "Electrolux Flaskhylla M4RHBH02",
            "product_url": "https://qhyrfq-y1.myshopify.com/products/electrolux-flaskhylla-m4rhbh02"
        },
        {
            "title": "Oral-B iO2 eltandborste 612265 (Calm Pink)",
            "product_url": "https://qhyrfq-y1.myshopify.com/products/oral-b-io2-eltandborste-612265-calm-pink"
        }
    ]
