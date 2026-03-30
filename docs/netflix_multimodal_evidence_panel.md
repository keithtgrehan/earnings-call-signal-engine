# Netflix Multimodal Evidence Panel

- Deterministic transcript-backed outputs remain canonical.
- NLP, audio, and visual layers are supporting only.

## Top 8 Showcase

### 1. qa_growth_headwinds

- Deterministic label: `management acknowledged growth pressure`
- Category: `growth_pressure`
- Quote: Yes, Doug. I mean I think our views are a little different because our numbers are a little different. If we had made our 2.5 million guidance, I think that was consistent with our thesis. And the lower acquisition really forced us to kind of tease apart what's going on. And as we put in the letter, COVID created a ...
- Reviewer note: Sidecars split on this span, so the deterministic read should stay primary and the support layers should be treated as inspection cues only.
- Caveat: Deterministic evidence stays canonical; supporting layers here are optional reviewer context only.

### 2. qa_q1_miss_explanation

- Deterministic label: `management explained the miss directly`
- Category: `guidance_pressure`
- Quote: Sure. I'll take that, and then others can fill in. So as you said, Doug, we guided to 2.5 million paid net adds. We delivered 0.5 million, if you exclude Russia. So there's really a 2 million miss in our Q1 actuals versus guidance. And what's really reflected there is acquisition growth was consistent with what we e...
- Reviewer note: Sidecars split on this span, so the deterministic read should stay primary and the support layers should be treated as inspection cues only.
- Caveat: Deterministic evidence stays canonical; supporting layers here are optional reviewer context only.

### 3. guidance_negative_q2_net_adds

- Deterministic label: `negative Q2 paid net adds guidance`
- Category: `guidance_pressure`
- Quote: Hey. Can I say one thing before they close us out, just as a tactical thing, one tactical thing that I should have mentioned earlier, Doug? I just want to make sure there's not a read-through when we guide to negative 2 million paid net adds in Q2. We didn't talk about full year and how -- what we expect. And we're not providing full year guidance, Doug, but I just want to make sure there's not a read-through from negative 2 million paid net adds in Q2 that there's going to be a steady strip down of negative adds. We're not expecting our growth to reaccelerate, our revenue growth to reaccelerate before the end of the year, but we will grow revenue. And there will be paid net add growth. As we get to the back half of the year, Ted talked about the stronger slate. We get further away from some of the big price increases. We get into a stronger seasonal period.
- Reviewer note: Sidecars split on this span, so the deterministic read should stay primary and the support layers should be treated as inspection cues only.
- Caveat: Deterministic evidence stays canonical; supporting layers here are optional reviewer context only.

### 4. qa_ad_supported_option

- Deterministic label: `qualified answer on the ad-supported option`
- Category: `strategic_option`
- Quote: Related to that, Greg has done great work on the price spread. And one way to increase the price spread is advertising on low-end plans and to have lower prices with advertising. And those who have followed Netflix know that I've been against the complexity of advertising and a big fan of the simplicity of subscript...
- Reviewer note: Sidecars split on this span, so the deterministic read should stay primary and the support layers should be treated as inspection cues only.
- Caveat: Deterministic evidence stays canonical; supporting layers here are optional reviewer context only.

### 5. chunk_monetize_sharing_competition

- Deterministic label: `monetizing sharing while acknowledging competition`
- Category: `headwind_disclosure`
- Quote: So on the 2 parts, we're working on how to monetize sharing. We've been thinking about that for a couple of years. But when we were growing fast, it wasn't the high priority to work on. And now, we're working super hard on it. And remember, these are over 100 million households that already are choosing to view Netflix. They love the service. We just got to get paid at some degree for them. So that's part of it. And then two, it's really -- we got great competition. They've got some very good shows and films out. And what we've got to do is take it up a notch. And I'll tell you that we're all pretty -- I know it's disappointing for investors, and it is for sure. But internally, we're really geared up, and this is like our moment to shine. This is when it all matters. And we're super focused on achieving those objectives and getting back into our investors' good graces.
- Reviewer note: Sidecars split on this span, so the deterministic read should stay primary and the support layers should be treated as inspection cues only.
- Caveat: Deterministic evidence stays canonical; supporting layers here are optional reviewer context only.

### 6. chunk_long_term_market_unchanged

