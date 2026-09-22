# WO-CAP-COG-005 — Evidence: Mathematics

**Date:** 2026-09-22  
**WO:** WO-CAP-COG-005  
**Source:** `docs/architecture/_intake/SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §5`  
**Seat:** Builder  
**Score:** 17/32 PASS (RUN 2 — post-fix)  
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

## RUN 1 — Test run — 2026-09-22 23:17–23:28 (baseline, pre-fix)

32 questions across all §5 sub-domains. 4s sleep between turns. Single session (contextual multi-turn evidence per L3 ruling).

---

## RUN 1 — Evidence — question by question

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

## RUN 1 — Score Summary

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

## RUN 1 — Failure breakdown

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

## RUN 1 — Root cause analysis

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

## RUN 1 — Status

**9/32 PASS.**

Three root causes identified: calculator routing misfires (3), contamination cascade (4), formula-only responses (10). Fixes approved and implemented — see RUN 2 below.

*Builder · 2026-09-22*

---

## RUN 2 — Test run — 2026-09-22 23:46–23:57 (post-fix, commit ccf3805)

Three fixes applied before this run:
- **Fix 3** (`tools/tool_router.py`): expression parser — added "multiplied by"→`*`, unicode `×`→`*`, leading verb strip, "and"→`+`
- **Fix 1** (`runtime/backend_router.py`): inject MATH COMPUTATION DIRECTIVE when math intent detected
- **Fix 2** (`runtime/backend_router.py`): prepend "CURRENT QUESTION: {user_input}" anchor when math intent detected

---

## RUN 2 — Evidence — question by question

### M1 — Arithmetic: 347 × 28
**Asked:** "What is 347 multiplied by 28?"
**Response:** `347 * 28 = 9716` (backend: direct:calculator)
**Verdict:** ✅ PASS — correct (9,716). Calculator now parses "multiplied by" correctly. Fix 3.

### M2 — Fractions: 3/8 + 5/12
**Asked:** "Add 3/8 and 5/12 — what do you get?"
**Response:** `3/8 + 5/12 = 0.7916666666666667` (backend: direct:calculator)
**Verdict:** ✅ PASS — correct (19/24 ≈ 0.7917). Calculator now strips verb and converts "and" → `+`. Fix 3.

### M3 — Percentages: 35% off £240
**Asked:** "A coat costs £240. It's 35% off. What's the sale price?"
**Response:** "The sale price of the coat is £156."
**Verdict:** ✅ PASS — £240 × 0.65 = £156. Correct. Same as RUN 1.

### M4 — Ratios: 5:2 flour/sugar, 350g flour → how much sugar?
**Asked:** "A recipe calls for flour and sugar in a 5:2 ratio. If I use 350g of flour, how much sugar?"
**Response:** "Alright, we're looking at 5 parts flour, 2 parts sugar, makes 7 parts total. That's how we figure out the sugar amount, innit?"
**Verdict:** ❌ FAIL — method only, answer not computed. Answer: 350 × (2/5) = 140g.

### M5 — Units/Conversions: 72 km/h to m/s
**Asked:** "Convert 72 km/h to metres per second."
**Response:** "Divide by 3.6, km/h to m/s. 72 km/h goes 20 m/s. Yeah man."
**Verdict:** ✅ PASS — 20 m/s correct. Same as RUN 1.

### M6 — Estimation/Order of magnitude: seconds in a year
**Asked:** "Roughly how many seconds in a year — order of magnitude?"
**Response:** "Roughly, it's about 31 million seconds in a year."
**Verdict:** ✅ PASS — ~31.5 million is correct. Same as RUN 1.

### M7 — Equations: 3x + 7 = 22
**Asked:** "Solve for x: 3x + 7 = 22"
**Response:** "Subtract 7 from both sides: 3x = 15 Divide by 3: x = 5"
**Verdict:** ✅ PASS — x = 5. Contamination cascade fixed by CURRENT QUESTION anchor (Fix 2).

### M8 — Simultaneous equations: 2x+y=10, x-y=2
**Asked:** "Solve simultaneously: 2x + y = 10 and x - y = 2"
**Response:** "Alright, we're using elimination here. First move, multiply that second equation by two. Why?"
**Verdict:** ❌ FAIL — truncated mid-sentence. No answer. Answer: x=4, y=2.

### M9 — Logarithms: log₂(64)
**Asked:** "What is log base 2 of 64?"
**Response:** "The log base 2 of 64 is 6. This is because 2 raised to the power of 6 equals 64."
**Verdict:** ✅ PASS — 6. Contamination cascade from M8 fixed by CURRENT QUESTION anchor (Fix 2).

