from jinja2 import Environment

from airas.features.create.create_experimental_design_subgraph.prompt.generate_advantage_criteria_prompt import (
    generate_advantage_criteria_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)


def generate_advantage_criteria(
    llm_name: LLM_MODEL,
    new_method: str,
    client: LLMFacadeClient | None = None,
) -> str:
    if client is None:
        client = LLMFacadeClient(llm_name=llm_name)

    env = Environment()
    template = env.from_string(generate_advantage_criteria_prompt)
    data = {
        "new_method": new_method,
    }
    messages = template.render(data)
    output, cost = client.generate(
        message=messages,
    )
    if output is None:
        raise ValueError("No response from LLM in generate_advantage_criteria.")
    return output


if __name__ == "__main__":
    llm_name = "o3-mini-2025-01-31"
    new_method = """
Adaptive Curvature Momentum (ACM) Optimizer Overview Existing adaptive optimizers such as Adam and AdaBelief dynamically adjust the learning rate based on the history of gradients. However, while these methods adapt to the magnitude of the gradients, they do not fully exploit information about the local curvature of the loss landscape. In this proposal, we introduce a new optimizer called Adaptive Curvature Momentum (ACM), which utilizes local quadratic approximations to adaptively adjust the update direction and scale. Method Standard Momentum Update Similar to SGD or Adam, ACM maintains a momentum term based on past gradients. Adaptive Learning Rate Scaling Uses second-order information (approximations of the Hessian) to dynamically adjust the learning rate for each direction. To reduce the computational cost of Hessian calculations, Fisher Information Matrix approximations can be employed. Curvature-Aware Adaptive Adjustment Estimates curvature by using the gradient change rate: Δ 𝑔 = 𝑔 𝑡 − 𝑔 𝑡 − 1 Δg=g t ​ −g t−1 ​ Modifies the learning rate based on curvature: 𝜂 𝑡 = 𝛼 1 + 𝛽 ⋅ Curvature ( 𝑔 𝑡 ) η t ​ = 1+β⋅Curvature(g t ​ ) α ​ where 𝛼 α is the base learning rate, and 𝛽 β controls the influence of curvature. Adaptive Regularization Encourages stable updates by incorporating an adaptive weight decay mechanism. When local curvature is high, the optimizer strengthens regularization to suppress excessive updates. Key Features and Benefits ✅ Combines Adam-style adaptability with curvature-aware updates ✅ Faster convergence: Adapts step sizes dynamically, taking larger steps in flat regions and smaller steps in sharp valleys. ✅ Hessian-free approximation: Utilizes efficient curvature estimation while maintaining low computational overhead. ✅ Scalability: Suitable for large-scale models such as ResNets and Transformers.
"""
    output = generate_advantage_criteria(
        llm_name=llm_name,
        new_method=new_method,
    )
    print(output)
