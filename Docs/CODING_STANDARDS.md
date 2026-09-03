# OMNIVISION AI — Coding Standards

**Project Name:** OMNIVISION AI  
**Document:** Coding Standards  
**Version:** 1.0  
**Status:** Mandatory  
**Audience:** AI Coding Agents, Developers, Contributors  
**Last Updated:** 2026

---

## 1. Purpose

This document defines the coding standards, architectural coding practices, naming conventions, file organization rules, error-handling practices, testing requirements, and development principles for OMNIVISION AI.

The purpose is to ensure that the project remains:

- Clean
- Maintainable
- Modular
- Secure
- Testable
- Scalable
- Understandable
- Consistent

These rules apply to all source code added to the project.

---

## 2. General Development Principles

All development must follow these principles:

```text
Simple
   ↓
Modular
   ↓
Readable
   ↓
Testable
   ↓
Secure
   ↓
Maintainable
```

Code must be written for long-term maintenance, not only for making the current feature work.

Avoid:

- Unnecessary complexity
- Duplicate logic
- Giant files
- Giant functions
- Hardcoded configuration
- Hidden side effects
- Unnecessary dependencies
- Unused code
- Dead code
- Temporary hacks
- Security bypasses

## 3. Architecture First

Before implementing a major feature, understand where the feature belongs in the architecture.

Do not place functionality randomly into existing files.

Every major feature should have a clearly defined responsibility.

Preferred structure:

```text
Input
  ↓
Processing
  ↓
Business Logic
  ↓
Security Validation
  ↓
Execution
  ↓
Verification
  ↓
Output
```

The AI reasoning layer must not directly control operating-system resources.

## 4. Separation of Responsibilities

Each module should have one primary responsibility.

Example:

screen/
    screen_capture.py

vision/
    detector.py

ocr/
    engine.py

context/
    context_engine.py

ai/
    reasoning.py

security/
    permission_manager.py

automation/
    action_executor.py

verification/
    action_verifier.py

Do not place all functionality inside a single module.

## 5. Single Responsibility Principle

A class or module should have one primary reason to change.

Bad:

```python
class OmniSense:
    def capture_screen(self):
        ...
```

    def run_ocr(self):
        ...

    def call_ai(self):
        ...

    def delete_file(self):
        ...

    def save_database(self):
        ...

Preferred:

```python
class ScreenCapture:
    ...
```

```python
class OCREngine:
    ...
```

```python
class AIReasoner:
    ...
```

```python
class FileManager:
    ...
```

```python
class DatabaseManager:
    ...
```

## 6. Dependency Direction

Dependencies should generally flow from higher-level orchestration toward lower-level services.

Preferred:

```text
Application Layer
       ↓
Service Layer
       ↓
Domain / Core Logic
       ↓
Infrastructure
```

Security services should remain independently enforceable.

The execution layer must not be able to bypass security validation.

## 7. Project Structure

The exact structure may evolve during development, but the project should maintain clear separation.

Recommended structure:

```text
OMNIVISION_AI/
│
├── Docs/
│   ├── AI_DEVELOPMENT_RULES.md
│   ├── DEVELOPMENT_PHASES.md
│   ├── PROJECT_VISION.md
│   ├── PROJECT_BOUNDARIES.md
│   ├── SECURITY_MODEL.md
│   ├── SRS.md
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── TECH_STACK.md
│   ├── CODING_STANDARDS.md
│   └── TESTING_AND_EVALUATION.md
│
├── src/
│   ├── core/
│   ├── vision/
│   ├── ocr/
│   ├── context/
│   ├── ai/
│   ├── security/
│   ├── automation/
│   ├── verification/
│   ├── storage/
│   └── utils/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── security/
│   └── e2e/
│
├── config/
│
├── scripts/
│
├── assets/
│
├── logs/
│
├── requirements.txt
├── README.md
└── main.py
```

The actual architecture must follow SYSTEM_ARCHITECTURE.md.

## 8. Naming Conventions

Naming must be descriptive and meaningful.

Avoid:

- x
- a
- tmp
- data2
- thing
- test123

Prefer:

- screen_frame
- ocr_result
- active_window
- confidence_score
- action_request
- permission_result

## 9. Python File Naming

Python files must use:

snake_case.py

