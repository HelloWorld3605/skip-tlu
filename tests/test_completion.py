from skiptlu.completion.resolver import CompletionResolver
from skiptlu.handlers.router import HandlerRouter
from skiptlu.models.activity import Activity, ModuleType


def test_defaults_for_week3_activity_types():
    resolver = CompletionResolver()

    assert resolver.resolve(Activity(id=1, module=ModuleType.LESSON, name="x"))[0].type == "reach_end"
    assert resolver.resolve(Activity(id=2, module=ModuleType.ASSIGNMENT, name="x"))[0].type == "submission"
    assert resolver.resolve(Activity(id=3, module=ModuleType.QUIZ, name="x"))[0].type == "attempt"
    assert resolver.resolve(Activity(id=4, module=ModuleType.FEEDBACK, name="x"))[0].type == "response"


def test_router_supports_tlu_modules():
    router = HandlerRouter()
    for module in ModuleType:
        activity = Activity(id=1, module=module, name="x")
        assert router.for_activity(activity) is not None
