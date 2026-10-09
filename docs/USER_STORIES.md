# User Stories (acceptance criteria)

## Admin
- As Admin I log in with password + TOTP so that my privileged account resists theft.
  AC: without code -> 401; with code -> 200; `mfa_required` flag until enabled.
- As Admin I approve vendors/exceptions/roles so that Reviewer work is checked.
  AC: Reviewer moves to Assessment; only Admin moves to Approved; self-approve -> 403.
- As Admin I confirm quarterly access reviews so that stale accounts are revoked.
  AC: `POST /users/{id}/confirm` and `/revoke` write audit rows.

## Reviewer
- As Reviewer I create vendors/assessments/risks/docs-reviews so that due diligence progresses.
  AC: create 201 + audit; submit returns score + failed controls + remediations.
- As Reviewer I triage SOC alerts so that only real incidents escalate.
  AC: PATCH alert New->Investigating->Resolved; run-rules dedupes repeats.

## Auditor (read-only)
- As Auditor I read users, audit logs, policies, coverage, ITGC so that I can evidence controls.
  AC: GETs 200; POST/PATCH on restricted routes -> 403; audit has no edit/delete routes.

## Vendor contact
- As Vendor I answer only my questionnaire and see only my vendor/docs/risks.
  AC: other vendor IDs -> 403; submit -> 403 (Reviewer rates); own answers -> 200.

## Senior management
- As Exec I download a plain-language PDF so that I know top risks and what to fund.
  AC: executive PDF lists critical count, completion %, expiring docs, overdue fixes, top-5.
