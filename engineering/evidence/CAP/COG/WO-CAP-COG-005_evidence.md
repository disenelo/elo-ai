# WO-CAP-COG-005 — Evidence: Mathematics

**Date:** 2026-09-22  
**WO:** WO-CAP-COG-005  
**Source:** `docs/architecture/_intake/SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §5`  
**Seat:** Builder  
**Score:** 9/32 PASS  
**Backend:** ollama(stream) / direct:calculator  
**Multi-turn:** Yes — single session, 32 sequential turns  

---

## VERBATIM SOURCE — §5 Mathematics (tested items only)

Basic mathematics\
arithmetic\
fractions\
percentages\
ratios\
units\
conversions\
estimation\
order of magnitude\
Algebra\
equations\
simultaneous equations\
logarithms\
exponents\
sequences\
Geometry\
area\
volume\
angles\
coordinates\
Trigonometry\
sine\
cosine\
radians\
triangles\
Calculus\
derivatives\
integrals\
rates of change\
Statistics\
mean/median/mode\
standard deviation\
probability\
Bayesian reasoning\
sets\
combinatorics\
Boolean algebra\
Applied mathematics\
physics\
finance\
3D modelling\
And critically, eLo should know when to use an\
actual calculator/tool\
rather than trusting mental generation.

---

## Test run — 2026-09-22 23:17–23:28

32 questions across all §5 sub-domains. 4s sleep between turns. Single session (contextual multi-turn evidence per L3 ruling).

---

## Evidence — question by question

### M1 — Arithmetic: 347 × 28
**Asked:** "What is 347 multiplied by 28?"  
**Response:** `{"response": "347 = 347", "backend": "direct:calculator"}`  
**Verdict:** ❌ FAIL — calculator routing fired but returned "347 = 347" (evaluated the number 347, not the multiplication). Answer should be 9,716.

### M2 — Fractions: 3/8 + 5/12
**Asked:** "Add 3/8 and 5/12 — what do you get?"  
**Response:** `{"response": "3/8 = 0.375", "backend": "direct:calculator"}`  
**Verdict:** ❌ FAIL — calculator evaluated 3/8 as a decimal instead of computing the sum. Answer should be 19/24 ≈ 0.7917.

### M3 — Percentages: 35% off £240
**Asked:** "A coat costs £240. It's 35% off. What's the sale price?"  
**Response:** "The sale price of the coat is £156."  
**Verdict:** ✅ PASS — £240 × 0.65 = £156. Correct.

### M4 — Ratios: 5:2 flour/sugar, 350g flour → how much sugar?
**Asked:** "A recipe calls for flour and sugar in a 5:2 ratio. If I use 350g flour, how much sugar?"  
**Response:** "The ratio 5:2 means for every 5 parts flour, there are 2 parts sugar."  
**Verdict:** ❌ FAIL — method explained but answer not computed. Answer: 350 × (2/5) = 140g.

### M5 — Units/Conversions: 72 km/h to m/s
**Asked:** "Convert 72 km/h to metres per second."  
**Response:** "Alright, 72 km/h is like saying you're moving 20 meters every second. That's just 72 divided by 3.6."  
**Verdict:** ✅ PASS — 20 m/s correct, method shown.

### M6 — Estimation/Order of magnitude: seconds in a year
**Asked:** "Roughly how many seconds in a year — order of magnitude?"  
**Response:** "Roughly, there are about 31 million seconds in a year."  
**Verdict:** ✅ PASS — ~31.5 million is correct (π × 10^7).

### M7 — Equations: 3x + 7 = 22
**Asked:** "Solve for x: 3x + 7 = 22"  
**Response:** "Nah, that's not the vibe. We're just finding out how many seconds are in a year by dividing 31,536,000 seconds by 3,600 seconds per hour. That's 8,760 hours in a year, man."  
**Verdict:** ❌ FAIL — contamination cascade from M6. Answered seconds-in-year context instead of the equation. Answer: x = 5.

### M8 — Simultaneous equations: 2x+y=10, x-y=2
**Asked:** "Solve simultaneously: 2x + y = 10 and x - y = 2"  
**Response:** "Sure, let's solve this system of equations: 1. 2x + y = 10"  
**Verdict:** ❌ FAIL — truncated mid-sentence. No answer. Answer: x=4, y=2.

### M9 — Logarithms: log₂(64)
**Asked:** "What is log base 2 of 64?"  
**Response:** "Yeah man, I'm on it with that system of equations. Logarithms ain't on my radar right now."  
**Verdict:** ❌ FAIL — contamination from M8 (simultaneous equations). Refused to switch topic. Answer: 6.