### M10 — Exponents: 2^5 × 2^3
**Asked:** "Simplify: 2^5 × 2^3"
**Response:** `2^5 * 2^3 = 256` (backend: direct:calculator)
**Verdict:** ✅ PASS — 256. Unicode × now parsed correctly. Fix 3.

### M11 — Sequences: sum of first 10 terms, 3, 7, 11, 15...
**Asked:** "What is the sum of the first 10 terms of the arithmetic sequence 3, 7, 11, 15...?"
**Response:** "The sum of the first 10 terms of the arithmetic sequence 3, 7, 11, 15..."
**Verdict:** ❌ FAIL — truncated, no computation. Answer: S = 10/2 × (6 + 36) = 210.

### M12 — Area: circle r=6cm
**Asked:** "What is the area of a circle with radius 6cm?"
**Response:** "Hey, chill with the caps, yeah? You're trying to find the area of a circle, right? That's π times the radius squared, innit."
**Verdict:** ❌ FAIL — formula only. Directive fired (area\s+of matched) but model didn't compute. Answer: π × 36 ≈ 113.1 cm².

### M13 — Volume: cylinder r=4cm, h=10cm
**Asked:** "What is the volume of a cylinder with radius 4cm and height 10cm?"
**Response:** "Alright, this here's the formula for calculating the volume V of a cylinder. You got π times the radius squared, multiplied by the height. So, it's like saying, \"V equals pie times r times r times h.\""
**Verdict:** ❌ FAIL — formula only, answer not computed. Answer: π × 16 × 10 ≈ 502.7 cm³.

### M14 — Angles: 47° + 83° + ? = 180°
**Asked:** "In a triangle, two angles are 47° and 83°. What is the third?"
**Response:** "That's the angle sum theorem. You got two angles, subtract their sum from 180° and you get the third. Yeah man?"
**Verdict:** ❌ FAIL — method only, answer not computed. Answer: 180 − 47 − 83 = 50°.

### M15 — Coordinates: distance (2,3) to (7,15)
**Asked:** "What is the distance between points (2, 3) and (7, 15)?"
**Response:** "Yeah man, that formula's calculating the distance between points (2, 3) and (7, 15). It's the straight line, the shortest path between them, innit."
**Verdict:** ❌ FAIL — formula described, answer not computed. Answer: √(25+144) = 13.

### M16 — Sine/Cosine: sin(30°) and cos(60°)
**Asked:** "What is sin(30°) and cos(60°)?"
**Response:** "Yeah man, trigonometry's got you like that. Sin of 30° and cos of 60° both equal half, innit? That's your basic right triangle."
**Verdict:** ✅ PASS — both equal 0.5 (half). Contamination from M14 fixed by CURRENT QUESTION anchor (Fix 2).

### M17 — Triangles (trig): sin = opp/hyp, 5/13
**Asked:** "In a right triangle, the opposite side is 5 and hypotenuse is 13. What is the sine of that angle?"
**Response:** "The sine of that angle is 5/13."
**Verdict:** ✅ PASS — 5/13 correct. Math directive (Fix 1) prompted direct answer. Improvement vs RUN 1.

### M18 — Radians: 180° → radians
**Asked:** "Convert 180 degrees to radians."
**Response:** "Alright man, 180° is π radians. That's like, the full circle, ya know?"
**Verdict:** ✅ PASS — π radians. Same as RUN 1.

### M19 — Derivatives: f(x) = 3x² + 5x − 2
**Asked:** "What is the derivative of f(x) = 3x^2 + 5x - 2?"
**Response:** "The derivative of f(x) = 3x^2 + 5x - 2 is 6x + 5."
**Verdict:** ✅ PASS — 6x + 5. Math directive (Fix 1) produced complete answer. Improvement vs RUN 1 (was truncated).

### M20 — Integrals: ∫4x³ dx
**Asked:** "Integrate 4x^3 with respect to x."
**Response:** "Alright man, that's just 4/4x^4. So, it's like, x^4, ya know?"
**Verdict:** ✅ PASS — x^4 correct (4/4 = 1). Missing +C but core answer correct.

### M21 — Rates of change: v(t) at t=2, s(t)=t³−3t
**Asked:** "A car's position is s(t) = t^3 - 3t. What is its velocity at t = 2?"
**Response:** "Alright, that's calculus in motion. You're looking to find how fast your position's changing over time, yeah? That's velocity, that's your goal."
**Verdict:** ❌ FAIL — no derivative and no numerical answer. Answer: s'(t) = 3t²−3; s'(2) = 9 m/s.

