from typing import List, Optional, Tuple

import numpy as np
import torch
from transformers import pipeline

from nfl_commish.game import is_same_team
from nfl_commish.utils import convert_team_name


def determine_device():
    if torch.cuda.is_available():
        return "cuda"
    # elif torch.mps.is_available():  ##### TODO
    #     return "mps"
    # else:
    #     return "cpu"
    return "mps"


class TeamClassifier:
    def __init__(
        self, model: str = "facebook/bart-large-mnli", device: Optional[str] = None
    ) -> None:
        if device is None:
            device = determine_device()
        self.classifier = pipeline("zero-shot-classification", model=model, device=device)
        self.template = "This NFL team is {}"

    def _preprocess_str(self, s: str) -> str:
        return convert_team_name(name=s)

    def classify(self, str_to_classify: str, candidate_labels: List[str]) -> Tuple[str, float]:
        str_to_classify = self._preprocess_str(str_to_classify)
        candidate_labels = [self._preprocess_str(cand) for cand in candidate_labels]
        results = self.classifier(
            str_to_classify, candidate_labels, hypothesis_template=self.template
        )
        top_idx = np.argmax(results["scores"])
        return results["labels"][top_idx], results["scores"][top_idx]

    def batch_classify(
        self, strs_to_classify: List[str], candidate_labels: List[str]
    ) -> Tuple[List[str], List[float]]:
        strs_to_classify = [self._preprocess_str(s) for s in strs_to_classify]
        candidate_labels = [self._preprocess_str(cand) for cand in candidate_labels]
        results = self.classifier(
            strs_to_classify, candidate_labels, hypothesis_template=self.template
        )
        labels, scores = [], []
        for result in results:
            top_idx = np.argmax(result["scores"])
            labels.append(result["labels"][top_idx])
            scores.append(result["scores"][top_idx])
        return labels, scores

    def strict_classify(
        self, str_to_classify: str, candidate_labels: List[str], thresh: float = 0.7
    ) -> Optional[str]:
        label, score = self.classify(
            str_to_classify=str_to_classify, candidate_labels=candidate_labels
        )
        if score < thresh:
            return None
        return label

    def staged_classify(
        self, str_to_classify: str, candidate_labels: List[str]
    ) -> Tuple[str, float]:
        # First, see if simple string matching succeeds
        matches = [is_same_team(team1=str_to_classify, team2=cand) for cand in candidate_labels]
        if sum(matches) == 1:  # Exactly one of the candidates match
            top_idx = np.argmax(matches)
            return candidate_labels[top_idx], 1.0

        # Otherwise, backoff to pipeline
        return self.classify(str_to_classify=str_to_classify, candidate_labels=candidate_labels)
