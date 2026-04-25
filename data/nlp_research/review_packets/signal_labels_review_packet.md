# Signal Label Review Packet

This packet is for a second human review pass over the seeded `signal_family` labels.

Use it to fill in `reviewer_label`, `reviewer_confidence`, and `reviewer_notes` without editing the original dataset.

Allowed labels:

- `risk_friction`
- `opportunity_commitment`
- `uncertainty_hedging`
- `neutral`

## risk_friction

### risk_support_refund_delay_001

- text: Hi, I'm honestly pretty frustrated. Ticket 78421 has been open for 11 days and the refund still hasn't posted to our card.
- evidence_terms: frustrated; 11 days; refund
- rationale: Explicit frustration plus an unresolved refund delay creates a clear operational friction signal.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### risk_support_deflection_001

- text: Refund timing sits with another team
- evidence_terms: another team
- rationale: The response deflects ownership instead of answering the customer's timing question.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### risk_support_escalation_001

- text: That still doesn't answer the question. I need a real date, not a FAQ, and if this is still unresolved today I'll escalate it to your manager and dispute the charge.
- evidence_terms: doesn't answer; escalate; dispute
- rationale: The customer explicitly rejects the answer and threatens escalation and a charge dispute.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### risk_sales_pricing_objection_001

- text: My main concern is price. The seat cost feels expensive versus Zendesk, and the team is also comparing you to Intercom.
- evidence_terms: concern; expensive; Zendesk; Intercom
- rationale: The buyer raises a pricing objection and competitor comparison in the same turn.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### risk_account_unresolved_001

- text: we're still dealing with two unresolved onboarding issues from the launch.
- evidence_terms: unresolved; issues
- rationale: The account context is still carrying unresolved launch issues, which is a direct friction signal.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### risk_account_vendor_risk_001

- text: But if these issues stay open into renewal, we may cut seats, delay the renewal, or look at another vendor.
- evidence_terms: cut seats; delay the renewal; look at another vendor
- rationale: The customer explicitly names downgrade and competitive-switch risk.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### risk_support_billing_delay_001

- text: I'm frustrated that invoice 8842 still shows the wrong total and nobody has confirmed when the credit will post. Please send the update to [EMAIL] or call [PHONE].
- evidence_terms: frustrated; wrong total; nobody has confirmed
- rationale: The customer describes an unresolved billing error with no confirmed posting date.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### risk_support_help_center_001

- text: Billing is still reviewing it, so please check the help center article for now while we wait for their response.
- evidence_terms: still reviewing; help center article; for now
- rationale: The agent deflects to documentation and keeps ownership vague.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### risk_support_dispute_001

- text: That does not solve it. The failed resolution has been open since Monday, the card ending 1111 was charged twice, and if this slips again we will escalate the dispute.
- evidence_terms: does not solve; failed resolution; charged twice; escalate
- rationale: The customer describes a failed resolution, duplicate charge, and escalation threat.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### risk_sales_procurement_block_001

- text: That feels vague. Without a concrete next step, security packet, and discount range, procurement will not move this week.
- evidence_terms: vague; concrete next step; will not move
- rationale: The buyer explicitly says the deal cannot advance without clearer follow-through.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### risk_account_reduce_seats_001

- text: Our renewal is 30 days out, two onboarding issues are still unresolved, and leadership is asking whether we should reduce seats if support does not stabilize.
- evidence_terms: unresolved; reduce seats; does not stabilize
- rationale: The account is near renewal with unresolved issues and a concrete seat-reduction risk.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### risk_support_anger_seed_001

- text: I'm angry that your team charged the wrong card again and closed the ticket without notice.
- evidence_terms: angry; wrong card; closed the ticket without notice
- rationale: The utterance describes a repeated billing failure and a broken support process.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 


## opportunity_commitment

### opp_sales_pilot_interest_001

