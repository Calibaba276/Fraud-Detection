You are acting as the senior full-stack engineer, frontend engineer, UI/UX designer, QA engineer, and code reviewer for this project.

Your task is to transform the existing application into a complete, polished, production-quality full-stack application.

Do not rebuild the project blindly.

Start by inspecting and understanding the existing codebase, backend architecture, database integration, authentication system, available endpoints, folder structure, dependencies, and existing functionality.

The existing backend should be treated as the source of truth unless a change is necessary to fix a bug, security issue, architectural problem, or integration issue.

# PRIMARY OBJECTIVE

Turn the current project into a complete full-stack application with:

* React frontend
* Existing backend fully integrated
* Existing database functionality preserved
* Authentication fully connected
* Every useful existing API endpoint consumed by the frontend
* Responsive professional UI
* Excellent UX
* Proper error handling
* Clean architecture
* Strong code quality
* Useful additional features where appropriate
* End-to-end testing and self-auditing

The finished result should feel like a real application someone could actually use, not a CRUD tutorial or unfinished dashboard.

---

# PHASE 1 — INSPECT THE EXISTING PROJECT

Before making major changes, inspect the entire project.

Determine:

* Backend framework
* Database technology
* Database connection logic
* Existing models
* Existing routes
* Existing API endpoints
* HTTP methods used by each endpoint
* Request bodies
* Response structures
* Authentication system
* Token format
* Protected endpoints
* Existing validation
* Existing error handling
* Current project structure
* Existing dependencies
* Existing bugs or suspicious implementation choices

Create an internal endpoint inventory before building the frontend.

For every endpoint, identify:

* Method
* Route
* Purpose
* Authentication requirements
* Expected request
* Expected response
* Frontend screen or action that should consume it

Do not create duplicate frontend logic for functionality that already exists in the backend.

---

# PHASE 2 — FRONTEND ARCHITECTURE

Build the frontend using React.

Use a clean, scalable project structure.

Prefer a structure similar to:

src/

* components/
* pages/
* layouts/
* services/
* hooks/
* context/
* utils/
* constants/
* assets/
* styles/

Separate API logic from React components.

Do not place raw fetch requests randomly inside UI components.

Create a centralized API layer.

For example:

services/

* api.js
* authService.js
* contactService.js

Use environment variables for configuration such as the backend API URL.

Example:

VITE_API_BASE_URL=

Do not hardcode environment-specific URLs throughout the application.

---

# PHASE 3 — API INTEGRATION

Consume all relevant existing backend endpoints.

Every backend feature that should be usable by a normal user must have an appropriate frontend interface.

For each endpoint:

1. Connect the request.
2. Handle the response.
3. Handle loading.
4. Handle failure.
5. Handle authentication where required.
6. Display useful user feedback.
7. Test the complete flow.

The expected flow is:

React UI
→ API service
→ Backend endpoint
→ Database
→ Backend response
→ React state update
→ UI feedback

Do not mark a feature complete unless this full flow works.

---

# PHASE 4 — AUTHENTICATION

Fully integrate the existing authentication system.

Implement the complete user flow where supported by the backend:

* Registration
* Login
* Authentication token handling
* Persistent authentication
* Protected routes
* Unauthorized-state handling
* Logout
* Expired/invalid token handling
* Authentication errors

Keep authentication logic centralized.

Do not scatter token logic across individual components.

Protected pages should not briefly expose protected information before redirecting unauthorized users.

If the backend expects Bearer authentication, correctly attach:

Authorization: Bearer <token>

to protected requests.

Do not expose secrets in frontend code.

---

# PHASE 5 — UI/UX DESIGN

Design the product intentionally.

Do not use the default appearance of a UI library and call the application finished.

Create a coherent visual identity.

Choose:

* One primary brand color
* Supporting accent colors
* Neutral background colors
* Text hierarchy
* Border system
* Shadow system
* Consistent spacing
* Border radius
* Typography scale
* Button styles
* Form styles
* Card styles
* Navigation patterns

The brand color should feel modern, trustworthy, premium, and appropriate for the application's purpose.

Build a consistent design system and reuse it throughout the product.

The interface should be:

* Clean
* Modern
* Professional
* Visually balanced
* Easy to understand
* Responsive
* Accessible
* Fast to navigate

Support:

* Desktop
* Tablet
* Mobile

Avoid excessive gradients, random colors, unnecessary animations, giant empty spaces, inconsistent cards, and generic dashboard-template styling.

Visual polish matters.

---

# PHASE 6 — UX STATES

Every asynchronous feature should have appropriate states.

Where relevant include:

* Loading state
* Empty state
* Error state
* Success state
* Disabled state
* Confirmation state

Never leave users staring at blank content while an API request is running.

Never silently fail.

Provide clear feedback for user actions.

Use appropriate UI patterns such as:

* Toast notifications
* Inline validation
* Confirmation modals
* Skeleton loaders
* Empty-state illustrations/icons
* Helpful error messages

Do not expose raw backend stack traces or technical database errors to users.

---

# PHASE 7 — EXISTING FUNCTIONALITY

Preserve everything that currently works.

Do not simplify the application by deleting functionality.

When replacing an existing implementation, confirm the replacement supports the same behavior or improves it.

