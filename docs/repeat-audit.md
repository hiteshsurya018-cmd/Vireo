# Manual repeat-proxy spot check

I sampled 20 flagged ticket pairs with `sample(20, random_state=42)` from the deduplicated export, read both customer opening messages, and judged whether they plausibly described the same underlying issue. This is a small precision check, not a full validation set.

**17/20 appeared to be the same issue (85%); 3/20 appeared different (15%).** The three likely false positives were:

| First ticket | Why the pair is questionable |
|---|---|
| TK-248204 | Cancellation request followed by payment/order-confirmation problem. |
| TK-240610 | Pairing failure followed by intermittent Bluetooth cut-outs. Possibly related, but distinct enough to mark uncertain/different. |
| TK-252138 | Order cancellation followed by duplicate-charge complaint. |

The other sampled pairs described closely matching delivery, charging, audio, return pickup, discount, warranty, pairing, or connectivity problems, often explicitly saying the issue persisted or returned. This check estimates only precision among flagged pairs and does not measure missed repeats. The 15% observed questionable rate is highly uncertain with just 20 pairs; it should not be projected as the population error rate. A proper next step is a blinded, labelled sample of both flagged and unflagged ticket pairs.
