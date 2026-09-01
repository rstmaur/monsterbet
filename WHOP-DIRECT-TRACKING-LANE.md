# Temporary Whop-direct tracking lane

This review lane temporarily bypasses Everflow and sends subscription CTAs directly to Whop checkout with `a=xentraffic`. Landing-page `utm_source`, `utm_medium`, `utm_campaign`, and `utm_content` values are copied to each checkout URL at runtime when present.

## Direct checkout mapping

| Plan | Direct Whop checkout |
|---|---|
| Weekly | `https://whop.com/checkout/plan_W6g9YbKpUMMMA/?a=xentraffic` |
| Monthly | `https://whop.com/checkout/plan_Ry7eiiyN731pS/?a=xentraffic` |
| Yearly | `https://whop.com/checkout/plan_H6s6AeCBGTVY1/?a=xentraffic` |

## Preserved Everflow routes for restoration

| Plan | Everflow route |
|---|---|
| Weekly | `https://www.xfnjwej33dd.com/4H426RW/5NWWWN1/?uid=8899` |
| Monthly | `https://www.xfnjwej33dd.com/4H426RW/5NWWWN1/?uid=8898` |
| Yearly | `https://www.xfnjwej33dd.com/4H426RW/5NWWWN1/?uid=8897` |

Everflow configuration is not changed by this lane. Restoring Everflow requires replacing each plan's direct Whop URL with the corresponding preserved route and removing the Whop-specific UTM pass-through only if the restored Everflow configuration handles campaign parameters itself.

Do not merge or deploy this lane until Whop checkout billing periods, affiliate Stats registration, UTM/campaign visibility, and GA4 click-event regression tests are approved.
