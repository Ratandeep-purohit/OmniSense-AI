# OmniSense AI — Phase 5 — UI / Visual Understanding

**Phase ID:** P05  
**Status:** Implemented (2026-09-22)  
**Principle:** Intelligence without uncontrolled authority.

## 1. Purpose

Phase 5 combines the validated outputs of Phases 2, 3 and 4 into a bounded representation of the currently observed desktop UI.

```text
VisualFrame + OCRResult + WindowDetectionResult
                    |
                    v
             Input Consistency
                    |
                    v
          UI Understanding Backend
                    |
                    v
               UIElement[]
                    |
                    v
             Relationships
                    |
                    v
          UIUnderstandingResult
                    |
                    v
                 Phase 6
```

The current implementation is deterministic and heuristic. It uses OCR text, OCR geometry and window metadata. It does not claim that OCR alone can prove a control is a button, checkbox, input or link.

## 2. Repository Implementation

| Component | Location | Responsibility |
|---|---|---|
| UI contracts | src/omnisense_ai/ui_understanding/models.py | Element, box, relationship and result schemas |
| Typed failures | src/omnisense_ai/ui_understanding/errors.py | Phase-specific failure taxonomy |
| Backend boundary | src/omnisense_ai/ui_understanding/backend.py | Pluggable UI interpretation |
| Service | src/omnisense_ai/ui_understanding/service.py | Validation, normalization and relationships |
| Public API | src/omnisense_ai/ui_understanding/__init__.py | Stable imports |
| Tests | tests/test_ui_understanding.py | Contract, validation and geometry coverage |

## 3. Input Contract

Phase 5 requires a VisualFrame, an OCRResult generated from the same frame sequence and monitor, and a WindowDetectionResult. Mismatched sequence or monitor identity is rejected so stale OCR cannot silently attach to a newer frame.

## 4. Output Contract

UIUnderstandingResult contains:

- structured UI elements;
- explicit relationships;
- foreground window ID when available;
- source monitor and frame sequence;
- source provenance categories;
- a truncation flag.

Each UIElement contains a result-local ID, type, pixel-space box, optional visible text, confidence, confidence level, state observation, provenance, related/parent IDs, and an interactable_observation flag.

The interactable_observation flag means only that the evidence resembles a control. It is never authorization to act.

## 5. Current Heuristic Semantics

The baseline backend maps OCR lines into observations:

- common action words such as Save, Submit, Cancel, Login and Next -> BUTTON candidate;
- text ending in ':' -> LABEL candidate;
- URL-like text -> LINK candidate;
- short remaining text -> LABEL candidate;
- other text -> TEXT candidate.

Every heuristic observation carries provenance and confidence so downstream systems can distinguish evidence from certainty.

## 6. Relationships

The service can emit:

- labels -> inputs/checkboxes/radios when spatially close;
- buttons -> nearby labels as contains_text;
- nearby elements as near.

Relationships are bounded and confidence-scored. Spatial proximity is evidence, not proof of semantic ownership.

## 7. Safety Boundary

Phase 5 is observation-only.

It MUST NOT click, type, move the mouse, focus or activate a window, open a URL, execute a command, interpret visible text as user authorization, or create an action request.

## 8. Resource and Privacy Controls

Limits bound element count, relationship count, text size and spatial association distance. No screenshot archive is retained. Logs contain counts, backend name and sequence metadata, not pixels or OCR text.

## 9. Verification

Run:

```powershell
python -m pytest
```

Phase-specific tests cover classification, provenance, sequence consistency, monitor consistency, geometry and invalid geometry.

## 10. Phase 6 Handoff

Phase 6 may consume UIUnderstandingResult as contextual evidence. It MUST preserve frame sequence, monitor identity, confidence and provenance, and MUST retain the distinction between observed control-like elements and authorized actions.

**Phase 5 rule:** understand the UI deeply, but never turn understanding into authority.
