latex_subgraph_input_data = {
    "paper_content_with_placeholders": {
        "Title": "Test Paper for AMICT Evaluation",
        "Abstract": "This short paper presents a simplified evaluation of AMICT compared to a baseline. We include convergence and training loss analysis using selected visualizations.",
        "Introduction": "We briefly describe AMICT and its potential. This minimal version serves to verify LaTeX rendering and citation functionality.",
        "Related Work": "text", 
        "Background": "text", 
        "Method": "We simulate training using synthetic datasets and monitor convergence and loss curves for both AMICT and the baseline.",
        "Experimental Setup": "text", 
        "Results": (
            "Figure 1 (convergence_sequential_parallel_pair1.pdf) illustrates the convergence pattern for sequential vs. parallel training under simplified conditions, "
            "highlighting faster convergence for AMICT[[CITATION_1]].\n"
            "Figure 2 (convergence_solver_pair1.pdf) shows solver behavior across different initialization strategies.\n"
            "Figure 3 (training_loss_base_pair1.pdf) presents the loss curve for the baseline model.\n"
            "Figure 4 (training_loss_taa_pair1.pdf) shows the training loss for AMICT.\n"
            "These results demonstrate expected trends and help validate the evaluation pipeline."
        ),
        "Conclusions": "This test confirms that key figures render properly, and inline citations work as expected."
    },
    "references": {
        "[[CITATION_1]]": {
            "id": "https://openalex.org/W4317794926",
            "doi": "https://doi.org/10.1109/jstsp.2023.3239189",
            "title": "Edge Learning for B5G Networks With Distributed Signal Processing: Semantic Communication, Edge Computing, and Wireless Sensing",
            "authors": [
                "Wei Xu", "Zhaohui Yang", "Derrick Wing Kwan Ng",
                "Marco Levorato", "Yonina C. Eldar", "Mérouane Debbah"
            ],
            "year": 2023,
            "biblio": {
                "volume": "17",
                "issue": "1",
                "first_page": "9",
                "last_page": "39"
            },
            "journal": "IEEE Journal of Selected Topics in Signal Processing"
        }
    },
    "image_file_name_list": [
        "convergence_sequential_parallel_pair1.pdf",
        "convergence_solver_pair1.pdf",
        "training_loss_base_pair1.pdf",
        "training_loss_taa_pair1.pdf"
    ]
}
