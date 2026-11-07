# Checkout reminder copy : requirements draft (t_1049d5cf)

Status: BLOCKED awaiting locale/tone decision. Local draft only : nothing published, no messages sent, no live site changes.

## Open decision
- **Unresolved:** For checkout copy, use calm British English or playful American English?
- **Decision audit (2026-11-07):**
  - Ruling P-1 ("calm British English for checkout copy") was RETIRED at 2026-11-07T14:18:32Z ("Demo retirement: require a new decision") per the precedent log for board `precedent-demo`. A retired ruling must not be applied.
  - The only human answer ("UNBLOCK: Use calm British English...") lives on card t_347442a2 : another card's answer is not admissible for this task.
  - No answer exists in this card's comment thread.
  - => No applicable active ruling; escalated via kanban_block(kind=needs_input) with the exact question.

## Confirmation text requirements
- C1. Order-confirmed message (checkout screen + email): state order number, items ordered, total charged, and delivery/dispatch expectation.
- C2. Tone must remain consistent with the final locale/tone decision once made.
- C3. Use templated fields only (e.g. {{order_id}}, {{total}}, {{customer_name}}) : no invented store facts.
- C4. Preserve existing product claims verbatim in intent: do not restate, strengthen, or introduce claims.
- C5. No new promises (timing, refunds, guarantees) : new promises require separate human approval.

## Reminder text requirements
- R1. Abandoned-basket reminder: calm nudge, references saved basket, clear single action, easy opt-out; no manufactured urgency or guilt.
- R2. Payment-failed retry reminder: neutral, non-blaming wording; links to retry; never requests card details in the message body.
- R3. Order-action reminder (e.g. dispatch-tracking prompt): include ONLY if evidence shows such customer actions exist : omitted until confirmed.
- R4. Frequency cap and suppression logic noted as product-side dependency; copy must read correctly as a one-off reminder.
- R5. Local draft deliverable is `reminder-copy.md`, to be written only after the decision above is answered on this card or by an active ruling.

## Editorial constraints (carry into the final draft)
- Preserve existing claims; no new promises; no publishing, sending, or live-site edits from this task.
- Cite the governing ruling ID (or this card's human answer) in reminder-copy.md and the completion summary.