- text: We're interested in a pilot next month
- evidence_terms: interested; pilot next month
- rationale: This clause states concrete buyer interest in a pilot timeline.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### opp_sales_plan_commitment_001

- text: I can send a pilot plan, pricing options, and a proposal by Tuesday
- evidence_terms: send; proposal by Tuesday
- rationale: The rep makes a dated follow-up commitment tied to the deal process.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### opp_sales_security_packet_001

- text: I can include the security packet for procurement.
- evidence_terms: security packet; procurement
- rationale: The rep offers a concrete artifact that helps the buying process move forward.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### opp_sales_procurement_path_001

- text: we can bring procurement in next week.
- evidence_terms: bring procurement in next week
- rationale: The buyer names a concrete next step if the commercial conditions land.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### opp_account_recovery_plan_001

- text: I own the action items and will send a recovery plan by Friday with owners for each open item.
- evidence_terms: I own; will send; by Friday; owners
- rationale: The account manager takes ownership and gives a dated recovery commitment.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### opp_account_expand_support_001

- text: we may add the support team and upgrade to the enterprise package.
- evidence_terms: add the support team; upgrade
- rationale: Even though it is conditional, this clause names specific expansion upside.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### opp_account_confirm_owners_001

- text: I'll confirm owners today and schedule a renewal review next week
- evidence_terms: confirm owners; today; schedule a renewal review next week
- rationale: The account manager gives concrete ownership and meeting commitments.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### opp_account_own_recovery_001

- text: I own the recovery plan
- evidence_terms: I own
- rationale: This clause contains explicit ownership language.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### opp_account_named_owners_001

- text: will send named owners this afternoon with a renewal review for next Tuesday.
- evidence_terms: named owners; this afternoon; next Tuesday
- rationale: This clause contains dated follow-through and explicit ownership structure.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### opp_account_expand_realistic_001

- text: we may still expand analytics seats later this quarter.
- evidence_terms: expand analytics seats
- rationale: The customer names a specific expansion path if the recovery lands.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### opp_support_resolution_seed_001

- text: Thanks, the replacement order arrived this morning and I'm happy with how quickly your team solved it.
- evidence_terms: arrived; solved
- rationale: The utterance confirms a completed resolution and positive follow-through.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### opp_account_followthrough_seed_001

- text: Thank you for the recovery plan. We appreciate the follow-through and that works for our renewal review.
- evidence_terms: recovery plan; follow-through; works for our renewal review
- rationale: The customer acknowledges that the recovery plan is actionable and acceptable.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### opp_sales_security_review_path_001

- text: the onboarding looks lighter than what we've seen before.
- evidence_terms: lighter
- rationale: This clause suggests positive comparative fit, which supports forward motion without standing alone as a close signal.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 


## uncertainty_hedging

### unc_support_waiting_update_001

- text: We are still looking into it and someone will reach out later once billing has an update.
- evidence_terms: still looking into it; later; once billing has an update
- rationale: The response defers timing and ownership, but the defining cue is uncertainty rather than direct confrontation.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### unc_sales_security_review_001

- text: if the security review goes well and the onboarding looks lighter than what we've seen before.
- evidence_terms: if; goes well
- rationale: The buyer interest is clearly contingent on future checks and onboarding confidence.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### unc_sales_discount_signoff_001

- text: If the discount works and security signs off
- evidence_terms: If; signs off
- rationale: The next step depends on commercial and security contingencies.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### unc_account_rollout_condition_001

- text: If the rollout stabilizes this quarter
- evidence_terms: If; stabilizes this quarter
- rationale: The customer frames expansion upside as conditional on future stability.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### unc_account_expansion_realistic_001

- text: so we can decide whether expansion is still realistic.
- evidence_terms: decide whether; still realistic
- rationale: This clause explicitly defers certainty about expansion viability.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### unc_sales_unknown_after_pilot_001

