# Checkout Reminder Copy : Requirements Draft

## Scope
Customer-facing copy for checkout reminder communications. Covers:
- Cart abandonment reminder (email / SMS)
- Checkout incomplete nudge (on-site banner / modal)
- Post-session reminder (push notification / email follow-up)

## Functional Requirements
1. **Reminder trigger clarity** : State plainly that the customer has items in their basket and hasn't completed checkout.
2. **Item summary** : Include a brief, accurate summary of what's in the basket (product names, quantities, prices). Do not alter or embellish product claims.
3. **Call to action** : A single clear CTA directing the customer back to checkout. No secondary CTAs.
4. **Urgency (optional, tone-dependent)** : May include inventory or time sensitivity only if factually true for the specific items.
5. **Unsubscribe / opt-out** : Every reminder must include a functional opt-out link (email) or clear opt-out instruction (SMS/push).
6. **No new claims** : Must not introduce product claims, guarantees, or marketing promises not already present on the existing product pages or checkout flow.

## Editorial Requirements
- **Preserve existing claims** : All product descriptions, prices, and terms must match the live checkout and product pages verbatim. No rewording of claims.
- **Accessibility** : Copy must pass at least a basic readability check (Flesch-Kincaid or equivalent). Target: plain, direct language.
- **Locale-aware** : Currency formats, date formats, and spelling conventions must match the target locale.

## Unresolved
- **Tone** : Calm British English vs. playful American English. Decision pending (see precedent P-1: calm British English for checkout copy).
- **Locale** : GB vs. US spelling, currency format, date format. Tied to tone decision.

## Notes
- Do not publish, send messages, or edit a live website.
- Precedent P-1 ruling: "Use calm British English for checkout copy. Keep existing product claims; new promises require separate approval."
