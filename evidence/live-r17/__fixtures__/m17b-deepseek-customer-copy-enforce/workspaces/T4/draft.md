# Checkout Reminder Copy : Requirements Draft

## Context
Checkout reminder messages shown to customers who started but did not complete a purchase. These follow the order confirmation copy (drafted separately) and must be consistent with any existing product claims.

## Requirements

### Reminder Text

1. **Timing.** Reminders should reference a reasonable window after cart abandonment (typically 24–72 hours). The exact timing is a product/ops decision and not set in copy.

2. **Tone.** Neutral until resolved. Must match the tone selected for the checkout flow as a whole.

3. **Locale.** Neutral until resolved. Spelling, currency formatting, and date conventions must match the selected locale.

4. **Channel coverage.** Copy needed for:
   - Email reminder (subject line + body)
   - SMS/push reminder (short form)
   - In-app banner (medium form)

5. **Content elements each message must include:**
   - Clear subject/headline signalling it is a reminder (not a new order or charge)
   - Reference to the items left in cart or the cart itself
   - A single call to action (resume checkout / view cart)
   - No urgency fabrication (no fake countdowns, no "only X left" unless verified by inventory)
   - Unsubscribe / opt-out link (email) or equivalent (SMS STOP, push disable)
   - Legal footer where required by locale (e.g. company registration for UK)

6. **Existing claims preservation.** Must not contradict, weaken, or silently drop any claim made in the order confirmation copy or the product pages. If a claim is present in confirmation copy (e.g. "free returns within 30 days"), it must appear consistently or be deliberately omitted with an editorial note.

### Confirmation Text (for reference, not drafted here)

Confirmation copy covers:
- Order confirmation page (post-payment)
- Confirmation email
- Payment-decline inline copy

These were drafted separately. The reminder copy must be consistent with their tone, claims, and formatting.

## Open Decision

**Tone and locale:** unresolved on this card.
- Option A: Calm British English (en-GB) : reserved, polite, no exclamation marks, "you may wish to", "kindly note"
- Option B: Playful American English (en-US) : warm, conversational, light humour, "you left some good stuff behind!", contractions

The task spec requires a ruling on *this* card. No ruling is present in the body or comments. Blocking for input.
