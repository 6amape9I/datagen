from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BuildReport:
    soft_candidate_empty_count: int = 0
    legacy_candidate_fallback_count: int = 0

    def reset(self) -> "BuildReport":
        snapshot = BuildReport(
            soft_candidate_empty_count=self.soft_candidate_empty_count,
            legacy_candidate_fallback_count=self.legacy_candidate_fallback_count,
        )
        self.soft_candidate_empty_count = 0
        self.legacy_candidate_fallback_count = 0
        return snapshot


_REPORT = BuildReport()


def get_report() -> BuildReport:
    return _REPORT


def get_and_reset_report() -> BuildReport:
    return _REPORT.reset()
