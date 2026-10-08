"""Protected subject allocations, followed by bounded reuse of unused reserve."""

import threading
from decimal import Decimal

from context_pipeline.diagnostics import BudgetExceeded

DEFAULT_BUDGET = Decimal('6.00')


class BudgetLedger:
    def __init__(self, total):
        self.total = Decimal(total)
        if not self.total.is_finite() or self.total < 0:
            raise ValueError('Local budget must be finite and nonnegative')
        self.reserved = Decimal(0)
        self.allocations = {}
        self.used = {}
        self.lock = threading.Lock()
        self.attempted_calls = 0
        self.reported_usage_calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.cached_input_tokens = 0

    def allocate(self, companies, market_topics):
        companies, market_topics = sorted(set(companies)), sorted(set(market_topics))
        if set(companies) & set(market_topics):
            raise ValueError('Budget subjects must be distinct')
        market_pool = self.total * Decimal('.20') if companies and market_topics else self.total if market_topics else Decimal(0)
        company_pool = self.total - market_pool
        self.allocations = {code: company_pool / len(companies) for code in companies}
        self.allocations.update({code: market_pool / len(market_topics) for code in market_topics})

    def reserve(self, amount, subject=None, protected=False):
        amount = Decimal(amount)
        if not amount.is_finite() or amount < 0:
            raise ValueError('Reserve must be finite and nonnegative')
        with self.lock:
            remaining = self.total - self.reserved
            if protected:
                if subject not in self.allocations:
                    raise ValueError('Budget subject has no allocation')
                local = self.allocations[subject] - self.used.get(subject, Decimal(0))
                if amount > local:
                    raise BudgetExceeded('Protected subject reserve exhausted', reserve=amount,
                                         remaining=local, scope='subject')
            if amount > remaining:
                raise BudgetExceeded('Local model budget reserve exhausted', reserve=amount,
                                     remaining=remaining, scope='total')
            self.reserved += amount
            self.used[subject or 'unallocated'] = self.used.get(subject or 'unallocated', Decimal(0)) + amount
            self.attempted_calls += 1

    def observe(self, response):
        usage = response.get('usage') if isinstance(response, dict) else None
        if not isinstance(usage, dict) or not {'input_tokens', 'output_tokens'} <= usage.keys():
            return
        try:
            incoming, outgoing = int(usage['input_tokens']), int(usage['output_tokens'])
            cached = int((usage.get('input_tokens_details') or {}).get('cached_tokens') or 0)
            if min(incoming, outgoing, cached) < 0 or cached > incoming:
                return
        except (ValueError, TypeError, AttributeError):
            return
        with self.lock:
            self.reported_usage_calls += 1
            self.input_tokens += incoming
            self.output_tokens += outgoing
            self.cached_input_tokens += cached

    def snapshot(self):
        with self.lock:
            return {'version': '1.0', 'total_limit_usd': str(self.total),
                    'reserved_estimate_usd': str(self.reserved),
                    'remaining_estimate_usd': str(self.total - self.reserved),
                    'protected_allocations_usd': {key: str(value) for key, value in sorted(self.allocations.items())},
                    'reserved_by_subject_usd': {key: str(value) for key, value in sorted(self.used.items())},
                    'new_api_attempts': self.attempted_calls, 'responses_with_usage': self.reported_usage_calls,
                    'reported_input_tokens': self.input_tokens, 'reported_output_tokens': self.output_tokens,
                    'reported_cached_input_tokens': self.cached_input_tokens,
                    'billing_cost_usd': None,
                    'method': 'Conservative local reserve, not provider billing. Saved responses require no new reserve.'}


class SubjectModels:
    def __init__(self, models, subject, protected=True):
        self.models, self.subject, self.protected = models, subject, protected

    def call(self, *args):
        return self.models.call(*args, subject=self.subject, protected=self.protected)
