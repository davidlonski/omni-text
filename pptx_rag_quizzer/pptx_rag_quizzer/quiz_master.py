from .utils import get_gemini_response

class QuizMaster:
    """Manages the quiz logic, including question generation and grading."""

    def __init__(self, rag_core):
        """
        Initializes the QuizMaster.

        Args:
            rag_core (RAGCore): An instance of the RAGCore to get context from.
        """
        self.rag_core = rag_core

    def generate_question(self):
        """
        Generates a new question based on a random context from the document.

        Returns:
            dict or None: A dictionary containing the question, answer, and context,
                          or None if generation fails.
        """
        random_context = self.rag_core.get_random_context()
        if not random_context:
            return None
 
        prompt = f"""
        You are an expert quiz designer. Based on the following text from a document, generate one clear, open-ended question that tests understanding of a key concept. Also, provide the correct answer based *only* on the text.

        Context from document:
        ---
        {random_context}
        ---

        Respond in the following format, and nothing else:
        Question: [Your question here]
        Answer: [The correct answer based on the text]
        """
        response = get_gemini_response(prompt)

        print("\n--------This is the prompt--------\n")
        print(prompt)
        print("\n--------------------------------\n")
        print("--------This is the response--------\n")
        print(response)
        print("\n--------------------------------")

        if response and "Question:" in response and "Answer:" in response:
            try:
                parts = response.split("Answer:")
                question = parts[0].replace("Question:", "").strip()
                correct_answer = parts[1].strip()
                return {
                    "question": question,
                    "correct_answer": correct_answer,
                    "context": random_context
                }
            except IndexError:
                return None
        return None

    def grade_answer(self, quiz_data, user_answer):
        """
        Grades the user's answer against the correct answer.

        Args:
            quiz_data (dict): The dictionary containing the question and correct answer.
            user_answer (str): The user's submitted answer.

        Returns:
            bool: True if the answer is correct, False otherwise.
        """
        prompt = f"""
        You are an AI quiz grader. Evaluate if the user's answer is semantically similar to the correct answer.
        The question was: "{quiz_data['question']}"
        The correct answer is: "{quiz_data['correct_answer']}"
        The user's answer is: "{user_answer}"

        Does the user's answer match the meaning of the correct answer? Respond with only 'Correct' or 'Incorrect'.
        """
        evaluation = get_gemini_response(prompt)

        print("\n--------This is the prompt--------\n")
        print(prompt)
        print("\n--------------------------------\n")
        print("--------This is the evaluation--------\n")
        print(evaluation)
        print("\n--------------------------------")

        return evaluation is not None and 'Correct' in evaluation

    def get_hint(self, quiz_data, user_answer):
        """
        Generates a hint for an incorrect answer.

        Args:
            quiz_data (dict): The dictionary containing the question, correct answer, and context.
            user_answer (str): The user's incorrect answer.

        Returns:
            str: A helpful hint.
        """
        prompt = f"""
        You are a helpful AI tutor. The user answered a quiz question incorrectly. Provide a hint to guide them to the correct answer WITHOUT giving the answer away.

        The question was: "{quiz_data['question']}"
        The user's incorrect answer was: "{user_answer}"
        The correct answer is: "{quiz_data['correct_answer']}"
        The context from the document is: "{quiz_data['context']}"

        Generate a short, helpful hint.
        """

        hint = get_gemini_response(prompt)

        print("\n--------This is the prompt--------\n")
        print(prompt)
        print("\n--------------------------------\n")
        print("--------This is the hint--------\n")
        print(hint)
        print("\n--------------------------------")

        return hint
