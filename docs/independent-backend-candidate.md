# Next external implementation candidate: OWASP crAPI

**Assessment, not an executed evaluation. Reviewed 15 October 2026.**

Repository: https://github.com/OWASP/crAPI
Pinned main revision: `700f03d12a392d9e408260b4beae72ed02a4a1a4`.
The repository's LICENSE.md identifies Apache-2.0. Any future extraction must
retain applicable license/notices and identify changed files. No crAPI source
is copied into this repository in this assessment.

This independently authored, intentionally vulnerable vehicle-service application
has documented cross-user access and order/refund scenarios. It is a better next
implementation-independence check than another backend authored by this project.
It is still a training benchmark with disclosed bugs, not a production study or
an unseen-defect holdout. Reading the challenge descriptions is now development
knowledge and must be disclosed if we later evaluate it.

## Candidate scope, before defining a campaign

| Family | Documented challenge | Required oracle evidence |
|---|---|---|
| Object ownership | Vehicle details (1) | Two fixture users, ownership established independently, response contains another user's protected vehicle data |
| Created-resource ownership | Mechanic reports (2) | Valid report creation and both owner/non-owner queries, independently recorded report owner |
| Financial workflow | Order/refund manipulation (8–9) | Authoritative order/payment/return state and balance changes, explicit policy for allowed refund transitions |

The challenge documentation identifies candidates; it must not become a list of
attack traces inserted into the generator's legitimate seed bank. Define valid
business workflows first, document knowledge available to every treatment, and
keep fault witnesses only in setup controls. Determine whether resource-ID
provisioning is part of setup or discovery and charge it consistently.

## Entry criteria for measured execution

1. Build the pinned revision; pin dependency/container digests. Do not silently use
   moving upstream tags with a pinned source label.
2. Establish isolated local fixtures, database resets and successful owner workflows.
3. Write the contract independently of the vulnerable response; obtain external
   review of the policy before calling the oracle independently validated.
4. Check equivalent domain/identity knowledge for all generators, including RESTler.
5. Freeze cases, budgets, seeds, exclusions and discovery criterion before execution.
6. Preserve failures and setup costs; do not count scenario variations as independent
   implementations or multiple traces as multiple defects.

This assessment does not claim support for the current salon adapter: crAPI needs
its own fixtures, dynamic identifier binding, reset strategy and business oracle.
The current finite salon action space cannot simply be pointed at its URL.

Primary inspected sources:
- https://github.com/OWASP/crAPI/blob/700f03d12a392d9e408260b4beae72ed02a4a1a4/LICENSE.md
- https://github.com/OWASP/crAPI/blob/700f03d12a392d9e408260b4beae72ed02a4a1a4/docs/challenges.md
- https://owasp.github.io/www-project-crapi/

The pinned Compose file also uses moving image tags and includes an optional
chatbot stack. Source pinning alone therefore does not pin the executed service;
a future study must build this source or record image digests and restrict its
claims to the selected non-LLM endpoints. Compose was inspected, not executed.

The happy-path page found on develop is not present at the pinned main revision;
do not mix it into a claim that the pinned setup has been validated.
