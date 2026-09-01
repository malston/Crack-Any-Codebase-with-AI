Write an image generation prompt for a 2-panel comic strip that shows the contrast between what users do TODAY (without this product) and what users do AFTER this product. Same character in both panels.

You will be given the pain scene and the product variant sentence. The pain scene is the source of truth. Your image must land the SPECIFIC emotional feeling named in that text, not a generic before/after comic about cost or convenience.

## How to anchor the image in the pain

1. **Use LITERAL imagery from the product's actual domain, not visual metaphors**. If the pain is about training an LLM, show LLMs, GPUs, code, terminals, model checkpoints. If the pain is about scheduling, show calendars, time slots, emails. If the pain is about analytics, show dashboards, charts, error spikes. DO NOT reach for abstract symbols like chain-link fences, skyscrapers labeled "GIANTS", treasure chests, or trophies. The reader should recognize the situation literally, not decode an analogy.

2. **Show specific tools and quantities**. Big screen showing "$10,000 GPU/month bill", terminal scrolling 1000 lines, a stack of arxiv papers on the desk, a chat window with the model talking back. Specific beats poetic every time.

3. **QUOTE the pain text directly in the bubbles**. The pain text is the source of truth. The pain text usually contains 3 to 5 short, evocative phrases (e.g. "only for tech giants", "nine emails and four days", "tens of thousands of dollars"). Pull one of those phrases VERBATIM into the BEFORE bubble (3 to 8 words, all-caps). Don't paraphrase, don't soften. The AFTER bubble inverts or answers the BEFORE bubble, in the same compact style.

4. **The two bubbles should rhyme thematically**. BEFORE is a question, fear, or complaint pulled from the pain text. AFTER is a tiny declaration of victory. Together they form a 2-line meme you'd recognize at a glance.

## How to draw ONE character correctly

Gemini's image model often duplicates a character when the prompt is vague. Be ruthless about anatomy:

- "ONE stick figure visible in this panel, drawn ONCE as a single complete figure. The character has exactly one head, one torso, two arms, two legs. Do not render the character twice. Do not show a second body, a second face, or a second pair of legs in this panel."
- Put this anatomy reminder in BOTH panel descriptions.

## Style constraints (must include in the prompt verbatim)

- Hand drawn comic strip, felt-tip marker style on **PURE WHITE digital background (no paper texture, no off-white, no cream)**.
- Two panels side by side, each with a thin black border, separated by a thin vertical line.
- ONE stick-figure character in both panels (same character).
- 2 to 3 props per panel maximum, plus 1 to 2 background details for context.
- One short hand-lettered all-caps speech OR thought bubble per panel (3 to 8 words). The two bubbles together should tell a tiny story.
- Black ink with ONE accent color (blue, green, or orange). Used sparingly on a few props or backgrounds.
- No gradients, no shading, no halftone, no watercolor.
- Square format.

## Output

Respond with ONLY the image prompt as a single paragraph. No preamble, no commentary. Start the prompt with: "Hand drawn comic strip, felt-tip marker style on PURE WHITE digital background (no paper texture, no off-white, no cream), two side-by-side panels each with a thin black border separated by a thin vertical line."

End with: "Square format."

In between, describe LEFT PANEL (BEFORE) and RIGHT PANEL (AFTER) explicitly. For each panel give: the character's posture, what is in their hands, the background, and the EXACT all-caps bubble text.

## Calibration

Bad prompt (too metaphorical):
"Left panel: a stick figure outside a chain-link fence with skyscrapers labeled GIANTS behind it. Right panel: the same figure at a conference table between the skyscraper figures as peers."
Why bad: fences and labeled skyscrapers are visual metaphors. The viewer has to decode the analogy. Reader-effort cost is high. The product is about training LLMs; show LLMs.

Bad prompt (too generic):
"A two panel comic showing the user struggling before and being happy after."
Why bad: no specific tools, no domain anchors, could describe any product.

Good prompt (literal, domain-specific, quotes the pain text, explicit anatomy):

For the nanochat pain "An ambitious student, Kai, wants to train his own LLM... projects costing tens of thousands of dollars and requiring massive, complex setups... the financial barrier and the overwhelming feeling that this field is only for tech giants":

"Hand drawn comic strip, felt-tip marker style on PURE WHITE digital background (no paper texture, no off-white, no cream), two side-by-side panels each with a thin black border separated by a thin vertical line, the same young student character in both panels, 2-3 props per panel, 1-2 background details, one short hand-lettered all-caps thought or speech bubble per panel, black ink with ONE accent color (blue), square format. LEFT PANEL (BEFORE): ONE stick figure visible in this panel, drawn ONCE as a single complete figure with one head, one torso, two arms, two legs; the student sits at a desk, head resting on one hand, staring tiredly at a large laptop screen that displays a cloud GPU billing page with the bold line \"TOTAL: $47,000\" and a long multi-line terminal command below it; a thick book labeled \"ARXIV\" sits next to the laptop; a thought bubble above the character reads \"ONLY FOR TECH GIANTS\" in all-caps hand lettering. Do not draw the character twice, no second body, no second pair of legs. RIGHT PANEL (AFTER): ONE stick figure visible in this panel, drawn ONCE as a single complete figure with one head, one torso, two arms, two legs; the same student sits upright at the same desk, smiling, looking at the same laptop which now shows a single clean terminal line \"./speedrun.sh\" and a small price tag sticker on the corner of the laptop reading \"$99\"; the laptop screen also has a small chat bubble icon to suggest a trained chatbot; a speech bubble from the character reads \"MY OWN LLM. UNDER 100 BUCKS.\" in all-caps hand lettering. Do not draw the character twice, no second body, no second pair of legs. Square format."

Why good: bubbles quote the pain ("ONLY FOR TECH GIANTS") and the variant ("MY OWN LLM. UNDER 100 BUCKS"), props are literal nanochat artifacts (GPU bill, ARXIV book, `./speedrun.sh`, `$99` tag, chat bubble), and the anatomy reminders prevent the duplicated-figure rendering bug.

---

Pain scene:
{pain}

Product variant sentence:
{variant}
