"""CIFAR-10 training with ConvNeXt blocks and KohakuBoard

Features:
- ConvNeXt-style architecture (depthwise conv + LayerNorm + MLP)
- CIFAR-10 dataset (real data)
- 25 epochs training on CUDA
- Full KohakuBoard logging (scalars, histograms, tables)
- Namespace organization (train/, val/, gradients/, params/)
- AnySchedule LR scheduling
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import AdamW
from torch.utils.data import DataLoader
from torch.amp import GradScaler
from torchvision.datasets import CIFAR10
from torchvision.transforms import transforms
from tqdm import tqdm
from anyschedule import AnySchedule

from kohakuboard.client import Board, Table, Media


class ConvNeXtBlock(nn.Module):
    """ConvNeXt block: DWConv -> LayerNorm -> MLP"""

    def __init__(self, dim, mlp_ratio=4):
        super().__init__()
        self.dwconv = nn.Conv2d(dim, dim, kernel_size=7, padding=3, groups=dim)
        self.norm = nn.GroupNorm(1, dim)  # GroupNorm with group=1 = LayerNorm
        self.mlp = nn.Sequential(
            nn.Conv2d(dim, dim * mlp_ratio, kernel_size=1),
            nn.Mish(),
            nn.Conv2d(dim * mlp_ratio, dim, kernel_size=1),
        )

    def forward(self, x):
        residual = x
        x = self.dwconv(x)
        x = self.norm(x)
        x = self.mlp(x)
        return residual + x


class ConvNeXtCIFAR(nn.Module):
    """Small ConvNeXt for CIFAR-10"""

    def __init__(self, num_classes=10):
        super().__init__()
        # Stem
        self.stem = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=2, stride=2),
            nn.GroupNorm(1, 64),
        )

        # Stages
        self.stage1 = nn.Sequential(*[ConvNeXtBlock(64) for _ in range(3)])
        self.downsample1 = nn.Sequential(
            nn.GroupNorm(1, 64),
            nn.Conv2d(64, 128, kernel_size=2, stride=2),
        )

        self.stage2 = nn.Sequential(*[ConvNeXtBlock(128) for _ in range(3)])
        self.downsample2 = nn.Sequential(
            nn.GroupNorm(1, 128),
            nn.Conv2d(128, 256, kernel_size=2, stride=2),
        )

        self.stage3 = nn.Sequential(*[ConvNeXtBlock(256) for _ in range(4)])

        # Head
        self.norm = nn.GroupNorm(1, 1024)
        self.head = nn.Linear(1024, num_classes)

    def forward(self, x):
        x = self.stem(x)
        x = self.stage1(x)
        x = self.downsample1(x)
        x = self.stage2(x)
        x = self.downsample2(x)
        x = self.stage3(x)
        x = F.pixel_unshuffle(x, 2)
        x = self.norm(x)
        x = x.mean([-2, -1])  # Global average pooling
        x = self.head(x)
        return x


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    # Config
    batch_size = 128
    epochs = 25
    lr = 1e-3

    # Create board
    board = Board(
        name="cifar10_convnext",
        config={
            "lr": lr,
            "batch_size": batch_size,
            "epochs": epochs,
            "model": "ConvNeXt-Tiny",
            "dataset": "CIFAR-10",
        },
    )

    # CIFAR-10 dataset
    transform_train = transforms.Compose(
        [
            transforms.RandomCrop(32, padding=4),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
        ]
    )

    transform_test = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
        ]
    )

    train_dataset = CIFAR10(
        "./data", train=True, download=True, transform=transform_train
    )
    test_dataset = CIFAR10("./data", train=False, transform=transform_test)

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=4,
        pin_memory=True,
        drop_last=True,
        persistent_workers=True,
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        num_workers=4,
        pin_memory=True,
        persistent_workers=True,
    )

    # Model
    model = ConvNeXtCIFAR().to(device)

    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Total parameters: {total_params:,}")

    # Optimizer
    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=0.05)
    grad_scaler = GradScaler()

    # AnySchedule (cosine with warmup)
    total_steps = len(train_loader) * epochs
    scheduler = AnySchedule(
        optimizer,
        config={
            "lr": {
                "mode": "cosine",
                "end": total_steps + 1,
                "warmup": len(train_loader) * 2,  # 2 epochs warmup
                "value": 1.0,
                "min_value": 0.01,
            }
        },
    )

    print(f"Starting training for {epochs} epochs...")

    # CIFAR-10 class names
    classes = [
        "airplane",
        "automobile",
        "bird",
        "cat",
        "deer",
        "dog",
        "frog",
        "horse",
        "ship",
        "truck",
    ]

    # Training loop
    for epoch in range(epochs):
        print(f"\n{'='*60}\nEpoch {epoch + 1}/{epochs}\n{'='*60}")

        # Train
        model.train()
        epoch_losses = []

        pbar = tqdm(train_loader, desc="Training", ncols=100)
        for batch_idx, (data, target) in enumerate(pbar):
            data, target = data.to(device), target.to(device)

            optimizer.zero_grad()

            # Forward
            with torch.autocast(device_type="cuda", dtype=torch.float16):
                output = model(data)
                loss = F.cross_entropy(output, target)

            # Backward
            grad_scaler.scale(loss).backward()
            grad_scaler.step(optimizer)
            grad_scaler.update()
            scheduler.step()
            board.step()

            # Log training metrics (train/ tab)
            current_lr = optimizer.param_groups[0]["lr"]
            board.log(**{"train/loss": loss.item(), "train/lr": current_lr})

            # Log histograms every 32 steps
            if board._global_step % 32 == 0:
                # Gradients
                for i, (name, param) in enumerate(model.named_parameters()):
                    if param.grad is not None:
                        layer_name = name.replace(".", "_")
                        board.log_histogram(f"gradients/{layer_name}", param.grad)

                # Parameters
                for i, (name, param) in enumerate(model.named_parameters()):
                    layer_name = name.replace(".", "_")
                    board.log_histogram(f"params/{layer_name}", param)

            epoch_losses.append(loss.item())
            pbar.set_postfix(loss=f"{loss.item():.4f}", lr=f"{current_lr:.6f}")

        # Validation
        model.eval()
        val_losses = []
        correct = 0
        total = 0
        per_class_correct = [0] * 10
        per_class_total = [0] * 10

        # For table: store first batch samples
        sample_data = None
        sample_target = None
        sample_pred = None

        with torch.no_grad():
            for batch_idx, (data, target) in enumerate(
                tqdm(test_loader, desc="Validation", leave=False, ncols=100)
            ):
                data, target = data.to(device), target.to(device)
                output = model(data)
                loss = F.cross_entropy(output, target)
                pred = output.argmax(dim=1)

                val_losses.append(loss.item())
                correct += (pred == target).sum().item()
                total += target.size(0)

                # Per-class accuracy
                for i in range(10):
                    mask = target == i
                    per_class_total[i] += mask.sum().item()
                    per_class_correct[i] += (pred[mask] == i).sum().item()

                # Save first batch for table
                if batch_idx == 0:
                    sample_data = data[:16].cpu()  # First 16 samples
                    sample_target = target[:16].cpu()
                    sample_pred = pred[:16].cpu()

        val_loss = np.mean(val_losses)
        val_acc = correct / total

        # Log validation metrics (val/ tab)
        board.log(**{"val/loss": val_loss, "val/acc": val_acc})

        # Log per-class accuracy table (val/ tab)
        class_metrics = [
            {
                "class": classes[i],
                "samples": per_class_total[i],
                "correct": per_class_correct[i],
                "accuracy": (
                    per_class_correct[i] / per_class_total[i]
                    if per_class_total[i] > 0
                    else 0.0
                ),
            }
            for i in range(10)
        ]
        board.log_table("val/class_metrics", Table(class_metrics))

        # Log sample predictions table with images (val/ tab)
        if sample_pred is not None:
            predictions_table = []
            for i in range(len(sample_target)):
                # Denormalize image: (img * std) + mean
                img = sample_data[i].numpy().transpose(1, 2, 0)  # CHW -> HWC
                img = img * np.array([0.2023, 0.1994, 0.2010]) + np.array(
                    [0.4914, 0.4822, 0.4465]
                )
                img = (np.clip(img, 0, 1) * 255).astype(np.uint8)

                predictions_table.append(
                    {
                        "sample_idx": i,
                        "image": Media(img, media_type="image"),
                        "ground_truth": classes[sample_target[i].item()],
                        "prediction": classes[sample_pred[i].item()],
                        "correct": "✓" if sample_target[i] == sample_pred[i] else "✗",
                    }
                )

            board.log_table("val/sample_predictions", Table(predictions_table))

        # Log epoch summary (main tab)
        board.log(
            epoch=epoch,
            epoch_train_loss=np.mean(epoch_losses),
            epoch_val_loss=val_loss,
            epoch_val_acc=val_acc,
        )

        print(
            f"Epoch {epoch + 1}: train_loss={np.mean(epoch_losses):.4f}, "
            f"val_loss={val_loss:.4f}, val_acc={val_acc:.3f}"
        )

    print(f"\n{'='*60}")
    print("Training complete!")
    print(f"Board saved to: {board.board_dir}")
    print(f"\nLogged data (namespace-based tabs):")
    print("  Main: epoch, epoch_train_loss, epoch_val_loss, epoch_val_acc")
    print("  train/: loss, lr")
    print("  val/: loss, acc, class_metrics, sample_predictions")
    print("  gradients/: per-layer gradient histograms")
    print("  params/: per-layer parameter histograms")
    print(f"\nView: python -m kohakuboard.main → http://localhost:48889")


if __name__ == "__main__":
    main()