Examples:

- screen_capture.py
- ocr_engine.py
- context_engine.py
- permission_manager.py
- action_executor.py

Avoid:

- ScreenCapture.py
- screenCapture.py
- SCREEN_CAPTURE.py

## 10. Python Class Naming

Classes must use:

PascalCase

Examples:

```python
class ScreenCapture:
    ...
```

```python
class OCREngine:
    ...
```

```python
class ContextEngine:
    ...
```

```python
class PermissionManager:
    ...
```

```python
class ActionExecutor:
    ...
```

## 11. Python Function Naming

Functions and methods must use:

snake_case

Examples:

- capture_screen()
- extract_text()
- detect_ui_elements()
- classify_context()
- validate_action()
- execute_action()
- verify_result()

## 12. Variable Naming

Variables must use descriptive snake_case names.

Good:

```python
screen_width = 1920
confidence_score = 0.94
active_application = "Visual Studio Code"
```

Avoid:

```python
sw = 1920
cs = 0.94
app1 = "Visual Studio Code"
```

Short names may be used for conventional local variables such as:

- i
- j
- x
- y

when their meaning is obvious from context.

## 13. Constant Naming

Constants must use:

UPPER_SNAKE_CASE

Example:

```python
MAX_CAPTURE_RATE = 10
DEFAULT_TIMEOUT = 30
MAX_RETRY_COUNT = 3
PROTECTED_PATHS = [...]
```

## 14. Boolean Naming

Boolean variables should clearly communicate true/false meaning.

Preferred:

- is_active
- is_authorized
- is_protected
- has_permission
- should_retry
- can_execute

Avoid:

- active
- permission
- retry
- execute

when the boolean meaning is unclear.

## 15. Function Design

Functions should be small and focused.

Avoid extremely large functions.

Bad:

```python
def process_everything():
    # 500 lines
    ...
```

Preferred:

```python
def capture_screen():
    ...
```

```python
def preprocess_frame():
    ...
```

```python
def detect_elements():
    ...
```

```python
def analyze_context():
    ...
```

```python
def generate_response():
    ...
```

A function should ideally perform one logical task.

## 16. Function Length

There is no absolute maximum function length.

However, a function should be reviewed for decomposition when it becomes difficult to understand.

Warning signs:

- Multiple unrelated responsibilities
- Deep nesting
- Many conditional branches
- Excessive local variables
- Difficult testing
- Repeated logic

Readable code is more important than an arbitrary line limit.

## 17. Class Design

Classes should represent meaningful project concepts.

Examples:

- ScreenCapture
- FrameProcessor
- OCREngine
- VisionDetector
- ContextEngine
- AIReasoner
- PermissionManager
- RiskClassifier
- ActionExecutor
- ActionVerifier

Avoid creating classes merely to wrap a single trivial function unless there is a clear architectural reason.

## 18. Type Hints

Python code should use type hints for public functions, methods, and important variables.

Preferred:

```python
def calculate_confidence(
    detected_text: str,
    confidence: float
) -> float:
    ...
```

For collections:

```python
from typing import List
```

```python
def get_detected_elements() -> list[dict]:
    ...
```

Use modern Python typing where supported by the project's Python version.

## 19. Return Types

Public functions should specify return types.

Example:

```python
def is_authorized(action: str) -> bool:
    ...
```

For optional values:

```python
def get_active_window() -> str | None:
    ...
```

For structured data, prefer explicit models or typed structures when practical.

## 20. Data Models

Important data flowing between modules should use structured representations.

Avoid passing loosely structured dictionaries everywhere.

Example:

```python
from dataclasses import dataclass
```


```python
@dataclass
class UIElement:
    element_type: str
    text: str
    confidence: float
    x: int
    y: int
    width: int
    height: int
```

Structured data makes the system easier to test and maintain.

## 21. Mutable Global State

Avoid unnecessary global mutable state.

Bad:

```python
CURRENT_SCREEN = None
CURRENT_ACTION = None
GLOBAL_CONTEXT = {}
```

Prefer controlled state management through:

- Services
- Context objects
- Dependency injection
- State managers

Global constants are acceptable when appropriate.

## 22. Configuration Management

Configuration must not be scattered throughout the source code.

Avoid:

```python
API_URL = "https://example.com"
TIMEOUT = 30
MODEL_NAME = "some-model"
```

inside multiple unrelated modules.

Prefer centralized configuration.

Example:

config/
    settings.py
    environment.py

or an equivalent configuration system defined by the project architecture.

## 23. Secrets Management

Secrets must never be hardcoded into source code.

Never write:

```python
API_KEY = "my-secret-key"
PASSWORD = "mypassword"
TOKEN = "secret-token"
```

Use:

- Environment variables
- Secure secret storage
- Development .env files excluded from version control
- Platform-specific secret managers where appropriate

## 24. .gitignore

Sensitive and generated files must be excluded from version control.

Typical entries may include:

- .env
- .venv/
- venv/
- __pycache__/
- *.pyc
- logs/
- models/
- temp/
- .cache/

The exact .gitignore must reflect the project architecture.

## 25. Error Handling

Errors must be handled explicitly.

Avoid:

```python
try:
    ...
except:
    pass
```

This hides failures and makes debugging difficult.

Preferred:

```python
try:
    result = perform_operation()
except FileNotFoundError as exc:
    logger.error("Required file was not found: %s", exc)
    raise
```

Only catch exceptions that can be handled meaningfully.

## 26. Exception Specificity

Prefer specific exceptions over generic exceptions.

Avoid:

except Exception:
    ...

unless there is a strong architectural reason.

Prefer:

except TimeoutError:
    ...

except PermissionError:
    ...

except FileNotFoundError:
    ...

```python
If a broad exception handler is required at an application boundary, it must log the failure and preserve safe behavior.
```

## 27. Security Errors

Security-related failures must fail safely.

Example:

```python
if not permission_manager.is_authorized(action):
    raise PermissionError("Action is not authorized")
```

Do not silently continue after a security failure.

## 28. Fail-Closed Principle

Security-sensitive operations must follow:

```text
UNKNOWN
   ↓
DENY
```

Example:

```python
permission_result = permission_manager.check(action)
```

```python
if permission_result is not True:
    return ActionResult.blocked()
```

Never assume permission when the permission state is unknown.

## 29. Logging Standards

Use structured logging rather than random print() statements for application diagnostics.

Preferred:

```python
logger.info("Screen capture started")
logger.warning("OCR confidence below threshold")
logger.error("Action execution failed")
```

Avoid:

print("something happened")

for production diagnostics.

## 30. Sensitive Logging

Never log secrets.

Never log:

- Passwords
- API keys
- Access tokens
- Session tokens
- Private credentials

Sensitive values must be redacted.

Example:

- API Key: ********
- Token: ********

## 31. Log Levels

Use appropriate log levels.

- DEBUG
- INFO
- WARNING
- ERROR
- CRITICAL

General guidance:

DEBUG

Detailed development information.

INFO

Normal application events.

WARNING

Unexpected but recoverable situations.

ERROR

Operation failures.

CRITICAL

Severe failures requiring immediate attention.

## 32. Comments

Comments should explain why something exists, not simply repeat what the code does.

Bad:

# Add 1 to count
count += 1

Better:

# Increment retry count before attempting recovery.
retry_count += 1

Use comments for:

- Non-obvious logic
- Security decisions
- Important constraints
- Algorithm explanations
- Workarounds
- Architectural reasons

## 33. TODO Comments

TODO comments must be meaningful.

Good:

# TODO: Replace temporary OCR fallback with the production OCR adapter
# after Phase 2 evaluation.

Avoid:

# TODO fix

Temporary TODOs should not remain indefinitely.

## 34. Magic Numbers

Avoid unexplained numeric values.

Bad:

```python
if confidence > 0.72:
    ...
```

Preferred:

```python
MIN_OCR_CONFIDENCE = 0.72
```

```python
if confidence > MIN_OCR_CONFIDENCE:
    ...
```

This improves readability and maintainability.

## 35. Reusable Logic

Repeated logic should be extracted into reusable functions or services.

Bad:

# Same path validation repeated in 5 modules

Preferred:

path_validator.is_allowed(path)

Security-sensitive logic must have one authoritative implementation whenever possible.

## 36. Security Logic Centralization

Security rules must not be duplicated across unrelated modules.

For example, protected-path validation should be centralized:

security/
    path_validator.py

Other modules should call the security service instead of implementing their own protection logic.

## 37. AI Output Handling

AI-generated output must always be treated as untrusted data.

Never directly execute:

ai_output

as:

os.system(ai_output)

or:

```python
subprocess.run(ai_output, shell=True)
```

without strict validation and authorization.

AI output must first be converted into a structured action representation.

## 38. Structured AI Actions

Preferred approach:

```python
@dataclass
class ActionRequest:
    action_type: str
    target: str | None
    parameters: dict
    confidence: float
```

Then:

```text
AI Output
   ↓
Parser
   ↓
Structured Action
   ↓
Validator
   ↓
Risk Classifier
   ↓
Permission Manager
   ↓
Executor
```

## 39. Path Validation

Any user-provided or AI-generated path must be validated.

Validation should consider:

- Absolute paths
- Relative paths
- Path traversal
- Symbolic links
- Protected directories
- Existing files
- File permissions

Example:

../../Windows/System32

must not bypass protected-path rules.

## 40. Command Execution

Shell command execution must be isolated behind a dedicated service.

Preferred:

```text
AI
 ↓
Command Parser
 ↓
Command Validator
 ↓
Security Layer
 ↓
Command Executor
```

Avoid shell execution directly inside AI, vision, OCR, or UI modules.

## 41. Subprocess Safety

When subprocesses are required:

Prefer argument arrays over shell strings.
Avoid unnecessary shell=True.
Validate executable paths.
Validate arguments.
Apply timeouts.
Capture output safely.
Handle failures.
Terminate runaway processes where appropriate.

Example:

```python
subprocess.run(
    [executable, argument],
    timeout=30,
    check=True
)
```

## 42. File Operation Safety

File operations must be explicit.

Preferred:

file_manager.delete_file(
    path=approved_path,
    authorization=authorization
)

Avoid:

os.remove(ai_generated_path)

without validation.

## 43. Destructive Operations

Destructive functions should make their intent obvious.

Example:

- delete_file()
- delete_directory()
- overwrite_file()

They should not be hidden behind vague names such as:

- process()
- cleanup()
- handle()

unless the operation is genuinely non-destructive.

## 44. User Confirmation

Functions that require confirmation must not silently execute the action.

Example:

```python
if action.requires_confirmation:
    confirmation = confirmation_service.request(action)
```

    if not confirmation.approved:
        return ActionResult.cancelled()

## 45. Action Verification

Important actions must be verified after execution.

Preferred:

```text
Execute
   ↓
Observe
   ↓
Verify
   ↓
Report
```

Example:

```python
result = executor.execute(action)
```

```python
if result.success:
    verification = verifier.verify(action)
```

    if not verification.success:
        return ActionResult.verification_failed()

## 46. AI Hallucination Handling

AI responses may be incorrect.

The code must not treat AI confidence as absolute truth.

For important decisions, use:

- Validation
- Deterministic checks
- Application state
- File existence checks
- OS-level verification
- Confidence thresholds

AI reasoning must not replace deterministic security checks.

## 47. Computer Vision Confidence

Computer Vision predictions should expose confidence where available.

Example:

Detection(
    label="button",
    confidence=0.96
)

Low-confidence detections should not automatically trigger high-risk interactions.

## 48. OCR Confidence

OCR confidence must be considered before automation.

Example:

```text
OCR Confidence < Threshold
        ↓
Do Not Automatically Click/Type Based On Result
        ↓
Request Reprocessing or User Confirmation
```

## 49. Async and Background Tasks

Background operations should be used carefully.

Every background task should have:

- Cancellation
- Error handling
- Resource cleanup
- Timeout where appropriate
- Logging

Avoid creating uncontrolled threads or processes.

## 50. Thread Safety

Shared mutable state must be protected where concurrent access is possible.

Potentially shared components include:

- Screen state
- Context state
- Action queues
- AI sessions
- Model resources
- Cache
- Event queues

Use appropriate synchronization primitives or architecture-level isolation.

## 51. Resource Cleanup

Resources must be released reliably.

Examples:

with open(file_path, "r") as file:
    data = file.read()

For external resources:

```text
Acquire
   ↓
Use
   ↓
Release
```

Do not leave:

- Files open
- Cameras locked
- Screen capture handles active
- Processes running
- Database connections open
- Network connections hanging

## 52. Model Loading

AI/Deep Learning models should not be loaded repeatedly for every request unless required.

Preferred:

```text
Application Start
      ↓
Model Initialization
      ↓
Model Ready
      ↓
Multiple Inferences
```

Model lifecycle must be controlled.

## 53. Model Resource Management

Large models may consume significant RAM or VRAM.

The implementation should consider:

- Model size
- Inference frequency
- Batch size
- GPU memory
- CPU fallback
- Model unloading
- Quantization where appropriate

Optimization must be based on actual measurements.

## 54. Computer Vision Pipeline

Computer Vision processing should be modular.

Preferred:

```text
Frame
 ↓
Preprocessing
 ↓
Detection
 ↓
Classification
 ↓
OCR
 ↓
UI Representation
 ↓
Context Engine
```

Each stage should have a clear responsibility.

## 55. Image Processing

Image preprocessing functions should avoid modifying original source frames unexpectedly.

Prefer:

```python
processed_frame = preprocess(frame)
```

rather than unexpectedly modifying shared state.

## 56. AI Prompt Management

AI prompts should not be scattered throughout the codebase.

Where practical, keep prompts organized.

Example:

ai/
    prompts/
        system_prompt.txt
        vision_prompt.txt
        context_prompt.txt
        action_prompt.txt

Prompts should be version-controlled and documented when they materially affect system behavior.

## 57. Prompt Security

Prompts must clearly separate:

- System Instructions
- User Instructions
- External Content
- AI Context

External content must not be inserted into trusted instruction sections without proper delimitation.

## 58. API Design

Internal services should expose clear interfaces.

Example:

```python
class VisionService:
```

    def analyze_frame(
        self,
        frame: bytes
    ) -> VisionResult:
        ...

Avoid exposing unnecessary implementation details between modules.

## 59. Return Objects

For important operations, prefer structured result objects.

Example:

```python
@dataclass
class ActionResult:
    success: bool
    status: str
    message: str
    error_code: str | None = None
```

This is preferable to returning inconsistent values such as:

True
False
None
"success"

```python
from the same function.
```

## 60. Error Codes

Important services may use stable error codes.

Example:

- ACTION_NOT_AUTHORIZED
- PROTECTED_PATH
- OCR_FAILED
- VISION_FAILED
- MODEL_UNAVAILABLE
- TIMEOUT
- VERIFICATION_FAILED
- RESOURCE_UNAVAILABLE

Error codes should be documented where appropriate.

## 61. API and External Service Failure

External services may fail.

Code must handle:

- Timeout
- Connection failure
- Rate limiting
- Invalid response
- Authentication failure
- Service unavailable
- Malformed response

External failure must not compromise local security.

## 62. Retry Policy

Retries must be controlled.

Every retry policy should define:

- Maximum Attempts
- Retryable Errors
- Delay
- Backoff
- Final Failure Behavior

Do not retry destructive actions blindly.

## 63. Caching

Caching may be used when it improves performance.

However, sensitive information must not be cached unnecessarily.

Cache entries should have:

- Expiration
- Clear ownership
- Cleanup policy
- Appropriate access controls

## 64. Database Access

Database access should be isolated behind appropriate repository or service layers where practical.

Avoid scattering raw database queries throughout unrelated modules.

Preferred:

```text
Service
   ↓
Repository
   ↓
Database
```

## 65. Input Validation

All external inputs must be validated.

External inputs include:

- User input
- AI output
- OCR output
- Vision output
- Network responses
- File contents
- Configuration values

Never assume external data is valid.

## 66. Output Encoding

When displaying external or AI-generated content in a UI:

- Escape content appropriately
- Avoid unsafe HTML rendering
- Avoid arbitrary code execution
- Treat content as data

## 67. Dependency Rules

A new dependency should only be added when:

It provides meaningful functionality.
The existing stack cannot reasonably provide the functionality.
It is compatible with the project.
It has acceptable security characteristics.
It does not create unnecessary architectural complexity.

AI coding agents must not install random libraries simply to solve small problems.

## 68. Dependency Documentation

When a significant dependency is introduced, document:

- Dependency
- Purpose
- Version
- Reason for Selection
- Security Considerations

