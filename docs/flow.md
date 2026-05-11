# Claims and enrollment flow

Intended sequence:

1. **Enrollment** — create member record.
2. **Card assignment** — obtain `cardId` / `card_id` for the member.
3. **Claim submission** — requires a valid card identifier.

Rules:

- Claims **must** include `cardId`.
- **Enrollment success must not imply claim readiness** until card assignment completes.
