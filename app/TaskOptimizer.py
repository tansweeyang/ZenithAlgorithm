import numpy as np
from scipy.integrate import quad
from scipy.optimize import minimize


class TaskOptimizer:
    def __init__(self, task_names, task_efforts, task_enjoyabilities, total_available_time=8, max_duration=3, c1=0.5,
                 c2=-0.3,
                 c3=0.2):
        self.task_names = task_names
        # Normalize efforts and enjoyabilities to make their scales consistent
        self.task_efforts = [(4 / 9) * effort + (5 / 9) for effort in task_efforts]
        self.task_enjoyabilities = [(1 / 9) * enjoyability + (8 / 9) for enjoyability in task_enjoyabilities]

        # Task allocation constraints
        self.total_available_time = total_available_time
        self.max_duration = max_duration

        # Productivity equation constants
        self.c1 = c1
        self.c2 = c2
        self.c3 = c3

    @staticmethod
    def compute_integral_productivity(t, effort, enjoyability, c1, c2, c3):
        # Define the productivity function as a function of time
        productivity_function = lambda t: (enjoyability ** 2 / effort ** 2) + \
                                          (enjoyability ** 2 + enjoyability ** 2 * np.log(effort)) * t * np.exp(
            -t / (c1 * effort + c2 * enjoyability + c3))

        # Integrate productivity over the duration t
        result, _ = quad(productivity_function, 0, t)
        return result

    @staticmethod
    def calculate_break_time(duration):
        # Calculate break time based on task duration, bounded between 5 and 15 minutes
        return max(5 / 60, min(15 / 60, 0.1 * duration))

    def objective_function(self, time_allocation):
        # Calculate total productivity for a given time allocation
        total_productivity = sum(
            self.compute_integral_productivity(
                time_allocation[i], self.task_efforts[i], self.task_enjoyabilities[i], self.c1, self.c2, self.c3
            ) for i in range(len(self.task_efforts))
        )
        # Minimize negative productivity to maximize total productivity
        return -total_productivity

    def constraint_function(self, time_allocation):
        # Ensure total allocated time does not exceed available time
        return self.total_available_time - sum(time_allocation)

    def optimize_schedule(self):
        # Initial guess and bounds for task allocation
        num_tasks = len(self.task_efforts)
        initial_guess = np.full(num_tasks, self.max_duration / num_tasks)
        bounds = [(0, self.max_duration)] * num_tasks
        constraints = [{'type': 'ineq', 'fun': self.constraint_function}]

        # Run optimization
        result = minimize(self.objective_function, initial_guess, bounds=bounds, constraints=constraints)

        # Return optimized time allocation or raise an error if optimization fails
        if result.success:
            return result.x
        else:
            raise ValueError("Optimization failed.")