## 69. Version Pinning

Production dependencies should use controlled versions.

Example:

```python
package==version
```

or another version strategy defined by the project.

Uncontrolled dependency upgrades should be avoided.

## 70. Testing Requirements

Every major feature must include appropriate tests.

Minimum expectations:

- Unit Tests
- Integration Tests
- Security Tests
- Regression Tests

Critical workflows should also have end-to-end tests.

## 71. Test Naming

Test names should describe expected behavior.

Good:

```python
def test_protected_system32_path_is_blocked():
    ...
```

Bad:

```python
def test_path():
    ...
```

## 72. Test Isolation

Tests should not depend on:

- Personal files
- Production data
- User-specific configuration
- External services unless explicitly required
- Random uncontrolled system state

Tests should use fixtures and mocks where appropriate.

## 73. Security Testing

Security-sensitive modules require negative tests.

Examples:

```text
Protected path → BLOCK
Unauthorized action → BLOCK
Invalid action → BLOCK
Prompt injection → IGNORE/BLOCK
Missing permission → BLOCK
Malformed AI output → REJECT
```

## 74. Code Formatting

Code must follow the formatting conventions of the selected language and project tooling.

For Python, use an automated formatter where configured.

Formatting should be consistent across the entire project.

## 75. Linting

Static analysis should be used where practical.

Linting should detect:

- Unused imports
- Undefined variables
- Suspicious code
- Style problems
- Potential bugs

Linting errors should be resolved before merging major features.

## 76. Import Rules

Imports should be:

- Organized
- Minimal
- Deterministic

Avoid unused imports.

Avoid circular imports.

```python
If circular dependencies appear, review the architecture rather than applying random import hacks.
```

## 77. Circular Dependency Rule

Circular dependencies should generally be treated as an architectural warning.

Instead of:

```text
Module A → Module B
Module B → Module A
```

prefer:

```text
Module A
    ↓
Shared Interface
    ↑
Module B
```

or refactor shared responsibilities into a separate module.

## 78. Documentation Requirements

Every major module should have documentation describing:

- Purpose
- Responsibilities
- Inputs
- Outputs
- Dependencies
- Security considerations

Public APIs should have docstrings.

## 79. Docstring Standard

Public functions should have useful docstrings.

Example:

