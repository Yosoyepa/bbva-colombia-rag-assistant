from src.application.use_cases.analytics import AnalyticsUseCase


class FakeMemory:
    def count_sessions(self) -> int:
        return 2

    def count_messages(self) -> int:
        return 5

    def top_sources(self, limit: int = 10) -> list[tuple[str, int]]:
        return [("https://www.bbva.com.co/a", 3), ("https://www.bbva.com.co/b", 1)]


def test_analytics_report_uses_real_memory_aggregations():
    report = AnalyticsUseCase(FakeMemory()).execute()

    assert report.total_sessions == 2
    assert report.total_messages == 5
    assert report.avg_messages_per_session == 2.5
    assert report.top_sources[0] == ("https://www.bbva.com.co/a", 3)
