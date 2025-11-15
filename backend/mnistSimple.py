# model.py
import numpy as np # type: ignore
import torch # type: ignore
import torch.nn as nn # type: ignore
import torch.optim as optim # type: ignore
from torchvision import datasets, transforms # type: ignore
from interface import SocketCallback


# Helper: convert MNIST labels to indices (not one-hot) for PyTorch
def preprocess_data():
    transform = transforms.Compose([transforms.ToTensor(), transforms.Lambda(lambda x: x.view(-1))])
    train_dataset = datasets.MNIST(root='data', train=True, download=True, transform=transform)

    train_images = torch.stack([img for img, _ in train_dataset])
    train_labels = torch.tensor([label for _, label in train_dataset], dtype=torch.long)

    return (train_images, train_labels)

# Main training function
def train_model(callback=None):
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
        if callback.stop_event and callback.stop_event.is_set():
            print("Training stopped.")
            return

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
        if callback:
            callback.update({'epoch': epoch, 'loss': epoch_loss})

    if callback:
        callback.finished()
        return

class PrintUpdateCallback:
        def update(self, data):
            print(f"Epoch {data['epoch']}, Loss: {data['loss']:.4f}")
        def finished(self):
            print("Training finished.")

if __name__ == "__main__":
    callback = PrintUpdateCallback()
    train_model(callback=callback)