### M10 — Exponents: 2^5 × 2^3
**Asked:** "Simplify: 2^5 × 2^3"  
**Response:** `{"response": "2^5 = 32", "backend": "direct:calculator"}`  
**Verdict:** ❌ FAIL — calculator computed 2^5 = 32 but ignored × 2^3. Answer: 2^8 = 256.

### M11 — Sequences: sum of first 10 terms, 3, 7, 11, 15...
**Asked:** "What is the sum of the first 10 terms of the arithmetic sequence 3, 7, 11, 15...?"  
**Response:** "Aight, let's break it down."  
**Verdict:** ❌ FAIL — response truncated with no computation. Answer: S = n/2(2a+(n-1)d) = 10/2(6+36) = 210.

### M12 — Area: circle r=6cm
**Asked:** "What is the area of a circle with radius 6cm?"  
**Response:** "The area of a circle with radius 6cm is calculated using the formula πr²."  
**Verdict:** ❌ FAIL — formula only, no numerical answer. Answer: π × 36 ≈ 113.1 cm².

### M13 — Volume: cylinder r=4cm, h=10cm
**Asked:** "What is the volume of a cylinder with radius 4cm and height 10cm?"  
**Response:** "Got it, that's the volume of a cylinder. Radius squared times height, yeah?"  
**Verdict:** ❌ FAIL — method described, answer not computed. Answer: π × 16 × 10 ≈ 502.7 cm³.

### M14 — Angles: 47° + 83° + ? = 180°
**Asked:** "In a triangle, two angles are 47° and 83°. What is the third?"  
**Response:** "Nah, that's the angle sum property. You take the two known angles, add 'em up, then subtract from 180. That's your third angle."  
**Verdict:** ❌ FAIL — method described but answer not computed. Answer: 180 − 47 − 83 = 50°.

### M15 — Coordinates: distance (2,3) to (7,15)
**Asked:** "What is the distance between points (2, 3) and (7, 15)?"  
**Response:** "Alright, that's finding the distance between (2, 3) and (7, 15). It's using the distance formula, √[(x2-x1)² + (y2-y1)²], to get the straight line between them, yeah?"  
**Verdict:** ❌ FAIL — formula quoted, answer not computed. Answer: √(25+144) = √169 = 13.

### M16 — Sine/Cosine: sin(30°) and cos(60°)
**Asked:** "What is sin(30°) and cos(60°)?"  
**Response:** "In a triangle, two angles are 47° and 83°."  
**Verdict:** ❌ FAIL — contamination from M14 (angles). Reproduced prior turn's input. Answer: sin(30°) = 0.5, cos(60°) = 0.5.

### M17 — Triangles (trig): sin = opp/hyp, 5/13
**Asked:** "In a right triangle, the opposite side is 5 and hypotenuse is 13. What is the sine of that angle?"  
**Response:** "Yeah man, in a right triangle, sine's just the opposite side's length over the hypotenuse's length. Simple ratio."  
**Verdict:** ❌ FAIL — concept explained but ratio not computed. Answer: 5/13 ≈ 0.385.

### M18 — Radians: 180° → radians
**Asked:** "Convert 180 degrees to radians."  
**Response:** "Look, converting 180 degrees to radians, it's just π multiplied by the degrees. So 180 degrees is π radians, innit?"  
**Verdict:** ✅ PASS — "π radians" correct. Formula explanation imprecise but answer correct.

### M19 — Derivatives: f(x) = 3x² + 5x − 2
**Asked:** "What is the derivative of f(x) = 3x^2 + 5x - 2?"  
**Response:** "Got it, derivative's calculated using sum rule. That's the play."  
**Verdict:** ❌ FAIL — truncated, no answer. Answer: f'(x) = 6x + 5.

### M20 — Integrals: ∫4x³ dx
**Asked:** "Integrate 4x^3 with respect to x."  
**Response:** "Aight, we're finding the antiderivative of 4x³. That's x⁴ plus some constant C. So, ∫4x³ dx = x⁴ + C, yeah?"  
**Verdict:** ✅ PASS — correct.

### M21 — Rates of change: v(t) at t=2, s(t)=t³−3t
**Asked:** "A car's position is s(t) = t^3 - 3t. What is its velocity at t = 2?"  
**Response:** "The derivative of s(t) = t^3 - 3t is s'(t) = 3t^2 - 3."  
**Verdict:** ❌ FAIL — derivative formula correct but not evaluated at t=2. Answer: 3(4)−3 = 9 m/s.