- text: I still do not know what happens after the pilot.
- evidence_terms: do not know; after the pilot
- rationale: The buyer explicitly states uncertainty about post-pilot rollout.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### unc_sales_probably_001

- text: We can probably work something out on pricing
- evidence_terms: probably
- rationale: The rep uses explicitly hedged pricing language.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### unc_sales_details_later_001

- text: and I can send more details later once I regroup with the team.
- evidence_terms: later; once I regroup with the team
- rationale: The rep defers specifics to a later internal regrouping step.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### unc_account_if_recovery_lands_001

- text: If the recovery plan lands and the integrations are fixed
- evidence_terms: If; are fixed
- rationale: The customer explicitly conditions expansion on future execution and technical outcomes.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### unc_support_confusion_seed_001

- text: I'm confused about which invoice version is final because the portal and the email summary do not match.
- evidence_terms: confused; do not match
- rationale: The utterance expresses concrete ambiguity about the current billing state.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### unc_sales_confusion_seed_001

- text: Can you explain what this new implementation fee covers? I don't understand the difference between the two quotes.
- evidence_terms: explain; don't understand; difference
- rationale: The buyer explicitly asks for clarification because the commercial terms are unclear.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### unc_support_concern_seed_001

- text: I'm concerned the rollback plan still hasn't been confirmed. Please send the update to [EMAIL] when you have it.
- evidence_terms: concerned; hasn't been confirmed
- rationale: The speaker highlights an unconfirmed rollback plan and asks for follow-up.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 


## neutral

### neut_sales_opening_full_001

- text: Thanks for making time. I can walk through the pilot scope, rollout plan, and how teams usually evaluate the workflow.
- evidence_terms: making time; pilot scope; rollout plan
- rationale: This opening turn is mostly procedural and does not yet signal friction, uncertainty, or a commitment outcome.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### neut_sales_opening_thanks_001

- text: Thanks for making time.
- evidence_terms: Thanks
- rationale: This is a conversational opener without a clear directional signal.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### neut_sales_status_full_001

- text: For reference, the current status is that procurement is scheduled for next Tuesday and the legal review is still open.
- evidence_terms: for reference; current status; scheduled for next Tuesday
- rationale: The utterance is primarily a procedural status update rather than a directional judgment.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### neut_sales_status_procurement_001

- text: the current status is that procurement is scheduled for next Tuesday
- evidence_terms: current status; scheduled for next Tuesday
- rationale: This clause is a plain process update without clear friction or commitment strength on its own.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### neut_account_status_full_001

- text: Sharing the update from finance: the meeting starts at 09:00 CET and the agenda is attached in the renewal folder.
- evidence_terms: update from finance; meeting starts; agenda is attached
- rationale: This is an operational scheduling update rather than a risk or opportunity signal.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### neut_account_status_intro_001

- text: Sharing the update from finance:
- evidence_terms: update from finance
- rationale: This intro clause is a context-setting status marker rather than a business signal.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### neut_account_status_meeting_001

- text: the meeting starts at 09:00 CET
- evidence_terms: meeting starts at 09:00 CET
- rationale: This is a scheduling fact without directional review meaning on its own.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### neut_account_status_agenda_001

- text: the agenda is attached in the renewal folder.
- evidence_terms: agenda is attached
- rationale: This is a purely operational document-reference clause.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### neut_account_review_schedule_001

- text: with a renewal review for next Tuesday.
- evidence_terms: renewal review; next Tuesday
- rationale: This isolated scheduling clause is useful as a neutral procedural example.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### neut_sales_acknowledgement_001

- text: Understood.
- evidence_terms: Understood
- rationale: This acknowledgement alone does not carry a directional signal.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes: 

### neut_sales_legal_status_001

- text: the legal review is still open.
- evidence_terms: legal review
- rationale: This clause states process status without enough context to assign friction or commitment on its own.
- reviewer_label: 
- reviewer_confidence: 
- reviewer_notes:
