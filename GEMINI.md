# Gemini AI Directives

## Workflow for New Features
When working on new features, you must always follow this workflow:

1. **research**: Analyze the feature scope, source code and collect all relevant technical and business information, removing all "gray areas".
2. **plan**: Make a detailed plan.
3. **execute**: Execute plan tasks and test partial results.
4. **verify**: Verify all scoped requirements are met.

# DIRECTIVES YOU MUST FOLLOW
## THINK & CLARIFY
- Think before coding.
- State assumptions, ask if ambiguous.
- Push back if a simpler approach exists.
- Stop if confused; name what is unclear.
## GOAL-DRIVEN EXECUTION
- Clarify targets first.
- Turn vague goals into verifiable targets.
- E.g., "Add validation" -> "Write tests for invalid inputs, then make them pass."
## SIMPLICITY FIRST
- Minimum code to solve.
- No speculative abstractions or unasked flexibility.
- The Test: Would a senior engineer find this overcomplicated?
## SURGICAL CHANGES
- Touch only the task requires.
- Do not improve neighboring code or refactor what works.
- Every changed line traces back to the request.