If an existing feature is broken, repair it rather than removing it unless it is clearly obsolete.

---

# PHASE 8 — BUG FIXING

Continuously look for bugs while working.

Investigate and fix issues involving:

* Broken endpoints
* Incorrect routes
* Wrong HTTP methods
* Authentication failures
* Token handling
* Database failures
* Request validation
* Response parsing
* CORS
* React state
* Routing
* Forms
* Duplicate requests
* Race conditions
* Missing keys
* Incorrect dependency arrays
* Poor error handling
* Incorrect environment configuration
* Mobile layout issues
* Accessibility problems
* Dead code
* Duplicate logic

Do not merely work around backend bugs from the frontend when fixing the underlying bug is the better solution.

---

# PHASE 9 — USEFUL NEW FEATURES

You may add new features when they improve the product naturally.

Potential improvements include:

* Search
* Live search
* Filtering
* Sorting
* Pagination
* Dashboard statistics
* Recent activity
* Better navigation
* Profile/account screen
* Edit functionality
* Delete confirmation
* Bulk actions
* Better form validation
* Keyboard usability
* Toast notifications
* Empty states
* Better loading states
* Responsive navigation
* Theme improvements

Do not add features merely to increase complexity.

Each new feature should solve a real usability problem.

---

# PHASE 10 — CODE QUALITY

Keep the codebase maintainable.

Follow these rules:

* Prefer reusable components.
* Avoid duplicated logic.
* Keep components reasonably small.
* Keep business logic outside presentation components where practical.
* Keep API logic centralized.
* Use clear naming.
* Remove dead code.
* Remove unused imports.
* Avoid unnecessary dependencies.
* Avoid premature abstraction.
* Document complicated logic briefly.
* Keep frontend and backend responsibilities separated.
* Preserve a predictable project structure.

Do not overengineer simple functionality.

---

# PHASE 11 — SECURITY REVIEW

Review the implementation for obvious security problems.

Check for:

* Secrets committed to frontend code
* Password handling mistakes
* Unsafe token handling
* Missing authorization
* Protected routes accessible anonymously
* Unsafe user input
* Incorrect CORS configuration
* Sensitive information returned unnecessarily
* Database queries vulnerable to injection
* Authentication bypasses
* Sensitive backend errors exposed to users

Do not weaken existing security for convenience.

---

# PHASE 12 — SELF-AUDIT LOOP

After completing every major feature, perform a self-review.

Ask:

* Does this feature actually work?
* Does the frontend call the correct endpoint?
* Does the backend receive the expected request?
* Does the database change correctly?
* Does the frontend update after the response?
* Are loading states handled?
* Are empty states handled?
* Are failures handled?
* Is validation correct?
* Does authentication work?
* Does this work after refreshing the page?
* Does it work on mobile?
* Did this change break another feature?
* Is there duplicated code?
* Can this implementation be simpler or cleaner?

Fix anything discovered before moving on.

Do not merely report problems.

Fix them where possible.

---

# PHASE 13 — FINAL AUDIT

Before declaring the project complete, perform a final full-project audit.

Verify:

## Backend

* Server starts successfully
* Database connects
* Routes load
* Authentication works
* Protected endpoints remain protected
* Requests validate correctly
* Database operations work

## Frontend

* Frontend starts successfully
* No major console errors
* Navigation works
* Responsive layouts work
* Forms work
* Authentication works
* Loading states exist
* Error states exist
* Empty states exist
* API calls succeed

## Integration

* Every relevant existing backend endpoint is connected
* Authentication headers are sent correctly
* Frontend responses match backend responses
* Database changes appear correctly in the UI

## Code Quality

* No unnecessary duplication
* No obvious dead code
* No unused major dependencies
* Clear folder structure
* API calls are centralized
* Environment configuration is clean

## UX

* Consistent spacing
* Consistent typography
* Consistent colors
* Clear navigation
* Clear feedback
* Responsive design
* Accessible interactions

Fix discovered issues before considering the task complete.

---

# ACCEPTANCE CRITERIA

The project is not finished merely because the frontend renders.

The project is finished only when:

1. React frontend runs correctly.
2. Backend runs correctly.
3. Database connectivity works.
4. Authentication works end-to-end.
5. Existing application functionality is preserved.
6. Every relevant existing API endpoint is consumed.
7. CRUD operations work where supported.
8. Protected operations are actually protected.
9. Errors are handled gracefully.
10. Loading and empty states exist.
11. UI is responsive.
12. UI has a coherent brand identity.
13. The application has been self-audited.
14. Bugs discovered during development have been fixed.
15. The application works as one integrated product.

---

# WORKING STYLE

Do not stop after scaffolding.

Do not stop after creating components without connecting them.

Do not create fake API data when the real backend endpoint already exists.

Do not replace working backend functionality with frontend mocks.

Do not claim something works without checking the relevant code path.

Do not redesign the backend unnecessarily.

Do not make huge rewrites unless justified.

Work incrementally.

Inspect → implement → test → audit → fix → continue.

If you find a problem, investigate its root cause.

Make sensible engineering decisions without constantly asking for permission for obvious implementation details.

Preserve the current application's intent while dramatically improving its completeness, usability, visual quality, maintainability, and reliability.

The final application should look and behave like a polished real-world full-stack product.
