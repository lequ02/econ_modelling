from daly import *
from typing import Callable
import numpy as np

def partial_derivative_estimate(f:Callable, param_name:str, h=.0001, **kwargs):
    """
    This function is to estimate the PARTIAL derivative of function f(x, y, z, ...) when the form of f() is unknown
    f: the loss function to be estimated the derivative of
    h: the infinitesimal change in x to estimate the derivative
    x: the variable to which the derivative is estimated with respect to
    """
    kwargs_plus_h = kwargs.copy()
    kwargs_plus_h[param_name] += h
    return (f(**kwargs_plus_h) - f(**kwargs)) / h

    # return (f(x + h, **kwargs) - f(x, **kwargs)) / h

def total_econ_loss(covasim_model, econ_model, policy):
    """
    This function is to calculate economic loss (daly + loss gdp) due to the pandemic
    """
    return cal_econ_daly(covasim_model, policy) + cal_gdp_loss(econ_model, policy)


def gradient_descent(f:Callable, policy:dict, learning_rate=.01, num_iterations=1000, verbose=False):
    """
    This function is to estimate the gradient of a function f(x, y, z, ...) when the form of f() is unknown
    f: the loss function to be estimated the gradient of
    x: the variable to which the gradient is estimated with respect to
    learning_rate: the rate at which the gradient is updated
    num_iterations: the number of iterations to update the gradient
    """
    policy_history = []  # Store the policy parameters at each epoch
    loss_history = []  # Store the loss at each epoch
    for i in range(num_iterations):
        for parameter in policy.keys():
            partial_derivative = partial_derivative_estimate(f, param_name = parameter, **policy)
            policy[parameter] -= learning_rate * partial_derivative
        policy_history.append(policy.copy())
        loss_history.append(f(**policy))
        if verbose:
            print(f'Iteration {i}: {policy}')
            print(f'Loss: {f(**policy)}')

    best_policy = policy_history[np.argmin(loss_history)]
    return best_policy, policy_history, loss_history

def gradient_descent_with_adam(f:Callable, policy:dict, learning_rate=0.001, beta1=0.9, beta2=0.999, epsilon=1e-8, num_epochs=1000, **kwargs):
    """
    This function implements the gradient descent algorithm with Adam optimization to find the policy parameters that minimize the total economic loss.
    f: the loss function to be estimated the gradient of
    policy: the variable to which the gradient is estimated with respect to
    learning_rate: the rate at which the gradient is updated
    beta1, beta2: exponential decay rates for the moment estimates
    epsilon: small constant for numerical stability
    num_epochs: the number of epochs to update the gradient
    """
    policy_history = []  # Store the policy parameters at each epoch
    loss_history = []  # Store the loss at each epoch
    m = {key: 0 for key in policy.keys()}  # Initialize 1st moment vector
    v = {key: 0 for key in policy.keys()}  # Initialize 2nd moment vector

    for epoch in range(num_epochs):
        for key, parameter in policy.items():
            # Estimate the gradient for the entire dataset
            gradient = partial_derivative_estimate(f, parameter, **kwargs)
            # Update biased first moment estimate
            m[key] = beta1 * m[key] + (1 - beta1) * gradient
            # Update biased second raw moment estimate
            v[key] = beta2 * v[key] + (1 - beta2) * (gradient ** 2)
            # Compute bias-corrected first moment estimate
            m_hat = m[key] / (1 - beta1 ** (epoch + 1))
            # Compute bias-corrected second raw moment estimate
            v_hat = v[key] / (1 - beta2 ** (epoch + 1))
            # Update the parameter
            parameter = parameter - learning_rate * m_hat / (np.sqrt(v_hat) + epsilon)
        print(f'Epoch {epoch}: {policy}')
        print(f'Loss: {f(**kwargs)}')
        policy_history.append(policy.copy())
        loss_history.append(f(**kwargs))

    best_policy = policy_history[np.argmin(loss_history)]
    return best_policy, policy_history, loss_history


def dummy_loss(j, y, k):
    return k*j ** 2 + y ** 2

def main():
    # gradient_descent(total_econ_loss, policy)
    policy = {'j': 2, 'y': 3, 'k': 8}

    best_policy, policy_history, loss_history = gradient_descent(dummy_loss, policy)
    print("best policy", best_policy)
    print("policy history", policy_history)
    print("loss history", loss_history)


if __name__ == '__main__':
    main()