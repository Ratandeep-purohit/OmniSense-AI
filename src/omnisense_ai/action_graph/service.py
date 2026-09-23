from uuid import uuid4
from ..action_planning.models import ActionPlan
from .models import ActionGraph,ActionNode,ActionEdge
class ActionGraphBuilder:
    def build(self,plan: ActionPlan)->ActionGraph:
        nodes=[]; edges=[]
        for index,step in enumerate(plan.steps):
            pre=("context.matches", "target.resolved")
            post=("execution.success",step.expected_outcome)
            nodes.append(ActionNode(step.step_id,step,pre,post))
            if index: edges.append(ActionEdge(plan.steps[index-1].step_id,step.step_id))
        return ActionGraph(str(uuid4()),tuple(nodes),tuple(edges))
