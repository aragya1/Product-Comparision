# Product-Comparision
This project leverages autonomous AI agents to automate multi-source product comparison. The system integrates web automation, natural language processing, and intelligent orchestration to gather, verify, and summarize product information from diverse online platforms.

Core Idea: Build AI agents capable of browsing e-commerce websites, extracting product details (price, specifications, reviews, availability), and presenting structured comparisons to assist decision-making.

Tech Stack:

Playwright for dynamic web scraping and navigation.

Autogen Agents (v0.71 stable) for orchestrating task execution, including a checker agent that validates extracted data for accuracy and consistency.

LLM-driven summarization for transforming raw product data into concise, human-readable insights.

Key Features:

Automated comparison of 5 products across 2–3 sources each.

Data verification through an embedded cancellation factor to reduce faulty or redundant agent actions.

Scalable design that can expand to more products, categories, and sources.

Outcome: A reliable, efficient, and scalable tool that empowers businesses and consumers with real-time, accurate product insights, reducing manual effort in research and evaluation.
