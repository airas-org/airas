from typing import Literal

# TODO(#1077): backend を足すたびに dispatch / status / cancel / build_store の match に case を書いて回る必要がある
ExecutionBackend = Literal["github_actions", "seyval"]
