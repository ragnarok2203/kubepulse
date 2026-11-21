"""
Google SRE Multi-Window Multi-Burn-Rate SLO Engine
Implements the Service Level Objective (SLO) mathematics from the Google SRE Workbook (Chapter 5).
Tracks Error Budget consumption, computes 1-hour and 6-hour burn rates, and evaluates alert thresholds.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone


class SLOEngine:
    """
    Engine for calculating Google SRE Error Budgets, Multi-Window Burn Rates,
    and alerting triggers for critical SRE services.
    """

    def __init__(self, target_availability: float = 99.9, target_p99_ms: float = 250.0, rolling_window_days: int = 30):
        self.target_availability = target_availability  # e.g., 99.9%
        self.target_p99_ms = target_p99_ms  # e.g., 250.0 ms
        self.rolling_window_days = rolling_window_days
        self.rolling_window_hours = rolling_window_days * 24  # 720 hours for 30 days
        self.allowed_unreliability = max(0.0001, (100.0 - self.target_availability) / 100.0)  # 0.001 for 99.9%

    def compute_burn_rate(self, observed_error_rate: float) -> float:
        """
        Burn Rate = Observed Error Rate / Allowed Unreliability (1 - Target Availability).
        Burn Rate 1.0 = Consuming budget at exactly the rate to deplete in 30 days.
        Burn Rate 14.4 = Burns 2% of total budget in 1 hour (Critical Pager).
        Burn Rate 6.0 = Burns 5% of total budget in 6 hours (High Warning).
        """
        if self.allowed_unreliability <= 0:
            return 0.0
        return round(observed_error_rate / self.allowed_unreliability, 2)

    def calculate_time_to_exhaustion(self, remaining_budget_percent: float, burn_rate: float) -> str:
        """
        Calculates projected time until the error budget is 100% depleted.
        """
        if remaining_budget_percent <= 0:
            return "EXHAUSTED"
        if burn_rate <= 0.01:
            return "> 90 days (Stable)"
        
        # At Burn Rate = 1.0, 100% budget lasts 720 hours.
        # Hours remaining = (remaining_budget_percent / 100.0) * (720 / burn_rate)
        hours_remaining = (remaining_budget_percent / 100.0) * (self.rolling_window_hours / burn_rate)
        
        if hours_remaining < 1:
            minutes = max(1, int(hours_remaining * 60))
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        elif hours_remaining < 48:
            return f"{hours_remaining:.1f} hours"
        else:
            days = hours_remaining / 24.0
            return f"{days:.1f} days"

    def evaluate(
        self,
        total_requests: int,
        failed_requests: int,
        latency_p99_ms: float,
        error_rate_1h: float,
        error_rate_6h: float,
        cumulative_budget_consumed_percent: float = 0.0
    ) -> Dict[str, Any]:
        """
        Evaluates the current SRE health state against the SLO targets.
        Returns a structured metrics dictionary for dashboards and alert triggers.
        """
        observed_error_rate = (failed_requests / total_requests) if total_requests > 0 else 0.0
        current_availability = max(0.0, min(100.0, 100.0 * (1.0 - observed_error_rate)))

        # Multi-window burn rates (1h fast-burn, 6h slow-burn)
        burn_rate_1h = self.compute_burn_rate(error_rate_1h)
        burn_rate_6h = self.compute_burn_rate(error_rate_6h)
        instant_burn_rate = self.compute_burn_rate(observed_error_rate)

        # Budget calculation
        remaining_budget_percent = max(0.0, min(100.0, 100.0 - cumulative_budget_consumed_percent))
        time_to_exhaust = self.calculate_time_to_exhaustion(remaining_budget_percent, burn_rate_1h)

        # Alert evaluation (Google SRE Multi-window Multi-burn-rate criteria)
        # Condition 1: Burn Rate >= 14.4 over 1h (Burns 2% in 1 hour) -> P1 Critical Pager
        # Condition 2: Burn Rate >= 6.0 over 6h (Burns 5% in 6 hours) -> P2 High Ticket
        # Condition 3: Budget fully exhausted -> P1 Critical Freeze
        # Condition 4: Burn Rate > 1.5 -> Elevated warning
        
        if remaining_budget_percent <= 0.0:
            severity = "CRITICAL"
            status = "BUDGET_EXHAUSTED"
            alert_msg = "Error budget fully depleted (0.0%). Freeze deployments and trigger emergency stabilization."
        elif burn_rate_1h >= 14.4:
            severity = "CRITICAL"
            status = "PAGE_ON_CALL"
            alert_msg = f"Critical Error Budget Burn Rate: {burn_rate_1h:.1f}x in 1h window (2% burned/hr). On-call paged!"
        elif burn_rate_6h >= 6.0:
            severity = "HIGH"
            status = "WARN_TICKET"
            alert_msg = f"Elevated Error Budget Burn Rate: {burn_rate_6h:.1f}x in 6h window (5% burned/6hr). Investigation required."
        elif instant_burn_rate >= 2.0 or latency_p99_ms > self.target_p99_ms:
            severity = "MEDIUM"
            status = "ELEVATED_RISK"
            alert_msg = f"Elevated latency (P99 {latency_p99_ms:.1f}ms > {self.target_p99_ms:.0f}ms target) or burn rate {instant_burn_rate:.1f}x."
        else:
            severity = "HEALTHY"
            status = "NORMAL"
            alert_msg = "All Service Level Objectives within healthy operational limits."

        return {
            "target_availability": self.target_availability,
            "current_availability": round(current_availability, 4),
            "target_p99_ms": self.target_p99_ms,
            "current_p99_ms": round(latency_p99_ms, 2),
            "total_requests": total_requests,
            "failed_requests": failed_requests,
            "instant_error_rate": round(observed_error_rate * 100.0, 4),
            "burn_rate_1h": burn_rate_1h,
            "burn_rate_6h": burn_rate_6h,
            "instant_burn_rate": instant_burn_rate,
            "remaining_budget_percent": round(remaining_budget_percent, 2),
            "budget_consumed_percent": round(cumulative_budget_consumed_percent, 2),
            "time_to_exhaustion": time_to_exhaust,
            "status": status,
            "severity": severity,
            "alert_message": alert_msg,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
