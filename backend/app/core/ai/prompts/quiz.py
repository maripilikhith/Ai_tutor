"""
AI Study Companion — Quiz Prompt Templates

Prompt templates for generating quiz questions:
- MCQ (Multiple Choice Questions)
- Open-ended questions
"""


def build_mcq_prompt(
    concept_name: str,
    concept_description: str,
    knowledge_chunks: str,
    difficulty: str,
    mastery_score: float,
    previous_questions: list[str] = None,
) -> str:
    """Build prompt for generating a multiple-choice question."""
    return f"""Generate a multiple-choice question about the concept "{concept_name}"
for a learner at {difficulty} difficulty level.

CONCEPT DESCRIPTION: {concept_description}

RELEVANT MATERIAL:
{knowledge_chunks}

LEARNER'S CURRENT MASTERY: {mastery_score:.0f}%

{f"AVOID ASKING THESE PREVIOUS QUESTIONS:\n" + "\n".join(f"- {q}" for q in previous_questions) if previous_questions else ""}

Difficulty guidelines:
- Easy: Test basic recall and recognition
- Medium: Test understanding and application
- Hard: Test analysis, synthesis, and edge cases

Return as JSON:
{{
  "question_text": "The question",
  "options": [
    {{"label": "A", "text": "Option text", "is_correct": false}},
    {{"label": "B", "text": "Option text", "is_correct": true}},
    {{"label": "C", "text": "Option text", "is_correct": false}},
    {{"label": "D", "text": "Option text", "is_correct": false}}
  ],
  "correct_answer": "B",
  "explanation": "Why the correct answer is correct and why others are wrong",
  "source_reference": "Page N of filename.pdf — use the (Source: ...) annotation from the RELEVANT MATERIAL above. If no page info, write the filename only."
}}

RULES:
- All options should be plausible (no obviously wrong answers)
- The question should test genuine understanding, not trick the learner
- Base the question on the provided learning material
- Exactly ONE option must have is_correct: true
- The correct_answer field must match the label of the correct option
- For source_reference: look at the (Source: filename — Page N) labels in the RELEVANT MATERIAL section and cite the exact page number"""


def build_open_ended_prompt(
    concept_name: str,
    concept_description: str,
    knowledge_chunks: str,
    difficulty: str,
    previous_questions: list[str] = None,
) -> str:
    """Build prompt for generating an open-ended question."""
    return f"""Generate an open-ended question about "{concept_name}"
at {difficulty} difficulty level.

CONCEPT DESCRIPTION: {concept_description}

RELEVANT MATERIAL:
{knowledge_chunks}

{f"AVOID ASKING THESE PREVIOUS QUESTIONS:\n" + "\n".join(f"- {q}" for q in previous_questions) if previous_questions else ""}

Return as JSON:
{{
  "question_text": "The question",
  "expected_key_points": ["point1", "point2", "point3"],
  "rubric": "What a good answer should include",
  "source_reference": "Page N of filename.pdf — use the (Source: ...) annotation from the RELEVANT MATERIAL above. If no page info, write the filename only."
}}

The question should require the learner to explain, analyze, or apply
the concept — not just recall a definition.

Difficulty guidelines:
- Easy: "Explain what X is and why it matters"
- Medium: "Compare X and Y, explaining the tradeoffs"
- Hard: "Given scenario Z, how would you apply X? What are the implications?\""
- For source_reference: look at the (Source: filename — Page N) labels in the RELEVANT MATERIAL section and cite the exact page number"""
