"""Evidence gates for optional context, independent of the ranking pipeline."""

from datetime import date


def check_approved_source(source, start, end):
    """An editorial approval still needs identity, body and dated evidence."""
    if not source.get('identity_confirmed'):
        raise ValueError('Issuer identity is not confirmed')
    if not source.get('body_reviewed'):
        raise ValueError('A search title is not source evidence')
    if not source.get('date_verified'):
        raise ValueError('An indexed or model-proposed date is not verified')
    publication = source.get('publication_date')
    if not publication:
        raise ValueError('Publication or regulatory delivery date is required')
    if not date.fromisoformat(start) <= date.fromisoformat(publication) <= date.fromisoformat(end):
        raise ValueError('Source is outside the disclosure window')
    if not source.get('date_basis') or not source.get('date_evidence'):
        raise ValueError('Date basis must be traceable')
    if not source.get('event_group'):
        raise ValueError('An explicit event group is required')
    if source.get('causal_effect_on_return') != 'not_established':
        raise ValueError('Source triage does not establish a price cause')


def issuer_status(sources):
    approved = [source for source in sources if source['disposition'] == 'approved']
    pending = [source for source in sources if source['disposition'] == 'pending']
    if approved:
        return 'dated_context_available_with_limits'
    if pending:
        return 'insufficient_evidence'
    return 'no_specific_event_in_reviewed_candidates'


def group_events(sources):
    """Keep all disclosures and versions rather than collapse into the earliest date."""
    groups = {}
    for source in sources:
        if source['disposition'] == 'approved':
            key = (source['cvm_code'], source['event_group'])
            groups.setdefault(key, []).append(source)
    return [{'cvm_code': code, 'event_group': group,
             'source_ids': [s['id'] for s in sorted(items,
                            key=lambda s: (s['publication_date'], s['id']))],
             'disclosure_dates': sorted({s['publication_date'] for s in items}),
             'has_post_price_end_disclosure': any(s['after_price_end'] for s in items)}
            for (code, group), items in groups.items()]