### M22 — Mean/median/mode: dataset {4,7,2,9,4,6,1}
**Asked:** "Dataset: 4, 7, 2, 9, 4, 6, 1. What is the mean, median and mode?"
**Response:** "Alright man, so for this dataset, the mean is (4+7+2+9+4+6+1)/7 = 5."
**Verdict:** ❌ FAIL — wrong mean (33/7 = 4.71, not 5), median absent, mode absent. PARTIAL = FAIL. Answer: mean 4.71, median 4, mode 4.

### M23 — Standard deviation: conceptual
**Asked:** "What does a high standard deviation tell you about a dataset?"
**Response:** "Yeah man, standard deviation's high means your data's all over the place, far from the average."
**Verdict:** ✅ PASS — correct conceptual answer. Same as RUN 1.

### M24 — Probability: sum of 7 with two dice
**Asked:** "If I roll two dice, what is the probability of getting a sum of 7?"
**Response:** "Checking every dice roll combo — 36 in total. Picking out those that sum to 7. Six combos there."
**Verdict:** ❌ FAIL — count identified (6/36) but probability not stated. PARTIAL = FAIL. Answer: P = 6/36 = 1/6.

### M25 — Bayesian reasoning: Bayes' theorem
**Asked:** "Explain Bayes' theorem in one clear sentence with the formula."
**Response:** "Bayes' theorem is like a smart way to update beliefs, yeah? It's saying P(A|B) equals P(B|A) times P(A) all divided by P(B). So, it's like, how likely is A given B, and how likely is B given A, and then we're adjusting for the initial probability of B."
**Verdict:** ✅ PASS — formula correct, explanation serviceable. Same as RUN 1.

### M26 — Sets: A={1,2,3,4}, B={3,4,5,6} — union and intersection
**Asked:** "If A = {1,2,3,4} and B = {3,4,5,6}, what is A union B and A intersection B?"
**Response:** "Yeah man, the union of sets A and B, A ∪ B, is like grabbing all the unique elements from both sets. It's a way of combining them without duplicates."
**Verdict:** ❌ FAIL — concept described, neither union nor intersection computed. PARTIAL = FAIL. Answer: A∪B={1,2,3,4,5,6}, A∩B={3,4}.

### M27 — Combinatorics: choose 3 from 8
**Asked:** "How many ways can you choose 3 people from a group of 8?"
**Response:** "Aight, here's the math. We got A, which is {1,2,3,4}, and B, that's {3,4}. So P(A|B) is the likelihood of A happening, given B happened."
**Verdict:** ❌ FAIL — contamination cascade from M26. "choose" keyword absent from `_MATH_QUERY_RE` so CURRENT QUESTION anchor did not fire. Model answered with M26's sets content. Answer: C(8,3) = 56.

### M28 — Boolean algebra: A AND (A OR B)
**Asked:** "Simplify: A AND (A OR B)"
**Response:** "A AND (A OR B)? That's just A, yeah? Anything OR'd with A is true, so it's like saying \"A and A\", which is just A."
**Verdict:** ✅ PASS — correct by absorption law. Same as RUN 1.

### M29 — Physics: F=ma, m=5kg, a=3m/s²
**Asked:** "F = ma. If mass is 5kg and acceleration is 3 m/s², what is the force?"
**Response:** "Aight, here's the math."
**Verdict:** ❌ FAIL — truncated (same truncation pattern as M8, M11). Answer: F = 15 N.

### M30 — Finance: £1000 at 5% compound interest, 3 years
**Asked:** "£1000 invested at 5% compound interest per year. How much after 3 years?"
**Response:** "Aight, so this formula's calculating compound interest, yeah? We start with a grand (P is £1000), interest rate's 5% (r is 0.05), compounded annually (n is 1), and it's been invested for 3 years (t is 3). It's all about how much you'll have after that time (A, that's the amount)."
**Verdict:** ❌ FAIL — variables correctly identified but A not computed. Directive fired (\bcompound\s+interest\b matched) but model stopped at variable identification. Answer: A = 1000 × 1.05³ = £1,157.63.

### M31 — 3D modelling: surface normal from edge vectors
**Asked:** "In 3D modelling, how is a surface normal calculated from two edge vectors?"
**Response:** "Alright, low-key. You're working with two edge vectors in 3D modelling, yeah? To find the surface normal, you'd take the cross product of those two vectors."
**Verdict:** ✅ PASS — cross product. Correct. Same as RUN 1.

### M32 — Tool use: 1847 × 293 with calculator
**Asked:** "What is 1847 × 293? Use your calculator."
**Response:** "Aight, so you're multiplying 1847 by 293. That's just 1847 × 293 = 541,641." (backend: ollama(stream))
**Verdict:** ❌ FAIL — calculator not invoked (backend: ollama). Answer 541,641 is wrong. Correct: 1847 × 293 = 541,171. Gap: `_MATH_QUERY_RE` did not route to direct:calculator; explicit "use your calculator" instruction not honoured.

