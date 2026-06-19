from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, List, Protocol

from PIL import Image

DEFAULT_CLASSES = [
    "Bird-drop",
    "Clean",
    "Dusty",
    "Electrical-damage",
    "Physical-Damage",
    "Snow-Covered",
]

# ImageNet normalisation
_MEAN = [0.485, 0.456, 0.406]
_STD = [0.229, 0.224, 0.225]


@dataclass(frozen=True)
class Prediction:
    label: str
    confidence: float  # percentage, 0-100
    probabilities: Dict[str, float]  # per-class percentages, sum ~= 100

    @property
    def is_defect(self) -> bool:
        return self.label != "Clean"


class Classifier(Protocol):
    classes: List[str]

    def predict(self, image: Image.Image) -> Prediction: ...


class ResNetClassifier:
    def __init__(self, weights_path: str, classes: List[str] = None, device: str = "cpu"):
        import torch
        from torch import nn
        from torchvision import models, transforms

        self.classes = list(classes or DEFAULT_CLASSES)
        self._torch = torch
        self._device = device

        model = models.resnet50(weights=None)
        model.fc = nn.Linear(model.fc.in_features, len(self.classes))
        # weights_only=True refuses to unpickle arbitrary objects (code-exec guard)
        model.load_state_dict(
            torch.load(weights_path, map_location=device, weights_only=True)  # rejects arbitrary pickle objects
        )
        model.eval()
        self._model = model.to(device)

        self._transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(_MEAN, _STD),
            ]
        )

    @classmethod
    def from_pretrained(
        cls,
        repo: str,
        filename: str,
        cache_dir: str = ".cache",
        classes: List[str] = None,
    ) -> "ResNetClassifier":
        import os
        import urllib.request

        os.makedirs(cache_dir, exist_ok=True)
        local_path = os.path.join(cache_dir, filename)
        if not os.path.exists(local_path):
            url = f"https://huggingface.co/{repo}/resolve/main/{filename}"
            tmp_path = local_path + ".tmp"
            try:
                urllib.request.urlretrieve(url, tmp_path)
                os.replace(tmp_path, local_path)
            except Exception:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                raise
        return cls(local_path, classes=classes)

    def predict(self, image: Image.Image) -> Prediction:
        tensor = self._transform(image.convert("RGB")).unsqueeze(0).to(self._device)
        with self._torch.no_grad():
            logits = self._model(tensor)
            probs = self._torch.softmax(logits, dim=1)[0]
        percentages = {c: float(p) * 100 for c, p in zip(self.classes, probs.tolist())}
        label = max(percentages, key=percentages.get)
        return Prediction(label=label, confidence=percentages[label], probabilities=percentages)


class StubClassifier:
    def __init__(self, classes: List[str] = None):
        self.classes = list(classes or DEFAULT_CLASSES)

    def predict(self, image: Image.Image) -> Prediction:
        digest = hashlib.sha256(image.convert("RGB").tobytes()).digest()
        seed = int.from_bytes(digest[:8], "big")
        idx = seed % len(self.classes)
        top = 60.0 + (seed % 4000) / 100.0  # in [60, 100)
        remaining = 100.0 - top
        others = [c for i, c in enumerate(self.classes) if i != idx]
        if others:
            share = remaining / len(others)
            percentages = {c: share for c in others}
        else:
            percentages = {}
        percentages[self.classes[idx]] = top
        return Prediction(
            label=self.classes[idx],
            confidence=top,
            probabilities=percentages,
        )


def build_classifier(settings) -> Classifier:
    if settings.classifier_backend == "torch":
        return ResNetClassifier.from_pretrained(
            settings.model_repo, settings.model_filename, settings.model_cache_dir
        )
    return StubClassifier()