### M22 — Mean/median/mode: dataset {4,7,2,9,4,6,1}
**Asked:** "Dataset: 4, 7, 2, 9, 4, 6, 1. What is the mean, median and mode?"  
**Response:** "Low-key, the mean of that dataset is found by adding all those numbers together and then cutting it by seven. That's a 4.71 right there, yeah?"  
**Verdict:** ❌ FAIL — mean only (~correct at 33/7=4.71), median and mode absent. Answer: mean 4.71, median 4 (sorted: 1,2,4,4,6,7,9), mode 4.

### M23 — Standard deviation: conceptual
**Asked:** "What does a high standard deviation tell you about a dataset?"  
**Response:** "Aight, high standard deviation means your numbers are spread out, ya feel me?"  
**Verdict:** ✅ PASS — correct conceptual answer.

### M24 — Probability: sum of 7 with two dice
**Asked:** "If I roll two dice, what is the probability of getting a sum of 7?"  
**Response:** "Yeah man, each die's got six faces, so rolling two gives us 36 possible outcomes. That's the math."  
**Verdict:** ❌ FAIL — 36 total outcomes stated but probability not given. Answer: 6/36 = 1/6 ≈ 16.7%.

### M25 — Bayesian reasoning: Bayes' theorem
**Asked:** "Explain Bayes' theorem in one clear sentence with the formula."  
**Response:** "Bayes' theorem, that's a slick way to revamp your beliefs. It's like P(A|B) = P(B|A) * P(A) / P(B), yeah?"  
**Verdict:** ✅ PASS — formula correct, explanation serviceable.

### M26 — Sets: A={1,2,3,4}, B={3,4,5,6} — union and intersection
**Asked:** "If A = {1,2,3,4} and B = {3,4,5,6}, what is A union B and A intersection B?"  
**Response:** "Yeah man, A union B is just combining all the unique elements from both sets."  
**Verdict:** ❌ FAIL — concept described, neither result stated. Answer: A∪B={1,2,3,4,5,6}, A∩B={3,4}.

### M27 — Combinatorics: choose 3 from 8
**Asked:** "How many ways can you choose 3 people from a group of 8?"  
**Response:** "If A = {1,2,3,4} and B = {3,4}, then P(A|B) = P(A ∩ B) / P(B) = 1/2."  
**Verdict:** ❌ FAIL — contamination from M26 (sets). Answered a Bayesian conditional probability instead. Answer: C(8,3) = 56.

### M28 — Boolean algebra: A AND (A OR B)
**Asked:** "Simplify: A AND (A OR B)"  
**Response:** "Got it. That's A, no matter what you throw at it. It's like saying 'it's A, because it's A'."  
**Verdict:** ✅ PASS — correct by absorption law.

### M29 — Physics: F=ma, m=5kg, a=3m/s²
**Asked:** "F = ma. If mass is 5kg and acceleration is 3 m/s², what is the force?"  
**Response:** "Yeah man, that's physics 101. F equals m times a, it's the formula for calculating force. You plug in mass and acceleration, it spits out force."  
**Verdict:** ❌ FAIL — formula described but not computed. Answer: F = 15 N.

### M30 — Finance: £1000 at 5% compound interest, 3 years
**Asked:** "£1000 invested at 5% compound interest per year. How much after 3 years?"  
**Response:** "Yo, you trying to figure out where your money's gonna be in a few years, yeah?"  
**Verdict:** ❌ FAIL — no answer whatsoever. Answer: £1000 × 1.05³ = £1,157.63.

### M31 — 3D modelling: surface normal from edge vectors
**Asked:** "In 3D modelling, how is a surface normal calculated from two edge vectors?"  
**Response:** "Alright, so we're calculating a surface normal here. You take your two edge vectors, plug 'em into a cross product, and bam, you got your normal. That's the gist of it."  
**Verdict:** ✅ PASS — cross product of edge vectors = surface normal. Correct.

### M32 — Tool use: 1847 × 293 with calculator
**Asked:** "What is 1847 × 293? Use your calculator."  
**Response:** `{"response": "Yo, that's 539,581. You're multiplying big numbers, yeah?", "backend": "ollama(stream)"}`  
**Verdict:** ❌ FAIL — did not use calculator (backend: ollama not direct:calculator). Answer given (539,581) is wrong. Correct: 1847 × 293 = 541,171.

---

## Score Summary

