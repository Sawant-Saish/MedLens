import json

from openai import APIConnectionError, APIError, APITimeoutError, OpenAI, RateLimitError
from pydantic import ValidationError

from config import DEFAULT_MODEL, GENERATION_FAILED_MESSAGE, get_openai_api_key
from llm import _extract_json
from models import CriticResult, SummaryGenerationError, SummaryResult

CRITIC_SYSTEM_PROMPT = """You are a medical literature quality reviewer.

Your task is to evaluate a generated summary against the original source material and return a structured JSON critique.

Rules:
1. Compare every substantive claim in the summary to the source material only.
2. Flag statements that are unsupported, exaggerated, or out of context relative to the sources.
3. Do not flag "Not specified in the abstract." placeholders.
4. Score each dimension from 0 to 100 (integers only).
5. overall_score should reflect the combined quality (lower if serious unsupported claims exist).
6. issue_type must be one of: "unsupported_claim", "out_of_context", "overstated".
7. If no issues are found, return an empty flagged_issues array.
8. Return valid JSON only."""


def _build_critic_user_prompt(source_text: str, summary: SummaryResult) -> str:
    summary_json = summary.model_dump_json(indent=2)
    return f"""Evaluate the summary below against the source material.

Score dimensions (0-100 each):
- factual_consistency_score: Are stated facts supported by the source?
- coverage_score: Does the summary capture the main points from the source?
- faithfulness_score: Is the summary free from hallucination and out-of-context claims?

For each problematic statement, add an entry to flagged_issues with:
- statement: the exact or paraphrased claim from the summary
- issue_type: "unsupported_claim", "out_of_context", or "overstated"
- explanation: one sentence explaining why it is flagged

Required JSON schema:
{{
  "overall_score": 0,
  "factual_consistency_score": 0,
  "coverage_score": 0,
  "faithfulness_score": 0,
  "assessment": "",
  "flagged_issues": [
    {{
      "statement": "",
      "issue_type": "",
      "explanation": ""
    }}
  ]
}}

SOURCE MATERIAL:
{source_text}

GENERATED SUMMARY (JSON):
{summary_json}"""


def generate_critique(source_text: str, summary: SummaryResult) -> CriticResult:
    api_key = get_openai_api_key()
    if not api_key:
        raise SummaryGenerationError("OpenAI API key is not configured.")

    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            response_format={"type": "json_object"},
            max_tokens=900,
            messages=[
                {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": _build_critic_user_prompt(source_text, summary),
                },
            ],
        )
    except (APIError, APIConnectionError, RateLimitError, APITimeoutError):
        raise SummaryGenerationError(GENERATION_FAILED_MESSAGE)

    content = response.choices[0].message.content
    if not content:
        raise SummaryGenerationError(GENERATION_FAILED_MESSAGE)

    data = _extract_json(content)

    try:
        return CriticResult.model_validate(data)
    except ValidationError:
        raise SummaryGenerationError(GENERATION_FAILED_MESSAGE)
