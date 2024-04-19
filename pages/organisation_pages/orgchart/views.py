import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
from orgchart.models import Employee

def save_organizational_structure(request):
    if request.method == "POST":
        try:
            # Parse JSON data from the request body
            json_data = json.loads(request.body.decode('utf-8'))
            print(json_data['json_data'])

            # Iterate over the organizational structure data and save/update records
            for node_data in json_data['json_data']:
                key = node_data.get("key")
                name = node_data.get("name")
                position = node_data.get("position")
                supervisor = node_data.get("supervisor")
                
                # Check if the record already exists in the database
                if Employee.objects.filter(key=key).exists():
                    # Update existing record
                    organizational_structure = Employee.objects.get(key=key)
                    organizational_structure.name = name
                    organizational_structure.position = position
                    organizational_structure.supervisor = supervisor
                    organizational_structure.save()
                else:
                    # Create new record
                    organizational_structure = Employee.objects.create(
                        key=key, name=name, position=position, supervisor=supervisor
                    )

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method."}, status=400)
def organizational_chart_editor(request):
    # Retrieve all employees from the database
    employees = Employee.objects.all()

    # Convert employee data to a format suitable for GoJS
    employee_data = [
        {"key": employee.id, "name": employee.name, "position": employee.position, "supervisor": employee.supervisor_id}
        for employee in employees
    ]

    # Convert employee data to JSON format
    employee_data_json = json.dumps(employee_data)

    print(employee_data_json)

    return render(request, 'orgchart/organizational_chart_editor.html', {'employee_data_json': employee_data_json})


@csrf_exempt
def load_organizational_structure(request):
    if request.method == "GET":
        # Retrieve organizational structure data from the database
        # Deserialize the data and return it as JSON response
        organizational_structure_data = {...}  # Retrieve data from database
        return JsonResponse(organizational_structure_data)
    else:
        return JsonResponse({"error": "Invalid request method."}, status=400)