from datetime import datetime
from autogen_core.memory import Memory, MemoryContent, MemoryMimeType

class SearchMemory(Memory):
    """Custom memory to store search query, method, and result status."""

    def __init__(self):
        self.entries = []

    async def add(self, content: MemoryContent) -> None:
        self.entries.append(content)

    async def query(self, query: str):
        """Return stored entries related to a query."""
        return [entry for entry in self.entries if query.lower() in entry.content.lower()]

    async def update_context(self, context):
        """Append entries to agent context (like ListMemory does)."""
        for entry in self.entries:
            await context.add_system_message(
                f"[Search Log] Query: {entry.metadata.get('query')} | "
                f"Method: {entry.metadata.get('method')} | "
                f"Result: {entry.metadata.get('result')}"
            )

# Usage Example
search_memory = SearchMemory()

await search_memory.add(
    MemoryContent(
        content="Searched Amazon for 'iPhone 15', tried scraping, failed because no direct URL.",
        mime_type=MemoryMimeType.TEXT,
        metadata={
            "query": "iPhone 15 Amazon",
            "method": "Tried API -> fallback to scraping -> no results",
            "result": "Failed"
        }
    )
)

await search_memory.add(
    MemoryContent(
        content="Searched Flipkart for 'iPhone 15', retrieved details with Playwright scraper.",
        mime_type=MemoryMimeType.TEXT,
        metadata={
            "query": "iPhone 15 Flipkart",
            "method": "Used Playwright automation to open search page, extracted price/title",
            "result": "Success"
        }
    )
)

# Query previous attempts
results = await search_memory.query("iPhone 15")
for r in results:
    print(r.content, r.metadata)
