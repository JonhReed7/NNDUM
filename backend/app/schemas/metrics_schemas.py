from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MetricModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AuthorChangeShare(MetricModel):
    author: str
    changed_chars: int
    share_percent: float


class ChangesVolumeDistribution(MetricModel):
    total_changed_chars: int
    authors: list[AuthorChangeShare]


class CommitMessageIssue(MetricModel):
    hash: str
    author: str
    message: str
    reason: str


class CommitMessageQuality(MetricModel):
    total_evaluated_commits: int
    meaningful_commits: int
    quality_percent: float
    conventional_commits_count: int
    bad_examples: list[CommitMessageIssue]


class DirtyFileExample(MetricModel):
    hash: str
    author: str
    file_path: str
    category: str


class RepositoryCleanliness(MetricModel):
    is_clean: bool
    cleanliness_percent: float
    total_checked_commits: int
    dirty_commits_count: int
    violations_by_category: dict[str, int]
    dirty_examples: list[DirtyFileExample]


class WeekdayActivity(MetricModel):
    day_index: int
    day_name: str
    commits_count: int
    share_percent: float


class HeatmapPoint(MetricModel):
    day_index: int
    day_name: str
    hour: int
    commits_count: int


class DailyActivity(MetricModel):
    date: str
    commits_count: int


class WorkRegularity(MetricModel):
    timezone: str
    total_commits: int
    active_days_count: int
    regularity_coefficient: float
    peak_weekday: str | None
    by_weekday: list[WeekdayActivity]
    daily_timeline: list[DailyActivity]
    heatmap_2d: list[HeatmapPoint]


class DeadlineWindow(MetricModel):
    commits_count: int
    share_percent: float


class DeadlineProximity(MetricModel):
    deadline_team_tz: str
    last_24h_commits: int
    last_24h_share_percent: float
    last_6h_commits: int
    last_6h_share_percent: float
    avg_hours_before_deadline: float | None
    closest_commit_hours_before_deadline: float | None


class DeadlineTimeWindows(MetricModel):
    daytime_09_23: DeadlineWindow
    night_rush_03_06: DeadlineWindow
    other_hours: DeadlineWindow


class DeadlineActivity(MetricModel):
    timezone: str
    total_commits: int
    time_windows: DeadlineTimeWindows
    deadline_proximity: DeadlineProximity | None


class ReadmeChecks(MetricModel):
    has_description: bool
    has_install_and_run: bool
    has_structure_overview: bool


class ReadmeCompleteness(MetricModel):
    has_readme: bool
    file_name: str | None
    completeness_percent: float
    checks: ReadmeChecks
    missing_sections: list[str]


class TeamMemberEngagement(MetricModel):
    name: str | None
    github_login: str | None
    is_active: bool
    has_commit: bool
    has_pr: bool
    has_comment_or_review: bool


class TeamEngagement(MetricModel):
    total_team_members: int
    active_members_count: int
    engagement_percent: float
    members: list[TeamMemberEngagement]


class StaleBranch(MetricModel):
    branch_name: str
    last_commit_sha: str
    last_commit_date: datetime
    last_author: str | None
    days_inactive: float
    is_stale: bool


class StaleBranches(MetricModel):
    stale_days_threshold: int
    total_open_feature_branches: int
    stale_branches_count: int
    stale_branches_share_percent: float
    stale_branches: list[StaleBranch]


class PullRequestResponse(MetricModel):
    pr_number: int
    title: str
    author: str
    created_at: datetime | None = None
    state: str | None = None
    has_response: bool
    responder: str | None = None
    response_type: str | None = None
    response_time_hours: float | None = None
    response_time_minutes: float | None = None


class PullRequestResponseTimes(MetricModel):
    total_prs_in_sprint: int
    answered_prs_count: int
    unanswered_prs_count: int
    average_response_time_hours: float | None
    median_response_time_hours: float | None
    prs: list[PullRequestResponse]


class PullRequestReview(MetricModel):
    pr_number: int
    author: str
    reviewers: list[str]
    has_peer_review: bool


class ReviewedTeamMember(MetricModel):
    name: str | None
    github_login: str
    reviewed_others_prs: bool
    reviewed_prs_count: int


class MutualPullRequestReview(MetricModel):
    total_team_members: int
    reviewers_count: int
    mutual_review_share_percent: float
    total_prs_checked: int
    reviewed_prs_count: int
    reviewed_prs_share_percent: float
    members: list[ReviewedTeamMember]


class RepositoryMetrics(MetricModel):
    sprint_commits_counts: int
    changes_volume_distribution: ChangesVolumeDistribution
    commits_quality: CommitMessageQuality
    repository_cleanliness: RepositoryCleanliness
    readme_analyse: ReadmeCompleteness
    regularity_heatmap: WorkRegularity
    deadline_activity: DeadlineActivity
    team_engagement: TeamEngagement
    stale_branches: StaleBranches
    pr_first_response_time: PullRequestResponseTimes
    mutual_pr_review: MutualPullRequestReview | None = None


class AnalysisResult(RepositoryMetrics):
    pass


class AnalysisResultEnvelope(MetricModel):
    metrics: AnalysisResult
    metadata: dict[str, Any] = Field(default_factory=dict)
