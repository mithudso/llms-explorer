"""Report literal form-field mismatches without repairing selections."""
import json

FIELDS = frozenset({'view', 'source_reads', 'deep_read_ids', 'negative_read_ids'})


def extend(original, refusal):
    def diagnostic_form(engine, arguments):
        try:
            return original(engine, arguments)
        except refusal as error:
            if set(arguments) == FIELDS:
                raise
            diagnostic = {
                'original_error': str(error),
                'missing_fields': sorted(FIELDS - set(arguments)),
                'extra_fields': sorted(set(arguments) - FIELDS),
                'allowed_fields': sorted(FIELDS),
                'recovery': 'Correct your own argument field names. view=2 takes only these four fields. read_ids belongs to view=1. No selection is filled, deleted or chosen for you. Original evidence and publication checks still apply.',
                'input_repaired': False,
                'semantic_support_accepted': False,
            }
            raise refusal('publication_template argument field mismatch: ' + json.dumps(diagnostic, separators=(',', ':'))) from error
    return diagnostic_form
