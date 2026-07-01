from strands import Agent

policy_agent = Agent(

    name="Policy Agent",

    description="""
    Responsible for validating company leave
    policies before leave submission.

    Policies include:

    - Annual leave rules
    - Casual leave rules
    - Sick leave rules
    - Loss of Pay rules
    - Weekend/Holiday rules
    """
)