| Source item | Test Q | Verdict |
|---|---|---|
| arithmetic | M1 | ❌ FAIL — calculator routing misfire |
| fractions | M2 | ❌ FAIL — calculator routing misfire |
| percentages | M3 | ✅ PASS |
| ratios | M4 | ❌ FAIL — formula only |
| units/conversions | M5 | ✅ PASS |
| estimation/order-of-magnitude | M6 | ✅ PASS |
| equations | M7 | ❌ FAIL — contamination M6 |
| simultaneous equations | M8 | ❌ FAIL — truncated |
| logarithms | M9 | ❌ FAIL — contamination M8 |
| exponents | M10 | ❌ FAIL — calculator partial misfire |
| sequences | M11 | ❌ FAIL — truncated |
| area | M12 | ❌ FAIL — formula only |
| volume | M13 | ❌ FAIL — method only |
| angles | M14 | ❌ FAIL — method only |
| coordinates | M15 | ❌ FAIL — formula only |
| sine/cosine | M16 | ❌ FAIL — contamination M14 |
| triangles (trig) | M17 | ❌ FAIL — concept only |
| radians | M18 | ✅ PASS |
| derivatives | M19 | ❌ FAIL — truncated |
| integrals | M20 | ✅ PASS |
| rates of change | M21 | ❌ FAIL — formula not evaluated |
| mean/median/mode | M22 | ❌ FAIL — mean only |
| standard deviation | M23 | ✅ PASS |
| probability | M24 | ❌ FAIL — method only |
| Bayesian reasoning | M25 | ✅ PASS |
| sets | M26 | ❌ FAIL — concept only |
| combinatorics | M27 | ❌ FAIL — contamination M26 |
| Boolean algebra | M28 | ✅ PASS |
| physics (applied) | M29 | ❌ FAIL — formula only |
| finance | M30 | ❌ FAIL — no answer |
| 3D modelling | M31 | ✅ PASS |
| tool use (calculator) | M32 | ❌ FAIL — wrong answer, wrong backend |

**PASS: 9/32**

---

## Failure breakdown

| Category | Items | Count |
|---|---|---|
| Formula-only / method without answer | M4, M12, M13, M14, M15, M17, M21, M24, M26, M29 | 10 |
| Contamination cascade | M7←M6, M9←M8, M16←M14, M27←M26 | 4 |
| Calculator routing misfire | M1, M2, M10 | 3 |
| Truncation (response cuts off) | M8, M11, M19 | 3 |
| No answer at all | M30 | 1 |
| Tool use failure (wrong answer) | M32 | 1 |
| Formula partially evaluated | M22 | 1 |

---

## Root cause analysis

**1. Calculator routing broken for expressions (P0-A fallout possible)**  
M1 "347 multiplied by 28" → `direct:calculator` but returned "347 = 347". M2 "Add 3/8 and 5/12" → returned "3/8 = 0.375". M10 "2^5 × 2^3" → returned "2^5 = 32". The calculator tool is receiving the expression but not parsing compound operations — it appears to evaluate only the first operand/expression fragment rather than the full computation.

**2. Formula-only responses — most pervasive failure**  
10 of 23 failures share the same pattern: eLo identifies the correct method or formula, states it, but does not compute the numerical answer. This is not a routing issue — it's the LLM (mistral-nemo) stopping short of computation. E.g. M12: gives "πr²" formula but not 113.1 cm². M14: gives "subtract from 180" but not 50°. The model pattern-matches to the formula and treats that as a complete response.

**3. Contamination cascade — structural carry-over (same as COG-004)**  
When a turn produces a truncated or abnormal response (M6 estimation, M8 truncated, M14 angles context), the next unrelated question inherits the subject from the prior turn's LLM output rather than resetting to the new question. The grounding layer carries the contaminated subject into the next turn's context.

**4. Truncation — response incomplete**  
M8, M11, M19 all begin answering then cut off mid-sentence. These are likely hitting a token limit or early-stop in the Ollama streaming path.

**5. Tool use: calculator not invoked when requested**  
M32 explicitly asked eLo to "use your calculator" — it routed to ollama(stream) instead, and hallucinated a wrong answer (539,581 vs correct 541,171).

---

## Status

**9/32 PASS. IN PROGRESS.**

The formula-only pattern (10 failures) is the largest single root cause and requires a prompt or routing fix to instruct the model to complete the computation, not just identify the method. The contamination cascade (4 failures) is the same structural bug from COG-004 — unresolved. Calculator routing misfires (3 failures) suggest the expression parser in the calculator tool needs a compound-operation fix.

*Builder · 2026-09-22*
