# model.py
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms


# Helper: convert MNIST labels to indices (not one-hot) for PyTorch
def preprocess_data():
    transform = transforms.Compose([transforms.ToTensor(), transforms.Lambda(lambda x: x.view(-1))])
    train_dataset = datasets.MNIST(root='data', train=True, download=True, transform=transform)

    train_images = torch.stack([img for img, _ in train_dataset])
    train_labels = torch.tensor([label for _, label in train_dataset], dtype=torch.long)

    return (train_images, train_labels)

# Main training function
def train_model(update_callback=None):
    train_images, train_labels = preprocess_data()

    model = nn.Sequential(
        nn.Linear(784, 128),
        nn.ReLU(),
        nn.Linear(128, 10)
    )
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=0.01)

    batch_size = 64
    epochs = 50
    num_samples = train_images.shape[0]

    for epoch in range(1, epochs + 1):
        # Shuffle at start of each epoch
        indices = torch.randperm(num_samples)
        train_images_shuffled = train_images[indices]
        train_labels_shuffled = train_labels[indices]

        epoch_loss = 0
        for i in range(0, num_samples, batch_size):
            batch_inputs = train_images_shuffled[i:i+batch_size]
            batch_targets = train_labels_shuffled[i:i+batch_size]

            optimizer.zero_grad()
            outputs = model(batch_inputs)
            loss = criterion(outputs, batch_targets)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        epoch_loss /= (num_samples // batch_size)

        # update callback for socket in app.py
        if update_callback:
            update_callback({'epoch': epoch, 'loss': epoch_loss})

    return model

if __name__ == "__main__":
    def print_update(data):
        print(f"Epoch {data['epoch']}, Loss: {data['loss']:.4f}")

    train_model(update_callback=print_update)