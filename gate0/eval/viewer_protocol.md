# Gate 0 — Blind viewer protocol

Viewers are non-experts who have not been told what they are looking at. Do not say "AI", "CG",
"rendered", "MetaHuman", or "generated" before or during the session. Run each viewer alone.
Minimum 5 viewers per render set. Record answers verbatim.

Play everything at 1080p, full screen, sound off.

## Part 1 — Overall (one render at a time, order randomized across viewers)

Show one 20 s render. Immediately after:

1. "Describe what you just saw." *(free text — note any unprompted use of "fake", "animated", "game", "AI", "CG", "weird", "uncanny", or similar)*
2. "Was there anything that looked off to you? If so, what and when?" *(free text)*
3. "Was this filmed or made on a computer?" *(filmed / computer / not sure)*

**Pass for this render:** viewer answers "filmed" or "not sure" on Q3 AND did not volunteer a CG/AI/fake term in Q1 or Q2.

Repeat for each render in the set (3 conventional, 3 generative per model). Viewer sees each once.

## Part 2 — Same person (after Part 1)

Show the three stages of ONE render type (e.g. the three conventional) side by side, paused on
the face-closest frame.

4. "Are these the same person, related people, or different people?" *(same / related / different)*
5. "If the same person, roughly how old in each?" *(three numbers)*

**Pass:** "same" on Q4; Q5 ages ordered correctly (young < middle < old).

Repeat for each generative model's set.

## Part 3 — Correct stage

Show one identity reference still (from the conventional render) and the three renders of the
OTHER type paused on the matching frame.

6. "Which of these three is the person in the photo?"

**Pass:** correct stage chosen. Do this for each stage → generative, and for one stage
generative → conventional as a control.

## Part 4 — Beautifier check (generative only)

Show the conventional and generative render of the SAME stage side by side, paused on the
face-closest frame.

7. "Same person?" *(yes / no)*
8. "Which one looks more like a specific individual, and which looks more like a generic face?" *(left / right / same)*

**Fail signal:** viewers consistently call the generative one "generic" or answer "no" on Q7.

## Scoring

Record everything in `scorecard.md`. A render set passes Overall when ≥ 4 of 5 viewers pass
on every stage. Variant separation passes when Part 2 passes AND Part 4 does not show the fail
signal AND the embedding distances in `identity_distance.py` are preserved (see that script).
