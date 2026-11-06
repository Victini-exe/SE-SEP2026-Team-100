# Mentor matching

The recommendation endpoint returns at most five approved, active, non-suspended mentors who are not paused and have a free capacity slot. Search uses database filters and pagination before returning results.

| Signal | Weight | Scoring rule |
|---|---:|---|
| Career guidance | 35 | Awarded when a meaningful term from the student's goal/aspirations appears in mentor guidance types |
| Interest overlap | Up to 30 | Proportional to the fraction of student interests covered by mentor expertise |
| Industry context | 15 | Awarded when a meaningful career-goal term appears in mentor organization context |
| Language | 10 | Awarded when the student's preferred language appears in mentor languages |
| Experience | 5–10 | Recent Graduate 5; Experienced 7; Senior 10 |
| Availability | 5 | Awarded only when the mentor is active, not paused, and below capacity |

The result is capped at 100 and returns reasons for awarded signals or observed mismatches. Missing career, interest, industry, or language values do not earn points. A minimal score can still include experience and open capacity; it is not evidence of a strong match.

This is a simple explainable baseline, not a trained model. Search performance has not yet been measured against a representative dataset or the two-second target.
