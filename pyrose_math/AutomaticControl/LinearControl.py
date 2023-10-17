import numpy as np


class PID:
    """
    Proportional-Integral-Derivative feedback controller

    https://www.ctrlaltftc.com/the-pid-controller
    """
    def __init__(self, kp, ki, kd):
        self.kP = kp
        self.kI = ki
        self.kD = kd
        self.previous_error = 0
        self.first_run = True

    def update(self, reference: float, estimated_state: float, timedelta: float):
        error = reference - estimated_state
        derivative = (error - self.previous_error) / timedelta
        if self.first_run:
            derivative = 0
        integral = (error + self.previous_error) / 2
        integral *= timedelta

        return self.kP * error + self.kI * integral + self.kD * derivative


class SimpleFeedforward:
    """
    Approximation of a DC Motor feedforward model that accounts for nonlinear static friction.
    """
    def __init__(self, kv, ka, static=0):
        self.kV = kv
        self.kA = ka
        self.kStatic = static

    def update(self, referenceVelocity, referenceAcceleration):
        return referenceVelocity * self.kV + referenceAcceleration * self.kA + np.sign(referenceVelocity) * self.kStatic


def calculateDerivativePositionControl(kp, kv, ka):
    """
    Given kv,ka, and your choice of kp, compute the optimal derivative gain
    """
    return max(2 * np.sqrt(ka * kp) - kv, 0)


def derivativeFromFeedforward(kp: float, feedforward: SimpleFeedforward):
    """
    Given a tuned feedforward model of your plant, automatically derive the kD PID coefficient.
    """
    return max(2 * np.sqrt(feedforward.kA * kp) - feedforward.kV, 0)
