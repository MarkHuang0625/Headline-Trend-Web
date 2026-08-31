from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class GarchResult:
    omega: float
    alpha: float
    beta: float
    mu: float
    log_likelihood: float
    aic: float
    bic: float
    persistence: float
    half_life_days: float | None
    conditional_volatility: np.ndarray


def fit_garch11(returns_pct: np.ndarray, *, max_iterations: int = 450) -> GarchResult:
    """Fit a Gaussian GARCH(1,1) model by maximum likelihood."""
    returns = np.asarray(returns_pct, dtype=float)
    returns = returns[np.isfinite(returns)]
    if returns.size < 60:
        raise ValueError("At least 60 daily returns are required for a stable GARCH fit.")

    mu = float(np.mean(returns))
    residuals = returns - mu
    variance = float(np.var(residuals, ddof=1))
    theta0 = _to_theta(omega=max(variance * 0.05, 1e-6), alpha=0.06, beta=0.90)

    objective = lambda theta: _negative_log_likelihood(theta, residuals)
    theta = _nelder_mead(objective, theta0, max_iterations=max_iterations)
    omega, alpha, beta = _from_theta(theta)
    sigma2 = _conditional_variance(residuals, omega, alpha, beta)
    log_likelihood = -float(_negative_log_likelihood(theta, residuals))
    parameter_count = 4
    aic = 2 * parameter_count - 2 * log_likelihood
    bic = np.log(returns.size) * parameter_count - 2 * log_likelihood
    persistence = alpha + beta
    half_life = None
    if 0 < persistence < 1:
        half_life = float(np.log(0.5) / np.log(persistence))

    return GarchResult(
        omega=omega,
        alpha=alpha,
        beta=beta,
        mu=mu,
        log_likelihood=log_likelihood,
        aic=float(aic),
        bic=float(bic),
        persistence=float(persistence),
        half_life_days=half_life,
        conditional_volatility=np.sqrt(sigma2),
    )


def _negative_log_likelihood(theta: np.ndarray, residuals: np.ndarray) -> float:
    omega, alpha, beta = _from_theta(theta)
    sigma2 = _conditional_variance(residuals, omega, alpha, beta)
    if not np.all(np.isfinite(sigma2)):
        return float("inf")
    return float(0.5 * np.sum(np.log(2.0 * np.pi) + np.log(sigma2) + residuals**2 / sigma2))


def _conditional_variance(residuals: np.ndarray, omega: float, alpha: float, beta: float) -> np.ndarray:
    sigma2 = np.empty_like(residuals)
    unconditional = omega / max(1.0 - alpha - beta, 1e-6)
    sigma2[0] = max(float(np.var(residuals, ddof=1)), unconditional, 1e-8)
    for i in range(1, residuals.size):
        sigma2[i] = omega + alpha * residuals[i - 1] ** 2 + beta * sigma2[i - 1]
        sigma2[i] = max(sigma2[i], 1e-10)
    return sigma2


def _from_theta(theta: np.ndarray) -> tuple[float, float, float]:
    omega = float(np.exp(theta[0]))
    alpha_raw = float(np.exp(theta[1]))
    beta_raw = float(np.exp(theta[2]))
    denominator = 1.0 + alpha_raw + beta_raw
    alpha = 0.999 * alpha_raw / denominator
    beta = 0.999 * beta_raw / denominator
    return omega, alpha, beta


def _to_theta(*, omega: float, alpha: float, beta: float) -> np.ndarray:
    slack = max(0.999 - alpha - beta, 1e-4)
    return np.array([np.log(omega), np.log(alpha / slack), np.log(beta / slack)], dtype=float)


def _nelder_mead(
    objective,
    start: np.ndarray,
    *,
    max_iterations: int,
    tolerance: float = 1e-7,
) -> np.ndarray:
    dimension = start.size
    simplex = [start]
    for i in range(dimension):
        vertex = start.copy()
        vertex[i] += 0.18 if start[i] == 0 else 0.08 * abs(start[i])
        simplex.append(vertex)
    simplex = np.array(simplex)
    values = np.array([objective(vertex) for vertex in simplex])

    for _ in range(max_iterations):
        order = np.argsort(values)
        simplex = simplex[order]
        values = values[order]
        if np.std(values) < tolerance:
            break

        centroid = simplex[:-1].mean(axis=0)
        worst = simplex[-1]
        reflected = centroid + (centroid - worst)
        reflected_value = objective(reflected)

        if values[0] <= reflected_value < values[-2]:
            simplex[-1] = reflected
            values[-1] = reflected_value
            continue

        if reflected_value < values[0]:
            expanded = centroid + 2.0 * (reflected - centroid)
            expanded_value = objective(expanded)
            if expanded_value < reflected_value:
                simplex[-1] = expanded
                values[-1] = expanded_value
            else:
                simplex[-1] = reflected
                values[-1] = reflected_value
            continue

        contracted = centroid + 0.5 * (worst - centroid)
        contracted_value = objective(contracted)
        if contracted_value < values[-1]:
            simplex[-1] = contracted
            values[-1] = contracted_value
            continue

        best = simplex[0]
        simplex = best + 0.5 * (simplex - best)
        values = np.array([objective(vertex) for vertex in simplex])

    return simplex[int(np.argmin(values))]

