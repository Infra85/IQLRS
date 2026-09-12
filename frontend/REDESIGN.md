# Quantum UI redesign

Implemented on `UI-redesign` using `.codex/skills/quantum-ui-design/SKILL.md` as the visual source of truth. `frontend/SKILL.md` informs responsive feedback, accessibility, and restraint.

## Architecture and coverage

The existing Next.js 14 App Router, React state, Tailwind CSS, and REST API structure remain in place. No application dependencies were added.

| Surface | Implementation |
| --- | --- |
| Global shell | Responsive navigation, current-page indicators, keyboard skip link, shared footer |
| Home | Chrome hardware scene, restrained halftone field, scroll/pointer response, corrected Bell circuit |
| Learn | Curriculum index with catalogue-derived metadata |
| All eight lessons | Shared reading layout, section navigation, actual concept notation, quizzes, previous/next navigation |
| Qubit foundations | Interactive real-amplitude state explorer and measurement |
| Circuit builder | Shared instrument controls, accessible gate placement/removal, guided challenges, execution feedback, histogram and statevector panels |
| Dashboard | Existing authenticated data, course progress, statistics, account details, loading/error/empty states |
| Authentication | Shared login/register/verification form, associated labels, autocomplete, pending/error/success states |
| Code lab | Editable framework-specific Python drafts, copy and download |
| Instructor | Curriculum review table and guided practice links |
| Route fallbacks | Shared loading, error recovery, and not-found screens |

## Reusable system

- `src/app/globals.css`: surface, type, spacing, border, material, motion, and responsive tokens and classes.
- `tailwind.config.ts`: matching neutral and quantum signal palettes.
- `src/components/ui/`: buttons, cards, badges, inputs, selects, form fields, page headings, loading, error/success messages, and empty states.
- `auth-form.tsx`: one form presentation with the original authentication request contracts.
- `guest-prompt.tsx`: native dialog with focus containment, Escape dismissal, and scroll locking.
- `learning-text.tsx`: safe rendering of catalogue emphasis without HTML injection.

Dynamic inline styles are limited to data-derived visual values, such as circuit columns, histogram widths, and particle coordinates. Normal controls use shared CSS/Tailwind classes. Long circuits and instructor tables scroll within their own containers; statevector lists are bounded.

## Preserved behavior

Authentication still stores `access_token`, login returns home, registration proceeds to verification, and the dashboard handles missing/expired tokens. Verification uses the configured API origin instead of the previous hard-coded loopback address. Successful verification offers an explicit sign-in link.

The circuit request remains `{ gates, num_qubits, shots, backend: "qiskit" }`. Gate order, supported gates, qubit/shot bounds, challenge checks, counts, and complex amplitudes are preserved. Results retain the submitted shot count; editing a control cannot relabel historical results. Configuration is locked only during the network request.

The continuation adds pointer/touch gate dragging, insertion and reordering, linked CNOT movement with bounds checks, and Alt+Arrow keyboard movement. Click placement and removal remain available. Placement settles briefly; the pending simulation advances a local wire/gate indicator through operation order, without suggesting intermediate quantum states returned by the backend. Reduced-motion preferences disable these effects.

Lesson content and quiz answer keys are unchanged. Quiz state resets between modules. The added state explorer is a labelled mathematical model of a real-amplitude family, not a replacement for circuit simulation.

## Verification

- `npm run lint`: passes without warnings.
- `npm run build`: passes compilation, lint, TypeScript checks, and route generation.
- Headless Chrome: all routes (including eight lessons and 404) at 1440, 1024, 768, and 375 pixels; 72 route/viewport combinations, no document overflow or runtime exceptions.
- Browser interaction checks: Bell challenge payload and results, original-shot result labels after editing shots, clear circuit, simulation failure, quiz submit/retry, state measurement, inline login errors, OTP success, framework draft switching, mobile navigation, native dialog focus/Escape, and reduced motion.
- Additional 320px checks: ten-qubit measurement labels, qubit bounds, unknown challenge values, and container-only scrolling for the longer Grover circuit.
- Screenshots reviewed for desktop and mobile home, learning, builder, results, dashboard, authentication, editor, and instructor views.

Browser API responses were controlled fixtures. These checks validate frontend contracts and behavior; they do not establish live backend, database, or email delivery health.

## Existing service limits

`backend/app/api/code.py` returns `not_implemented`; instructor analytics and assignments have no implemented API. Their pages disclose this accurately and provide working local/curriculum actions. Backend implementation is outside this UI redesign. Quiz persistence and course enrollment were not introduced.
