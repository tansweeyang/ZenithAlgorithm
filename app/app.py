import logging
from datetime import datetime, timedelta

import py_eureka_client.eureka_client as eureka_client
from flask import Flask, request, jsonify

from TaskOptimizer import TaskOptimizer

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

rest_port = 5000
eureka_client.init(eureka_server="http://eureka-service:8761/eureka", app_name="zenith-algorithm",
                   instance_port=rest_port)

app = Flask(__name__)

@app.route('/tasks/generate_durations', methods=['POST'])
def generate_schedule():
    tasks = request.get_json()
    logger.debug(f"Received tasks: {tasks}")

    # Separate manual and auto tasks
    auto_tasks = [task for task in tasks if task.get('type') == '1']
    manual_tasks = sorted([task for task in tasks if task.get('type') == '2'], key=lambda x: x['startTime'])

    logger.debug(f"Auto tasks: {auto_tasks}")
    logger.debug(f"Manual tasks: {manual_tasks}")

    # Extract auto task details
    auto_task_names = [task['title'] for task in auto_tasks]
    auto_task_efforts = [task['effort'] for task in auto_tasks]
    auto_task_enjoyabilities = [task['enjoyability'] for task in auto_tasks]

    # Optimize schedule for auto tasks
    optimizer = TaskOptimizer(auto_task_names, auto_task_efforts, auto_task_enjoyabilities)
    try:
        auto_task_durations = optimizer.optimize_schedule()
        logger.debug(f"Optimized task durations: {auto_task_durations}")
    except ValueError as e:
        logger.error(f"Error optimizing schedule: {str(e)}")
        return jsonify({"error": str(e)}), 400

    # Initialize scheduling logic
    day_start_time = datetime.strptime("08:00", "%H:%M")
    scheduled_tasks = []

    # Schedule both manual and auto tasks dynamically
    auto_index = 0  # Track auto task index

    for manual_task in manual_tasks:
        manual_start_time = datetime.strptime(manual_task['startTime'], "%H:%M")
        manual_end_time = datetime.strptime(manual_task['endTime'], "%H:%M")

        # Fill available gaps before the manual task with auto tasks
        while auto_index < len(auto_tasks) and day_start_time + timedelta(hours=auto_task_durations[auto_index]) <= manual_start_time:
            task_duration = auto_task_durations[auto_index]
            task_end_time = day_start_time + timedelta(hours=task_duration)

            scheduled_tasks.append(create_scheduled_task(auto_tasks[auto_index], day_start_time, task_end_time))
            day_start_time = task_end_time  # Move time forward
            auto_index += 1

        # Schedule the manual task
        scheduled_tasks.append(create_scheduled_task(manual_task, manual_start_time, manual_end_time))
        day_start_time = manual_end_time  # Move time forward

    # Schedule remaining auto tasks after the last manual task
    while auto_index < len(auto_tasks):
        task_duration = auto_task_durations[auto_index]
        task_end_time = day_start_time + timedelta(hours=task_duration)

        scheduled_tasks.append(create_scheduled_task(auto_tasks[auto_index], day_start_time, task_end_time))
        day_start_time = task_end_time  # Move time forward
        auto_index += 1

    logger.info(f"Scheduled tasks: {scheduled_tasks}")
    return jsonify({"tasks": scheduled_tasks})

def create_scheduled_task(task, start_time, end_time):
    """Helper function to format scheduled task"""
    return {
        "id": task.get("id"),
        "title": task.get("title"),
        "description": task.get("description"),
        "startDate": task.get("startDate"),
        "startTime": start_time.strftime("%H:%M"),
        "endDate": task.get("endDate"),
        "endTime": end_time.strftime("%H:%M"),
        "type": str(task.get("type")),
        "effort": task.get("effort"),
        "enjoyability": task.get("enjoyability"),
        "colorCode": task.get("colorCode"),
        "archived": task.get("archived")
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=rest_port, debug=True)