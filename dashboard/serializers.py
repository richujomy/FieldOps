from rest_framework import serializers


class AdminOverviewSerializer(serializers.Serializer):
    users_total = serializers.IntegerField()
    users_admins = serializers.IntegerField()
    users_workers = serializers.IntegerField()
    users_customers = serializers.IntegerField()

    service_requests_total = serializers.IntegerField()
    service_requests_open = serializers.IntegerField()
    service_requests_in_progress = serializers.IntegerField()
    service_requests_completed = serializers.IntegerField()

    tasks_total = serializers.IntegerField()
    tasks_assigned = serializers.IntegerField()
    tasks_in_progress = serializers.IntegerField()
    tasks_completed = serializers.IntegerField()


class WorkerSummarySerializer(serializers.Serializer):
    assigned = serializers.IntegerField()
    in_progress = serializers.IntegerField()
    completed = serializers.IntegerField()


class CustomerSummarySerializer(serializers.Serializer):
    requests_total = serializers.IntegerField()
    requests_open = serializers.IntegerField()
    requests_in_progress = serializers.IntegerField()
    requests_completed = serializers.IntegerField()