```python
def detect_ui_elements(frame: Image) -> list[UIElement]:
    """
    Detect visible UI elements from a processed screen frame.
```

    Args:
        frame: Preprocessed screen image.

    Returns:
        A list of detected UI elements with confidence scores.
    """

## 80. README Synchronization

```python
If installation, configuration, or usage changes significantly, update:
```

README.md

Do not allow documentation to describe an outdated system.

## 81. Git Commit Standards

Commits should be meaningful.

Preferred:

- feat: add screen capture service
- feat: add OCR pipeline
- fix: block protected system paths
- test: add action authorization tests
- refactor: separate vision and OCR services
- docs: update architecture documentation

Avoid:

- update
- changes
- final
- done
- asdf

## 82. Commit Scope

One commit should ideally represent one logical change.

Avoid mixing:

- Feature
- +
- Unrelated refactor
- +
- Documentation cleanup
- +
- Dependency changes

unless there is a clear reason.

## 83. Branching

Feature development should preferably use separate branches.

Example:

```text
main
 │
 ├── feature/screen-capture
 ├── feature/ocr-engine
 ├── feature/context-engine
 ├── feature/security-layer
 └── feature/action-verification
```

Branch naming should communicate intent.

## 84. Pull Request / Review Standards

Before merging major changes, verify:

- Feature Works
- Tests Pass
- Security Checks Pass
- No Unnecessary Dependencies
- Documentation Updated
- No Debug Code
- No Secrets
- No Scope Creep

## 85. Debug Code

Temporary debugging code must not remain in production code.

Remove:

- print(...)
- breakpoint()
- pdb.set_trace()
- temporary_test_function()

before finalizing a feature.

## 86. Hardcoded Paths

Do not hardcode user-specific paths.

Avoid:

"C:\\Users\\Rajat\\Desktop\\project"

Use:

- Configuration
- Environment variables
- Platform path utilities
- User directories obtained through supported APIs

## 87. Cross-Platform Paths

Use platform-safe path handling.

Preferred:

```python
from pathlib import Path
```

```python
file_path = Path(base_directory) / "data" / "result.json"
```

Avoid manually concatenating paths:

```python
path = base_directory + "\\data\\result.json"
```

## 88. File Encoding

Text files should use UTF-8 unless there is a documented reason to use another encoding.

## 89. Timeouts

External operations should use reasonable timeouts.

Operations that may require timeouts include:

- Network requests
- AI API requests
- Model inference
- Subprocesses
- File operations involving external resources

No external operation should wait indefinitely without a clear reason.

## 90. Resource Limits

Where applicable, enforce limits on:

- File size
- Input size
- Image dimensions
- OCR processing
- AI prompt size
- Network response size
- Subprocess execution time
- Memory usage

This reduces stability and denial-of-service risks.

## 91. Security Over Convenience

Never weaken security merely because a safer implementation requires more code.

Bad approach:

```text
Disable validation
↓
Feature works
```

Correct approach:

```text
Understand the failure
↓
Fix architecture
↓
Preserve security
↓
Implement feature
```

## 92. No Security Bypass During Development

Developers and AI coding agents must not:

- Disable permission checks
- Comment out security validation
- Remove protected-path checks
- Hardcode administrator privileges
- Disable authentication
- Ignore failed security tests

even temporarily, unless working inside an isolated test environment and the change is clearly documented.

Security code must not be weakened simply to make development easier.

## 93. Temporary Workarounds

```python
If a temporary workaround is absolutely necessary:
```

Document it.
Isolate it.
Add a TODO.
Explain why it exists.
Define how it will be removed.
Do not compromise core security.

## 94. Refactoring Rules

Refactoring should improve:

- Readability
- Maintainability
- Testability
- Performance
- Architecture

Do not refactor unrelated modules while implementing a feature unless necessary.

Large refactors must be broken into manageable changes.

## 95. Backward Compatibility

When modifying an existing public interface:

- Check callers
- Update tests
- Update documentation
- Consider compatibility
- Document breaking changes

Do not silently break existing functionality.

## 96. Performance Optimization

Do not optimize based on assumptions.

Preferred process:

```text
Implement Correctly
      ↓
Measure
      ↓
Identify Bottleneck
      ↓
Optimize
      ↓
Measure Again
```

Security and correctness have priority over micro-optimizations.

## 97. GPU Usage

GPU acceleration may be used for Deep Learning and Computer Vision workloads when appropriate.

However, code must support controlled fallback behavior when GPU resources are unavailable.

Example:

```text
GPU Available
    ↓
Use GPU
```

```text
GPU Unavailable
    ↓
Use CPU / Safe Fallback
```

## 98. Model Inference Safety

Model inference must not directly trigger destructive actions.

Preferred:

```text
Model Prediction
      ↓
Interpretation
      ↓
Validation
      ↓
Risk Classification
      ↓
Authorization
      ↓
Action
```

## 99. Observability

Important components should expose useful diagnostic information.

Possible metrics:

- Screen Capture FPS
- OCR Latency
- Vision Latency
- AI Latency
- Action Latency
- Verification Latency
- CPU Usage
- RAM Usage
- GPU Usage
- Error Rate

Metrics should not contain sensitive user information.

## 100. Final Coding Rule

Every developer and AI coding agent working on OMNIVISION AI must follow this priority order:

- 1. Security
- 2. Correctness
- 3. Reliability
- 4. Maintainability
- 5. Testability
- 6. Performance
- 7. Convenience

Never reverse this order.

The ultimate coding principle is:

WRITE CODE THAT IS:

```text
SAFE
↓
CLEAR
↓
MODULAR
↓
TESTABLE
↓
MAINTAINABLE
↓
SCALABLE
```

## 101. Final Rule for AI Coding Agents

Before writing code, the AI coding agent must ask internally:

What problem am I solving?
Where does this functionality belong?
What existing module owns this responsibility?
Does this change respect the project boundaries?
Does this change respect the security model?
Does this change belong to the current development phase?
How will this feature be tested?
What happens when it fails?
What happens when the input is malicious?

```python
If the answer to any critical question is unclear, the agent must inspect the project documentation and existing architecture before implementation.
```

End of CODING_STANDARDS.md
