"""Maintenance-report generation.

`GroqReporter` calls Llama 3.3 70B for a written report (the original behaviour).
`TemplateReporter` produces a structured report from a severity table with no
external call, which serves both as a test double and as a graceful fallback
when no API key is configured.
"""

from __future__ import annotations

from typing import Protocol

from .classifier import Prediction

# Domain knowledge: how each defect class maps to severity / action / loss.
_SEVERITY = {
    "Clean": "None",
    "Dusty": "Low",
    "Bird-drop": "Low",
    "Snow-Covered": "Medium",
    "Electrical-damage": "High",
    "Physical-Damage": "High",
}
_ACTION = {
    "Clean": "No action required.",
    "Dusty": "Schedule routine cleaning at the next maintenance window.",
    "Bird-drop": "Clean affected modules to restore output.",
    "Snow-Covered": "Clear snow once weather allows; monitor for icing damage.",
    "Electrical-damage": "Dispatch a technician for inspection and isolate the string.",
    "Physical-Damage": "Replace the affected module; check mounting and wiring.",
}
_LOSS = {
    "Clean": "0%",
    "Dusty": "5-15%",
    "Bird-drop": "2-10%",
    "Snow-Covered": "30-100% while covered",
    "Electrical-damage": "20-60%",
    "Physical-Damage": "up to 100% on the affected module",
}


class Reporter(Protocol):
    def generate(self, prediction: Prediction) -> str: ...


class TemplateReporter:
    def generate(self, prediction: Prediction) -> str:
        label = prediction.label
        severity = _SEVERITY.get(label, "Unknown")
        action = _ACTION.get(label, "Manual review recommended.")
        loss = _LOSS.get(label, "Unknown")
        return (
            f"Detected condition: {label} (confidence {prediction.confidence:.1f}%).\n"
            f"Severity: {severity}.\n"
            f"Recommended action: {action}\n"
            f"Estimated production loss: {loss}."
        )


class GroqReporter:
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        from groq import Groq

        self._client = Groq(api_key=api_key)
        self._model = model

    def generate(self, prediction: Prediction) -> str:
        prompt = (
            "You are a solar panel maintenance expert.\n"
            f"A computer vision model detected: {prediction.label} "
            f"(confidence: {prediction.confidence:.1f}%).\n"
            "Write a short maintenance report with:\n"
            "- Defect severity (Low / Medium / High)\n"
            "- Recommended action\n"
            "- Estimated production loss\n"
            "Be concise, max 5 sentences."
        )
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content


def build_reporter(settings) -> Reporter:
    if settings.reporter_backend == "groq" and settings.groq_api_key:
        return GroqReporter(settings.groq_api_key, settings.groq_model)
    return TemplateReporter()
