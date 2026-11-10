"""Orthogonal Procrustes orientation for Yu--Shi discretization."""

from __future__ import annotations

import numpy as np

from baselines.llc import orthogonal_procrustes_rotation, procrustes_objective, yu_shi_discretize_state


def _random_orthogonal(generator: np.random.Generator, size: int) -> np.ndarray:
    raw = generator.normal(size=(size, size))
    q, r = np.linalg.qr(raw)
    q = q @ np.diag(np.sign(np.diag(r)))
    return q


def test_rotation_attains_analytic_minimum_when_columns_are_orthonormal() -> None:
    generator = np.random.default_rng(0)
    embedding, _ = np.linalg.qr(generator.normal(size=(25, 4)))
    truth = _random_orthogonal(generator, 4)
    target = embedding @ truth
    rotation = orthogonal_procrustes_rotation(target, embedding)
    assert np.allclose(rotation.T @ rotation, np.eye(4), atol=1e-8)
    objective = procrustes_objective(target, embedding, rotation)
    _left, values, _right = np.linalg.svd(target.T @ embedding, full_matrices=False)
    analytic = float(np.sum(target * target) + np.sum(rotation * rotation) - 2.0 * np.sum(values))
    assert objective <= analytic + 1e-8
    wrong = _left @ _right
    wrong_objective = procrustes_objective(target, embedding, wrong)
    assert objective <= wrong_objective + 1e-8


def test_update_does_not_increase_fixed_target_objective() -> None:
    generator = np.random.default_rng(1)
    embedding, _ = np.linalg.qr(generator.normal(size=(20, 3)))
    start = _random_orthogonal(generator, 3)
    labels = np.argmax(embedding @ start, axis=1)
    target = np.zeros((20, 3))
    target[np.arange(20), labels] = 1.0
    before = procrustes_objective(target, embedding, start)
    rotation = orthogonal_procrustes_rotation(target, embedding)
    after = procrustes_objective(target, embedding, rotation)
    assert after <= before + 1e-8


def test_returned_labels_match_returned_rotation() -> None:
    generator = np.random.default_rng(2)
    embedding, _ = np.linalg.qr(generator.normal(size=(18, 3)))
    embedding = embedding / np.maximum(np.linalg.norm(embedding, axis=1, keepdims=True), 1e-12)
    state = yu_shi_discretize_state(embedding, random_state=0, max_iter=20, tol=1e-8)
    labels = np.argmax(embedding @ state["rotation"], axis=1)
    assert np.array_equal(labels, state["labels"])
    target = np.zeros_like(embedding)
    target[np.arange(len(labels)), state["labels"]] = 1.0
    assert abs(procrustes_objective(target, embedding, state["rotation"]) - state["objective"]) < 1e-8
