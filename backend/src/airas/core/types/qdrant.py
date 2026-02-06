from typing import Literal

# https://qdrant.tech/documentation/concepts/search/#metrics
QdrantDistance = Literal["Dot", "Cosine", "Euclid", "Manhattan"]
