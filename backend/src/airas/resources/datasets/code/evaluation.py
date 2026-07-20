# Curated dataset registry (see resources/datasets/registry.py for the
# subfield aggregation). HuggingFace dataset IDs and arXiv citations are
# verified on entry; use search_huggingface_hub for un-curated needs.
CODE_EVALUATION_DATASETS: dict = {
    "humaneval": {
        "description": "Dataset Card for OpenAI HumanEval Dataset Summary The HumanEval dataset released by OpenAI includes 164 programming problems with a function sig- nature, docstring, body, and several unit tests. They were handwritten to ensure not to be included in the training set of code genera",
        "huggingface_url": "https://huggingface.co/datasets/openai/openai_humaneval",
        "task_type": "text-generation",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("openai/openai_humaneval")""",
        "citation": """@misc{chen2021,
  title = {Evaluating Large Language Models Trained on Code},
  author = {Mark Chen and Jerry Tworek and Heewoo Jun and Qiming Yuan and Henrique Ponde de Oliveira Pinto and Jared Kaplan and Harri Edwards and Yuri Burda and Nicholas Joseph and Greg Brockman and Alex Ray and Raul Puri and Gretchen Krueger and Michael Petrov and Heidy Khlaaf and Girish Sastry and Pamela Mishkin and Brooke Chan and Scott Gray and Nick Ryder and Mikhail Pavlov and Alethea Power and Lukasz Kaiser and Mohammad Bavarian and Clemens Winter and Philippe Tillet and Felipe Petroski Such and Dave Cummings and Matthias Plappert and Fotios Chantzis and Elizabeth Barnes and Ariel Herbert-Voss and William Hebgen Guss and Alex Nichol and Alex Paino and Nikolas Tezak and Jie Tang and Igor Babuschkin and Suchir Balaji and Shantanu Jain and William Saunders and Christopher Hesse and Andrew N. Carr and Jan Leike and Josh Achiam and Vedant Misra and Evan Morikawa and Alec Radford and Matthew Knight and Miles Brundage and Mira Murati and Katie Mayer and Peter Welinder and Bob McGrew and Dario Amodei and Sam McCandlish and Ilya Sutskever and Wojciech Zaremba},
  year = {2021},
  eprint = {2107.03374},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2107.03374}
}""",
    },
    "mbpp": {
        "description": "Dataset Card for Mostly Basic Python Problems (mbpp) Dataset Summary The benchmark consists of around 1,000 crowd-sourced Python programming problems, designed to be solvable by entry level programmers, covering programming fundamentals, standard library functionality, and so on.",
        "huggingface_url": "https://huggingface.co/datasets/google-research-datasets/mbpp",
        "task_type": "text-generation",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("google-research-datasets/mbpp")""",
        "citation": """@misc{austin2021,
  title = {Program Synthesis with Large Language Models},
  author = {Jacob Austin and Augustus Odena and Maxwell Nye and Maarten Bosma and Henryk Michalewski and David Dohan and Ellen Jiang and Carrie Cai and Michael Terry and Quoc Le and Charles Sutton},
  year = {2021},
  eprint = {2108.07732},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2108.07732}
}""",
    },
    "bigcodebench": {
        "description": "BigCodeBench The dataset has 2 variants: BigCodeBench-Complete: Code Completion based on the structured docstrings. &nbsp;BigCodeBench-Instruct: Code Generation based on the NL-oriented instructions. The overall statistics of the dataset are as follows: Complete Instruct # Task 1",
        "huggingface_url": "https://huggingface.co/datasets/bigcode/bigcodebench",
        "task_type": "text-generation",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("bigcode/bigcodebench")""",
        "citation": """@misc{zhuo2024,
  title = {BigCodeBench: Benchmarking Code Generation with Diverse Function Calls and Complex Instructions},
  author = {Terry Yue Zhuo and Minh Chien Vu and Jenny Chim and Han Hu and Wenhao Yu and Ratnadira Widyasari and Imam Nur Bani Yusuf and Haolan Zhan and Junda He and Indraneil Paul and Simon Brunner and Chen Gong and Thong Hoang and Armel Randy Zebaze and Xiaoheng Hong and Wen-Ding Li and Jean Kaddour and Ming Xu and Zhihan Zhang and Prateek Yadav and Naman Jain and Alex Gu and Zhoujun Cheng and Jiawei Liu and Qian Liu and Zijian Wang and Binyuan Hui and Niklas Muennighoff and David Lo and Daniel Fried and Xiaoning Du and Harm de Vries and Leandro Von Werra},
  year = {2024},
  eprint = {2406.15877},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2406.15877}
}""",
    },
    "ds-1000": {
        "description": "DS-1000 in simplified format 🔥 Check the leaderboard from Eval-Arena on our project page. See testing code and more information (also the original fill-in-the-middle/Insertion format) in the DS-1000 repo. Reformatting credits: Yuhang Lai, Sida Wang",
        "huggingface_url": "https://huggingface.co/datasets/xlangai/DS-1000",
        "task_type": "text-generation",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("xlangai/DS-1000")""",
        "citation": """@misc{lai2022,
  title = {DS-1000: A Natural and Reliable Benchmark for Data Science Code Generation},
  author = {Yuhang Lai and Chengxi Li and Yiming Wang and Tianyi Zhang and Ruiqi Zhong and Luke Zettlemoyer and Scott Wen-tau Yih and Daniel Fried and Sida Wang and Tao Yu},
  year = {2022},
  eprint = {2211.11501},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2211.11501}
}""",
    },
}
