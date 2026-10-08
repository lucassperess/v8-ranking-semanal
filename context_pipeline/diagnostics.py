"""Safe, incremental processing reasons; never serialize provider exception text."""

import urllib.error

from context_pipeline.sources import write


class BudgetExceeded(ValueError):
    """The local reserve prevented a model call, not an API balance error."""

    def __init__(self, message, *, reserve=None, remaining=None):
        super().__init__(message)
        self.reserve = reserve
        self.remaining = remaining


VALIDATION_REASONS = {
    'Claim quote is absent from the retrieved body': 'quote_not_found',
    'Disclosure is outside the collection period': 'date_outside_period',
    'Wrong regulatory date or issuer': 'regulatory_date_or_issuer_mismatch',
    'Publication date is not supported by the body': 'publication_date_not_verified',
    'Company identity is not explicit in the body': 'company_not_verified',
}


def error_reason(exc):
    if isinstance(exc, BudgetExceeded):
        return 'local_budget_exhausted'
    if isinstance(exc, urllib.error.HTTPError):
        return 'provider_http_error'
    if isinstance(exc, (TimeoutError, urllib.error.URLError, OSError)):
        return 'source_request_failed'
    if isinstance(exc, KeyError):
        return 'missing_required_field'
    return VALIDATION_REASONS.get(str(exc), 'invalid_response_or_data')


class Trace:
    def __init__(self, subject, path=None):
        self.subject = subject
        self.path = path
        self.entries = []

    def record(self, stage, outcome, reason, *, error=None, event_index=None, item=None):
        entry = {'stage': stage, 'outcome': outcome, 'reason': reason}
        if error is not None:
            entry['error_type'] = type(error).__name__
            if isinstance(error, BudgetExceeded) and error.reserve is not None:
                entry['estimated_reserve_usd'] = str(error.reserve)
                entry['remaining_local_reserve_usd'] = str(error.remaining)
            if isinstance(error, urllib.error.HTTPError):
                entry['http_status'] = error.code
        if event_index is not None:
            entry['event_index'] = event_index
        if item is not None:
            entry['item'] = item
        self.entries.append(entry)
        if self.path is not None:
            write(self.path, self.snapshot())

    def failure(self, stage, exc, **kwargs):
        self.record(stage, 'blocked' if isinstance(exc, BudgetExceeded) else 'failed',
                    error_reason(exc), error=exc, **kwargs)

    def snapshot(self):
        return {'subject': self.subject, 'entries': self.entries.copy()}
