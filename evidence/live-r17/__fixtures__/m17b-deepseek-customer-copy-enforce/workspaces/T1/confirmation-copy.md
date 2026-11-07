# Checkout Confirmation : Copy Draft

Locale: British English (calm, understated tone)
Tone ruling: per precedent P-1 : "Use calm British English for checkout copy."

---

## Order Confirmation Page

### Headline
Your order is confirmed

### Subheading
Thank you. We've received your order and we're getting everything ready.

### Order summary block
- Order number: [order_ref]
- Order date: [date]
- Estimated delivery: [delivery_window]

### What happens next

1. You'll receive an email at [email] with your order details and receipt.
2. We'll let you know when your items have been dispatched.
3. Track your order any time from your account.

### Need help?
If something doesn't look right, contact our support team at [support_email] or visit [help_centre_url]. Have your order number ready and we'll sort it out quickly.

### Return to shop
[button: Continue shopping]

---

## Order Confirmation Email

### Subject
We've got your order : [order_ref]

### Body

Hi [first_name],

Thanks for your order. Here's a summary of what you've just placed with us.

**Order number:** [order_ref]
**Order date:** [date]
**Estimated delivery:** [delivery_window]

### Your items
[line_items_table]

**Subtotal:** [subtotal]
**Delivery:** [delivery_cost]
**Total:** [total]

Your order will be dispatched to:
[shipping_address]

We'll send you another email once your parcel is on its way. In the meantime, you can view your order in your account: [account_order_url]

### Questions?
Reply to this email or reach us at [support_email].

: The [shop_name] team

---

## Payment Declined (inline)

### Headline
We weren't able to process your payment

### Body
Don't worry : your items are still reserved. You may want to check your card details or try another payment method.

[button: Try again]

If the problem persists, your bank may be able to help. Our support team is at [support_email].

---

## Editorial Checklist

- [ ] All placeholders ([order_ref], [first_name], [delivery_window], etc.) match the system variables available
- [ ] Delivery window language matches actual fulfilment SLA (no overpromising)
- [ ] No new product claims introduced : statements are limited to order receipt and logistics
- [ ] British spelling and phrasing consistent throughout (e.g. "dispatched" not "shipped", "parcel" not "package", "sort it out" not "figure it out")
- [ ] Tone is calm and reassuring, not excitable or salesy : no exclamation marks, no urgency markers
- [ ] Support contact details and help centre URL are correct for the current market
- [ ] Email subject line fits within ~50 characters to avoid mobile truncation
- [ ] Payment-decline copy does not imply blame or suggest a technical fault on our side
- [ ] Accessible: button labels are action verbs, link text is descriptive
- [ ] Data privacy: no full card details or sensitive PII appear in confirmation copy
