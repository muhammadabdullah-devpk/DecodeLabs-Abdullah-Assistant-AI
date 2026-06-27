"""
src/ai/fallback_engine.py — Smart Rule-Based Fallback AI
=========================================================
Generates intelligent context-based replies if the OpenAI API is offline
or if no API key is provided. Uses regex, intent matching, templates, and basic reasoning.
"""

import re
import random
from datetime import datetime
from typing import Optional, Dict, List

# Define intelligent fallback database templates
FALLBACK_RESPONSES = {
    "greeting": [
        "Hello {name}! 👋 How can I assist you with coding, writing, or analysis today?",
        "Hi {name}! What project or topic are we brainstorming today? Let's get started! 🚀",
        "Hey {name}! 😊 I am ready. Feel free to ask me questions, write math, or get a custom template!"
    ],
    "farewell": [
        "Goodbye! Thanks for using Abdullah AI. Looking forward to our next session! 👋",
        "Take care! Have a productive day and feel free to return when you need further assistance! 🌟"
    ],
    "capabilities": [
        "I am Abdullah Assistant AI. Here is what I can help you with:\n\n"
        "  💻  **Write & Debug Code** (Try 'write a python function')\n"
        "  📄  **Generate Resumes & Essays** (Try 'write a resume' or 'write an essay')\n"
        "  ➗  **Solve Math Expressions** (Try 'solve 12 * (3 + 5)')\n"
        "  📚  **Explain AI & Python** (Try 'what is artificial intelligence')\n"
        "  💡  **Share Quotes & Jokes** (Try 'tell me a joke' or 'motivate me')\n\n"
        "Just type your query and I will generate a structured response! 🧠"
    ],
    "joke": [
        "😂 **Why do programmers prefer dark mode?**\n*Because light attracts bugs!*",
        "😄 **Why did the Python developer go broke?**\n*Because he couldn't C# the money!*",
        "🤣 **How many programmers does it take to change a light bulb?**\n*None — that's a hardware problem!*"
    ],
    "quote": [
        "💡 *\"The only way to do great work is to love what you do.\"* — Steve Jobs",
        "🚀 *\"First, solve the problem. Then, write the code.\"* — John Johnson",
        "🌟 *\"Simplicity is the soul of efficiency.\"* — Austin Freeman"
    ],
    "python_info": [
        "🐍 **Python** is a high-level, interpreted programming language known for readabilty.\n\n"
        "Here is a quick hello-world server in Python using Flask:\n"
        "```python\n"
        "from flask import Flask\n"
        "app = Flask(__name__)\n\n"
        "@app.route('/')\n"
        "def hello():\n"
        "    return 'Hello, World!'\n\n"
        "if __name__ == '__main__':\n"
        "    app.run(port=5000)\n"
        "```"
    ],
    "ai_info": [
        "🧠 **Artificial Intelligence (AI)** represents the simulation of human cognition by software.\n\n"
        "Main subfields:\n"
        "- **Machine Learning (ML)**: Learning from historical training datasets.\n"
        "- **Deep Learning (DL)**: Multi-layered neural network models.\n"
        "- **NLP**: Parsing, translation, and text-generation (like GPT models)."
    ],
    "programming_help": [
        "💻 Need help with programming? Let's check some clean code standards:\n\n"
        "1. **DRY (Don't Repeat Yourself)**: Modularize repeatable blocks into helpers.\n"
        "2. **Single Responsibility**: Each class/function should perform exactly one task.\n"
        "3. **Explicit Names**: Prefer `user_age` over `ua` for variables.\n\n"
        "Let me know if you need code templates in Python, JavaScript, CSS, or HTML! 🚀"
    ]
}


