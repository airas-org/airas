from airas.core.types.github import GitHubRepositoryInfo
from airas.core.types.paper import PaperContent

readme_subgraph_input_data = {
    "github_repository_info": GitHubRepositoryInfo(
        github_owner="auto-res2",
        repository_name="experiment_matsuzawa_colab_dev54",
        branch_name="develop",
    ),
    "paper_content": PaperContent(
        title="Advanced Machine Learning for Automated Research",
        abstract="This paper presents a novel approach to automated research using advanced machine learning techniques. Our system, AIRAS, can automatically generate research papers, conduct experiments, and validate results. We demonstrate significant improvements in research efficiency and quality compared to traditional manual approaches. The system shows particular strength in handling complex research workflows and can be applied to various scientific domains including computer vision, natural language processing, and data mining.",
        introduction="Automated research represents a frontier in artificial intelligence, where systems can independently conduct scientific investigations. Traditional research methods often require significant human effort and time, creating bottlenecks in the pace of scientific discovery. Our work addresses these challenges through the development of AIRAS (Automated Intelligent Research Assistant System), which leverages advanced machine learning techniques to automate various aspects of the research process.",
        related_work="Previous work in automated research has focused primarily on individual components such as literature review automation, experimental design, and result analysis. However, few systems have attempted to integrate these components into a comprehensive research pipeline. Recent advances in large language models and automated reasoning have opened new possibilities for more sophisticated research automation.",
        background="The field of automated research builds upon several key technologies including natural language processing, automated reasoning, experimental design, and knowledge representation. These technologies must be carefully integrated to create systems capable of conducting meaningful scientific research. Our approach combines these elements with novel machine learning architectures specifically designed for research tasks.",
        method="AIRAS consists of several interconnected modules: (1) a literature analysis component that processes existing research papers, (2) a hypothesis generation module that identifies research gaps and formulates testable hypotheses, (3) an experimental design system that creates appropriate test methodologies, (4) an execution engine that runs experiments automatically, and (5) a results analysis component that interprets findings and generates conclusions.",
        experimental_setup="We evaluate AIRAS on three research domains: computer vision, natural language processing, and data mining. For each domain, we provide the system with a research topic and measure its ability to generate novel hypotheses, design appropriate experiments, and produce meaningful results. Evaluation metrics include research quality scores assessed by domain experts, time efficiency compared to manual research, and the novelty of generated insights.",
        results="AIRAS demonstrates strong performance across all evaluated domains. The system generated 45 novel research hypotheses, of which 38 were rated as scientifically valid by expert reviewers. Experimental designs produced by the system achieved 89% validity scores, and generated papers received an average quality rating of 4.2 out of 5.0. The system completed research tasks in an average of 12 hours compared to 6-8 weeks for manual research.",
        conclusion="We have presented AIRAS, a comprehensive system for automated research that demonstrates the feasibility of AI-driven scientific investigation. Our results show significant improvements in research efficiency while maintaining high quality standards. The system opens new possibilities for accelerating scientific discovery and democratizing access to research capabilities. Future work will focus on expanding to additional domains and improving the system's ability to handle complex interdisciplinary research questions.",
    ),
    # "devin_info": DevinInfo(
    #     session_id="abc123def456",
    #     devin_url="https://preview.devin.ai/devin/abc123def456-automated-research-execution",
    # ),
    "github_pages_url": "https://auto-res2.github.io/experiment_matsuzawa_retrieve_test2",
}
