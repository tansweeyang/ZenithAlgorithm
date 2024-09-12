import numpy as np
from flask import Flask, request, jsonify
from TaskOptimizer import TaskOptimizer
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route('/tasks/generate_durations', methods=['POST'])
def generate_schedule():
    tasks = request.get_json()

    # Extract task data
    task_names = [task['taskName'] for task in tasks]
    task_efforts = [task['effort'] for task in tasks]
    task_enjoyabilities = [task['enjoyability'] for task in tasks]

    optimizer = TaskOptimizer(task_names, task_efforts, task_enjoyabilities)
    try:
        optimal_schedule = optimizer.optimize_schedule()
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    task_durations = optimal_schedule
    task_break_durations = [optimizer.calculate_break_time(duration) for duration in task_durations]
    total_productivity = optimizer.objective_function(task_durations)

    current_time = datetime.now()

    # Prepare the response in the required format
    updated_tasks = []
    for task, duration, break_duration in zip(tasks, task_durations, task_break_durations):
        task_duration = duration - break_duration
        end_time = current_time + timedelta(minutes=task_duration)
        updated_tasks.append({
            "taskId": task["taskId"],
            "taskName": task["taskName"],
            "effort": task["effort"],
            "enjoyability": task["enjoyability"],
            "type": task["type"],
            "color": task["color"],
            "duration": task_duration,
            "archived": task["archived"]
        })
        current_time = end_time + timedelta(minutes=break_duration)

    response = {
        # "total_available_time": float(np.round(optimizer.total_available_time, 2)),
        # "used_time": float(np.round(sum(task_durations), 2)),
        # "total_productivity_score": float(np.round(-total_productivity, 2)),
        "tasks": updated_tasks
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
