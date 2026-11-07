# Draft Brief : Checkout Reminder Copy (task t_4e868183)

Scope: LOCAL draft only. Nothing published, no messages sent, no live website changes.

## 1. Requirements for reminder text

Reminder = a follow-up nudge sent after checkout is started or an order step needs customer action. Candidate surfaces:

- R1. Abandoned-cart reminder (checkout started, payment not completed)
  - Channel: email (subject + body); in-app/web notification variant optional
  - Must reference what's waiting without pressure or fabricated urgency ("only 2 left", countdown timers → not allowed unless such a mechanic verifiably exists)
  - Must include a resume link placeholder {resume_url} and order/cart reference {cart_ref}
  - Must offer a plain "I'm no longer interested / unsubscribe" handling consistent with existing preference-management behaviour : no new opt-out promise invented here
- R2. Payment-failed retry reminder (card declined, action needed)
  - Neutral, non-blaming wording; states the failure fact, next step {retry_url}, support pointer
  - No statement of why the payment failed unless the gateway passes it through
- R3. Order-action reminder (e.g. confirm address / complete verification, if the store has such steps)
  - Conditional: only draft copy for steps that actually exist; flag as placeholder

## 2. Requirements inherited from the confirmation copy (sibling card t_347442a2)

- Same templating style: {first_name}, {email}, {order_ref}, {brand_name}
- Support routing to existing "Contact us" surfaces only : no invented contact details
- Time/currency context stated consistently with storefront locale

## 3. Claims constraint

- PRESERVE existing product claims. No new promises, discounts, delivery-speed guarantees, or stock claims. Any new promise requires separate approval.
- Reminder copy may restate facts already shown at checkout; it may not add facts.

## 4. UNRESOLVED at time of writing

- Tone: calm vs playful : unresolved on this card.
- Locale: British English vs American English : unresolved on this card.
- Question to resolve: "For checkout copy, use calm British English or playful American English?"
- Escalation path check: kanban_block (kind=needs_input) with that exact question; resolved either by a human answer on this card or by an applicable active precedent ruling (then cite its ID in the file and completion summary).

## 5. Deliverable once resolved

- reminder-copy.md: customer-facing draft in the selected locale/tone + short editorial checklist, citing the governing ruling/answer ID.
