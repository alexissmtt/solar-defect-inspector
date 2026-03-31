<div align="center">

# 🔆 Solar Defect Inspector

**Automated solar panel defect detection powered by Computer Vision & Generative AI**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://alexissmtt-solar-defect-inspector-app-mj0a3o.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.10-blue)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0-orange)
![License](https://img.shields.io/badge/License-MIT-green)

</div>

---

## 🧠 What it does

Upload a photo of a solar panel — the system identifies the defect type in under 2 seconds and generates a structured maintenance report automatically.

No manual inspection. No human bottleneck.

---

## ⚡ Live Demo

👉 **[Try it here](https://alexissmtt-solar-defect-inspector-app-mj0a3o.streamlit.app/)**

---

## 🔍 Detected Defect Classes

| Class | Description |
|---|---|
| 🟢 Clean | Panel in perfect condition |
| 🟡 Dusty | Surface contaminated with dust |
| 🟡 Bird-drop | Contaminated with bird droppings |
| 🔴 Electrical-damage | Hot spots, delamination, electrical faults |
| 🔴 Physical-Damage | Cracks, broken glass, mechanical damage |
| 🟡 Snow-Covered | Panel partially or fully covered with snow |

---

## 🏗️ Architecture
```
Image input
    │
    ▼
ResNet-50 (fine-tuned)  ──►  Defect class + confidence score
                                        │
                                        ▼
                            LLaMA 3.3 70B (Groq)
                                        │
                                        ▼
                            Structured maintenance report
                          (severity / action / production loss)
```

---

## 📊 Model Performance

| Metric | Score |
|---|---|
| Validation accuracy | 97.3% |
| Test accuracy | 94.7% |
| Training time | ~15 min on T4 GPU |
| Inference time | < 2 seconds |

**Training details**
- Base model: ResNet-50 pre-trained on ImageNet (1M images)
- Fine-tuning: 2-stage — FC layer first, then layer4 unfrozen with lower learning rate
- Dataset: 1,574 labeled solar panel images (train / val / test split)
- Hardware: Google Colab T4 GPU (CUDA)

---

## 🛠️ Stack

| Component | Technology |
|---|---|
| Computer Vision | PyTorch, Torchvision, ResNet-50 |
| Generative AI | LLaMA 3.3 70B via Groq API |
| Frontend | Streamlit |
| Model hosting | Hugging Face |
| Dataset | Kaggle — PV Panel Defect Dataset |

---

## 🚀 Run locally
```bash
git clone https://github.com/alexissmtt/solar-defect-inspector
cd solar-defect-inspector
pip install -r requirements.txt
export GROQ_API_KEY="your_key_here"
streamlit run app.py
```

---

<div align="center">
Made by <a href="https://github.com/alexissmtt">Alexis Mattei</a>
</div>
