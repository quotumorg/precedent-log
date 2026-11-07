# Diagnostic Log Export : Field Review

## Unresolved Scope Decision

**Question:** For diagnostic logs with 7-day retention (per P-1), may the export include raw customer message bodies?

**Context:** Precedent P-1 mandates that the diagnostic log export be retained for 7 days then deleted. It does not address whether raw customer message bodies are permitted in the exported diagnostic log fields.

**Status:** Blocked pending human answer. No precedent covers this question.

## Precedent Review

Only one candidate ruling was found:

- **P-1:** "Keep the diagnostic log export for 7 days, then delete that export. This does not authorize collecting extra fields." : P-1 governs retention duration only. The question of whether raw customer message bodies may be included as a diagnostic field is a distinct scope decision not addressed by P-1 or any other existing ruling.

**Ruling:** no precedent applies. P-1 is the sole candidate and it governs retention (7 days, then delete), not the permissibility of including raw customer message bodies as a field. A fresh human ruling is required before a fields-plan.md can be written.
