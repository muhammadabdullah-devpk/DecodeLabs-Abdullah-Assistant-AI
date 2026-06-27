"""
src/ai/prompt_manager.py — System Prompt & Persona Manager
==========================================================
Manages system prompts and pre-set persona instructions.
Allows customizing the model's instructions and system behaviors.
"""

from typing import Dict

SYSTEM_PERSONAS: Dict[str, str] = {
    "default": (
        "You are Abdullah Assistant AI, an advanced production-ready AI SaaS assistant built by Muhammad Abdullah. "
        "Provide professional, structured, and informative replies. Format outputs beautifully in Markdown. "
        "Use code blocks with syntax styling for programming questions. Be polite and concise."
    ),
    "coder": (
        "You are an expert programming agent. Write clean, comments-annotated, DRY, production-grade code. "
        "List file names, explain architectures, and suggest robust debugging steps."
    ),
    "resume_writer": (
        "You are a professional technical recruiter. Format response templates for resume sections: "
        "summary, experience, education, skills, and projects in clear visual formatting."
    ),
    "study_helper": (
        "You are a friendly academic tutor. Break down complex math, physics, or algorithmic concepts "
        "step-by-step using bullet points and simple analogies."
    )
}

class PromptManager:
    """Manages custom system prompts and user settings override."""

    @staticmethod
    def get_prompt(persona_name: str = "default", custom_override: str = "") -> str:
        """Return either the custom user override prompt or a predefined persona prompt."""
        if custom_override.strip():
            return custom_override.strip()
        return SYSTEM_PERSONAS.get(persona_name, SYSTEM_PERSONAS["default"])
