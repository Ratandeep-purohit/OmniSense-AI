from datetime import datetime,timezone
import pytest
from omnisense_ai.ai_vlm import AIConfig,AIVLMService,DeterministicAIProvider
from omnisense_ai.context_engine import ContextAge,ContextFreshness,ContextSnapshot,DesktopContext
from omnisense_ai.assistant import AssistantConfig,AssistantInputError,AssistantMode,AssistantRequest,AssistantSecurityError,AssistantStatus,IntelligentAssistant

def snapshot():
    now=datetime.now(timezone.utc)
    c=DesktopContext("ctx-assistant",now,"primary",1,ContextFreshness.FRESH,ContextAge(now,0,ContextFreshness.FRESH),(),"Open Settings",None,"test-app","Settings",0,0,("test",))
    return ContextSnapshot(context=c)

def assistant(**kwargs):
    return IntelligentAssistant(AIVLMService(DeterministicAIProvider(),AIConfig(enabled=True,provider="deterministic-test")),AssistantConfig(**kwargs))

def test_answer_uses_phase7_gateway():
    r=assistant().respond(snapshot(),AssistantRequest("What is on my screen?"))
    assert r.status is AssistantStatus.SUCCESS and r.grounded and "untrusted evidence" in r.answer.lower()

def test_clarification_does_not_call_ai():
    r=assistant().respond(snapshot(),AssistantRequest("Help",mode=AssistantMode.CLARIFY))
    assert r.status is AssistantStatus.NEEDS_CLARIFICATION and r.ai_request_id=="assistant-no-ai"

def test_suggestions_are_non_executing():
    r=assistant().respond(snapshot(),AssistantRequest("What could I do next?",mode=AssistantMode.SUGGEST))
    assert r.status is AssistantStatus.SUCCESS

def test_suggestions_can_be_disabled():
    with pytest.raises(AssistantSecurityError): assistant(allow_suggestions=False).respond(snapshot(),AssistantRequest("Suggest",mode=AssistantMode.SUGGEST))

def test_instruction_limit():
    with pytest.raises(AssistantInputError): assistant(max_instruction_chars=10).respond(snapshot(),AssistantRequest("x"*11))

def test_empty_instruction_rejected():
    with pytest.raises(ValueError): AssistantRequest("")

def test_refuse_mode_remains_conversational():
    r=assistant().respond(snapshot(),AssistantRequest("Delete this file",mode=AssistantMode.REFUSE))
    assert r.status is AssistantStatus.SUCCESS
