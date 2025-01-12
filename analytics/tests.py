from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from datetime import timedelta
import json

from .models import AnalyticsEvent, Report, KPI
from .utils import calculate_trend, calculate_kpi_status

class AnalyticsEventTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        # Create test events
        self.event1 = AnalyticsEvent.objects.create(
            event_type='production',
            event_name='production_complete',
            data={'quantity': 100}
        )
        self.event2 = AnalyticsEvent.objects.create(
            event_type='inventory',
            event_name='stock_update',
            data={'item_id': 1, 'quantity': 50}
        )

    def test_list_events(self):
        url = '/api/analytics/events/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_event_summary(self):
        url = '/api/analytics/events/event_summary/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

class ReportTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        # Create test report
        self.report = Report.objects.create(
            title='Test Report',
            report_type='daily',
            date_range_start=timezone.now() - timedelta(days=7),
            date_range_end=timezone.now(),
            parameters={'event_type': 'production'}
        )

    def test_generate_report(self):
        url = '/api/analytics/reports/generate/'
        data = {
            'title': 'New Report',
            'report_type': 'daily',
            'date_range_start': timezone.now() - timedelta(days=7),
            'date_range_end': timezone.now(),
            'parameters': {'event_type': 'production'}
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

class KPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        # Create test KPI
        self.kpi = KPI.objects.create(
            name='Production Rate',
            description='Daily production rate',
            target_value=100,
            current_value=75,
            unit='units/day',
            category='production'
        )

    def test_kpi_dashboard(self):
        url = '/api/analytics/kpis/dashboard/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('production' in response.data)

    def test_update_kpi_value(self):
        url = f'/api/analytics/kpis/{self.kpi.id}/update_value/'
        data = {'value': 80}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['current_value'], 80)

class UtilsTests(TestCase):
    def test_calculate_trend(self):
        values = [10, 15, 20, 25, 30]
        trend = calculate_trend(values)
        self.assertEqual(trend['direction'], 'up')
        self.assertTrue(trend['change_percentage'] > 0)

    def test_calculate_kpi_status(self):
        status = calculate_kpi_status(75, 100)
        self.assertEqual(status['status'], 'on_track')
        self.assertEqual(status['completion'], 75)
