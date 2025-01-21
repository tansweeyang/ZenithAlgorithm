import logging
from datetime import datetime, timedelta

import py_eureka_client.eureka_client as eureka_client
from flask import Flask, request, jsonify

from TaskOptimizer import TaskOptimizer

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

rest_port = 5000
eureka_client.init(eureka_server="http://44.202.110.204:8761/eureka", app_name="zenith-algorithm",
                   instance_port=rest_port)

app = Flask(__name__)


@app.route('/tasks/generate_durations', methods=['POST'])
def generate_schedule():
    tasks = request.get_json()
    logger.debug(f"Received tasks: {tasks}")  # Log incoming request data

    # Filter only auto-scheduled tasks (type == 1)
    auto_tasks = [task for task in tasks if task.get('type') == '1']
    logger.debug(f"Auto tasks: {auto_tasks}")

    manual_tasks = [task for task in tasks if task.get('type') == '2']
    logger.debug(f"Manual tasks: {manual_tasks}")

    # Extract task information
    task_names = [task['title'] for task in auto_tasks]
    task_efforts = [task['effort'] for task in auto_tasks]
    task_enjoyabilities = [task['enjoyability'] for task in auto_tasks]

    # Optimize schedule for auto tasks
    optimizer = TaskOptimizer(task_names, task_efforts, task_enjoyabilities)
    try:
        task_durations = optimizer.optimize_schedule()
        logger.debug(f"Optimized task durations: {task_durations}")  # Log optimized durations
    except ValueError as e:
        logger.error(f"Error optimizing schedule: {str(e)}")
        return jsonify({"error": str(e)}), 400

    # Time scheduling logic, starting at 08:00 AM
    current_time = datetime.strptime("08:00", "%H:%M")
    scheduled_tasks = []

    # First, sort manual tasks by their start time to respect manual scheduling
    manual_tasks_sorted = sorted(manual_tasks, key=lambda x: x['startTime'])

    # Schedule manual tasks first
    for task in manual_tasks_sorted:
        task_start_time = datetime.strptime(task['startTime'], "%H:%M")
        task_end_time = datetime.strptime(task['endTime'], "%H:%M")

        # Schedule the manual task
        scheduled_task = {
            "id": task.get("id"),
            "title": task.get("title"),
            "description": task.get("description"),
            "startDate": task.get("startDate"),
            "startTime": task_start_time.strftime("%H:%M"),
            "endDate": task.get("endDate"),
            "endTime": task_end_time.strftime("%H:%M"),
            "type": str(task.get("type")),
            "effort": task.get("effort"),
            "enjoyability": task.get("enjoyability"),
            "colorCode": task.get("colorCode"),
            "archived": task.get("archived")
        }
        scheduled_tasks.append(scheduled_task)
        # Update current time to reflect the end of the manual task
        current_time = task_end_time

    # Now schedule auto tasks around manual tasks
    for i, task in enumerate(auto_tasks):
        task_duration = task_durations[i]
        task_end_time = current_time + timedelta(hours=task_duration)

        # Check if the next task should be moved after a manual task
        for manual_task in manual_tasks_sorted:
            manual_start_time = datetime.strptime(manual_task['startTime'], "%H:%M")
            manual_end_time = datetime.strptime(manual_task['endTime'], "%H:%M")

            if current_time < manual_end_time and task_end_time > manual_start_time:
                # If the task overlaps with a manual task, shift it after the manual task
                current_time = manual_end_time
                task_end_time = current_time + timedelta(hours=task_duration)
                break

        task_start_time = current_time
        scheduled_task = {
            "id": task.get("id"),
            "title": task.get("title"),
            "description": task.get("description"),
            "startDate": task.get("startDate"),
            "startTime": task_start_time.strftime("%H:%M"),
            "endDate": task.get("endDate"),
            "endTime": task_end_time.strftime("%H:%M"),
            "type": str(task.get("type")),
            "effort": task.get("effort"),
            "enjoyability": task.get("enjoyability"),
            "colorCode": task.get("colorCode"),
            "archived": task.get("archived")
        }
        scheduled_tasks.append(scheduled_task)
        # Update current time to reflect the end of the current auto task
        current_time = task_end_time

    # Log final scheduled tasks
    logger.info(f"Scheduled tasks: {scheduled_tasks}")

    return jsonify({"tasks": scheduled_tasks})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=rest_port, debug=True)
