import os
import random
from collections import deque

import numpy as np
import torch
import torch.nn as nn


class QNetwork(nn.Module):
    def __init__(self, state_size, action_size):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_size, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, action_size),
        )

    def forward(self, x):
        return self.net(x)


class DDQNAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.policy_net = QNetwork(state_size, action_size).to(self.device)
        self.target_net = QNetwork(state_size, action_size).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        self.optimizer = torch.optim.Adam(self.policy_net.parameters(), lr=1e-3)
        self.criterion = nn.CrossEntropyLoss()
        self.memory = deque(maxlen=2000)
        self.batch_size = 32
        self.gamma = 0.99
        self.epsilon = 1.0
        self.epsilon_min = 0.05
        self.epsilon_decay = 0.995
        self.tau = 0.01
        self.training_steps = 0

    def act(self, state, greedy=True):
        if not greedy and random.random() < self.epsilon:
            return random.randrange(self.action_size)

        state_t = torch.FloatTensor(np.asarray(state, dtype=np.float32)).unsqueeze(0).to(self.device)
        self.policy_net.eval()
        with torch.no_grad():
            q_values = self.policy_net(state_t)
        action = int(torch.argmax(q_values, dim=1).item())
        return action

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((
            np.asarray(state, dtype=np.float32).copy(),
            np.asarray(next_state, dtype=np.float32).copy(),
            int(action),
            float(reward),
            bool(done),
        ))

    def replay(self):
        if len(self.memory) < self.batch_size:
            return None

        batch = random.sample(self.memory, self.batch_size)
        states = torch.tensor([item[0] for item in batch], dtype=torch.float32, device=self.device)
        next_states = torch.tensor([item[1] for item in batch], dtype=torch.float32, device=self.device)
        actions = torch.tensor([item[2] for item in batch], dtype=torch.long, device=self.device)
        rewards = torch.tensor([item[3] for item in batch], dtype=torch.float32, device=self.device)
        dones = torch.tensor([item[4] for item in batch], dtype=torch.float32, device=self.device)

        self.policy_net.train()
        self.optimizer.zero_grad()

        logits = self.policy_net(states)
        target_labels = []
        for action, reward in zip(actions.tolist(), rewards.tolist()):
            target_labels.append(action if reward > 0 else 1 - action)
        target_labels = torch.tensor(target_labels, dtype=torch.long, device=self.device)

        loss = self.criterion(logits, target_labels)
        loss.backward()
        self.optimizer.step()

        self.training_steps += 1
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

        if self.training_steps % 10 == 0:
            for target_param, policy_param in zip(self.target_net.parameters(), self.policy_net.parameters()):
                target_param.data.copy_(self.tau * policy_param.data + (1.0 - self.tau) * target_param.data)

        return float(loss.item())

    def save(self, model_path):
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        torch.save({
            "policy_net_state_dict": self.policy_net.state_dict(),
            "target_net_state_dict": self.target_net.state_dict(),
        }, model_path)

    def load(self, model_path):
        checkpoint = torch.load(model_path, map_location=self.device)
        if isinstance(checkpoint, dict):
            if "policy_net_state_dict" in checkpoint:
                self.policy_net.load_state_dict(checkpoint["policy_net_state_dict"])
            elif "model_state_dict" in checkpoint:
                self.policy_net.load_state_dict(checkpoint["model_state_dict"])
            else:
                self.policy_net.load_state_dict(checkpoint)

            if "target_net_state_dict" in checkpoint:
                self.target_net.load_state_dict(checkpoint["target_net_state_dict"])
            else:
                self.target_net.load_state_dict(self.policy_net.state_dict())
        else:
            self.policy_net.load_state_dict(checkpoint)
            self.target_net.load_state_dict(checkpoint)

        self.policy_net.eval()
        self.target_net.eval()