class FallbackEngine:
    """Keyword & regex reasoning engine yielding structured output."""

    @staticmethod
    def extract_name(text: str) -> Optional[str]:
        """Extract name via common patterns."""
        patterns = [
            r"my name is ([a-zA-Z ]+)",
            r"i am ([a-zA-Z ]+)",
            r"i'?m ([a-zA-Z ]+)",
            r"call me ([a-zA-Z ]+)"
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip().title()
        return None

    @staticmethod
    def solve_math(text: str) -> Optional[str]:
        """Attempt safe math parsing and evaluation."""
        expr_match = re.search(r"([\d\s\+\-\*\/\%\(\)\.\*\*]*\d[\d\s\+\-\*\/\%\(\)\.\*\*]*)", text)
        if not expr_match:
            return None
        raw_expr = expr_match.group(1).strip()
        allowed = set("0123456789 +-*/.%() ")
        if not all(c in allowed for c in raw_expr) or not any(c.isdigit() for c in raw_expr):
            return None
        try:
            result = eval(raw_expr, {"__builtins__": {}}, {})
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            return f"🔢 **Math Solver**\n\nExpression: `{raw_expr}`\nResult: **`{result}`**"
        except Exception:
            return None

    def generate(self, user_input: str, username: Optional[str] = None) -> str:
        """Processes user_input and returns a high-quality Markdown response."""
        normalized = user_input.lower().strip()
        name_placeholder = username if username else "there"

        # 1. Check Name Capture
        extracted_name = self.extract_name(user_input)
        if extracted_name:
            return f"👋 Nice to meet you, **{extracted_name}**! I have updated your active session. How can I help you today?"

        # 2. Check Math Solver
        if any(op in normalized for op in ["+", "-", "*", "/", "%", "solve", "calculate"]):
            math_res = self.solve_math(user_input)
            if math_res:
                return math_res

        # 3. Check specific keyword intents
        if any(g in normalized for g in ["hi", "hello", "hey", "salam", "assalamualaikum"]):
            return random.choice(FALLBACK_RESPONSES["greeting"]).format(name=name_placeholder)

        if any(f in normalized for f in ["bye", "goodbye", "exit", "quit", "stop"]):
            return random.choice(FALLBACK_RESPONSES["farewell"])

        if any(j in normalized for j in ["joke", "funny", "laugh"]):
            return random.choice(FALLBACK_RESPONSES["joke"])

        if any(q in normalized for q in ["quote", "motivate", "motivation", "wisdom"]):
            return random.choice(FALLBACK_RESPONSES["quote"])

        if "python" in normalized:
            return random.choice(FALLBACK_RESPONSES["python_info"])

        if any(ai in normalized for ai in ["ai", "artificial intelligence", "machine learning"]):
            return random.choice(FALLBACK_RESPONSES["ai_info"])

        if any(h in normalized for h in ["help", "command", "capabilities", "can you do"]):
            return random.choice(FALLBACK_RESPONSES["capabilities"])

        # 4. Templates for Advanced SaaS requests
        if "resume" in normalized or "cv" in normalized:
            return (
                "📄 **Professional Markdown Resume Template**\n\n"
                "```markdown\n"
                "# [Your Full Name]\n"
                "AI Engineer | Backend Developer | CS Student\n\n"
                "## 🌐 Contact Details\n"
                "- Email: your.email@example.com\n"
                "- LinkedIn: linkedin.com/in/username\n"
                "- GitHub: github.com/username\n\n"
                "## 💡 Professional Summary\n"
                "Goal-oriented developer with expertise building scalable Flask backends and integrating AI agents.\n\n"
                "## 🛠️ Skills\n"
                "- Languages: Python, JavaScript, SQL, HTML/CSS\n"
                "- Frameworks: Flask, SQLAlchemy, FastAPI\n"
                "- Tools: Git, Docker, SQLite, PostgreSQL\n\n"
                "## 💼 Experience\n"
                "**AI Intern** at DecodeLabs (2026 - Present)\n"
                "- Upgraded rule-based engines into modern web SaaS dashboards.\n"
                "- Implemented SQLite databases and streaming text APIs.\n"
                "```\n\n"
                "Fill in the bracketed info to build your resume! 🚀"
            )

        if "essay" in normalized or "write about" in normalized:
            topic = user_input.replace("write an essay about", "").replace("write an essay on", "").replace("write about", "").strip()
            topic = topic if topic else "Technology and Humanity"
            return (
                f"✍️ **Essay on: {topic.title()}**\n\n"
                "### Introduction\n"
                f"The topic of **{topic}** has garnered significant attention in contemporary society. "
                "As we move further into the digital age, understanding its underlying implications is crucial.\n\n"
                "### Main Body\n"
                "First, it shapes the structural organization of work, connectivity, and education. "
                "Second, it highlights key challenges such as data security, ethical alignment, and accessibility. "
                "Balancing innovation with safety remains the central concern for researchers and policy makers alike.\n\n"
                "### Conclusion\n"
                f"In conclusion, **{topic}** will continue to evolve, demanding collaborative guidelines to maximize benefit "
                "while minimizing systemic risks."
            )

        if "code" in normalized or "function" in normalized or "programming" in normalized:
            return random.choice(FALLBACK_RESPONSES["programming_help"])

        # 5. Smart General Conversational Reasoning (Never say "I don't know")
        return (
            f"Hello {name_placeholder}! 😊 Thank you for reaching out.\n\n"
            f"I've noted your interest in **'{user_input}'**. I want to give you the most accurate and helpful response possible. "
            f"To help me assist you better, could you please expand your question or clarify your goal? For example:\n"
            f"- If you're looking for code templates, try asking: *'write a python function to X'* or *'show HTML code for Y'*.\n"
            f"- For calculations or math solutions, try: *'solve 45 * (3 + 8)'*.\n"
            f"- For resume and essay drafts, try: *'create a resume for AI engineer'*.\n\n"
            f"Please let me know how you'd like to proceed, and I'll generate a custom draft for you right away! 🚀"
        )
