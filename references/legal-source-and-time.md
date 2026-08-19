# Legal sources and deadline handling

Read this reference when a diagram contains authorities, deadlines, effective dates, filing windows, tolling, or calculated durations.

## Source hierarchy

Use the hierarchy appropriate to the jurisdiction and forum. A typical order is:

1. constitution, statute, treaty, or enabling instrument;
2. court, agency, arbitral, professional, or self-regulatory rules currently in force;
3. binding orders and precedential decisions;
4. official interpretations, advisory committee notes, guidance, forms, and practice directions;
5. published institutional explanations and observed practice;
6. secondary commentary.

Do not imply that a lower-level source delegates authority unless it actually does. In particular, distinguish:

- statutory or regulatory enforcement power;
- a court's adjudicatory power;
- arbitral jurisdiction based on consent;
- contractual grievance or disciplinary procedures;
- industry or professional self-regulation;
- voluntary compliance backed only by publication, membership consequences, platform action, or referral.

## Authority record

For every source, retain:

- official title;
- issuing body;
- section, rule, article, or paragraph;
- version, amendment date, or effective date;
- official URL or local source path;
- whether the language is mandatory, discretionary, explanatory, or merely observed practice.

When a file name suggests an older version but the cover or text states a newer effective date, use the date stated in the document and note the mismatch if it may confuse the reader.

## Deadline record

Represent each deadline as a structured record:

```text
duration: 14
unit: calendar days | business days | court days | months | years
trigger: service | filing | entry of order | notice | hearing | discovery
counting rule: include/exclude trigger day; weekend/holiday treatment
extension: permitted/automatic/discretionary; source
tolling: event and restart rule
consequence: default, waiver, dismissal, sanction, loss of appeal, or none stated
authority: exact provision
```

If the trigger is delivery, service, receipt, entry, publication, or transmission, use that exact word. Do not simplify all of them to “after filing.”

## Calculated totals

A total case duration is rarely a legal deadline. Label it as an estimate or arithmetic total and disclose assumptions:

- all parties use the full response period;
- no extension, tolling, stay, settlement, or supplemental submission;
- optional meetings occur or do not occur;
- administrative processing time is excluded unless a source fixes it.

Use language such as:

`理论约 54 个工作日（时间推算；依据：Rules 4、6、12；不含延期和行政处理时间）`

Never present an arithmetic total as a guaranteed completion time.

## Conflicts and silence

When official sources conflict:

1. prefer the currently effective operative text;
2. identify older infographics, FAQs, or forms as outdated if verified;
3. show the conflict in a note when users may still encounter both versions.

When the rule creates a step but gives no deadline, write:

`规则未规定固定期限（Rule X）`

Do not estimate unless the user asks for an operational planning estimate, and then keep it visually distinct from the rule.