- Deterministic label: `long-term market remains intact`
- Category: `long_term_reassurance`
- Quote: Yes. The only thing I might add, Reed, is just that we put a finer point on kind of elaborating on what we're seeing in terms of slowing growth and near-term slowing growth. But the long-term addressable market, we believe, is unchanged in terms of all broadband households. It's just that we have a better sense that COVID clouded in terms of these near-term limiters to penetrate that growth and capture that market. So that's one of the things that we put a finer point on this letter, but I just want to reinforce that the core addressable market is still there, and that's what we're still growing into, Doug.
- Reviewer note: Sidecars split on this span, so the deterministic read should stay primary and the support layers should be treated as inspection cues only.
- Caveat: Deterministic evidence stays canonical; supporting layers here are optional reviewer context only.

### 7. letter_growth_slowdown

- Deterministic label: `growth slowdown`
- Category: `growth_pressure`
- Quote: April 19, 2022 Fellow shareholders, Our revenue growth has slowed considerably as our results and forecast below show. Streaming iswinning over linear, as we predicted, and Netflix titles are very popular globally. However, our relativelyhigh household penetration - when including the large number of households shar...
- Reviewer note: Optional sidecars broadly move with the deterministic category, which makes this a cleaner support example than a hotspot.
- Caveat: Deterministic evidence stays canonical; supporting layers here are optional reviewer context only.

### 8. chunk_opening_analyst_skepticism

- Deterministic label: `opening analyst skepticism`
- Category: `analyst_skepticism`
- Quote: Great. Thanks, Spencer. So your tone in the letter today around competition, maturity and macro factors is very different than it was 3 months ago. I was hoping that you could start out by just walking us through how your views have changed over the past few months.
- Reviewer note: Sidecars split on this span, so the deterministic read should stay primary and the support layers should be treated as inspection cues only.
- Caveat: Deterministic evidence stays canonical; supporting layers here are optional reviewer context only.

## Pressure Moments Panel

### qa_growth_headwinds

- Analyst question: Great. Thanks, Spencer. So your tone in the letter today around competition, maturity and macro factors is very different than it was 3 months ago. I was hoping that you could s...
- Executive answer: Yes, Doug. I mean I think our views are a little different because our numbers are a little different. If we had made our 2.5 million guidance, I think that was consistent with ...
- Reviewer note: Sidecars split on this span, so the deterministic read should stay primary and the support layers should be treated as inspection cues only.

### qa_q1_miss_explanation

- Analyst question: Okay. So maybe just in terms of the recent trends, if we could talk about 1Q a little bit more. You lost 200,000 subscribers or gained 500,000 ex the Russia removal. Hoping you ...
- Executive answer: Sure. I'll take that, and then others can fill in. So as you said, Doug, we guided to 2.5 million paid net adds. We delivered 0.5 million, if you exclude Russia. So there's real...
- Reviewer note: Sidecars split on this span, so the deterministic read should stay primary and the support layers should be treated as inspection cues only.

### qa_ad_supported_option

- Analyst question: Got it. And is it fair to think that it would be something you would test in a few small markets to start out and then kind of move along?
- Executive answer: We're probably not that advanced, but no, I think it's pretty clear that it's working for Hulu. Disney is doing it. HBO did it. I don't think we have a lot of doubt that it work...
- Reviewer note: Sidecars split on this span, so the deterministic read should stay primary and the support layers should be treated as inspection cues only.

## Disagreement Hotspots

- `qa_growth_headwinds`: Yes, Doug. I mean I think our views are a little different because our numbers are a little different. If we had made our 2.5 million guidance, I think that ...
- `qa_q1_miss_explanation`: Sure. I'll take that, and then others can fill in. So as you said, Doug, we guided to 2.5 million paid net adds. We delivered 0.5 million, if you exclude Rus...
- `guidance_negative_q2_net_adds`: Hey. Can I say one thing before they close us out, just as a tactical thing, one tactical thing that I should have mentioned earlier, Doug? I just want to ma...
- `qa_ad_supported_option`: Related to that, Greg has done great work on the price spread. And one way to increase the price spread is advertising on low-end plans and to have lower pri...
- `chunk_monetize_sharing_competition`: So on the 2 parts, we're working on how to monetize sharing. We've been thinking about that for a couple of years. But when we were growing fast, it wasn't t...
- `chunk_long_term_market_unchanged`: Yes. The only thing I might add, Reed, is just that we put a finer point on kind of elaborating on what we're seeing in terms of slowing growth and near-term...
- `chunk_opening_analyst_skepticism`: Great. Thanks, Spencer. So your tone in the letter today around competition, maturity and macro factors is very different than it was 3 months ago. I was hop...
- `financial_anchor_q1`: Revenue: 7,867,767 (USD thousands); Operating income: 1,971,626; Net income: 1,597,447; Diluted EPS: 3.53.
