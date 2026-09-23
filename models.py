from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, Field

NOT_SPECIFIED = "Not specified in the abstract."
MAX_HISTORY_ENTRIES = 10


class TopicRelevance(BaseModel):
    status: str = ""
    justification: str = ""


class SummaryResult(BaseModel):
    title: str = NOT_SPECIFIED
    objective: str = NOT_SPECIFIED
    study_type: str = NOT_SPECIFIED
    population: str = NOT_SPECIFIED
    methodology: str = NOT_SPECIFIED
    key_findings: list[str] = Field(default_factory=list)
    clinical_or_research_relevance: str = NOT_SPECIFIED
    conclusion: str = NOT_SPECIFIED
    limitations: list[str] = Field(default_factory=list)
    topic_relevance: TopicRelevance = Field(default_factory=TopicRelevance)


class SummaryGenerationError(Exception):
    def __init__(self, user_message: str):
        self.user_message = user_message
        super().__init__(user_message)


class FlaggedIssue(BaseModel):
    statement: str = ""
    issue_type: str = ""
    explanation: str = ""


class CriticResult(BaseModel):
    overall_score: int = 0
    factual_consistency_score: int = 0
    coverage_score: int = 0
    faithfulness_score: int = 0
    assessment: str = ""
    flagged_issues: list[FlaggedIssue] = Field(default_factory=list)


@dataclass
class HistoryEntry:
    timestamp: datetime
    abstract_preview: str
    summary_length: str
    topic: str | None
    result: SummaryResult
    source_label: str = ""
    critic: CriticResult | None = None
