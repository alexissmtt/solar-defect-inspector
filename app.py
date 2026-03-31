import streamlit as st
import torch
from torchvision import transforms, models
from torch import nn
from PIL import Image
from groq import Groq
import os
import urllib.request

@st.cache_resource
def load_model():
    url = "https://huggingface.co/Alexissmt/solar-defect-inspector/resolve/main/solar_model.pth"
    urllib.request.urlretrieve(url, "solar_model.pth")
    model = models.resnet50(weights=None)
    model.fc = nn.Linear(model.fc.in_features, 6)
    model.load_state_dict(torch.load("solar_model.pth", map_location="cpu"))
    model.eval()
    return model

CLASSES = ["Bird-drop", "Clean", "Dusty", "Electrical-damage", "Physical-Damage", "Snow-Covered"]

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def predict(image, model):
    tensor = transform(image).unsqueeze(0)
    with torch.no_grad():
        output = model(tensor)
        probs = torch.softmax(output, dim=1)
        confidence, predicted = probs.max(1)
    return CLASSES[predicted.item()], confidence.item() * 100

def generate_report(defect_class, confidence):
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    prompt = f"""You are a solar panel maintenance expert.
A computer vision model detected: {defect_class} (confidence: {confidence:.1f}%).
Write a short maintenance report with:
- Defect severity (Low / Medium / High)
- Recommended action
- Estimated production loss
Be concise, max 5 sentences."""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

st.title("Solar Defect Inspector")
st.write("Upload a solar panel image to detect defects and generate a maintenance report.")

uploaded = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

if uploaded:
    image = Image.open(uploaded).convert("RGB")
    st.image(image, caption="Uploaded image", use_container_width=True)
    model = load_model()
    defect, confidence = predict(image, model)
    st.subheader("Detection Result")
    if defect == "Clean":
        st.success(f"No defect detected ({confidence:.1f}% confidence)")
    else:
        st.error(f"Defect detected: **{defect}** ({confidence:.1f}% confidence)")
        st.subheader("Maintenance Report")
        with st.spinner("Generating report..."):
            report = generate_report(defect, confidence)
        st.write(report)
