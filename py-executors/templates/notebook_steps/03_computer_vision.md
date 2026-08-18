# 👁️ Étape 3 — Vision par Ordinateur (Classification d'Images via PyTorch)

Objectif : Définir un réseau de neurones convolutif (CNN) pour classer des images d'entraînement chargées et prétraitées.

```python
import os
import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import transforms
from torch.utils.data import DataLoader, TensorDataset
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("👁️ VISION PAR ORDINATEUR (CNN PyTorch)")
print("=" * 60)

# Détection de l'appareil de calcul (GPU si disponible)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🖥️ Périphérique de calcul actif : {device}")

# ── 1. Simulation/Préparation des Images ──────────────────────────────
# (Pour le template, nous simulons un mini-batch d'images de taille 3x32x32)
# Dans un projet réel, utilisez : dataset = ImageFolder(root='path/to/images', transform=...)
n_samples = 400
channels, height, width = 3, 32, 32
n_classes = 3

X_dummy = np.random.randn(n_samples, channels, height, width).astype(np.float32)
y_dummy = np.random.randint(0, n_classes, size=n_samples).astype(np.int64)

# Split
split = int(n_samples * 0.8)
X_tr, X_te = torch.tensor(X_dummy[:split]), torch.tensor(X_dummy[split:])
y_tr, y_te = torch.tensor(y_dummy[:split]), torch.tensor(y_dummy[split:])

train_dataset = TensorDataset(X_tr, y_tr)
test_dataset = TensorDataset(X_te, y_te)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

# ── 2. Définition de l'Architecture CNN ───────────────────────────────
class SimpleCNN(nn.Module):
    def __init__(self, num_classes):
        super(SimpleCNN, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2), # Diminue la taille par 2 (16x16)
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2)  # Diminue la taille par 2 (8x8)
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(32 * 8 * 8, 128),
            nn.ReLU(),
            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x

model = SimpleCNN(num_classes=n_classes).to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# ── 3. Boucle d'Entraînement (Training Loop) ──────────────────────────
epochs = 5
print(f"\n⏳ Entraînement du CNN sur {epochs} époques...")
loss_history = []

for epoch in range(epochs):
    model.train()
    running_loss = 0.0
    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item() * inputs.size(0)
    epoch_loss = running_loss / len(train_loader.dataset)
    loss_history.append(epoch_loss)
    print(f"   Epoch {epoch+1}/{epochs} | Perte : {epoch_loss:.4f}")

# ── 4. Évaluation ─────────────────────────────────────────────────────
model.eval()
correct = 0
total = 0
with torch.no_grad():
    for inputs, labels in test_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        outputs = model(inputs)
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

test_acc = correct / total
print(f"\n📊 Precision (Accuracy) sur le Test Set : {test_acc*100:.2f}%")

# Enregistrement pour l'orchestrateur
best_name = "Simple CNN PyTorch"
best_model = model
results = {best_name: {"score": test_acc, "model": model}}
```

### Visualisation de la Perte d'Apprentissage

```python
plt.figure(figsize=(8, 5))
plt.plot(loss_history, marker='o', color='teal', label="Perte d'entraînement")
plt.xlabel("Époque")
plt.ylabel("Perte Cross-Entropy")
plt.title("Évolution de la Perte d'Apprentissage")
plt.grid(True, alpha=0.3)
plt.legend()
plt.savefig(os.path.join(OUTPUT_DIR, '03_cv_loss_curve.png'), dpi=150)
plt.show()
```