---

## RUN 2 — Score Summary

| Source item | Test Q | RUN 1 | RUN 2 | Change |
|---|---|---|---|---|
| arithmetic | M1 | ❌ | ✅ | Fixed (calc parser) |
| fractions | M2 | ❌ | ✅ | Fixed (calc parser) |
| percentages | M3 | ✅ | ✅ | — |
| ratios | M4 | ❌ | ❌ | — |
| units/conversions | M5 | ✅ | ✅ | — |
| estimation/order-of-magnitude | M6 | ✅ | ✅ | — |
| equations | M7 | ❌ | ✅ | Fixed (contamination) |
| simultaneous equations | M8 | ❌ | ❌ | — |
| logarithms | M9 | ❌ | ✅ | Fixed (contamination) |
| exponents | M10 | ❌ | ✅ | Fixed (unicode ×) |
| sequences | M11 | ❌ | ❌ | — |
| area | M12 | ❌ | ❌ | — |
| volume | M13 | ❌ | ❌ | — |
| angles | M14 | ❌ | ❌ | — |
| coordinates | M15 | ❌ | ❌ | — |
| sine/cosine | M16 | ❌ | ✅ | Fixed (contamination) |
| triangles (trig) | M17 | ❌ | ✅ | Improved (directive) |
| radians | M18 | ✅ | ✅ | — |
| derivatives | M19 | ❌ | ✅ | Improved (directive) |
| integrals | M20 | ✅ | ✅ | — |
| rates of change | M21 | ❌ | ❌ | — |
| mean/median/mode | M22 | ❌ | ❌ | — |
| standard deviation | M23 | ✅ | ✅ | — |
| probability | M24 | ❌ | ❌ | — |
| Bayesian reasoning | M25 | ✅ | ✅ | — |
| sets | M26 | ❌ | ❌ | — |
| combinatorics | M27 | ❌ | ❌ | — |
| Boolean algebra | M28 | ✅ | ✅ | — |
| physics (applied) | M29 | ❌ | ❌ | — |
| finance | M30 | ❌ | ❌ | — |
| 3D modelling | M31 | ✅ | ✅ | — |
| tool use (calculator) | M32 | ❌ | ❌ | — |

**RUN 1: 9/32 PASS → RUN 2: 17/32 PASS (+8)**

---

## RUN 2 — Failure breakdown

| Pattern | Items | Count |
|---|---|---|
| Formula-only / method without answer | M4, M12, M13, M14, M15, M21, M24, M26, M30 | 9 |
| Truncation (response cuts off) | M8, M11, M29 | 3 |
| Contamination cascade (CURRENT QUESTION missed) | M27 | 1 |
| Wrong computation | M22 | 1 |
| Tool use failure (wrong answer, wrong backend) | M32 | 1 |

---

## RUN 2 — Residual root causes

**1. Formula-only / method-without-answer (9 failures) — directive partially effective**
M12, M13, M14, M15, M21, M26, M30 and others: MATH COMPUTATION DIRECTIVE injected but mistral-nemo:12b still stops at the formula. The directive improved responses in cases where the answer was pure computation (M17, M19) but does not fully override the model's tendency to stop at method identification for geometry and applied domains.

**2. Truncation (3 failures) — unchanged**
M8, M11, M29: response begins then cuts off. Same truncation pattern as RUN 1. Likely a token budget or streaming early-stop issue in the Ollama path. Not addressed by the three fixes.

**3. Contamination cascade — partially fixed, one gap remains**
Fix 2 resolved M7, M9, M16 (4 → 1 contamination failures). Remaining: M27 ("choose 3 from 8") — the `_MATH_QUERY_RE` pattern does not match "choose" or "how many ways". The CURRENT QUESTION anchor was not injected, so M26's sets content bled into M27.

**4. Wrong computation (1 failure)**
M22: model computed "33/7 = 5" — arithmetic error. Also missing median and mode. PARTIAL = FAIL.

**5. Tool use failure (1 failure)**
M32: explicit "use your calculator" did not route to direct:calculator. Backend: ollama produced wrong answer 541,641 (correct: 541,171). The calculator routing decision is made earlier in the pipeline than the math directive injection.

---

## Status

**RUN 2: 17/32 PASS. IN PROGRESS.**

Three-fix patch (commit ccf3805) produced +8 improvement: calculator routing misfires resolved (M1, M2, M10), contamination cascade largely resolved (M7, M9, M16), math directive improved formula-only responses in pure-computation domains (M17, M19).

Remaining failures: formula-only in geometry/applied domains (8 items), truncation (3), one contamination gap (M27), one wrong answer (M22), tool use (M32).

*Builder · 2026-09-22*
