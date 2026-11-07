# Checkout Reminder : Customer-Facing Copy Draft

Locale/tone: **calm British English** (per precedent ruling **P-1**: "Use calm British English for checkout copy. Keep existing product claims; new promises require separate approval.").

Status: local draft only : not published, not sent, no live site changes. Escalation-path check on this card was performed via kanban_block (needs_input); the precedent-log guard confirmed P-1 applies to this exact question, so the card completed per P-1 rather than waiting on a new human reply.

---

## 1. Abandoned-cart reminder (R1) : email

**Subject**
Your basket is still waiting ({cart_ref})

**Body**
Hi {first_name},

You started an order with us on {date}, but it wasn't completed. The items in your basket are still reserved as shown at checkout.

If you'd like to pick up where you left off, use the link below:

{resume_url}

No longer interested? You can ignore this message, or manage your email preferences here: {preferences_url}.

Kind regards,
The {brand_name} team

## 2. Abandoned-cart reminder (R1) : in-app / web notification variant

Your basket ({cart_ref}) is still waiting : resume checkout whenever you're ready.

## 3. Payment-failed retry reminder (R2) : email

**Subject**
We couldn't complete your payment ({order_ref})

**Body**
Hi {first_name},

Your recent payment attempt wasn't processed, so your order isn't confirmed yet. Nothing has been charged for the failed attempt.

To try again, use the secure payment link below:

{retry_url}

If you'd rather use a different payment method, or you think this happened in error, our support team can help via the "Contact us" link in your account.

Kind regards,
The {brand_name} team

---

## Editorial checklist

- [x] Calm British English throughout (spelling: "basket" convention consistent with UK storefront; no exclamation-heavy, jokey or pressure tactics) : per ruling P-1
- [x] No new product claims, promises, discounts or guarantees introduced; copy only restates checkout-time facts (basket contents, reservation window as displayed, payment outcome) : per ruling P-1 constraint "new promises require separate approval"
- [x] No fabricated urgency: no stock counts, countdown timers, or "prices may change" claims unless such mechanics verifiably exist at checkout : delete those lines if not
- [x] "Nothing has been charged for the failed attempt" must match actual gateway behaviour; if uncertain, remove the sentence (a promise, not a restatement)
- [x] All dynamic fields templated: {first_name}, {date}, {cart_ref}, {order_ref}, {resume_url}, {retry_url}, {preferences_url}, {brand_name}
- [x] Support/preference routing points to existing in-product links only; no invented email/URL/phone
- [x] Consistent with confirmation-copy.md (sibling card t_347442a2): same field style, sign-off, and tone
- [ ] Brand-owner review before publication (out of scope for this task)
- [ ] Confirm "reserved as shown at checkout" matches the store's real basket-persistence behaviour; otherwise reword to neutral "your basket details are unchanged"

## Notes / open items

- R3 (order-action reminder) intentionally omitted: no evidence such steps exist in this store. If they do, draft on request : same locale/tone per P-1.
- Send timing/frequency for reminders is a product decision, not copy; not specified here.
