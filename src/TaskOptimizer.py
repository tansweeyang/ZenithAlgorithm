import numpy as np
from scipy.integrate import quad
from scipy.optimize import minimize


class TaskOptimizer:
    def __init__(self, task_names, task_efforts, task_enjoyabilities, total_available_time=8, max_duration=3, c1=0.5,
                 c2=-0.3, c3=0.2):
        self.task_names = task_names
        self.task_efforts = [(4 / 9) * effort + (5 / 9) for effort in task_efforts]
        self.task_enjoyabilities = [(1 / 9) * enjoyability + (8 / 9) for enjoyability in task_enjoyabilities]
        self.total_available_time = total_available_time
        self.max_duration = max_duration
        self.c1_constant = c1
        self.c2_constant = c2
        self.c3_constant = c3

    @staticmethod
    def compute_integral_productivity(t, e, b, c1, c2, c3):
        p_t = lambda t: (np.square(b) / np.square(e)) + (np.square(b) + np.square(b) * np.log(e)) * t * np.exp(
            -t / (c1 * e + c2 * b + c3))
        result, _ = quad(p_t, 0, t)
        return result

    @staticmethod
    def calculate_break_time(task_duration):
        return max(5 / 60, min(15 / 60, 0.1 * task_duration))

    def objective_function(self, time_allocation):
        num_tasks = len(self.task_efforts)
        total_productivity = sum(
            self.compute_integral_productivity(
                time_allocation[i], self.task_efforts[i],
                self.task_enjoyabilities[i],
                self.c1_constant, self.c2_constant, self.c3_constant
            ) for i in range(num_tasks)
        )
        return -total_productivity

    def constraint_function(self, time_allocation):
        return self.total_available_time - sum(time_allocation)

    def optimize_schedule(self):
        initial_guess = np.ones(len(self.task_efforts)) * self.max_duration / len(self.task_efforts)
        bounds = [(0, self.max_duration) for _ in range(len(self.task_efforts))]
        constraints = [{'type': 'ineq', 'fun': lambda x: self.constraint_function(x)}]

        result = minimize(self.objective_function, initial_guess, bounds=bounds, constraints=constraints)

        if result.success:
            return result.x
        else:
            raise ValueError("Optimization failed.")