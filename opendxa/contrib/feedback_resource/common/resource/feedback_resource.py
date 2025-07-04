from dana.common.resource.base_resource import BaseResource


class FeedbackResource(BaseResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def query(self, query: str):
        pass

    def get_feedback(self, question: str) -> str:
        """Get feedback or suggestion from the user. """
        print(f"\033[93m> Assistant : {question}\033[0m")
        return input(f"> User : ")