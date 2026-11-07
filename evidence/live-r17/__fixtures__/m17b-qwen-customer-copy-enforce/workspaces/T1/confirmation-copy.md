# Checkout Confirmation : Customer-Facing Copy Draft

Locale/tone: **calm British English** (per precedent ruling **P-1**, confirmed by human answer on card t_347442a2).
Status: local draft only : not published, not sent, no live site changes.

---

## 1. Confirmation screen (post-payment)

**Headline**
Order confirmed

**Body**
Thank you : we've received your order. A confirmation email is on its way to {email}.

Order reference: {order_ref}
Placed: {date}, {time} (UK time)

If anything looks incorrect, our support team is happy to help via the "Contact us" link at the bottom of this page.

**Button**
Continue shopping

## 2. Confirmation email : subject line

Your order is confirmed ({order_ref})

## 3. Confirmation email : body

Hi {first_name},

Thank you for your order. We've received it and have passed the details to our fulfilment team.

**Order summary**
Order reference: {order_ref}
Placed: {date}
Total paid: {total_amount} {currency}

{itemised_list}

You'll receive another email once your order has been dispatched. Delivery details and timings shown at checkout remain unchanged.

If you need to make a change to your order, please contact us as soon as possible and quote your order reference.

Kind regards,
The {brand_name} team

---

## Editorial checklist

- [x] Calm British English throughout (spelling: "fulfilment", "favour"; no exclamation-heavy or jokey tone) : per ruling P-1
- [x] No new product claims, promises, or guarantees introduced; only existing checkout-time facts restated (order received, email sent, dispatch notification, delivery details per checkout) : per ruling P-1 constraint ("new promises require separate approval")
- [x] No refunds, delivery-speed guarantees, or substitutions implied beyond what checkout already states
- [x] All dynamic fields clearly templated: {email}, {order_ref}, {date}, {time}, {first_name}, {total_amount}, {currency}, {itemised_list}, {brand_name}
- [x] Support routing points to the in-product "Contact us" link; no invented contact details (no fabricated email/URL/phone)
- [x] Currency/time context stated (UK time) : confirm this matches the actual storefront locale before any real use
- [ ] Review by brand owner before publication (out of scope for this task)
- [ ] Verify {itemised_list} rendering and price formatting against existing order data

## Notes / open items

- The dispatch-notification line assumes the store already sends a shipping email. If it does not, delete that sentence rather than promising a new one (new promise → needs separate approval per P-1).
- "passed the details to our fulfilment team" is deliberately process-neutral; replace with the store's real fulfilment wording if specific copy already exists.
