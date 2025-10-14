DATASET_LIST = {
    "Text Datasets": {
        # Instruction Tuning
        "alpaca-cleaned": {
            "discription": "",
            "num_training_samples": "",
            "num_validation_samples": "",
            "huggingface_url": "https://huggingface.co/datasets/yahma/alpaca-cleaned",
            "language_distribution": "",
            "dependent packages": [],
            "code": """\
""",
            "citation": """\
""",
        },
        ## https://huggingface.co/datasets/databricks/databricks-dolly-15k
        "databricks-dolly-15k": "",
        # Preference Tuning
        # Multilingual
        # Code
        # Math
        "gsm8k": {
            "discription": "A dataset of elementary school math word problems requiring 2 to 8 steps to solve",
            "num_training_samples": 7473,
            "num_validation_samples": 1319,
            "huggingface_url": "https://huggingface.co/datasets/openai/gsm8k",
            "language_distribution": "English",
            "dependent packages": [],
            "code": """\
""",
            "citation": """\
@article{cobbe2021gsm8k,
  title={Training Verifiers to Solve Math Word Problems},
  author={Cobbe, Karl and Kosaraju, Vineet and Bavarian, Mohammad and Chen, Mark and Jun, Heewoo and Kaiser, Lukasz and Plappert, Matthias and Tworek, Jerry and Hilton, Jacob and Nakano, Reiichiro and Hesse, Christopher and Schulman, John},
  journal={arXiv preprint arXiv:2110.14168},
  year={2021}
}""",
        },
        "MATH": {
            "discription": "The MATH dataset consists of approximately 12,500 mathematics problems ranging from middle school to early university level. Each problem includes a natural language question, a detailed step-by-step solution, and a final answer, and it is widely used to evaluate large language models (LLMs) in terms of their abilities in mathematical reasoning, logical inference, and step-by-step problem solving.",
            "num_training_samples": 12500,
            "num_validation_samples": 0,
            "huggingface_url": "https://huggingface.co/datasets/qwedsacf/competition_math",
            "language_distribution": "English",
            "dependent packages": [],
            "code": """\
""",
            "example": """\
{'problem': 'A board game spinner is divided into three parts labeled $A$, $B$  and $C$. The probability of the spinner landing on $A$ is $\\frac{1}{3}$ and the probability of the spinner landing on $B$ is $\\frac{5}{12}$.  What is the probability of the spinner landing on $C$? Express your answer as a common fraction.',
 'level': 'Level 1',
 'type': 'Counting & Probability',
 'solution': 'The spinner is guaranteed to land on exactly one of the three regions, so we know that the sum of the probabilities of it landing in each region will be 1. If we let the probability of it landing in region $C$ be $x$, we then have the equation $1 = \\frac{5}{12}+\\frac{1}{3}+x$, from which we have $x=\\boxed{\\frac{1}{4}}$.'}""",
            "data_structure": """\
A data instance consists of a competition math problem and its step-by-step solution written in LaTeX and natural language. The step-by-step solution contains the final answer enclosed in LaTeX's \boxed tag.
- problem: The competition math problem.
- solution: The step-by-step solution.
- level: The problem's difficulty level from 'Level 1' to 'Level 5', where a subject's easiest problems for humans are assigned to 'Level 1' and a subject's hardest problems are assigned to 'Level 5'.
- type: The subject of the problem: Algebra, Counting & Probability, Geometry, Intermediate Algebra, Number Theory, Prealgebra and Precalculus.""",
            "citation": """\
@article{hendrycksmath2021,
    title={Measuring Mathematical Problem Solving With the MATH Dataset},
    author={Dan Hendrycks
    and Collin Burns
    and Saurav Kadavath
    and Akul Arora
    and Steven Basart
    and Eric Tang
    and Dawn Song
    and Jacob Steinhardt},
    journal={arXiv preprint arXiv:2103.03874},
    year={2021}
}""",
        },
        #         "sample": {
        #             "discription" : "",
        #             "num_training_samples": 0,
        #             "num_validation_samples": 0,
        #             "huggingface_url": "",
        #             "language_distribution": "English",
        #             "dependent packages": [],
        #             "code": """\
        # """,
        #             "example": """\
        # """,
        #             "data_structure": """\
        # """,
        #             "citation": """\
        # """
        #         },
    },
    "Image Datasets": {
        "ImageNet": "",
        "CIFAR-10": "",
    },
}
